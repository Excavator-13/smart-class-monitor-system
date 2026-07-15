package com.smartclass.monitor.controller;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.common.response.PageResult;
import com.smartclass.monitor.dto.AlertStatusUpdateRequest;
import com.smartclass.monitor.service.AlertService;
import com.smartclass.monitor.vo.AlertStatsVO;
import com.smartclass.monitor.vo.AlertVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@Tag(name = "frontend-api", description = "前端业务接口")
public class AlertController {

    private final AlertService alertService;

    public AlertController(AlertService alertService) {
        this.alertService = alertService;
    }

    @GetMapping("/alerts")
    @Operation(summary = "告警列表", description = "分页查询告警，支持按视频源、类型、状态、等级、时间范围筛选")
    public ApiResponse<PageResult<AlertVO>> list(
            @RequestParam(required = false) String streamId,
            @RequestParam(required = false) String alertType,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String level,
            @RequestParam(required = false) String startTime,
            @RequestParam(required = false) String endTime,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int pageSize) {
        return ApiResponse.success(
                alertService.listAlerts(streamId, alertType, status, level, startTime, endTime, page, pageSize));
    }

    @GetMapping("/alerts/{id}")
    @Operation(summary = "告警详情", description = "查询告警详情，snapshot_url 和 record_url 为相对路径")
    public ApiResponse<AlertVO> detail(@PathVariable Long id) {
        return ApiResponse.success(alertService.getAlertDetail(id));
    }

    @PutMapping("/alerts/{id}/status")
    @Operation(summary = "更新告警状态", description = "标记告警状态（unhandled/processing/handled/false_alarm/ignored）")
    public ApiResponse<Void> updateStatus(@PathVariable Long id,
                                           @Valid @RequestBody AlertStatusUpdateRequest request) {
        alertService.updateStatus(id, request);
        return ApiResponse.success();
    }

    @GetMapping("/alert-stats")
    @Operation(summary = "首页统计卡片", description = "返回今日告警数、未处理数和各类型分布")
    public ApiResponse<AlertStatsVO> stats() {
        return ApiResponse.success(alertService.getStats());
    }
}
