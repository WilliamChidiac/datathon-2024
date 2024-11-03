import boto3
from botocore.exceptions import NoCredentialsError

s3 = boto3.client('s3')

def upload_file_to_s3(file_name, bucket, object_name=None):
    try:
        s3.upload_file(file_name, bucket, object_name or file_name)
        print(f"File {file_name} uploaded to {bucket}/{object_name or file_name}")
    except NoCredentialsError:
        print("Credentials not available")

def download_file_from_s3(bucket, object_name, file_name):
    try:
        s3.download_file(bucket, object_name, file_name)
        print(f"File {object_name} downloaded from {bucket} to {file_name}")
    except NoCredentialsError:
        print("Credentials not available")
