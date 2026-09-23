import json
import os
import urllib.parse

import boto3

s3 = boto3.client("s3")
sns = boto3.client("sns")

URL_EXPIRY_SECS = int(os.environ.get("URL_EXPIRY_SECS", "3600"))


def lambda_handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        print(json.dumps({"msg": "audio detectado", "bucket": bucket, "key": key}))

        url = _presigned_url(bucket, key)
        filename = key.rsplit("/", 1)[-1]

        message = (
            f"Tu audio ya está listo: {filename}\n\n"
            f"Puedes descargarlo aquí (enlace válido {URL_EXPIRY_SECS // 60} minutos):\n"
            f"{url}"
        )

        sns.publish(
            TopicArn=os.environ["TOPIC_ARN"],
            Subject="Tu audio está listo 🎧",
            Message=message,
        )

        print(json.dumps({"msg": "notificación enviada", "key": key}))

    return {"statusCode": 200}


def _presigned_url(bucket: str, key: str) -> str:
    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=URL_EXPIRY_SECS,
    )