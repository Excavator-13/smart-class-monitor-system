package com.smartclass.monitor.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;

@Schema(description = "新增视频源请求")
public class StreamCreateRequest {

    @NotBlank(message = "视频源名称不能为空")
    @Schema(description = "视频源展示名称", example = "一号教室")
    private String streamName;

    @NotBlank(message = "stream_id 不能为空")
    @Schema(description = "业务标识，必须与推流端 Stream Key 一致", example = "classroom_01")
    private String streamId;

    @NotBlank(message = "RTMP 地址不能为空")
    @Schema(description = "RTMP 推拉流地址", example = "rtmp://localhost:9090/live/classroom_01")
    private String rtmpUrl;

    @Schema(description = "备注")
    private String remark;

    public String getStreamName() { return streamName; }
    public void setStreamName(String v) { this.streamName = v; }
    public String getStreamId() { return streamId; }
    public void setStreamId(String v) { this.streamId = v; }
    public String getRtmpUrl() { return rtmpUrl; }
    public void setRtmpUrl(String v) { this.rtmpUrl = v; }
    public String getRemark() { return remark; }
    public void setRemark(String v) { this.remark = v; }
}