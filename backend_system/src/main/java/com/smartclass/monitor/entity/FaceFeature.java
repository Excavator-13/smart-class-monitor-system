package com.smartclass.monitor.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class FaceFeature {
    private Long id;
    private Long studentId;
    private Integer featureDim;
    private String featureVector;  // JSON string from MySQL JSON column
    private String imagePath;
    private Double qualityScore;
    private String qualityJson;
    private String bboxJson;
    private String modelName;
    private String modelVersion;
    private Integer version;
    private Boolean enabled;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private LocalDateTime deletedAt;
}
