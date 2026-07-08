package com.smartclass.monitor.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

@Schema(description = "AI 告警入库请求")
public class AlertIngestRequest {

    @NotBlank @Schema(description = "AI 生成的事件唯一 ID", example = "evt_20260707102030001")
    private String eventId;

    @NotBlank @Schema(description = "视频源 ID", example = "classroom_01")
    private String streamId;

    @NotBlank @Schema(description = "告警类型", example = "flame_detected")
    private String alertType;

    @Schema(description = "告警中文名称", example = "明火检测")
    private String alertName;

    @NotBlank @Schema(description = "告警等级", example = "high")
    private String level;

    @Schema(description = "置信度 0-1", example = "0.91")
    private Double confidence;

    @NotBlank @Schema(description = "事件发生时间 ISO 8601", example = "2026-07-07T10:20:30+08:00")
    private String occurredAt;

    @Schema(description = "持续时间（秒）", example = "1.5")
    private Double durationSeconds;

    @Schema(description = "关联学生 ID")
    private String studentId;

    @Schema(description = "目标信息 {track_id, bbox}")
    private Object targetInfo;

    @Schema(description = "关联区域 ID")
    private Long zoneId;

    @Schema(description = "截图相对路径（必须以 / 开头）", example = "/snapshots/20260707/evt_xxx.jpg")
    private String snapshotPath;

    @Schema(description = "录像相对路径（必须以 / 开头）", example = "/records/20260707/classroom_01.flv")
    private String recordPath;

    @Schema(description = "事件在录像中的偏移秒数", example = "630.5")
    private Double eventTimeOffset;

    @Schema(description = "扩展信息（模型名、触发规则等）")
    private Object extra;

    public String getEventId() { return eventId; }
    public void setEventId(String v) { this.eventId = v; }
    public String getStreamId() { return streamId; }
    public void setStreamId(String v) { this.streamId = v; }
    public String getAlertType() { return alertType; }
    public void setAlertType(String v) { this.alertType = v; }
    public String getAlertName() { return alertName; }
    public void setAlertName(String v) { this.alertName = v; }
    public String getLevel() { return level; }
    public void setLevel(String v) { this.level = v; }
    public Double getConfidence() { return confidence; }
    public void setConfidence(Double v) { this.confidence = v; }
    public String getOccurredAt() { return occurredAt; }
    public void setOccurredAt(String v) { this.occurredAt = v; }
    public Double getDurationSeconds() { return durationSeconds; }
    public void setDurationSeconds(Double v) { this.durationSeconds = v; }
    public String getStudentId() { return studentId; }
    public void setStudentId(String v) { this.studentId = v; }
    public Object getTargetInfo() { return targetInfo; }
    public void setTargetInfo(Object v) { this.targetInfo = v; }
    public Long getZoneId() { return zoneId; }
    public void setZoneId(Long v) { this.zoneId = v; }
    public String getSnapshotPath() { return snapshotPath; }
    public void setSnapshotPath(String v) { this.snapshotPath = v; }
    public String getRecordPath() { return recordPath; }
    public void setRecordPath(String v) { this.recordPath = v; }
    public Double getEventTimeOffset() { return eventTimeOffset; }
    public void setEventTimeOffset(Double v) { this.eventTimeOffset = v; }
    public Object getExtra() { return extra; }
    public void setExtra(Object v) { this.extra = v; }
}
