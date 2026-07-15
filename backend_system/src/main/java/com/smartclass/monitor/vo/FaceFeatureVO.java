package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "人脸特征元数据（前端用，不含特征向量）")
public class FaceFeatureVO {

    @Schema(description = "特征记录ID")
    private Long id;

    @Schema(description = "注册图片路径")
    private String imagePath;

    @Schema(description = "质量评分", example = "0.91")
    private Double qualityScore;

    @Schema(description = "质量详情 JSON")
    private String qualityJson;

    @Schema(description = "人脸框 JSON")
    private String bboxJson;

    @Schema(description = "特征维度", example = "512")
    private Integer featureDim;

    @Schema(description = "版本号")
    private Integer version;

    @Schema(description = "创建时间")
    private String createdAt;

    public Long getId() { return id; }
    public void setId(Long v) { this.id = v; }
    public String getImagePath() { return imagePath; }
    public void setImagePath(String v) { this.imagePath = v; }
    public Double getQualityScore() { return qualityScore; }
    public void setQualityScore(Double v) { this.qualityScore = v; }
    public String getQualityJson() { return qualityJson; }
    public void setQualityJson(String v) { this.qualityJson = v; }
    public String getBboxJson() { return bboxJson; }
    public void setBboxJson(String v) { this.bboxJson = v; }
    public Integer getFeatureDim() { return featureDim; }
    public void setFeatureDim(Integer v) { this.featureDim = v; }
    public Integer getVersion() { return version; }
    public void setVersion(Integer v) { this.version = v; }
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String v) { this.createdAt = v; }
}
