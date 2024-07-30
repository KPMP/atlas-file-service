import os, sys, redis
from minio import Minio
import boto3
import botocore.exceptions
from minio.error import S3Error
from flask import Flask, redirect, send_file, Response
from flask_cors import CORS
import mysql.connector
import logging
import requests
import json

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
    def __init__(self):
        logger.debug(
            "Start: MYSQLConnection().__init__(), trying to load environment variables in docker"
        )
        self.host = None
        self.port = 3306
        self.user = None
        self.password = None
        self.database_name = "knowledge_environment"

        try:
            self.host = os.environ.get("MYSQL_HOST")
            self.user = os.environ.get("MYSQL_USER")
            self.password = os.environ.get("MYSQL_PASSWORD")
        except Exception as connectError:
            logger.warning(
                "Can't load environment variables from docker... trying local .env file instead...", connectError
            )

    def get_db_cursor(self):
        try:
            if (self.database.is_connected() == False):
                self.get_db_connection();
            self.cursor = self.database.cursor(buffered=False, dictionary=True)
            return self.cursor
        except Exception as error:
            logger.error("Can't get mysql cursor", error)
            os.sys.exit()

    def get_db_connection(self):
        try:
            self.database = mysql.connector.connect(
                host=self.host,
                user=self.user,
                port=self.port,
                password=self.password,
                database=self.database_name,
            )
            self.database.get_warnings = True
            return self.database
        except Exception as error:
            logger.error("Can't connect to MySQL", error)
            os.sys.exit()

    def get_data(self, sql, query_data=None):
        try:
            self.get_db_cursor()
            data = []
            self.cursor.execute(sql, query_data)
            for row in self.cursor:
                data.append(row)
            return data
        except Exception as error:
            logger.error("Can't get knowledge_environment data.", error)
        finally:
            self.cursor.close()


db = MYSQLConnection()
db.get_db_connection()


def get_file_info_by_file_name(file_name):
    return db.get_data(
        "SELECT * FROM repo_file_v WHERE file_name = %s",
        (file_name,),
    )


@app.route('/v1/file/download/<packageId>/<objectName>', methods=['GET'])
def downloadFile(packageId, objectName):
    result = get_file_info_by_file_name(objectName)
    if result[0]["access"] == "open":
        try:
            objectNameFull = packageId + '/' + objectName
            object = minioClient.get_object(s3Bucket, objectNameFull, request_headers=None)
            payload = {
                "client_id": "XXXXXXXXXX.YYYYYYYYYY",
                "events": [
                    {
                        "name": "file_download",
                        "params": {
                            "file_name": result[0]["file_name"]
                        }
                    }
                ]
            }
            requests.post(url, json=payload, headers={'content-type': 'application/json'}, verify=True)
            return send_file(object, as_attachment=True, download_name=objectName)
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
        logger.error(err)
    except botocore.exceptions.ParamValidationError as error:
        logger.error(err)

