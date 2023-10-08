import teslapy
import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError
import os
import logging
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["TABLE_NAME"]
table = dynamodb.Table(table_name)

email_param = os.environ["EMAIL_SSM_PARAM_NAME"]
refresh_token_param = os.environ["REFRESH_TOKEN_SSM_PARAM"]
bucket = os.environ["BUCKET_NAME"]
logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.resource("s3")
ssm_client = boto3.client("ssm")


def db_load():
    logger.info("loading cache from s3")
    cache_obj = s3.Object(bucket, "cache.json")
    response = cache_obj.get()
    body = response.get("Body").read()
    logger.info(f"loaded cache from s3: {body}")
    return json.loads(body)


def db_dump(cache):
    logger.info("saving cache to s3")
    cache_obj = s3.Object(bucket, "cache.json")
    cache_obj.put(Body=(bytes(json.dumps(cache).encode("UTF-8"))))
    logger.info("saved cache to s3")


def persist_vehicle_data(key, vehicle_data_document):
    try:
        table.put_item(Item=vehicle_data_document)
    except ClientError as err:
        logger.error(
            "Couldn't add charging history %s to table %s. Here's why: %s: %s",
            key,
            table_name,
            err.response["Error"]["Code"],
            err.response["Error"]["Message"],
        )


def get_vehicle_data(Vehicle):
    data = Vehicle.get_vehicle_data()
    dataAsJson = json.dumps(data)
    return json.loads(dataAsJson, parse_float=Decimal)


def export_vehicle_data(Tesla):
    vehicle = Tesla.vehicle_list()[0]

    if not vehicle.available():
        logger.info("vehicle not available.")
        return None

    vehicle.sync_wake_up()
    logger.info("getting vehicle data...")
    data = get_vehicle_data(vehicle)
    logger.info("...done")

    timestamp = int(
        time.mktime(
            datetime.now()
            .replace(hour=5, minute=0, second=0, microsecond=0)
            .timetuple()
        )
    )
    data["timestamp"] = timestamp
    logger.info("persisting vehicle data for %s...", timestamp)
    persist_vehicle_data(timestamp, data)
    logger.info("...done")


def handler(event, context):
    email = ssm_client.get_parameter(Name=email_param)["Parameter"]["Value"]
    with teslapy.Tesla(email, cache_loader=db_load, cache_dumper=db_dump) as tesla:
        logger.info("Exporting vehicle data...")
        export_vehicle_data(Tesla=tesla)
        logger.info("complete")
        return
