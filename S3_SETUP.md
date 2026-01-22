# Allas Setup Instructions for iNaturalist ETL

This guide explains how to set up CSC Allas S3-compatible object storage for the iNaturalist ETL container deployment.

## Overview

The container will download two files from Allas on startup:
1. `inaturalist-suomi-20-users.csv` - User email data (configurable via `S3_USERS_FILE`)
2. `latest.tsv` - Private observation data (configurable via `S3_OBSERVATIONS_FILE`)

After downloading, it runs `inat.py production auto true 5` by default (configurable via environment variables or command arguments).

## Step 1: Set Up Allas Storage

### Get Your Allas Credentials

1. **Get your credentials** from CSC Allas:
   - Access key ID
   - Secret access key
   - Bucket name
   - Endpoint URL: `https://a3s.fi` (Allas S3 endpoint)

   You can get these credentials through:
   - CSC's web interface (Files and storage services)
   - Using `allas-conf` command on CSC computing environments
   - CSC documentation: https://docs.csc.fi/data/Allas/

### Create a Bucket (if needed)

If you don't have a bucket yet, create one using:
- CSC's web interface
- `a-commands` on CSC computing environments
- `s3cmd` or `rclone` tools

### Upload Files to Allas

Upload both required files to your Allas bucket:

**Using s3cmd:**
```bash
s3cmd put inaturalist-suomi-20-users.csv s3://your-bucket-name/
s3cmd put latest.tsv s3://your-bucket-name/
```

**Using rclone:**
```bash
rclone copy inaturalist-suomi-20-users.csv allas:your-bucket-name/
rclone copy latest.tsv allas:your-bucket-name/
```

**Using CSC web interface:**
- Navigate to Files and storage services in CSC web interface
- Select your bucket
- Upload the files

**Note**: The file names in Allas should match what you configure in the container (see Step 2).

## Step 2: Configure Container Environment Variables

Set these environment variables in your OpenShift deployment:

### Required Variables:

- `AWS_ACCESS_KEY_ID` - Your Allas access key ID
- `AWS_SECRET_ACCESS_KEY` - Your Allas secret access key
- `S3_BUCKET` - Your Allas bucket name
- `S3_ENDPOINT_URL` - Set to `https://a3s.fi` (Allas S3 endpoint)

### Optional Variables:

- `S3_USERS_FILE` - Path to users file in Allas (defaults to `inaturalist-suomi-20-users.csv`)
- `S3_OBSERVATIONS_FILE` - Path to observations file in Allas (defaults to `latest.tsv`)
- `ETL_TARGET` - Target environment: `staging` or `production` (default: `production`)
- `ETL_MODE` - Mode: `auto` or `manual` (default: `auto`)
- `ETL_FULL_LOGGING` - Full logging: `true` or `false` (default: `true`)
- `ETL_SLEEP` - Sleep between requests in seconds (default: `5`)

**Note**: Default behavior runs `inat.py production auto true 5`. Override with environment variables or by providing command arguments.

## Step 3: OpenShift Deployment Configuration

### Using OpenShift Web Console:

1. Create a new deployment or edit existing one
2. Go to **Environment** tab
3. Add the environment variables listed in Step 2
4. For sensitive values (Allas credentials), use **Secret** instead of **ConfigMap**:
   - Create a Secret with keys: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - Reference the secret in your deployment

### Using OpenShift CLI (oc):

```bash
# Create a secret for Allas credentials
oc create secret generic inaturalist-etl-allas-credentials \
    --from-literal=AWS_ACCESS_KEY_ID='<your-allas-access-key>' \
    --from-literal=AWS_SECRET_ACCESS_KEY='<your-allas-secret-key>'

# Create a configmap for other settings
oc create configmap inaturalist-etl-config \
    --from-literal=S3_BUCKET='your-bucket-name' \
    --from-literal=S3_ENDPOINT_URL='https://a3s.fi' \
    --from-literal=ETL_TARGET='production' \
    --from-literal=ETL_MODE='auto' \
    --from-literal=ETL_FULL_LOGGING='true' \
    --from-literal=ETL_SLEEP='5'

# In your deployment YAML, reference them:
# envFrom:
#   - secretRef:
#       name: inaturalist-etl-allas-credentials
#   - configMapRef:
#       name: inaturalist-etl-config
```

### Example Deployment YAML:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inaturalist-etl
spec:
  replicas: 1
  selector:
    matchLabels:
      app: inaturalist-etl
  template:
    metadata:
      labels:
        app: inaturalist-etl
    spec:
      containers:
      - name: inaturalist-etl
        image: your-registry/inaturalist-etl:latest
        env:
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: inaturalist-etl-allas-credentials
              key: AWS_ACCESS_KEY_ID
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: inaturalist-etl-allas-credentials
              key: AWS_SECRET_ACCESS_KEY
        - name: S3_BUCKET
          value: "your-bucket-name"
        - name: S3_ENDPOINT_URL
          value: "https://a3s.fi"
        - name: S3_USERS_FILE
          value: "inaturalist-suomi-20-users.csv"  # Optional, defaults to this
        - name: S3_OBSERVATIONS_FILE
          value: "latest.tsv"  # Optional, defaults to this
        # Default command: inat.py production auto true 5
        # Override with args if needed:
        # args: ["python3", "inat.py", "staging", "auto", "false", "10"]
```

Create the secret:
```bash
oc create secret generic inaturalist-etl-allas-credentials \
    --from-literal=AWS_ACCESS_KEY_ID='<your-allas-access-key>' \
    --from-literal=AWS_SECRET_ACCESS_KEY='<your-allas-secret-key>'
```

## Step 4: Test the Setup

1. Build and push your container image
2. Deploy to OpenShift with the environment variables set
3. Check the container logs to verify:
   - Files are downloaded successfully from Allas
   - ETL process starts correctly

```bash
# View logs
oc logs -f deployment/inaturalist-etl
```

## Security Best Practices

1. **Never commit credentials to git** - Use OpenShift Secrets
2. **Rotate access keys regularly** - Set up a rotation schedule
3. **Use least privilege** - Only grant read access to the specific files needed
4. **Enable bucket encryption** - Encrypt data at rest in Allas (if available)
5. **Monitor access** - Review access logs if available
6. **Use different buckets/keys for staging and production** - Isolate environments

## Troubleshooting

### Error: "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set"
- Verify environment variables are set in your OpenShift deployment
- Check that secrets are properly referenced

### Error: "Failed to download file from Allas"
- Verify bucket name is correct
- Ensure `S3_ENDPOINT_URL` is set to `https://a3s.fi`
- Check that your Allas credentials have read access to the bucket
- Verify file paths in Allas match `S3_USERS_FILE` and `S3_OBSERVATIONS_FILE`
- Verify credentials are correct and not expired
- The entrypoint script automatically sets required checksum validation environment variables for Allas

### Error: "Access Denied"
- Verify your Allas credentials have read permissions for the bucket
- Check that the bucket exists and is accessible
- Ensure access key hasn't been disabled or revoked

### Files not found
- Verify file names in Allas match your configuration
- Check file paths don't have leading slashes (use `file.csv` not `/file.csv`)
- Verify files were uploaded successfully to Allas

## Additional Resources

- [CSC Allas Documentation](https://docs.csc.fi/data/Allas/)
- [Using Allas with Python and boto3](https://docs.csc.fi/data/Allas/using_allas/python_boto3/)
