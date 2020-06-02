from datetime import timedelta
import os, sys, redis
from minio import Minio
from minio.error import (ResponseError, BucketAlreadyOwnedByYou, BucketAlreadyExists)
from flask import Flask, redirect, send_file

app = Flask(__name__)
cache = redis.Redis(host='redis', port=6379)
minioAccessKey = os.environ.get('MINIO_ACCESS_KEY')
minioSecretKey = os.environ.get('MINIO_SECRET_KEY')
s3Bucket = os.environ.get('BUCKET_NAME')
minioUrl = os.environ.get('MINIO_URL')
minioClient = Minio(minioUrl, access_key=minioAccessKey, secret_key=minioSecretKey, secure=False)

@app.route('/file/download/<objectName>')
def downloadFile(objectName):
    try:
        object = minioClient.get_object(s3Bucket, objectName, request_headers=None)
        return send_file(object, as_attachment=True, attachment_filename=objectName)
    except ResponseError as err:
        print(err)
        return err

@app.route('/file/downloadpre/<objectName>')
def downloadFilePre(objectName):        
    try:
        return redirect(minioClient.presigned_get_object(s3Bucket, objectName, expires=timedelta(days=2)))
    except ResponseError as err:
        print(err)
        return err