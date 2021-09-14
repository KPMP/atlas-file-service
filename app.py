from datetime import timedelta
import os, sys, redis
from minio import Minio
import boto3
import botocore.exceptions
from minio.error import S3Error
from flask import Flask, redirect, send_file, Response

app = Flask(__name__)
cache = redis.Redis(host='redis', port=6379)
minioAccessKey = os.environ.get('MINIO_ACCESS_KEY')
minioSecretKey = os.environ.get('MINIO_SECRET_KEY')
s3Bucket = os.environ.get('BUCKET_NAME')
minioUrl = os.environ.get('MINIO_URL')
minioClient = Minio(minioUrl, access_key=minioAccessKey, secret_key=minioSecretKey, secure=False)
s3_client = boto3.client(
    's3',
    'us-east-1',
    aws_access_key_id='MINIO_ACCESS_KEY',
    aws_secret_access_key='MINIO_SECRET_KEY'
)

@app.route('/v1/file/download/<packageId>/<objectName>', methods=['GET'])
def downloadFile(packageId, objectName):
    try:
        objectNameFull = packageId + '/' + objectName
        object = minioClient.get_object(s3Bucket, objectNameFull, request_headers=None)
        return send_file(object, as_attachment=True, attachment_filename=objectName)
    except S3Error as err:
        print(err)
        return err

@app.route('/v1/derived/download/<packageId>/<objectName>', methods=['GET'])
def downloadDerivedFile(packageId, objectName):
    try:
        objectNameFull = packageId + '/derived/' + objectName
        object = minioClient.get_object(s3Bucket, objectNameFull, request_headers=None)
        return send_file(object, as_attachment=False)
    except S3Error as err:
        print(err)
        return err

@app.route('/v1/derived/downloads3/<packageId>/<objectName>', methods=['GET'])
def downloadDerivedFile(packageId, objectName):
    try:
        objectNameFull = packageId + '/derived/' + objectName
        file = s3_client.get_object(Bucket=s3Bucket, Key=objectNameFull)
        return Response(
            file['Body'].read(),
            mimetype='application/octet-stream')
    except botocore.exceptions.ClientError as error:
        return error
    except botocore.exceptions.ParamValidationError as error:
        return error