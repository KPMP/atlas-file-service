import os, sys, redis
from minio import Minio
import boto3
import botocore.exceptions
from minio.error import S3Error
from flask import Flask, redirect, send_file, Response
from flask_cors import CORS
from mysql.connector import pooling
import logging
import requests
from werkzeug.wsgi import FileWrapper
import json
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app)
cache = redis.Redis(host='redis', port=6379)
minioAccessKey = os.environ.get('MINIO_ACCESS_KEY')
minioSecretKey = os.environ.get('MINIO_SECRET_KEY')
s3Bucket = os.environ.get('BUCKET_NAME')
minioUrl = os.environ.get('MINIO_URL')
apiSecret = os.environ.get("API_SECRET")
ga4Id = os.environ.get("GA4_ID")
url = "https://www.google-analytics.com/mp/collect?measurement_id=" + ga4Id + "&api_secret=" + apiSecret

http = requests.Session()
executor = ThreadPoolExecutor(max_workers=4)


def send_download_event(object_name):
    payload = {
        "client_id": "XXXXXXXXXX.YYYYYYYYYY",
        "events": [
            {
                "name": "AtlasRepositoryDownload",
                "params": {
                    "event_category": "Repository",
                    "event_action": "Download",
                    "label": object_name
                }
            }]
    }
    try:
        http.post(url, json=payload, timeout=5)
    except requests.RequestException:
        logger.warning("Failed to send GA4 download event", exc_info=True)
minioClient = Minio(minioUrl, access_key=minioAccessKey, secret_key=minioSecretKey, secure=False)
s3_client = boto3.client(
    's3',
    'us-east-1',
    aws_access_key_id=minioAccessKey,
    aws_secret_access_key=minioSecretKey
)

logger = logging.getLogger("atlas-file-service")
logging.basicConfig(level=logging.ERROR)


class MYSQLConnection:

    def __init__(self, pool_size=None):
        logger.info("Start: MYSQLConnection().__init__(), creating connection pool")
        self.host = os.environ.get("MYSQL_HOST")
        self.port = 3306
        self.user = os.environ.get("MYSQL_USER")
        self.password = os.environ.get("MYSQL_PASSWORD")
        self.database_name = "knowledge_environment"
        self.pool_size = pool_size or int(os.environ.get("MYSQL_POOL_SIZE", 8))
        self.pool = None

    def init_pool(self):
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="atlas-file-service",
                pool_size=self.pool_size,
                autocommit=True,
                pool_reset_session=False,
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database_name,
            )
            return self.pool
        except Exception:
            logger.exception("Can't create MySQL connection pool")
            sys.exit(1)

    def get_data(self, sql, query_data=None):
        connection = None
        cursor = None
        try:
            connection = self.pool.get_connection()
            cursor = connection.cursor(buffered=False, dictionary=True)
            cursor.execute(sql, query_data)
            return cursor.fetchall()
        except Exception:
            logger.exception("Can't get knowledge_environment data.")
            return None
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()


db = MYSQLConnection()
db.init_pool()


def get_file_info_by_file_name(file_name):
    return db.get_data(
        "SELECT access FROM repo_file_v WHERE file_name = %s LIMIT 1",
        (file_name,),
    )

@app.route('/v1/file/download/<packageId>/<objectName>', methods=['POST', 'GET'])
def downloadFile(packageId, objectName):
    result = get_file_info_by_file_name(objectName)
    if result and result[0]["access"] == "open":
        try:
            objectNameFull = packageId + '/' + objectName
            object = minioClient.get_object(s3Bucket, objectNameFull, request_headers=None)
            executor.submit(send_download_event, objectName)
            file_wrapper = FileWrapper(object, 1024 * 1024)
            headers = {
                'Content-Disposition': 'attachment; filename="{}"'.format(objectName)
            }
            response = Response(file_wrapper,
                                mimetype='application/octet-stream',
                                direct_passthrough=True,
                                headers=headers)
            response.call_on_close(lambda: (object.close(), object.release_conn()))
            return response
        except S3Error as err:
            logger.error(err)
            return err
    else:
        return "File not found", 404


@app.route('/v1/derived/download/<packageId>/<objectName>', methods=['GET'])
def downloadDerivedFileS3PS(packageId, objectName):
    try:
        objectNameFull = packageId + '/derived/' + objectName
        return s3_client.generate_presigned_url('get_object',
                                                Params={'Bucket': s3Bucket, 'Key': objectNameFull},
                                                ExpiresIn=3600)
    except botocore.exceptions.ClientError as error:
        logger.error(error)
    except botocore.exceptions.ParamValidationError as error:
        logger.error(error)