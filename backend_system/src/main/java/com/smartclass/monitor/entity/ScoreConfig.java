package com.smartclass.monitor.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class ScoreConfig {
    private Long id;
    private String alertType;
    private String label;
    private String level;
    private Integer score;
    private String note;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
