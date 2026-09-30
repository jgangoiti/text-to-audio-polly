import os

# Deben fijarse ANTES de importar el handler: se leen a nivel de módulo
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("DEFAULT_VOICE_ID", "Lucia")
os.environ.setdefault("DEFAULT_ENGINE", "neural")
os.environ.setdefault("DEFAULT_LANGUAGE_CODE", "es-ES")
os.environ.setdefault("OUTPUT_BUCKET", "output-bucket-test")

from unittest.mock import patch

import boto3
from moto import mock_aws

from src.lambda_handler import handler


def _make_bucket_with_object(key: str, body: bytes, bucket: str = "source-bucket"):
    s3 = boto3.client("s3", region_name="eu-west-1")
    s3.create_bucket(
        Bucket=bucket,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )
    s3.put_object(Bucket=bucket, Key=key, Body=body)
    return bucket


def _event(bucket: str, key: str) -> dict:
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {"key": key},
                }
            }
        ]
    }


@mock_aws
def test_lambda_handler_happy_path_spanish():
    bucket = _make_bucket_with_object(
        "notas/hola.txt", "Hola, esto es una prueba".encode("utf-8")
    )
    event = _event(bucket, "notas/hola.txt")

    fake_task = {"SynthesisTask": {"TaskId": "abc123", "TaskStatus": "scheduled"}}

    with patch.object(handler, "comprehend") as mock_comprehend, \
         patch.object(handler, "polly") as mock_polly:

        mock_comprehend.detect_dominant_language.return_value = {
            "Languages": [{"LanguageCode": "es", "Score": 0.98}]
        }
        mock_polly.start_speech_synthesis_task.return_value = fake_task

        result = handler.lambda_handler(event, context=None)

    assert result == {"statusCode": 200}
    mock_polly.start_speech_synthesis_task.assert_called_once()
    _, kwargs = mock_polly.start_speech_synthesis_task.call_args
    assert kwargs["VoiceId"] == "Lucia"
    assert kwargs["LanguageCode"] == "es-ES"
    assert kwargs["OutputS3KeyPrefix"] == "notas/hola"


@mock_aws
def test_lambda_handler_low_confidence_falls_back_to_default():
    bucket = _make_bucket_with_object("dudoso.txt", "xyz abc 123".encode("utf-8"))
    event = _event(bucket, "dudoso.txt")

    with patch.object(handler, "comprehend") as mock_comprehend, \
         patch.object(handler, "polly") as mock_polly:

        # Comprehend detecta inglés pero con confianza por debajo del umbral (0.5)
        mock_comprehend.detect_dominant_language.return_value = {
            "Languages": [{"LanguageCode": "en", "Score": 0.3}]
        }
        mock_polly.start_speech_synthesis_task.return_value = {
            "SynthesisTask": {"TaskId": "id1", "TaskStatus": "scheduled"}
        }

        handler.lambda_handler(event, context=None)

    _, kwargs = mock_polly.start_speech_synthesis_task.call_args
    assert kwargs["VoiceId"] == os.environ["DEFAULT_VOICE_ID"]
    assert kwargs["LanguageCode"] == os.environ["DEFAULT_LANGUAGE_CODE"]


@mock_aws
def test_lambda_handler_unsupported_language_falls_back_to_default():
    bucket = _make_bucket_with_object("japones.txt", "こんにちは".encode("utf-8"))
    event = _event(bucket, "japones.txt")

    with patch.object(handler, "comprehend") as mock_comprehend, \
         patch.object(handler, "polly") as mock_polly:

        # Alta confianza, pero "ja" no está en VOICE_MAP
        mock_comprehend.detect_dominant_language.return_value = {
            "Languages": [{"LanguageCode": "ja", "Score": 0.99}]
        }
        mock_polly.start_speech_synthesis_task.return_value = {
            "SynthesisTask": {"TaskId": "id2", "TaskStatus": "scheduled"}
        }

        handler.lambda_handler(event, context=None)

    _, kwargs = mock_polly.start_speech_synthesis_task.call_args
    assert kwargs["VoiceId"] == os.environ["DEFAULT_VOICE_ID"]
    assert kwargs["LanguageCode"] == os.environ["DEFAULT_LANGUAGE_CODE"]


@mock_aws
def test_lambda_handler_skips_empty_file():
    bucket = _make_bucket_with_object("vacio.txt", "   \n  ".encode("utf-8"))
    event = _event(bucket, "vacio.txt")

    with patch.object(handler, "comprehend") as mock_comprehend, \
         patch.object(handler, "polly") as mock_polly:

        result = handler.lambda_handler(event, context=None)

    assert result == {"statusCode": 200}
    mock_comprehend.detect_dominant_language.assert_not_called()
    mock_polly.start_speech_synthesis_task.assert_not_called()


@mock_aws
def test_lambda_handler_comprehend_exception_falls_back_to_default():
    bucket = _make_bucket_with_object("error.txt", "algo de texto".encode("utf-8"))
    event = _event(bucket, "error.txt")

    with patch.object(handler, "comprehend") as mock_comprehend, \
         patch.object(handler, "polly") as mock_polly:

        mock_comprehend.detect_dominant_language.side_effect = Exception("Comprehend caído")
        mock_polly.start_speech_synthesis_task.return_value = {
            "SynthesisTask": {"TaskId": "id3", "TaskStatus": "scheduled"}
        }

        result = handler.lambda_handler(event, context=None)

    assert result == {"statusCode": 200}
    _, kwargs = mock_polly.start_speech_synthesis_task.call_args
    assert kwargs["VoiceId"] == os.environ["DEFAULT_VOICE_ID"]
    assert kwargs["LanguageCode"] == os.environ["DEFAULT_LANGUAGE_CODE"]


@mock_aws
def test_lambda_handler_truncates_text_exceeding_max_chars():
    long_text = "a" * (handler.MAX_CHARS + 5000)  # supera el límite de Polly
    bucket = _make_bucket_with_object("largo.txt", long_text.encode("utf-8"))
    event = _event(bucket, "largo.txt")

    with patch.object(handler, "comprehend") as mock_comprehend, \
         patch.object(handler, "polly") as mock_polly:

        mock_comprehend.detect_dominant_language.return_value = {
            "Languages": [{"LanguageCode": "es", "Score": 0.98}]
        }
        mock_polly.start_speech_synthesis_task.return_value = {
            "SynthesisTask": {"TaskId": "id4", "TaskStatus": "scheduled"}
        }

        handler.lambda_handler(event, context=None)

    _, kwargs = mock_polly.start_speech_synthesis_task.call_args
    assert len(kwargs["Text"]) == handler.MAX_CHARS