import teslapy
import boto3
import json
import time
import os
import logging

email_param = os.environ['EMAIL_SSM_PARAM_NAME']
refresh_token_param =  os.environ['REFRESH_TOKEN_SSM_PARAM']   
bucket = os.environ['BUCKET_NAME']
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    ssm_client = boto3.client('ssm')
    email = ssm_client.get_parameter(Name=email_param)
    refresh_token = ssm_client.get_parameter(Name=refresh_token_param)

    with teslapy.Tesla(email) as tesla:
        logger.info('refreshing tesla auth')
        try:
            tesla.refresh_token(refresh_token=refresh_token)
        except:
            logger.error('failed to refresh tesla auth')
            exit(1)
        
        logger.info('getting charge history')
        try:
            vehicle = tesla.vehicle_list()[0]
            charge_history = vehicle.get_charge_history()
        except:
            logger.error('failed to retrieve charge history')

        logger.info('storing data in s3')
        s3_object_name = f'{int(time.time())}_charge_data.json'
        s3 = boto3.resource('s3')
        s3_object = s3.Object(bucket, s3_object_name)
        s3_object.put(Body=(bytes(json.dumps(charge_history).encode('UTF-8'))))
        logger.info(f'stored data in {s3_object_name} in bucket {bucket}')
