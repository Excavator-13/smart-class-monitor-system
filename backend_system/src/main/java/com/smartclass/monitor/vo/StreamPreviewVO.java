package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "视频源播放地址")
public class StreamPreviewVO {

    @Schema(description = "MJPEG 流地址", example = "http://localhost:5000/video_feed/classroom_01")
    private String mjpegUrl;

    @Schema(description = "RTMP 拉流地址，仅管理员和内部服务返回", example = "rtmp://localhost:9090/live/classroom_01", nullable = true)
    private String rtmpUrl;

    @Schema(description = "HLS 播放地址")
    private String hlsUrl;

    public String getMjpegUrl() { return mjpegUrl; }
    public void setMjpegUrl(String v) { this.mjpegUrl = v; }
    public String getRtmpUrl() { return rtmpUrl; }
    public void setRtmpUrl(String v) { this.rtmpUrl = v; }
    public String getHlsUrl() { return hlsUrl; }
    public void setHlsUrl(String v) { this.hlsUrl = v; }
}
