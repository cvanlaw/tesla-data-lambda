import boto3
import json
import logging
from botocore.exceptions import ClientError
from decimal import Decimal

logger = logging.getLogger()
s3 = boto3.resource("s3")
ssm_client = boto3.client("ssm")
dynamodb = boto3.resource("dynamodb")


def put_object_in_bucket(bucket: str, key: str, object_to_put: dict):
    logger.info(f"storing {key} in {bucket}")
    s3_object = s3.Object(bucket, key)
    s3_object.put(Body=(bytes(json.dumps(object_to_put).encode("UTF-8"))))
    logger.info(f"stored {key} in {bucket}")


def get_ssm_param_value(param_name: str):
    logger.info(f"getting parameter {param_name}")
    param = ssm_client.get_parameter(Name=param_name)["Parameter"]["Value"]
    logger.info(f"retrieved parameter {param_name}")
    return param


def persist_vehicle_data(table_name: str, key: str, vehicle_data_document):
    try:
        table = dynamodb.Table(table_name)
        table.put_item(Item=vehicle_data_document)
    except ClientError as err:
        logger.error(
            "Couldn't add charging history %s to table %s. Here's why: %s: %s",
            key,
            table_name,
            err.response["Error"]["Code"],
            err.response["Error"]["Message"],
        )


def persist_charging_history(table_name: str, key: str, charging_history_document):
    try:
        table = dynamodb.Table(table_name)
        table.put_item(
            Item={
                "timestamp": key,
                "supercharger": charging_history_document["supercharger"],
                "home": charging_history_document["home"],
            }
        )
    except ClientError as err:
        logger.error(
            "Couldn't add charging history %s to table %s. Here's why: %s: %s",
            key,
            table_name,
            err.response["Error"]["Code"],
            err.response["Error"]["Message"],
        )


def archive_charging_history(bucket: str, key: str):
    try:
        s3.Object(bucket, f"processed/{key}").copy_from(
            CopySource={"Bucket": bucket, "Key": key}
        )
        s3.Object(bucket, key).delete()
    except ClientError as err:
        logger.error("Couldn't archive object %s/%s", bucket, key)


def load_object(bucket, key):
    content_object = s3.Object(bucket, key)
    file_content = content_object.get()["Body"].read().decode("utf-8")
    return json.loads(file_content, parse_float=Decimal)
