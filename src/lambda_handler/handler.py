import json
import os
import urllib.parse

import boto3

s3 = boto3.client("s3")
polly = boto3.client("polly")
comprehend = boto3.client("comprehend")

MAX_CHARS = 100_000  # límite de StartSpeechSynthesisTask
COMPREHEND_MAX_BYTES = 5_000  # límite de DetectDominantLanguage
MIN_CONFIDENCE = 0.5

# mapa idioma detectado -> (VoiceId, Engine, LanguageCode)
# todas las voces aquí soportan motor neural; si añades un idioma nuevo,
# comprueba con polly.describe_voices(LanguageCode=..., Engine="neural")
VOICE_MAP = {
    "es": ("Lucia", "neural", "es-ES"),
    "en": ("Joanna", "neural", "en-US"),
    "fr": ("Lea", "neural", "fr-FR"),
    "de": ("Vicki", "neural", "de-DE"),
    "it": ("Bianca", "neural", "it-IT"),
    "pt": ("Ines", "neural", "pt-PT"),
}

DEFAULT_VOICE_ID = os.environ["DEFAULT_VOICE_ID"]
DEFAULT_ENGINE = os.environ["DEFAULT_ENGINE"]
DEFAULT_LANGUAGE_CODE = os.environ["DEFAULT_LANGUAGE_CODE"]


def lambda_handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        print(json.dumps({"msg": "procesando objeto", "bucket": bucket, "key": key}))

        text = _read_text(bucket, key)

        if not text.strip():
            print(json.dumps({"msg": "archivo vacío, se omite", "key": key}))
            continue

        if len(text) > MAX_CHARS:
            print(json.dumps({
                "msg": "texto truncado, excede el límite de Polly",
                "original_len": len(text),
                "max_chars": MAX_CHARS,
            }))
            text = text[:MAX_CHARS]

        voice_id, engine, language_code = _detect_voice(text)

        task = _start_synthesis(text, key, voice_id, engine, language_code)

        print(json.dumps({
            "msg": "tarea de síntesis lanzada",
            "task_id": task["SynthesisTask"]["TaskId"],
            "status": task["SynthesisTask"]["TaskStatus"],
            "voice_id": voice_id,
            "language_code": language_code,
        }))

    return {"statusCode": 200}


def _read_text(bucket: str, key: str) -> str:
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8")


def _detect_voice(text: str) -> tuple[str, str, str]:
    sample = text.encode("utf-8")[:COMPREHEND_MAX_BYTES].decode("utf-8", errors="ignore")

    try:
        result = comprehend.detect_dominant_language(Text=sample)
        languages = sorted(
            result["Languages"], key=lambda l: l["Score"], reverse=True
        )
    except Exception as e:
        print(json.dumps({"msg": "fallo detectando idioma, se usa el por defecto", "error": str(e)}))
        return DEFAULT_VOICE_ID, DEFAULT_ENGINE, DEFAULT_LANGUAGE_CODE

    if not languages:
        return DEFAULT_VOICE_ID, DEFAULT_ENGINE, DEFAULT_LANGUAGE_CODE

    top = languages[0]
    lang_code = top["LanguageCode"]  # ej. "es", "en"
    confidence = top["Score"]

    print(json.dumps({"msg": "idioma detectado", "lang_code": lang_code, "confidence": confidence}))

    if confidence < MIN_CONFIDENCE or lang_code not in VOICE_MAP:
        print(json.dumps({"msg": "idioma no soportado o baja confianza, se usa el por defecto"}))
        return DEFAULT_VOICE_ID, DEFAULT_ENGINE, DEFAULT_LANGUAGE_CODE

    return VOICE_MAP[lang_code]


def _start_synthesis(text: str, source_key: str, voice_id: str, engine: str, language_code: str) -> dict:
    stem = source_key.rsplit(".", 1)[0]

    return polly.start_speech_synthesis_task(
        Text=text,
        TextType="text",
        OutputFormat="mp3",
        OutputS3BucketName=os.environ["OUTPUT_BUCKET"],
        OutputS3KeyPrefix=stem,
        VoiceId=voice_id,
        Engine=engine,
        LanguageCode=language_code,
    )