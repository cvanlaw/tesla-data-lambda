from logging_config import configure_logging
from tesla_utils import (
    get_charge_history,
    get_vehicle_data,
    vehicle_available,
    sync_vehicle,
)
from aws_utils import put_object_in_bucket, persist_vehicle_data
from history_slicer import slice
import logging
import os
import time
import datetime
import urllib.parse

configure_logging(logging.INFO)
bucket_name = os.environ["BUCKET_NAME"]
table_name = os.environ["TABLE_NAME"]
logger = logging.getLogger()


def run_charge_history_exporter(event, context):
    charge_history = get_charge_history()
    charge_history_key = f"charge_history/{int(time.time())}_charge_data.json"
    put_object_in_bucket(
        bucket=bucket_name, key=charge_history_key, object_to_put=charge_history
    )


def run_vehicle_data_exporter(event, context):
    if not vehicle_available():
        logger.info("vehicle not available")
        return

    sync_vehicle()
    vehicle_data = get_vehicle_data()
    timestamp = int(
        time.mktime(
            datetime.now()
            .replace(hour=5, minute=0, second=0, microsecond=0)
            .timetuple()
        )
    )
    vehicle_data["timestamp"] = timestamp
    persist_vehicle_data(table_name, timestamp, vehicle_data)


def run_history_slicer(event, context):
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )
    slice(bucket, key)
