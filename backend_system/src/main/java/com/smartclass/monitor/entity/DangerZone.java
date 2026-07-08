package com.smartclass.monitor.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class DangerZone {
    private Long id;
    private String streamId;
    private String zoneName;
    private String zoneType;
    private String shapeType;
    private String coordinates;    // JSON
    private Integer thresholdSeconds;
    private Double safeDistance;
    private Boolean enabled;
    private String configJson;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private LocalDateTime deletedAt;
}
