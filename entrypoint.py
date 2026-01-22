#!/usr/bin/env python3
"""
Entrypoint script for iNaturalist ETL container.
Downloads required files from Allas (CSC S3-compatible storage) and runs the ETL process.
"""

import os
import sys
import subprocess
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Set required checksum environment variables for Allas
os.environ["AWS_REQUEST_CHECKSUM_CALCULATION"] = "when_required"
os.environ["AWS_RESPONSE_CHECKSUM_VALIDATION"] = "when_required"


def validate_required_env_vars():
    """Validate that required environment variables are set."""
    required = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET"]
    missing = [var for var in required if not os.environ.get(var)]
    
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def create_privatedata_directory():
    """Create the privatedata directory if it doesn't exist."""
    privatedata_dir = Path("/app/privatedata")
    privatedata_dir.mkdir(parents=True, exist_ok=True)
    return privatedata_dir


def get_s3_client():
    """Create and return a boto3 S3 client configured for Allas."""
    endpoint_url = os.environ.get("S3_ENDPOINT_URL")
    
    if endpoint_url:
        print(f"Using S3-compatible endpoint: {endpoint_url}")
    else:
        print("Using default AWS S3 endpoint")
    
    # Set default region if not provided (may not be needed for Allas, but boto3 expects it)
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    
    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=region
    )


def download_file_from_s3(s3_client, bucket, s3_key, local_path):
    """Download a file from S3 to local path."""
    try:
        print(f"Downloading {s3_key}...")
        s3_client.download_file(bucket, s3_key, str(local_path))
        print(f"Successfully downloaded {s3_key} to {local_path}")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        print(f"Error: Failed to download {s3_key} from S3: {error_code}", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: Unexpected error downloading {s3_key}: {e}", file=sys.stderr)
        return False


def download_required_files():
    """Download both required files from Allas."""
    validate_required_env_vars()
    privatedata_dir = create_privatedata_directory()
    
    bucket = os.environ["S3_BUCKET"]
    users_file = os.environ.get("S3_USERS_FILE", "inaturalist-suomi-20-users.csv")
    observations_file = os.environ.get("S3_OBSERVATIONS_FILE", "latest.tsv")
    
    print(f"Downloading files from S3 bucket: {bucket}")
    print(f"  - Users file: {users_file}")
    print(f"  - Observations file: {observations_file}")
    
    try:
        s3_client = get_s3_client()
    except NoCredentialsError:
        print("Error: AWS credentials not found or invalid", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to create S3 client: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Download users CSV file
    users_local_path = privatedata_dir / "inaturalist-suomi-20-users.csv"
    if not download_file_from_s3(s3_client, bucket, users_file, users_local_path):
        sys.exit(1)
    
    # Download observations TSV file
    observations_local_path = privatedata_dir / "latest.tsv"
    if not download_file_from_s3(s3_client, bucket, observations_file, observations_local_path):
        sys.exit(1)
    
    print("Successfully downloaded all files from Allas")


def get_etl_arguments():
    """Get ETL arguments from environment variables or use defaults."""
    target = os.environ.get("ETL_TARGET", "production")
    mode = os.environ.get("ETL_MODE", "auto")
    full_logging = os.environ.get("ETL_FULL_LOGGING", "true")
    sleep = os.environ.get("ETL_SLEEP", "5")
    
    return [target, mode, full_logging, sleep]


def run_etl(args=None):
    """Run the ETL script with provided or default arguments."""
    # Change to app directory
    os.chdir("/app")
    
    if args:
        # Use provided command-line arguments
        cmd = ["python3", "inat.py"] + args
        print(f"Running ETL with provided arguments: {' '.join(cmd[1:])}")
    else:
        # Use environment variables or defaults
        etl_args = get_etl_arguments()
        cmd = ["python3", "inat.py"] + etl_args
        print("Running ETL with default settings:")
        print(f"  Target: {etl_args[0]}")
        print(f"  Mode: {etl_args[1]}")
        print(f"  Full logging: {etl_args[2]}")
        print(f"  Sleep: {etl_args[3]} seconds")
    
    # Execute the ETL script
    try:
        sys.exit(subprocess.run(cmd, check=False).returncode)
    except KeyboardInterrupt:
        print("\nETL interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: Failed to execute ETL script: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entrypoint function."""
    # Download required files from Allas
    download_required_files()
    
    # Run ETL with command-line arguments if provided, otherwise use defaults
    if len(sys.argv) > 1:
        # If arguments are provided, pass them to inat.py
        # Skip the script name itself
        run_etl(sys.argv[1:])
    else:
        # No arguments provided, use defaults from environment variables
        run_etl()


if __name__ == "__main__":
    main()
