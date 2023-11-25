import logging

def configure_logging(logging_level: int):
    if logging_level is None:
        logging_level = logging.INFO
    logging.getLogger().setLevel(logging_level)
    logging.getLogger('botocore').setLevel(logging.WARN)