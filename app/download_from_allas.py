#!/usr/bin/env python3
"""
Downloads data files from Allas S3 object storage at container startup.
This script runs before the main ETL process to ensure the data files are available locally.
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def download_file(s3_client, bucket, object_key, local_path):
    """Download a single file from Allas S3 storage."""
    print(f"Downloading {object_key} from bucket {bucket}...")
    try:
        s3_client.download_file(bucket, object_key, local_path)
        print(f"Successfully downloaded file to {local_path}")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        if error_code == 'NoSuchBucket':
            print(f"Error: Bucket '{bucket}' does not exist", file=sys.stderr)
        elif error_code == 'NoSuchKey':
            print(f"Error: Object '{object_key}' not found in bucket '{bucket}'", file=sys.stderr)
        elif error_code == '403':
            print(f"Error: Access denied. Check your credentials and bucket permissions", file=sys.stderr)
        else:
            print(f"Error: Failed to download file: {str(e)}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: Unexpected error during download: {str(e)}", file=sys.stderr)
        return False

def download_from_allas():
    """Download data files from Allas S3 storage."""
    
    # Get configuration from environment variables
    allas_endpoint = os.getenv('ALLAS_ENDPOINT')
    allas_access_key = os.getenv('ALLAS_ACCESS_KEY')
    allas_secret_key = os.getenv('ALLAS_SECRET_KEY')
    allas_bucket = os.getenv('ALLAS_BUCKET')
    
    # File 1: Email data
    allas_object_key_1 = os.getenv('ALLAS_OBJECT_KEY')
    local_file_path_1 = os.getenv('LOCAL_DATA_PATH')
    
    # File 2: Latest observation data
    allas_object_key_2 = os.getenv('ALLAS_OBJECT_KEY_2')
    local_file_path_2 = os.getenv('LOCAL_DATA_PATH_2')
    
    # File 3: JSON state file
    allas_object_key_3 = os.getenv('ALLAS_OBJECT_KEY_3')
    local_file_path_3 = os.getenv('LOCAL_DATA_PATH_3')
    
    # Validate required environment variables
    required_vars = {
        'ALLAS_ENDPOINT': allas_endpoint,
        'ALLAS_ACCESS_KEY': allas_access_key,
        'ALLAS_SECRET_KEY': allas_secret_key,
        'ALLAS_BUCKET': allas_bucket,
        'ALLAS_OBJECT_KEY': allas_object_key_1,
        'LOCAL_DATA_PATH': local_file_path_1,
        'ALLAS_OBJECT_KEY_2': allas_object_key_2,
        'LOCAL_DATA_PATH_2': local_file_path_2,
        'ALLAS_OBJECT_KEY_3': allas_object_key_3,
        'LOCAL_DATA_PATH_3': local_file_path_3,
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}", file=sys.stderr)
        sys.exit(1)
    
    # Create local directory if it doesn't exist
    local_dir_1 = os.path.dirname(local_file_path_1)
    local_dir_2 = os.path.dirname(local_file_path_2)
    local_dir_3 = os.path.dirname(local_file_path_3)
    for local_dir in [local_dir_1, local_dir_2, local_dir_3]:
        if local_dir and not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)
            print(f"Created directory: {local_dir}")
    
    # Initialize S3 client for Allas
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=allas_endpoint,
            aws_access_key_id=allas_access_key,
            aws_secret_access_key=allas_secret_key
        )
    except Exception as e:
        print(f"Error: Failed to initialize S3 client: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    # Download all three files
    success = True
    success = download_file(s3_client, allas_bucket, allas_object_key_1, local_file_path_1) and success
    success = download_file(s3_client, allas_bucket, allas_object_key_2, local_file_path_2) and success
    success = download_file(s3_client, allas_bucket, allas_object_key_3, local_file_path_3) and success
    
    if not success:
        print("Error: One or more files failed to download", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    download_from_allas()
