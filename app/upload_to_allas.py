#!/usr/bin/env python3
"""
Uploads the JSON state file to Allas S3 object storage.
This module provides functions to sync the state file back to Allas after each write.
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Global S3 client (initialized once)
_s3_client = None
_upload_config = None

def _get_s3_client():
    """Get or initialize the S3 client for Allas."""
    global _s3_client, _upload_config
    
    if _s3_client is not None:
        return _s3_client
    
    # Get configuration from environment variables
    allas_endpoint = os.getenv('ALLAS_ENDPOINT')
    allas_access_key = os.getenv('ALLAS_ACCESS_KEY')
    allas_secret_key = os.getenv('ALLAS_SECRET_KEY')
    allas_bucket = os.getenv('ALLAS_BUCKET')
    allas_object_key_3 = os.getenv('ALLAS_OBJECT_KEY_3')
    
    if not all(all([allas_endpoint, allas_access_key, allas_secret_key, allas_bucket, allas_object_key_3])):
        raise ValueError("Missing required Allas configuration for upload. Check environment variables.")
    
    # Store config for later use
    _upload_config = {
        'bucket': allas_bucket,
        'object_key': allas_object_key_3,
    }
    
    # Initialize S3 client
    try:
        _s3_client = boto3.client(
            's3',
            endpoint_url=allas_endpoint,
            aws_access_key_id=allas_access_key,
            aws_secret_access_key=allas_secret_key
        )
        return _s3_client
    except Exception as e:
        raise Exception(f"Failed to initialize S3 client for upload: {str(e)}")

def upload_state_file(local_file_path='./store/data.json', silent=False):
    """Upload the state file to Allas S3 storage.
    
    Args:
        local_file_path (str): Path to the local state file to upload
        silent (bool): If True, suppress error messages (for signal handlers)
    
    Returns:
        bool: True if upload succeeded, False otherwise
    """
    try:
        s3_client = _get_s3_client()
        config = _upload_config
        
        if not os.path.exists(local_file_path):
            if not silent:
                print(f"Warning: State file {local_file_path} does not exist, skipping upload", file=sys.stderr)
            return False
        
        # Upload the file
        s3_client.upload_file(local_file_path, config['bucket'], config['object_key'])
        if not silent:
            print(f"State file uploaded to Allas: {config['object_key']}")
        return True
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        if not silent:
            if error_code == '403':
                print(f"Error: Access denied when uploading to Allas. Check your credentials and bucket permissions", file=sys.stderr)
            else:
                print(f"Error: Failed to upload state file to Allas: {str(e)}", file=sys.stderr)
        return False
    except Exception as e:
        if not silent:
            print(f"Error: Unexpected error during upload: {str(e)}", file=sys.stderr)
        return False
