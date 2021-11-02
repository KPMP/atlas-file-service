import os, sys, redis
from minio import Minio
import boto3
import botocore.exceptions
from minio.error import S3Error
from flask import Flask, redirect, send_file, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
cache = redis.Redis(host='redis', port=6379)
minioAccessKey = os.environ.get('MINIO_ACCESS_KEY')
minioSecretKey = os.environ.get('MINIO_SECRET_KEY')
s3Bucket = os.environ.get('BUCKET_NAME')
minioUrl = os.environ.get('MINIO_URL')
minioClient = Minio(minioUrl, access_key=minioAccessKey, secret_key=minioSecretKey, secure=False)
s3_client = boto3.client(
    's3',
    'us-east-1',
    aws_access_key_id=minioAccessKey,
    aws_secret_access_key=minioSecretKey
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
def downloadDerivedFileS3PS(packageId, objectName):
    try:
        objectNameFull = packageId + '/derived/' + objectName
        return s3_client.generate_presigned_url('get_object',
                                                Params={'Bucket': s3Bucket, 'Key': objectNameFull},
                                                ExpiresIn=3600)
    except botocore.exceptions.ClientError as error:
        print(error)
    except botocore.exceptions.ParamValidationError as error:
        print(error)