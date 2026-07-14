package com.smartclass.monitor.controller;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.security.RequireRole;
import com.smartclass.monitor.service.ScoreConfigService;
import com.smartclass.monitor.vo.ScoreConfigVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@Tag(name = "frontend-api", description = "前端业务接口")
public class ScoreConfigController {

    private final ScoreConfigService scoreConfigService;

    public ScoreConfigController(ScoreConfigService scoreConfigService) {
        this.scoreConfigService = scoreConfigService;
    }

    @GetMapping("/score-config")
    @Operation(summary = "查询告警评分配置", description = "返回所有告警类型的评分权重配置")
    public ApiResponse<List<ScoreConfigVO>> list() {
        return ApiResponse.success(scoreConfigService.listAll());
    }

    @PutMapping("/score-config/{id}")
    @Operation(summary = "修改评分配置", description = "修改告警评分权重，仅管理员可操作")
    @RequireRole("admin")
    public ApiResponse<ScoreConfigVO> update(@PathVariable Long id,
                                             @RequestParam(required = false) String label,
                                             @RequestParam(required = false) String level,
                                             @RequestParam(required = false) Integer score,
                                             @RequestParam(required = false) String note) {
        return ApiResponse.success(scoreConfigService.updateConfig(id, label, level, score, note));
    }
}
