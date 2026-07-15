package com.smartclass.monitor.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

@Schema(description = "新增区域请求")
public class ZoneCreateRequest {

    @NotBlank @Schema(description = "视频源业务标识", example = "classroom_01")
    private String streamId;

    @NotBlank @Schema(description = "区域名称", example = "讲台危险区")
    private String zoneName;

    @NotBlank @Schema(description = "区域类型: danger/phone_forbidden", example = "danger")
    @Pattern(regexp = "^(danger|phone_forbidden)$", message = "区域类型必须为 danger 或 phone_forbidden")
    private String zoneType;

    @Schema(description = "归一化坐标 JSON (0-1 比例)", example = "[{\"x\":0.1,\"y\":0.2},{\"x\":0.5,\"y\":0.2},{\"x\":0.5,\"y\":0.5},{\"x\":0.1,\"y\":0.5}]")
    private String coordinates;

    @Schema(description = "停留阈值（秒）", example = "30")
    private Integer thresholdSeconds;

    @Schema(description = "接近预警距离（归一化比例）", example = "0.05")
    private Double safeDistance;

    public String getStreamId() { return streamId; }
    public void setStreamId(String v) { this.streamId = v; }
    public String getZoneName() { return zoneName; }
    public void setZoneName(String v) { this.zoneName = v; }
    public String getZoneType() { return zoneType; }
    public void setZoneType(String v) { this.zoneType = v; }
    public String getCoordinates() { return coordinates; }
    public void setCoordinates(String v) { this.coordinates = v; }
    public Integer getThresholdSeconds() { return thresholdSeconds; }
    public void setThresholdSeconds(Integer v) { this.thresholdSeconds = v; }
    public Double getSafeDistance() { return safeDistance; }
    public void setSafeDistance(Double v) { this.safeDistance = v; }
}