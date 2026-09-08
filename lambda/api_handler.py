import boto3
import json
import urllib.parse
from botocore.config import Config
from decimal import Decimal

# API Gateway-integrated Lambda.
# Generates pre-signed S3 upload/download URLs, lists files from DynamoDB,
# and deletes files from both S3 and DynamoDB.

BUCKET = "lab-shon"

s3 = boto3.client('s3', config=Config(signature_version='s3v4'))
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('OneDriveMetadata')

CORS = {"Access-Control-Allow-Origin": "*"}


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    path = event.get('path', '')

    if path == '/upload-url':
        file_name = event['queryStringParameters']['filename']
        url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={'Bucket': BUCKET, 'Key': file_name},
            ExpiresIn=3600
        )
        return {"statusCode": 200, "headers": CORS,
                "body": json.dumps({"upload_url": url, "key": file_name})}

    if path == '/download-url':
        db_file_name = event['queryStringParameters']['filename']
        s3_key = urllib.parse.unquote_plus(db_file_name)
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': BUCKET, 'Key': s3_key},
            ExpiresIn=3600
        )
        return {"statusCode": 200, "headers": CORS,
                "body": json.dumps({"download_url": url})}

    if path == '/delete-file':
        db_file_name = event['queryStringParameters']['filename']
        s3_key = urllib.parse.unquote_plus(db_file_name)
        s3.delete_object(Bucket=BUCKET, Key=s3_key)
        table.delete_item(Key={'file_id': db_file_name})
        return {"statusCode": 200, "headers": CORS,
                "body": json.dumps({"status": "deleted"})}

    if path == '/files':
        response = table.scan()
        return {"statusCode": 200, "headers": CORS,
                "body": json.dumps(response.get('Items', []), cls=DecimalEncoder)}

    return {"statusCode": 404, "headers": CORS,
            "body": json.dumps({"error": "Not found"})}
