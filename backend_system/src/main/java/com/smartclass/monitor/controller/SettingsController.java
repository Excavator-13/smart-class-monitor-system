package com.smartclass.monitor.controller;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.smartclass.monitor.service.ReportService;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.io.File;
import java.util.*;

@RestController
@RequestMapping("/api/settings")
public class SettingsController {

    private static final Logger log = LoggerFactory.getLogger(SettingsController.class);
    private static final Map<String, Object> DEFAULTS = Map.of(
            "contacts", List.of(
                    Map.of("name", "项重善", "mobile", "18601033435"),
                    Map.of("name", "章志超", "mobile", "15270985055")),
            "responsible", "项重善",
            "reportTime", "18:00"
    );

    private final Map<String, Object> store = new LinkedHashMap<>();
    private final ReportService reportService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${settings.file:data/settings.json}")
    private String settingsFilePath;

    @Value("${ai.base-url:http://localhost:5000}")
    private String aiBaseUrl;

    public SettingsController(ReportService reportService) {
        this.reportService = reportService;
    }

    @PostConstruct
    public void init() {
        loadFromFile();
        if (!store.isEmpty()) {
            reportService.updateSettings(store);
            log.info("从文件恢复设置: {} 项", store.size());
        }
    }

    @PutMapping
    public Map<String, Object> update(@RequestBody Map<String, Object> body) {
        store.putAll(body);
        reportService.updateSettings(body);

        writeToFile();

        try {
            new RestTemplate().postForObject(aiBaseUrl + "/api/contacts/sync", body, String.class);
        } catch (Exception ignored) {}

        return Map.of("ok", true, "stored", store.keySet());
    }

    @GetMapping
    public Map<String, Object> get() {
        if (store.isEmpty()) {
            return DEFAULTS;
        }
        return store;
    }

    private void writeToFile() {
        try {
            File file = new File(settingsFilePath);
            file.getParentFile().mkdirs();
            objectMapper.writerWithDefaultPrettyPrinter().writeValue(file, store);
            log.debug("设置已写入 {}", file.getAbsolutePath());
        } catch (Exception e) {
            log.warn("写入设置文件失败: {}", e.getMessage());
        }
    }

    private void loadFromFile() {
        try {
            File file = new File(settingsFilePath);
            if (!file.exists()) {
                log.info("设置文件不存在: {}", file.getAbsolutePath());
                return;
            }
            Map<String, Object> loaded = objectMapper.readValue(file, new TypeReference<LinkedHashMap<String, Object>>() {});
            store.putAll(loaded);
            log.info("从文件加载设置: {} 项", loaded.size());
        } catch (Exception e) {
            log.warn("读取设置文件失败: {}", e.getMessage());
        }
    }
}