package com.smartclass.monitor.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class RecordingFile {
    private Long id;
    private String streamId;
    private String eventId;
    private String filePath;
    private String fileName;
    private String fileExt;
    private Long fileSize;
    private LocalDateTime startedAt;
    private LocalDateTime endedAt;
    private Double durationSeconds;
    private String sourceType;
    private LocalDateTime createdAt;
    private LocalDateTime deletedAt;
}
