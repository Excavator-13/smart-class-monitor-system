package com.smartclass.monitor.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.smartclass.monitor.vo.AlertVO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDate;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

/**
 * AI 日报生成服务
 * 从数据库查询告警数据，调用千问 API 生成日报总结
 */
@Service
public class ReportService {

    private static final Logger log = LoggerFactory.getLogger(ReportService.class);

    @Value("${report.qwen.url:https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions}")
    private String qwenUrl;

    @Value("${report.qwen.key:sk-ws-H.EMXXLXM.TIDu.MEUCIGRQZ3OvMC3v_ytNOc4xIGCz_OeoLA3UF-YDoJ-k4rzhAiEAlUk0V2EexJVsnxduEsMYkOqdFrUxVhHRYx7AaZamLyg}")
    private String qwenKey;

    @Value("${report.qwen.model:qwen3.7-plus}")
    private String model;

    @Value("${report.ai-enabled:true}")
    private boolean aiEnabled;

    private final RestTemplate restTemplate = new RestTemplate();

    private final AlertService alertService;

    public ReportService(AlertService alertService) {
        this.alertService = alertService;
    }

    /** 前端传来的设置 */
    private volatile Map<String, Object> settings = new LinkedHashMap<>();

    /** 每隔 10 分钟检查是否到设置的日报时间 */
    @Scheduled(fixedRate = 600000)
    public void checkAndAutoGenerate() {
        if (!aiEnabled) return;
        String setTime = String.valueOf(settings.getOrDefault("reportTime", "18:00"));
        String now = LocalTime.now().truncatedTo(ChronoUnit.MINUTES).toString();
        if (now.length() >= 5) now = now.substring(0, 5);
        if (now.equals(setTime)) {
            log.info("定时生成日报 {} ", now);
            generateReport(queryTodayAlerts());
        }
    }

    public void updateSettings(Map<String, Object> s) { this.settings = s; }

    /** 最新的日报缓存 */
    private volatile Map<String, Object> latestReport;

    /** 日报历史 */
    private final List<Map<String, Object>> history = new ArrayList<>();

    /**
     * 根据告警列表生成日报
     */
    public Map<String, Object> generateReport(List<Map<String, Object>> alerts) {
        int total = alerts.size();
        if (total == 0) {
            Map<String, Object> empty = new LinkedHashMap<>();
            empty.put("date", today());
            empty.put("summary", "今日无告警事件，系统运行正常。");
            empty.put("alertsCount", 0);
            empty.put("alerts", Collections.emptyList());
            latestReport = empty;
            return empty;
        }

        // 统计
        long high = alerts.stream().filter(a -> "high".equals(a.get("level"))).count();
        long warning = alerts.stream().filter(a -> "warning".equals(a.get("level"))).count();
        Set<String> types = alerts.stream()
                .map(a -> String.valueOf(a.getOrDefault("alertType", a.getOrDefault("type", "未知"))))
                .collect(Collectors.toSet());

        // 完整类型计数（给前端统计图）
        Map<String, Long> typeCounts = alerts.stream()
                .collect(Collectors.groupingBy(
                    a -> String.valueOf(a.getOrDefault("alertType", a.getOrDefault("type", "未知"))),
                    Collectors.counting()
                ));

        // 模板总结
        String template = String.format(
                "今日共触发 %d 次告警，其中高危 %d 次、一般 %d 次，告警类型包括：%s。%s",
                total, high, warning,
                String.join("、", types),
                high > 0 ? "需重点关注。" : "整体态势平稳。"
        );

        String summary;
        if (aiEnabled) {
            summary = callQwen(alerts, template);
        } else {
            summary = template;
        }

        Map<String, Object> report = new LinkedHashMap<>();
        report.put("date", today());
        report.put("time", java.time.LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        report.put("summary", summary);
        report.put("alertsCount", total);
        report.put("raw", Map.of("high", high, "warning", warning, "types", types, "type_counts", typeCounts));

        // VL 分析每张截图
        List<Map<String, Object>> details = new ArrayList<>();
        for (Map<String, Object> a : alerts.size() > 10 ? alerts.subList(0, 10) : alerts) {
            Map<String, Object> d = new LinkedHashMap<>(a);
            String snap = String.valueOf(a.getOrDefault("snapshotUrl", a.getOrDefault("snapshot_path", "")));
            if (!snap.isBlank()) {
                d.put("snapshotUrl", snap);
                String desc = analyzeImage(snap, String.valueOf(a.getOrDefault("alertType", "")));
                if (desc != null && !desc.isBlank()) d.put("vlAnalysis", desc);
            }
            details.add(d);
        }
        report.put("alerts", details);

        latestReport = report;
        history.add(0, report);
        return report;
    }

    public Map<String, Object> getLatestReport() {
        return latestReport;
    }

    public List<Map<String, Object>> getHistory() {
        return history;
    }

    /** 调用千问 API */
    private String callQwen(List<Map<String, Object>> alerts, String fallback) {
        String apiUrl = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions";
        try {
            StringBuilder data = new StringBuilder();
            for (Map<String, Object> a : alerts.subList(0, Math.min(alerts.size(), 30))) {
                data.append(String.format("- [%s] %s (%s)\n",
                        a.getOrDefault("occurredAt", a.getOrDefault("time", "")),
                        a.getOrDefault("alertType", a.getOrDefault("type", "未知")),
                        a.getOrDefault("streamId", a.getOrDefault("location", ""))));
            }

            Map<String, Object> body = new LinkedHashMap<>();
            body.put("model", model);
            body.put("messages", List.of(
                    Map.of("role", "system", "content", "你是智慧教室安防系统的日报助手。根据告警数据，生成一段80字以内的专业日报总结。简洁、客观、有数据支撑。"),
                    Map.of("role", "user", "content", "今日告警数据：\n" + data + "\n请生成日报总结。")
            ));
            body.put("max_tokens", 200);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setBearerAuth(qwenKey);

            ResponseEntity<Map> resp = restTemplate.exchange(
                    apiUrl, HttpMethod.POST,
                    new HttpEntity<>(body, headers), Map.class
            );

            List<Map> choices = (List<Map>) resp.getBody().get("choices");
            if (choices != null && !choices.isEmpty()) {
                Map message = (Map) choices.get(0).get("message");
                Object content = message.get("content");
                if (content != null) return content.toString();
            }
        } catch (Exception e) {
            log.warn("千问 API 调用失败，使用模板: {} msg: {}", e.getClass().getSimpleName(), e.getMessage());
        }
        return fallback;
    }

    public List<Map<String, Object>> queryTodayAlerts() {
        try {
            String today = LocalDate.now().toString();
            String startTime = today + " 00:00:00";
            String endTime = today + " 23:59:59";
            var page = alertService.listAlerts(null, null, null, null, startTime, endTime, 1, 500);
            var records = page.getRecords();
            log.info("queryTodayAlerts: 查到 {} 条告警，第一条 streamId={}", records.size(),
                     records.isEmpty() ? "无" : records.get(0).getStreamId());
            return records.stream().map(a -> {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("alertType", a.getAlertType());
                m.put("level", a.getLevel());
                m.put("streamId", a.getStreamId());
                m.put("snapshotUrl", a.getSnapshotUrl());
                m.put("occurredAt", String.valueOf(a.getOccurredAt()));
                m.put("confidence", a.getConfidence());
                return m;
            }).collect(Collectors.toList());
        } catch (Exception e) {
            log.warn("查询今日告警失败: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    @Value("${report.snapshot-base-url:http://39.106.209.208:9092}")
    private String snapshotBaseUrl;

    /** 调 VL 模型分析单张截图 */
    private String analyzeImage(String imageUrl, String alertType) {
        if (imageUrl == null || imageUrl.isBlank()) return null;
        // 相对路径补全
        String fullUrl = imageUrl.startsWith("/") ? snapshotBaseUrl + imageUrl : imageUrl;
        try {
            // 下载图片 → base64
            byte[] imgBytes = restTemplate.getForObject(fullUrl, byte[].class);
            String b64 = imgBytes != null ? Base64.getEncoder().encodeToString(imgBytes) : "";
            if (b64.isEmpty()) return null;

            String vlUrl = qwenUrl;
            Map<String, Object> body = new LinkedHashMap<>();
            body.put("model", "qwen-vl-plus");
            body.put("messages", List.of(
                Map.of("role", "user", "content", List.of(
                    Map.of("type", "image_url", "image_url", Map.of("url", "data:image/jpeg;base64," + b64)),
                    Map.of("type", "text", "text", "请描述画面内容（人物行为、位置、异常情况），30字以内")
                ))
            ));
            body.put("max_tokens", 100);
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setBearerAuth(qwenKey);
            ResponseEntity<Map> resp = restTemplate.exchange(
                vlUrl, HttpMethod.POST, new HttpEntity<>(body, headers), Map.class);
            List<Map> choices = (List<Map>) resp.getBody().get("choices");
            if (choices != null && !choices.isEmpty()) {
                Map msg = (Map) choices.get(0).get("message");
                Object c = msg.get("content");
                if (c != null) return c.toString();
            }
        } catch (Exception e) {
            log.warn("VL分析失败 {}: {}", imageUrl, e.getMessage());
        }
        return null;
    }

    private String today() {
        return LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
    }

    private String toPercent(Object confidence) {
        if (confidence == null) return "?%";
        try {
            return Math.round(Double.parseDouble(confidence.toString()) * 100) + "%";
        } catch (NumberFormatException e) {
            return "?%";
        }
    }
}