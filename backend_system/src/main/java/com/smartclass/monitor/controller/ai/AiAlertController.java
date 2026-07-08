package com.smartclass.monitor.controller.ai;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.dto.AlertIngestRequest;
import com.smartclass.monitor.service.AlertEventService;
import com.smartclass.monitor.vo.AlertIngestResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

/**
 * AI 内部接口 —— 告警入库。
 * 禁止前端访问，使用 X-Internal-Token 鉴权。
 */
@RestController
@Tag(name = "ai-internal-api", description = "AI 服务调用 SpringBoot 的内部接口")
public class AiAlertController {

    private final AlertEventService alertEventService;

    public AiAlertController(AlertEventService alertEventService) {
        this.alertEventService = alertEventService;
    }

    @PostMapping("/alerts/ai")
    @Operation(summary = "AI 告警入库", description = "AI 检测到异常后写入确认告警。event_id 幂等：重复提交返回已有告警")
    public ApiResponse<AlertIngestResponse> ingestAlert(@Valid @RequestBody AlertIngestRequest request) {
        return ApiResponse.success(alertEventService.ingestAlert(request));
    }
}
