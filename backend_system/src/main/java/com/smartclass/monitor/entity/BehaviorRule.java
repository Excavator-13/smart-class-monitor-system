package com.smartclass.monitor.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class BehaviorRule {
    private Long id;
    private String ruleType;
    private String ruleName;
    private Boolean enabled;
    private Integer thresholdSeconds;
    private Double confidenceThreshold;
    private Integer cooldownSeconds;
    private String level;
    private String configJson;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private LocalDateTime deletedAt;
}
