import boto3
import json

# SQS-triggered Lambda.
# Consumes S3 "object created" events (delivered via SQS) and writes the
# file's metadata into the DynamoDB index table.

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('OneDriveMetadata')


def lambda_handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        if 'Records' in body:
            s3_data = body['Records'][0]['s3']
            file_key = s3_data['object']['key']
            size = s3_data['object']['size']

            table.put_item(Item={
                'file_id': file_key,
                'status': 'Available',
                'size_bytes': size
            })
    return {'statusCode': 200}
