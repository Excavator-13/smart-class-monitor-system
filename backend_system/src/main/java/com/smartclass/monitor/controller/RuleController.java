package com.smartclass.monitor.controller;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.dto.RuleCreateRequest;
import com.smartclass.monitor.dto.RuleUpdateRequest;
import com.smartclass.monitor.security.RequireRole;
import com.smartclass.monitor.service.RuleService;
import com.smartclass.monitor.vo.RuleVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@Tag(name = "frontend-api", description = "前端业务接口")
public class RuleController {

    private final RuleService ruleService;

    public RuleController(RuleService ruleService) {
        this.ruleService = ruleService;
    }

    @GetMapping("/rules")
    @Operation(summary = "查询规则列表", description = "按 rule_type 过滤行为检测规则")
    public ApiResponse<List<RuleVO>> list(@RequestParam(required = false) String ruleType) {
        return ApiResponse.success(ruleService.listRules(ruleType));
    }

    @PostMapping("/rules")
    @Operation(summary = "新增规则", description = "创建行为检测规则，含置信度阈值和冷却时间")
    @RequireRole("admin")
    public ApiResponse<RuleVO> create(@Valid @RequestBody RuleCreateRequest request) {
        return ApiResponse.success(ruleService.createRule(request));
    }

    @GetMapping("/rules/{id}")
    @Operation(summary = "规则详情", description = "根据主键 id 查询规则详情")
    public ApiResponse<RuleVO> detail(@PathVariable Long id) {
        return ApiResponse.success(ruleService.getRuleById(id));
    }

    @PutMapping("/rules/{id}")
    @Operation(summary = "更新规则", description = "更新规则阈值、置信度、冷却时间等，修改后通知 AI 刷新")
    @RequireRole("admin")
    public ApiResponse<Void> update(@PathVariable Long id, @RequestBody RuleUpdateRequest request) {
        ruleService.updateRule(id, request);
        return ApiResponse.success();
    }

    @DeleteMapping("/rules/{id}")
    @Operation(summary = "删除规则", description = "软删除规则，初版谨慎开放")
    @RequireRole("admin")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        ruleService.deleteRule(id);
        return ApiResponse.success();
    }
}