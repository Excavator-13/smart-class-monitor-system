package com.smartclass.monitor.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "编辑视频源请求")
public class StreamUpdateRequest {

    @Schema(description = "视频源展示名称", example = "一号教室")
    private String streamName;

    @Schema(description = "RTMP 推拉流地址", example = "rtmp://39.106.209.208:9090/live/classroom_01")
    private String rtmpUrl;

    @Schema(description = "配置状态：enabled / disabled", example = "enabled")
    private String status;

    @Schema(description = "备注")
    private String remark;

    public String getStreamName() { return streamName; }
    public void setStreamName(String v) { this.streamName = v; }
    public String getRtmpUrl() { return rtmpUrl; }
    public void setRtmpUrl(String v) { this.rtmpUrl = v; }
    public String getStatus() { return status; }
    public void setStatus(String v) { this.status = v; }
    public String getRemark() { return remark; }
    public void setRemark(String v) { this.remark = v; }
}
