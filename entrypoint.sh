#!/bin/bash

echo "user:x:$(id -u):0::/home/user:/sbin/nologin" >> /etc/passwd

rclone sync "store" "default:$OBJECT_STORE_PUBLIC"

rclone sync "privatedata" "default:$OBJECT_STORE_PRIVATE"

"$@"
