package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "操作日志")
public class OperationLogVO {

    @Schema(description = "日志主键", example = "1")
    private Long id;

    @Schema(description = "操作人ID", example = "1")
    private Long userId;

    @Schema(description = "操作用户名", example = "admin")
    private String username;

    @Schema(description = "操作动作", example = "create_stream")
    private String action;

    @Schema(description = "目标类型", example = "stream")
    private String targetType;

    @Schema(description = "目标ID", example = "classroom_01")
    private String targetId;

    @Schema(description = "HTTP 方法", example = "POST")
    private String method;

    @Schema(description = "请求路径", example = "/streams")
    private String requestUri;

    @Schema(description = "客户端 IP", example = "192.168.1.100")
    private String requestIp;

    @Schema(description = "响应 code", example = "0")
    private Integer resultCode;

    @Schema(description = "响应摘要", example = "success")
    private String resultMessage;

    @Schema(description = "操作时间", example = "2026-07-08 10:30:00")
    private String createdAt;

    public Long getId() { return id; }
    public void setId(Long v) { this.id = v; }
    public Long getUserId() { return userId; }
    public void setUserId(Long v) { this.userId = v; }
    public String getUsername() { return username; }
    public void setUsername(String v) { this.username = v; }
    public String getAction() { return action; }
    public void setAction(String v) { this.action = v; }
    public String getTargetType() { return targetType; }
    public void setTargetType(String v) { this.targetType = v; }
    public String getTargetId() { return targetId; }
    public void setTargetId(String v) { this.targetId = v; }
    public String getMethod() { return method; }
    public void setMethod(String v) { this.method = v; }
    public String getRequestUri() { return requestUri; }
    public void setRequestUri(String v) { this.requestUri = v; }
    public String getRequestIp() { return requestIp; }
    public void setRequestIp(String v) { this.requestIp = v; }
    public Integer getResultCode() { return resultCode; }
    public void setResultCode(Integer v) { this.resultCode = v; }
    public String getResultMessage() { return resultMessage; }
    public void setResultMessage(String v) { this.resultMessage = v; }
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String v) { this.createdAt = v; }
}
