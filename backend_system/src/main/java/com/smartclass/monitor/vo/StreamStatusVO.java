package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "视频源推流状态")
public class StreamStatusVO {

    @Schema(description = "业务标识", example = "classroom_01")
    private String streamId;

    @Schema(description = "是否在线", example = "true")
    private boolean online;

    @Schema(description = "推流时长/开始时间", example = "2026-07-07T10:00:00+08:00")
    private String uptime;

    @Schema(description = "状态：online / offline / unknown", example = "online")
    private String status;

    public String getStreamId() { return streamId; }
    public void setStreamId(String v) { this.streamId = v; }
    public boolean isOnline() { return online; }
    public void setOnline(boolean v) { this.online = v; }
    public String getUptime() { return uptime; }
    public void setUptime(String v) { this.uptime = v; }
    public String getStatus() { return status; }
    public void setStatus(String v) { this.status = v; }
}
