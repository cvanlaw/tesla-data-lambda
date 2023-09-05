import boto3
from botocore.exceptions import ClientError
import json
import logging
import os
import urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("loading function")

s3 = boto3.resource("s3")
dynamodb = boto3.resource("dynamodb")
table_name = os.environ["TABLE_NAME"]
table = dynamodb.Table(table_name)


def slice_charging_history(charging_history):
    supercharger_index = 2
    home_index = 1
    sliced_history = {}
    for item in charging_history["charging_history_graph"]["data_points"]:
        home_charge_amount_raw = (
            item["values"][home_index]["raw_value"]
            if item["values"][home_index]["value"] != "0"
            else 0
        )
        supercharger_charge_amount_raw = (
            item["values"][supercharger_index]["raw_value"]
            if item["values"][supercharger_index]["value"] != "0"
            else 0
        )
        sliced_history[item["timestamp"]["timestamp"]["seconds"]] = {
            "supercharger": supercharger_charge_amount_raw,
            "home": home_charge_amount_raw,
        }
    return sliced_history


def persist_charging_history(charging_history_document):
    try:
        table.put_item(
            Item={
                "timestamp": charging_history_document,
                "supercharger": charging_history_document["supercharger"],
                "home": charging_history_document["home"],
            }
        )
    except ClientError as err:
        logger.error(
            "Couldn't add charging history %s to table %s. Here's why: %s: %s",
            charging_history_document,
            table_name,
            err.response["Error"]["Code"],
            err.response["Error"]["Message"],
        )


def handler(event, context):
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )

    logger.info(f'received event for {key} in {bucket}')

    content_object = s3.Object(bucket, key)
    file_content = content_object.get()["Body"].read().decode("utf-8")
    json_content = json.loads(file_content)

    sliced = slice_charging_history(json_content)

    for item in sliced:
        logger.info(f'persisting {item}')
        persist_charging_history(item)
