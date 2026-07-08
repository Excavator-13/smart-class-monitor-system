package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

import java.util.List;

@Schema(description = "人脸注册结果")
public class FaceRegisterResponse {

    @Schema(description = "检测到的人脸数量", example = "1")
    private int faceCount;

    @Schema(description = "特征维度", example = "512")
    private int featureDim;

    @Schema(description = "质量评分", example = "0.91")
    private double qualityScore;

    @Schema(description = "人脸框坐标 [x, y, w, h]", example = "[160, 80, 320, 260]")
    private List<Integer> bbox;

    public int getFaceCount() { return faceCount; }
    public void setFaceCount(int v) { this.faceCount = v; }
    public int getFeatureDim() { return featureDim; }
    public void setFeatureDim(int v) { this.featureDim = v; }
    public double getQualityScore() { return qualityScore; }
    public void setQualityScore(double v) { this.qualityScore = v; }
    public List<Integer> getBbox() { return bbox; }
    public void setBbox(List<Integer> v) { this.bbox = v; }
}
