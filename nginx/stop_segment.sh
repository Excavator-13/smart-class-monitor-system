#!/bin/bash
STREAM_NAME=$1
PID_FILE="/tmp/ffmpeg_seg_${STREAM_NAME}.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    kill "$PID" 2>/dev/null
    rm -f "$PID_FILE"
fi