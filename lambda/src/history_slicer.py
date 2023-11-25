from aws_utils import load_object, persist_charging_history, archive_charging_history
import logging

logger = logging.getLogger()


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


def slice(bucket: str, key: str, table_name: str):
    json_content = load_object(bucket, key)
    sliced = slice_charging_history(json_content)
    for k in sliced:
        logger.info(f"persisting {k}")
        persist_charging_history(table_name, k, sliced[k])
    archive_charging_history(bucket, key)
