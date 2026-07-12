package com.smartclass.monitor.controller;

import com.smartclass.monitor.service.ReportService;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/settings")
public class SettingsController {

    private final Map<String, Object> store = new LinkedHashMap<>();
    private final ReportService reportService;

    public SettingsController(ReportService reportService) {
        this.reportService = reportService;
    }

    @PutMapping
    public Map<String, Object> update(@RequestBody Map<String, Object> body) {
        store.putAll(body);
        reportService.updateSettings(body);  // 通知定时任务
        return Map.of("ok", true, "stored", store.keySet());
    }

    @GetMapping
    public Map<String, Object> get() {
        return store.isEmpty()
            ? Map.of("contacts", List.of(
                Map.of("name","项重善","mobile","18601033435"),
                Map.of("name","章志超","mobile","15270985055")),
              "reportTime","18:00")
            : store;
    }
}
