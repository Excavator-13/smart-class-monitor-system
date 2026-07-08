package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "视频源信息")
public class StreamVO {

    @Schema(description = "数据库主键", example = "1")
    private Long id;

    @Schema(description = "业务标识", example = "classroom_01")
    private String streamId;

    @Schema(description = "展示名称", example = "一号教室")
    private String streamName;

    @Schema(description = "RTMP 地址", example = "rtmp://39.106.209.208:9090/live/classroom_01")
    private String rtmpUrl;

    @Schema(description = "配置状态", example = "enabled")
    private String status;

    @Schema(description = "位置", example = "教学楼A-301")
    private String location;

    @Schema(description = "备注")
    private String remark;

    @Schema(description = "创建时间", example = "2026-07-08 10:00:00")
    private String createdAt;

    public Long getId() { return id; }
    public void setId(Long v) { this.id = v; }
    public String getStreamId() { return streamId; }
    public void setStreamId(String v) { this.streamId = v; }
    public String getStreamName() { return streamName; }
    public void setStreamName(String v) { this.streamName = v; }
    public String getRtmpUrl() { return rtmpUrl; }
    public void setRtmpUrl(String v) { this.rtmpUrl = v; }
    public String getStatus() { return status; }
    public void setStatus(String v) { this.status = v; }
    public String getLocation() { return location; }
    public void setLocation(String v) { this.location = v; }
    public String getRemark() { return remark; }
    public void setRemark(String v) { this.remark = v; }
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String v) { this.createdAt = v; }
}
