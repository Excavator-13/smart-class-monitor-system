package com.smartclass.monitor.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;

@Schema(description = "告警状态更新请求")
public class AlertStatusUpdateRequest {

    @NotBlank @Schema(description = "目标状态", example = "processing")
    private String status;

    @Schema(description = "处理人 ID", example = "1")
    private Long handlerId;

    @Schema(description = "处理备注", example = "已确认，正在处理")
    private String remark;

    public String getStatus() { return status; }
    public void setStatus(String v) { this.status = v; }
    public Long getHandlerId() { return handlerId; }
    public void setHandlerId(Long v) { this.handlerId = v; }
    public String getRemark() { return remark; }
    public void setRemark(String v) { this.remark = v; }
}
