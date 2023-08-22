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
s3 = boto3.resource('s3')

def db_load():
    logger.info('loading cache from s3')
    cache_obj = s3.Object(bucket, 'cache.json')
    response = cache_obj.get()
    body = response.get('Body').read()
    logger.info(f'loaded cache from s3: {body}')
    return json.loads(body)
    
def db_dump(cache):
    logger.info('saving cache to s3') 
    cache_obj = s3.Object(bucket, 'cache.json')
    cache_obj.put(Body=(bytes(json.dumps(cache).encode('UTF-8'))))
    logger.info('saved cache to s3')

def handler(event, context):
    ssm_client = boto3.client('ssm')
    email = ssm_client.get_parameter(Name=email_param)
    refresh_token = ssm_client.get_parameter(Name=refresh_token_param)

    with teslapy.Tesla(email, cache_loader=db_load, cache_dumper=db_dump) as tesla:
        logger.info('refreshing tesla auth')
        try:
            tesla.refresh_token(refresh_token=refresh_token['Parameter']['Value'])
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
        s3_object_name = f'charge_history/{int(time.time())}_charge_data.json'
        s3_object = s3.Object(bucket, s3_object_name)
        s3_object.put(Body=(bytes(json.dumps(charge_history).encode('UTF-8'))))
        logger.info(f'stored data in {s3_object_name} in bucket {bucket}')
