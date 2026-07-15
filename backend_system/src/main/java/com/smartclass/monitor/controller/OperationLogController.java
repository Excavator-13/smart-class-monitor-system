package com.smartclass.monitor.controller;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.common.response.PageResult;
import com.smartclass.monitor.security.RequireRole;
import com.smartclass.monitor.service.OperationLogService;
import com.smartclass.monitor.vo.OperationLogVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

@RestController
@Tag(name = "system-api", description = "系统健康检查 / 日志 / 运维接口")
@RequireRole("admin")
public class OperationLogController {

    private final OperationLogService operationLogService;

    public OperationLogController(OperationLogService operationLogService) {
        this.operationLogService = operationLogService;
    }

    @GetMapping("/operation-logs")
    @Operation(summary = "查询操作日志", description = "分页查询操作审计日志，支持按用户、动作、目标类型/ID、时间范围筛选")
    public ApiResponse<PageResult<OperationLogVO>> list(
            @RequestParam(required = false) Long userId,
            @RequestParam(required = false) String action,
            @RequestParam(required = false) String targetType,
            @RequestParam(required = false) String targetId,
            @RequestParam(required = false) String startTime,
            @RequestParam(required = false) String endTime,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int pageSize) {
        return ApiResponse.success(
                operationLogService.listLogs(userId, action, targetType, targetId, startTime, endTime, page, pageSize));
    }
}