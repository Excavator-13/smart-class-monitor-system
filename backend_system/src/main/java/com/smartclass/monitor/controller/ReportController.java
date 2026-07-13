package com.smartclass.monitor.controller;

import com.smartclass.monitor.service.ReportService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 日报 API
 * GET  /report/latest   — 获取最新日报
 * POST /report/generate — 手动生成日报（传入告警列表）
 */
@RestController
@RequestMapping("/report")
public class ReportController {

    private final ReportService reportService;

    public ReportController(ReportService reportService) {
        this.reportService = reportService;
    }

    @GetMapping("/latest")
    public Map<String, Object> latest() {
        Map<String, Object> report = reportService.getLatestReport();
        if (report == null) {
            return Map.of("message", "暂无日报，请先调用 POST /report/generate 生成");
        }
        return report;
    }

    @PostMapping("/generate")
    public Map<String, Object> generate(@RequestBody(required = false) List<Map<String, Object>> alerts) {
        // 始终读数据库（含真实截图）
        return reportService.generateReport(reportService.queryTodayAlerts());
    }

    @GetMapping("/history")
    public List<Map<String, Object>> history() {
        return reportService.getHistory();
    }
}
