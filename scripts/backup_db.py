from dotenv import load_dotenv
from os import environ
from datetime import datetime
import boto3

load_dotenv()

today = datetime.now().strftime('%Y-%m-%d')
db_path = environ.get('DATABASE_PATH', 'db.sqlite3')

s3 = boto3.client('s3', 
                  endpoint_url=environ.get('AWS_ENDPOINT_URL_S3', None), 
                  aws_access_key_id=environ.get('AWS_ACCESS_KEY_ID', None), 
                  aws_secret_access_key=environ.get('AWS_SECRET_ACCESS_KEY', None))

s3.upload_file(db_path, environ.get('BUCKET_NAME', 'martin'), today + '.sqlite3')
