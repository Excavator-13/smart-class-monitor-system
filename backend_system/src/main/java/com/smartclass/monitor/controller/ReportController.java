package com.smartclass.monitor.controller;

import com.smartclass.monitor.service.ReportService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

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
        return reportService.generateReport(reportService.queryTodayAlerts());
    }

    @GetMapping("/history")
    public List<Map<String, Object>> history() {
        return reportService.getHistory();
    }

    @GetMapping("/{date}")
    public ResponseEntity<Map<String, Object>> getByDate(@PathVariable String date) {
        Map<String, Object> report = reportService.getReportByDate(date);
        if (report == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("message", "日报不存在: " + date));
        }
        return ResponseEntity.ok(report);
    }
}