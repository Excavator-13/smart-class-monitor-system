package com.smartclass.monitor.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class OperationLog {
    private Long id;
    private Long userId;
    private String username;
    private String action;
    private String targetType;
    private String targetId;
    private String method;
    private String requestUri;
    private String requestIp;
    private String requestBody;  // JSON, must be sanitized
    private Integer resultCode;
    private String resultMessage;
    private LocalDateTime createdAt;
}
