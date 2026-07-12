package com.smartclass.monitor.service;

import com.fasterxml.jackson.databind.ObjectMapper;
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

    @Value("${report.qwen.url:https://ws-bwonuhgq62ys3o1g.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions}")
    private String qwenUrl;

    @Value("${report.qwen.key:sk-ws-H.EMXPMID.91yA.MEUCIQC6JxHW4VNET1qOKTBSr18mHMtU8QFBk-LsyK2OmWOPygIgPuLCk8dpBFHYLsIEO4tNeigdh5RPhMj4hm9lUTtY0iY}")
    private String qwenKey;

    @Value("${report.qwen.model:qwen3.7-plus}")
    private String model;

    @Value("${report.ai-enabled:true}")
    private boolean aiEnabled;

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();

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
            generateReport(Collections.emptyList());
        }
    }

    public void updateSettings(Map<String, Object> s) { this.settings = s; }

    /** 最新的日报缓存 */
    private volatile Map<String, Object> latestReport;

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
        report.put("summary", summary);
        report.put("alertsCount", total);
        report.put("alerts", alerts.size() > 10 ? alerts.subList(0, 10) : alerts);
        report.put("raw", Map.of("high", high, "warning", warning, "types", types));

        latestReport = report;
        return report;
    }

    public Map<String, Object> getLatestReport() {
        return latestReport;
    }

    public List<Map<String, Object>> getHistory() {
        if (latestReport == null) {
            return Collections.emptyList();
        }
        return Collections.singletonList(latestReport);
    }

    /** 调用千问 API */
    private String callQwen(List<Map<String, Object>> alerts, String fallback) {
        try {
            StringBuilder data = new StringBuilder();
            for (Map<String, Object> a : alerts.subList(0, Math.min(alerts.size(), 30))) {
                data.append(String.format("- [%s] %s (%s, 置信度 %.0f%%)\n",
                        a.getOrDefault("occurredAt", a.getOrDefault("time", "")),
                        a.getOrDefault("alertType", a.getOrDefault("type", "未知")),
                        a.getOrDefault("streamId", a.getOrDefault("location", "")),
                        toPercent(a.get("confidence"))));
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
                    qwenUrl, HttpMethod.POST,
                    new HttpEntity<>(body, headers), Map.class
            );

            List<Map> choices = (List<Map>) resp.getBody().get("choices");
            if (choices != null && !choices.isEmpty()) {
                Map message = (Map) choices.get(0).get("message");
                return String.valueOf(message.getOrDefault("content", fallback));
            }
        } catch (Exception e) {
            log.warn("千问 API 调用失败，使用模板: {}", e.getMessage());
        }
        return fallback;
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