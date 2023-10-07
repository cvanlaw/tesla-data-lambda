import teslapy
import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError
import pytz
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


def get_previous_odometer():
    try:
        timestamp = int(
            pytz.timezone("America/New_York").localize(
                time.mktime(
                    datetime.now()
                    .replace(
                        day=datetime.now().day - 1,
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )
                    .timetuple()
                )
            )
        )
        logger.info("getting previous odometer for key %s", timestamp)
        resp = table.get_item(Key={"timestamp": timestamp})
        logger.info(f"retrieved item: {json.dumps(resp)}")
        return resp["Item"]["vehicle_state"]["odometer"]
    except ClientError as err:
        logger.error(
            "Couldn't get charging history %s from table %s. Here's why: %s: %s",
            timestamp,
            table_name,
            err.response["Error"]["Code"],
            err.response["Error"]["Message"],
        )


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


def export_vehicle_data(Tesla):
    vehicle = Tesla.vehicle_list()[0]
    vehicle.sync_wake_up()
    data = vehicle.get_vehicle_data()
    dataAsJson = json.dumps(data)
    dataFromJson = json.loads(dataAsJson, parse_float=Decimal)
    currentOdometer = dataFromJson["vehicle_state"]["odometer"]
    previousOdometer = get_previous_odometer()
    dataFromJson["dailyMileage"] = currentOdometer - previousOdometer
    timestamp = int(
        pytz.timezone("America/New_York").localize(
            time.mktime(
                datetime.now()
                .replace(hour=0, minute=0, second=0, microsecond=0)
                .timetuple()
            )
        )
    )
    dataFromJson["timestamp"] = timestamp
    persist_vehicle_data(timestamp, dataFromJson)


def update_refresh_token(refresh_token):
    ssm_client.put_parameter(
        Name=refresh_token_param, Value=refresh_token, Overwrite=True
    )


def handler(event, context):
    email = ssm_client.get_parameter(Name=email_param)["Parameter"]["Value"]
    refresh_token = ssm_client.get_parameter(Name=refresh_token_param)["Parameter"][
        "Value"
    ]

    with teslapy.Tesla(email, cache_loader=db_load, cache_dumper=db_dump) as tesla:
        logger.info("refreshing tesla auth")
        try:
            token = tesla.refresh_token(refresh_token=refresh_token)
            if not token["refresh_token"] == refresh_token:
                update_refresh_token(token["refresh_token"])
        except teslapy.HTTPError as e:
            logger.error("failed to refresh tesla auth. error: ", e)
            exit(1)

        export_vehicle_data(Tesla=tesla)
