import os

os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("TOPIC_ARN", "arn:aws:sns:eu-west-1:123456789012:test-topic")

from unittest.mock import patch

import boto3
from moto import mock_aws

from src.notifier_handler import handler


def _create_bucket(bucket: str = "output-bucket"):
    s3 = boto3.client("s3", region_name="eu-west-1")
    s3.create_bucket(
        Bucket=bucket,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )
    return bucket


def _put_object(bucket: str, key: str, body: bytes = b"contenido falso de audio"):
    s3 = boto3.client("s3", region_name="eu-west-1")
    s3.put_object(Bucket=bucket, Key=key, Body=body)


def _event(*records):
    return {
        "Records": [
            {"s3": {"bucket": {"name": bucket}, "object": {"key": key}}}
            for bucket, key in records
        ]
    }


@mock_aws
def test_notifier_happy_path_publishes_message_with_url():
    bucket = _create_bucket()
    _put_object(bucket, "notas/hola.mp3")
    event = _event((bucket, "notas/hola.mp3"))

    with patch.object(handler, "sns") as mock_sns:
        result = handler.lambda_handler(event, context=None)

    assert result == {"statusCode": 200}
    mock_sns.publish.assert_called_once()
    _, kwargs = mock_sns.publish.call_args
    assert kwargs["TopicArn"] == os.environ["TOPIC_ARN"]
    assert kwargs["Subject"] == "Tu audio está listo 🎧"
    assert "hola.mp3" in kwargs["Message"]
    assert "https://" in kwargs["Message"]


@mock_aws
def test_notifier_message_shows_expiry_in_minutes():
    bucket = _create_bucket()
    _put_object(bucket, "audio.mp3")
    event = _event((bucket, "audio.mp3"))

    with patch.object(handler, "sns") as mock_sns, \
         patch.object(handler, "URL_EXPIRY_SECS", 1800):
        handler.lambda_handler(event, context=None)

    _, kwargs = mock_sns.publish.call_args
    assert "30 minutos" in kwargs["Message"]


@mock_aws
def test_notifier_handles_multiple_records_in_one_event():
    bucket = _create_bucket()
    _put_object(bucket, "uno.mp3")
    _put_object(bucket, "dos.mp3")

    event = _event((bucket, "uno.mp3"), (bucket, "dos.mp3"))

    with patch.object(handler, "sns") as mock_sns:
        result = handler.lambda_handler(event, context=None)

    assert result == {"statusCode": 200}
    assert mock_sns.publish.call_count == 2


@mock_aws
def test_notifier_extracts_filename_from_nested_key():
    bucket = _create_bucket()
    _put_object(bucket, "carpeta/subcarpeta/final.mp3")
    event = _event((bucket, "carpeta/subcarpeta/final.mp3"))

    with patch.object(handler, "sns") as mock_sns:
        handler.lambda_handler(event, context=None)

    _, kwargs = mock_sns.publish.call_args
    first_line = kwargs["Message"].splitlines()[0]
    assert "final.mp3" in first_line
    assert "carpeta/subcarpeta/final.mp3" not in first_line