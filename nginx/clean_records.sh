#!/bin/bash
# /usr/local/script/clean_records.sh

DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_NAME="appdb"
DB_USER="root"
DB_PASS="MySQL@186zhunshixiaban3435"

mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" ${DB_PASS:+-p"$DB_PASS"} "$DB_NAME" -e \
    "DELETE FROM recording_file WHERE started_at < DATE_SUB(NOW(), INTERVAL 7 DAY);" \
    2>/dev/null

find /usr/local/rtmp_video -mtime +7 \( -name "*.flv" -o -name "*.mp4" \) -exec rm -f {} \;

find /usr/local/rtmp_video -type d -empty -delete

find /data/snapshots -mtime +7 -type f -exec rm -f {} \;

find /data/snapshots -type d -empty -delete