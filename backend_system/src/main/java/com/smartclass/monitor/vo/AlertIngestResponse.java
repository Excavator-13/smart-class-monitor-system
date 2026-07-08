package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "AI 告警入库响应")
public class AlertIngestResponse {

    @Schema(description = "告警主键", example = "10086")
    private Long alertId;

    @Schema(description = "告警状态", example = "unhandled")
    private String status;

    public Long getAlertId() { return alertId; }
    public void setAlertId(Long v) { this.alertId = v; }
    public String getStatus() { return status; }
    public void setStatus(String v) { this.status = v; }
}
