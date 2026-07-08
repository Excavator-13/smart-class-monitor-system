package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "告警信息")
public class AlertVO {

    @Schema(description = "告警主键", example = "10086")
    private Long id;

    @Schema(description = "事件唯一ID", example = "evt_20260707102030001")
    private String eventId;

    @Schema(description = "视频源ID", example = "classroom_01")
    private String streamId;

    @Schema(description = "视频源名称", example = "一号教室")
    private String streamName;

    @Schema(description = "学生ID")
    private Long studentId;

    @Schema(description = "学生姓名", example = "张三")
    private String studentName;

    @Schema(description = "告警类型", example = "phone_usage")
    private String alertType;

    @Schema(description = "告警等级", example = "warning")
    private String level;

    @Schema(description = "告警状态", example = "unhandled")
    private String status;

    @Schema(description = "置信度", example = "0.91")
    private Double confidence;

    @Schema(description = "截图URL（相对路径）", example = "/snapshots/20260707/phone_0001.jpg")
    private String snapshotUrl;

    @Schema(description = "录像URL（相对路径）", example = "/classroom_01-2026-07-07-10_30_00.mp4")
    private String recordUrl;

    @Schema(description = "发生时间", example = "2026-07-07 10:21:35")
    private String occurredAt;

    @Schema(description = "处理时间")
    private String handledAt;

    @Schema(description = "处理备注")
    private String remark;

    // getters/setters
    public Long getId() { return id; }
    public void setId(Long v) { this.id = v; }
    public String getEventId() { return eventId; }
    public void setEventId(String v) { this.eventId = v; }
    public String getStreamId() { return streamId; }
    public void setStreamId(String v) { this.streamId = v; }
    public String getStreamName() { return streamName; }
    public void setStreamName(String v) { this.streamName = v; }
    public Long getStudentId() { return studentId; }
    public void setStudentId(Long v) { this.studentId = v; }
    public String getStudentName() { return studentName; }
    public void setStudentName(String v) { this.studentName = v; }
    public String getAlertType() { return alertType; }
    public void setAlertType(String v) { this.alertType = v; }
    public String getLevel() { return level; }
    public void setLevel(String v) { this.level = v; }
    public String getStatus() { return status; }
    public void setStatus(String v) { this.status = v; }
    public Double getConfidence() { return confidence; }
    public void setConfidence(Double v) { this.confidence = v; }
    public String getSnapshotUrl() { return snapshotUrl; }
    public void setSnapshotUrl(String v) { this.snapshotUrl = v; }
    public String getRecordUrl() { return recordUrl; }
    public void setRecordUrl(String v) { this.recordUrl = v; }
    public String getOccurredAt() { return occurredAt; }
    public void setOccurredAt(String v) { this.occurredAt = v; }
    public String getHandledAt() { return handledAt; }
    public void setHandledAt(String v) { this.handledAt = v; }
    public String getRemark() { return remark; }
    public void setRemark(String v) { this.remark = v; }
}
