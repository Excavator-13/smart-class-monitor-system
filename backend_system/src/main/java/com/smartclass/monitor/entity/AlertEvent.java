package com.smartclass.monitor.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class AlertEvent {
    private Long id;
    private String eventId;
    private String streamId;
    private Long studentId;
    private String alertType;
    private String alertName;
    private String level;
    private String status;
    private Double confidence;
    private Double durationSeconds;
    private Long zoneId;
    private String targetInfo;   // JSON
    private String snapshotPath;
    private String recordPath;
    private Double eventTimeOffset;
    private String extra;        // JSON
    private LocalDateTime occurredAt;
    private LocalDateTime handledAt;
    private Long handlerId;
    private String remark;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
