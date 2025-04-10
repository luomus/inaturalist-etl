#!/bin/bash

i="all"
f="template.yml"
e=".env"

while getopts ":f:e:i::" flag; do
  case $flag in
    f) f=${OPTARG} ;;
    e) e=${OPTARG} ;;
    i) i=${OPTARG} ;;
  esac
done

set -a

source ./$e

set +a

BRANCH=$(git symbolic-ref --short -q HEAD)

if [ "$BRANCH" != "main" ]; then

  OBJECT_STORE_PRIVATE=$OBJECT_STORE_PRIVATE_DEV
  OBJECT_STORE_PUBLIC=$OBJECT_STORE_PUBLIC_DEV
  JOB_COMMAND=$JOB_COMMAND_DEV
  JOB_SCHEDULE=$JOB_SCHEDULE_DEV

fi

if [ $i = "config" ]; then

  ITEM=".items[0]"

elif [ $i = "secrets" ]; then

  ITEM=".items[1]"

elif [ $i = "job" ]; then

  ITEM=".items[2]"

elif [ $i = "all" ]; then

  ITEM=""

else

  echo "Object not found"
  exit 1

fi

LAJI_STAGING_TOKEN=$(echo -n $LAJI_STAGING_TOKEN | base64)
LAJI_PRODUCTION_TOKEN=$(echo -n $LAJI_PRODUCTION_TOKEN | base64)
RCLONE_ACCESS_KEY_ID=$(echo -n $RCLONE_ACCESS_KEY_ID | base64)
RCLONE_SECRET_ACCESS_KEY=$(echo -n $RCLONE_SECRET_ACCESS_KEY | base64)

echo "# $(oc project inaturalist-etl)"

oc process -f $f \
  -p BRANCH="$BRANCH" \
  -p LAJI_STAGING_TOKEN="$LAJI_STAGING_TOKEN" \
  -p LAJI_PRODUCTION_TOKEN="$LAJI_PRODUCTION_TOKEN" \
  -p OBJECT_STORE_PRIVATE="$OBJECT_STORE_PRIVATE" \
  -p OBJECT_STORE_PUBLIC="$OBJECT_STORE_PUBLIC" \
  -p RCLONE_ACCESS_KEY_ID="$RCLONE_ACCESS_KEY_ID" \
  -p RCLONE_SECRET_ACCESS_KEY="$RCLONE_SECRET_ACCESS_KEY" \
  -p JOB_COMMAND="$JOB_COMMAND" \
  -p JOB_SCHEDULE="$JOB_SCHEDULE" \
  | jq $ITEM