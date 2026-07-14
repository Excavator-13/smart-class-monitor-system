#!/bin/bash
WATCH_DIR="/usr/local/rtmp_video"
SEGMENTS_DIR="/usr/local/rtmp_video/segments"

DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_NAME="appdb"
DB_USER="root"
DB_PASS="MySQL@186zhunshixiaban3435"

insert_recording() {
    local FILE_PATH="$1"
    local SOURCE_TYPE="$2"
    local FNAME=$(basename "$FILE_PATH")
    local FEXT="${FNAME##*.}"
    local FSIZE=$(stat -c%s "$FILE_PATH" 2>/dev/null || echo 0)
    local MTIME=$(stat -c%Y "$FILE_PATH" 2>/dev/null || echo 0)
    local MEDIA_DURATION=$(ffprobe -v error -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 "$FILE_PATH" 2>/dev/null | tr -d '\r')

    local STREAM_ID=""
    local STARTED_AT=""
    local DURATION=0
    local ENDED_AT=""
    local HAS_MEDIA_DURATION=false

    if [[ "$MEDIA_DURATION" =~ ^[0-9]+([.][0-9]+)?$ ]] && \
       awk -v duration="$MEDIA_DURATION" 'BEGIN { exit !(duration > 0) }'; then
        HAS_MEDIA_DURATION=true
    fi

    if [ "$SOURCE_TYPE" = "segment" ]; then
        # 格式: classroom_01-2026-07-13-08_30_00.mp4
        if [[ "$FNAME" =~ ^(.+)-([0-9]{4}-[0-9]{2}-[0-9]{2})-([0-9]{2})_([0-9]{2})_([0-9]{2})\. ]]; then
            STREAM_ID="${BASH_REMATCH[1]}"
            STARTED_AT="${BASH_REMATCH[2]} ${BASH_REMATCH[3]}:${BASH_REMATCH[4]}:${BASH_REMATCH[5]}"
        fi
        if [ -n "$STARTED_AT" ]; then
            local START_EPOCH=$(date -d "$STARTED_AT" +%s 2>/dev/null || echo 0)
            if [ "$START_EPOCH" -gt 0 ]; then
                if [ "$HAS_MEDIA_DURATION" = true ]; then
                    DURATION="$MEDIA_DURATION"
                else
                    DURATION=30
                    echo "$(date) ffprobe 未读取到有效时长，切片回退 30 秒: $FNAME" >> /var/log/flv2mp4_error.log
                fi
                # recording_file.ended_at 精确到秒；向上取整可避免截断小数后产生查询空洞。
                local DURATION_CEIL=$(awk -v duration="$DURATION" \
                    'BEGIN { whole = int(duration); print (duration > whole ? whole + 1 : whole) }')
                local END_EPOCH=$(( START_EPOCH + DURATION_CEIL ))
                ENDED_AT=$(date -d "@$END_EPOCH" +"%Y-%m-%d %H:%M:%S")
            fi
        fi
    else
        # 格式: classroom_01-1783569094-2026-07-09-11_51_34.mp4
        if [[ "$FNAME" =~ ^(.+)-[0-9]+-([0-9]{4}-[0-9]{2}-[0-9]{2})-([0-9]{2})_([0-9]{2})_([0-9]{2})\. ]]; then
            STREAM_ID="${BASH_REMATCH[1]}"
            STARTED_AT="${BASH_REMATCH[2]} ${BASH_REMATCH[3]}:${BASH_REMATCH[4]}:${BASH_REMATCH[5]}"
        fi
        if [ -n "$STARTED_AT" ]; then
            local START_EPOCH=$(date -d "$STARTED_AT" +%s 2>/dev/null || echo 0)
            if [ "$START_EPOCH" -gt 0 ] && [ "$HAS_MEDIA_DURATION" = true ]; then
                DURATION="$MEDIA_DURATION"
                local DURATION_CEIL=$(awk -v duration="$DURATION" \
                    'BEGIN { whole = int(duration); print (duration > whole ? whole + 1 : whole) }')
                local END_EPOCH=$(( START_EPOCH + DURATION_CEIL ))
                ENDED_AT=$(date -d "@$END_EPOCH" +"%Y-%m-%d %H:%M:%S")
            elif [ "$START_EPOCH" -gt 0 ] && [ "$MTIME" -gt 0 ]; then
                DURATION=$(( MTIME - START_EPOCH ))
                ENDED_AT=$(date -d "@$MTIME" +"%Y-%m-%d %H:%M:%S")
                echo "$(date) ffprobe 未读取到有效时长，完整录像回退 mtime: $FNAME" >> /var/log/flv2mp4_error.log
            fi
        fi
    fi

    [ -z "$STREAM_ID" ] && return

    local REL_DIR=$(dirname "$FILE_PATH")
    REL_DIR="${REL_DIR#$WATCH_DIR}"
    [ -z "$REL_DIR" ] && REL_DIR="/"
    [ "${REL_DIR:0:1}" != "/" ] && REL_DIR="/$REL_DIR"

    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" ${DB_PASS:+-p"$DB_PASS"} "$DB_NAME" -e \
        "INSERT INTO recording_file (stream_id, event_id, file_path, file_name, file_ext, file_size, started_at, ended_at, duration_seconds, source_type)
         VALUES ('$STREAM_ID', NULL, '$REL_DIR', '$FNAME', '$FEXT', $FSIZE, ${STARTED_AT:+\"$STARTED_AT\"}, ${ENDED_AT:+\"$ENDED_AT\"}, $DURATION, '$SOURCE_TYPE');" \
        2>/dev/null && echo "$(date) 录像入库: $FNAME" || echo "$(date) 入库失败: $FNAME" >> /var/log/flv2mp4_error.log
}

process_file() {
    local FILE="$1"
    local SOURCE_TYPE="$2"
    if [[ "$FILE" == *.flv ]]; then
        MP4_FILE="${FILE%.flv}.mp4"
        ffmpeg -i "$FILE" -c copy -copyts "$MP4_FILE" > /dev/null 2>&1

        if [ $? -eq 0 ]; then
            rm -f "$FILE"
            echo "$(date) 转换成功: $FILE -> $MP4_FILE"
            insert_recording "$MP4_FILE" "$SOURCE_TYPE"
        else
            echo "$(date) 转换失败: $FILE" >> /var/log/flv2mp4_error.log
        fi
    fi
}

mkdir -p "$SEGMENTS_DIR"

inotifywait -m -r -e close_write --format '%w%f' "$WATCH_DIR" | while read FILE
do
    if [[ "$FILE" == "$SEGMENTS_DIR"* ]]; then
        process_file "$FILE" "segment"
    else
        process_file "$FILE" "nginx_record"
    fi
done