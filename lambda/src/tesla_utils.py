import logging
import json
import teslapy
import boto3
import os
from decimal import Decimal

logger = logging.getLogger()
bucket = os.environ["BUCKET_NAME"]
s3 = boto3.resource("s3")


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


def get_tesla_client():
    email_param = os.environ["EMAIL_SSM_PARAM_NAME"]
    ssm_client = boto3.client("ssm")
    email = ssm_client.get_parameter(Name=email_param)["Parameter"]["Value"]
    return teslapy.Tesla(email, cache_loader=db_load, cache_dumper=db_dump)


def get_vehicle():
    logger.info("getting vehicle")
    return get_tesla_client().vehicle_list()[0]


def get_charge_history():
    logger.info("getting vehicle charge history")
    return get_vehicle().get_charge_history()


def vehicle_available():
    logger.info("checking vehicle availability")
    return get_vehicle().available()


def sync_vehicle():
    logger.info("syncing vehicle")
    get_vehicle().sync_wake_up()


def get_vehicle_data():
    logger.info("getting vehicle data")
    data = get_vehicle().get_vehicle_data()
    dataAsJson = json.dumps(data)
    return json.loads(dataAsJson, parse_float=Decimal)
