package com.smartclass.monitor.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "编辑区域请求")
public class ZoneUpdateRequest {

    @Schema(description = "区域名称", example = "讲台危险区")
    private String zoneName;

    @Schema(description = "归一化坐标 JSON", example = "[{\"x\":0.1,\"y\":0.2},{\"x\":0.5,\"y\":0.5}]")
    private String coordinates;

    @Schema(description = "停留阈值（秒）", example = "30")
    private Integer thresholdSeconds;

    @Schema(description = "接近预警距离", example = "0.05")
    private Double safeDistance;

    @Schema(description = "是否启用", example = "true")
    private Boolean enabled;

    public String getZoneName() { return zoneName; }
    public void setZoneName(String v) { this.zoneName = v; }
    public String getCoordinates() { return coordinates; }
    public void setCoordinates(String v) { this.coordinates = v; }
    public Integer getThresholdSeconds() { return thresholdSeconds; }
    public void setThresholdSeconds(Integer v) { this.thresholdSeconds = v; }
    public Double getSafeDistance() { return safeDistance; }
    public void setSafeDistance(Double v) { this.safeDistance = v; }
    public Boolean getEnabled() { return enabled; }
    public void setEnabled(Boolean v) { this.enabled = v; }
}
