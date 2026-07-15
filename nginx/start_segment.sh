#!/bin/bash
STREAM_NAME=$1
SEG_DIR="/usr/local/rtmp_video/segments/$(date +%Y%m%d)"
mkdir -p "$SEG_DIR"

ffmpeg -i "rtmp://localhost:9090/live/$STREAM_NAME" \
       -c copy -f segment -segment_time 30 \
       -segment_format flv \
       -reset_timestamps 1 \
       -strftime 1 \
       "$SEG_DIR/${STREAM_NAME}-%Y-%m-%d-%H_%M_%S.flv" \
       &>/dev/null &

echo $! > "/tmp/ffmpeg_seg_${STREAM_NAME}.pid"