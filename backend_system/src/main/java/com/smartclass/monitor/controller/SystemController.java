package com.smartclass.monitor.controller;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.integration.AiClient;
import com.smartclass.monitor.integration.NginxClient;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;
import java.sql.Connection;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 系统健康检查控制器。
 * 返回 backend、database、AI、RTMP 四组件状态。
 * 任一组件不可用时仍返回 HTTP 200，标记对应组件为 down/degraded。
 */
@RestController
@Tag(name = "system-api", description = "系统健康检查 / 日志 / 运维接口")
public class SystemController {

    private static final Logger log = LoggerFactory.getLogger(SystemController.class);

    private final DataSource dataSource;
    private final AiClient aiClient;
    private final NginxClient nginxClient;

    public SystemController(DataSource dataSource, AiClient aiClient, NginxClient nginxClient) {
        this.dataSource = dataSource;
        this.aiClient = aiClient;
        this.nginxClient = nginxClient;
    }

    @GetMapping("/system/health")
    @Operation(summary = "系统健康检查", description = "返回后端、数据库、AI 服务、Nginx RTMP 状态。组件不可用时标记 down，仍返回 HTTP 200")
    public ApiResponse<Map<String, Object>> health() {
        Map<String, Object> status = new LinkedHashMap<>();
        status.put("backend", "up");
        status.put("database", checkDatabase());
        status.put("ai", checkAi());
        status.put("rtmp", checkRtmp());
        status.put("timestamp", LocalDateTime.now().toString());
        return ApiResponse.success(status);
    }

    private String checkDatabase() {
        try (Connection conn = dataSource.getConnection()) {
            return conn.isValid(3) ? "up" : "down";
        } catch (Exception e) {
            log.warn("Database health check failed: {}", e.getMessage());
            return "down";
        }
    }

    private String checkAi() {
        try {
            return aiClient.checkHealth() ? "up" : "down";
        } catch (Exception e) {
            log.warn("AI health check failed: {}", e.getMessage());
            return "down";
        }
    }

    private String checkRtmp() {
        try {
            return nginxClient.checkHealth() ? "up" : "down";
        } catch (Exception e) {
            log.warn("RTMP health check failed: {}", e.getMessage());
            return "down";
        }
    }
}
