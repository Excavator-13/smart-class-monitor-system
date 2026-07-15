package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "录像文件信息")
public class RecordingVO {

    @Schema(description = "录像主键", example = "1")
    private Long id;

    @Schema(description = "视频源ID", example = "classroom_01")
    private String streamId;

    @Schema(description = "文件名", example = "classroom_01-2026-07-07-10_30_00.mp4")
    private String fileName;

    @Schema(description = "文件相对路径", example = "/classroom_01-2026-07-07-10_30_00.mp4")
    private String filePath;

    @Schema(description = "文件扩展名", example = "mp4")
    private String fileExt;

    @Schema(description = "文件大小（字节）", example = "52428800")
    private Long fileSize;

    @Schema(description = "录像开始时间", example = "2026-07-07 10:30:00")
    private String startedAt;

    @Schema(description = "录像结束时间", example = "2026-07-07 11:30:00")
    private String endedAt;

    @Schema(description = "持续时长（秒）", example = "3600.0")
    private Double durationSeconds;

    @Schema(description = "来源类型", example = "nginx_record")
    private String sourceType;

    @Schema(description = "文件是否可用", example = "true")
    private boolean available;

    public Long getId() { return id; }
    public void setId(Long v) { this.id = v; }
    public String getStreamId() { return streamId; }
    public void setStreamId(String v) { this.streamId = v; }
    public String getFileName() { return fileName; }
    public void setFileName(String v) { this.fileName = v; }
    public String getFilePath() { return filePath; }
    public void setFilePath(String v) { this.filePath = v; }
    public String getFileExt() { return fileExt; }
    public void setFileExt(String v) { this.fileExt = v; }
    public Long getFileSize() { return fileSize; }
    public void setFileSize(Long v) { this.fileSize = v; }
    public String getStartedAt() { return startedAt; }
    public void setStartedAt(String v) { this.startedAt = v; }
    public String getEndedAt() { return endedAt; }
    public void setEndedAt(String v) { this.endedAt = v; }
    public Double getDurationSeconds() { return durationSeconds; }
    public void setDurationSeconds(Double v) { this.durationSeconds = v; }
    public String getSourceType() { return sourceType; }
    public void setSourceType(String v) { this.sourceType = v; }
    public boolean isAvailable() { return available; }
    public void setAvailable(boolean v) { this.available = v; }
}
