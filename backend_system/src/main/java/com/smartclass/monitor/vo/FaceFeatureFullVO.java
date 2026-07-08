package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

import java.util.List;

@Schema(description = "人脸特征完整数据（AI 内部接口专用，含特征向量）")
public class FaceFeatureFullVO {

    @Schema(description = "人员编号", example = "2024001")
    private String studentId;

    @Schema(description = "姓名", example = "张三")
    private String studentName;

    @Schema(description = "班级")
    private String className;

    @Schema(description = "特征向量（仅 AI 内部可获取）")
    private List<Double> featureVector;

    @Schema(description = "特征维度", example = "512")
    private Integer featureDim;

    @Schema(description = "是否启用")
    private Boolean enabled;

    public String getStudentId() { return studentId; }
    public void setStudentId(String v) { this.studentId = v; }
    public String getStudentName() { return studentName; }
    public void setStudentName(String v) { this.studentName = v; }
    public String getClassName() { return className; }
    public void setClassName(String v) { this.className = v; }
    public List<Double> getFeatureVector() { return featureVector; }
    public void setFeatureVector(List<Double> v) { this.featureVector = v; }
    public Integer getFeatureDim() { return featureDim; }
    public void setFeatureDim(Integer v) { this.featureDim = v; }
    public Boolean getEnabled() { return enabled; }
    public void setEnabled(Boolean v) { this.enabled = v; }
}
