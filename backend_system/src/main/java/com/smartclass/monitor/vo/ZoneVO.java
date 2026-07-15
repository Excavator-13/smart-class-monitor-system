package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "区域配置信息")
public class ZoneVO {

    @Schema(description = "区域主键", example = "1")
    private Long id;

    @Schema(description = "视频源业务标识", example = "classroom_01")
    private String streamId;

    @Schema(description = "区域名称", example = "讲台危险区")
    private String zoneName;

    @Schema(description = "区域类型", example = "danger")
    private String zoneType;

    @Schema(description = "形状类型", example = "polygon")
    private String shapeType;

    @Schema(description = "归一化坐标 JSON")
    private String coordinates;

    @Schema(description = "停留阈值（秒）", example = "30")
    private Integer thresholdSeconds;

    @Schema(description = "接近预警距离", example = "0.05")
    private Double safeDistance;

    @Schema(description = "是否启用")
    private Boolean enabled;

    @Schema(description = "创建时间", example = "2026-07-08 10:00:00")
    private String createdAt;

    public Long getId() { return id; }
    public void setId(Long v) { this.id = v; }
    public String getStreamId() { return streamId; }
    public void setStreamId(String v) { this.streamId = v; }
    public String getZoneName() { return zoneName; }
    public void setZoneName(String v) { this.zoneName = v; }
    public String getZoneType() { return zoneType; }
    public void setZoneType(String v) { this.zoneType = v; }
    public String getShapeType() { return shapeType; }
    public void setShapeType(String v) { this.shapeType = v; }
    public String getCoordinates() { return coordinates; }
    public void setCoordinates(String v) { this.coordinates = v; }
    public Integer getThresholdSeconds() { return thresholdSeconds; }
    public void setThresholdSeconds(Integer v) { this.thresholdSeconds = v; }
    public Double getSafeDistance() { return safeDistance; }
    public void setSafeDistance(Double v) { this.safeDistance = v; }
    public Boolean getEnabled() { return enabled; }
    public void setEnabled(Boolean v) { this.enabled = v; }
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String v) { this.createdAt = v; }
}
