#!/bin/bash
# /usr/local/script/clean_records.sh
# 删除7天前的 flv 录像文件
find /usr/local/rtmp_video -mtime +7 -name "*.flv" -exec rm -f {} \;

# 删除7天前的切片 mp4 文件
find /usr/local/rtmp_video/segments -mtime +7 -name "*.mp4" -exec rm -f {} \;

# 清理空的切片日期目录
find /usr/local/rtmp_video/segments -type d -empty -delete