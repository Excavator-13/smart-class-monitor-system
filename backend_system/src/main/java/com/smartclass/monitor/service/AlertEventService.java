package com.smartclass.monitor.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.smartclass.monitor.common.exception.BusinessException;
import com.smartclass.monitor.dto.AlertIngestRequest;
import com.smartclass.monitor.entity.AlertEvent;
import com.smartclass.monitor.mapper.AlertEventMapper;
import com.smartclass.monitor.mapper.ScoreConfigMapper;
import com.smartclass.monitor.entity.ScoreConfig;
import com.smartclass.monitor.vo.AlertIngestResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Set;

@Service
public class AlertEventService {

    private static final Logger log = LoggerFactory.getLogger(AlertEventService.class);
    private static final ObjectMapper objectMapper = new ObjectMapper();

    private final AlertEventMapper mapper;
    private final ScoreConfigMapper scoreConfigMapper;
    private static final Set<String> VALID_LEVELS = Set.of("info", "warning", "high");

    public AlertEventService(AlertEventMapper mapper, ScoreConfigMapper scoreConfigMapper) {
        this.mapper = mapper;
        this.scoreConfigMapper = scoreConfigMapper;
    }

    public AlertIngestResponse ingestAlert(AlertIngestRequest req) {
        // 1. 幂等检查
        AlertEvent existing = mapper.findByEventId(req.getEventId());
        if (existing != null) {
            AlertIngestResponse resp = new AlertIngestResponse();
            resp.setAlertId(existing.getId());
            resp.setStatus(existing.getStatus());
            return resp;
        }

        // 2. 校验路径格式
        validatePath(req.getSnapshotPath(), "snapshot_path");
        validatePath(req.getRecordPath(), "record_path");

        // 3. 入库
        AlertEvent event = new AlertEvent();
        event.setEventId(req.getEventId());
        event.setStreamId(req.getStreamId());
        event.setAlertType(req.getAlertType());
        event.setAlertName(req.getAlertName());
        event.setLevel(resolveLevel(req.getAlertType(), req.getLevel()));
        event.setConfidence(req.getConfidence());
        event.setDurationSeconds(req.getDurationSeconds());
        event.setZoneId(req.getZoneId());
        event.setSnapshotPath(req.getSnapshotPath());
        event.setRecordPath(req.getRecordPath());
        event.setEventTimeOffset(req.getEventTimeOffset());
        event.setStatus("unhandled");

        if (req.getOccurredAt() != null) {
            try {
                event.setOccurredAt(LocalDateTime.parse(req.getOccurredAt(),
                        DateTimeFormatter.ISO_OFFSET_DATE_TIME));
            } catch (Exception e) {
                throw new BusinessException(400, "occurred_at 格式错误，需 ISO 8601");
            }
        }

        // student_id: AI 可能传 student_no，尝试转换为 Long
        if (req.getStudentId() != null) {
            try {
                event.setStudentId(Long.valueOf(req.getStudentId()));
            } catch (NumberFormatException e) {
                // 传的不是数字主键，忽略
                event.setStudentId(null);
            }
        }

        // JSON 序列化
        try {
            if (req.getTargetInfo() != null) event.setTargetInfo(objectMapper.writeValueAsString(req.getTargetInfo()));
            if (req.getExtra() != null) event.setExtra(objectMapper.writeValueAsString(req.getExtra()));
        } catch (JsonProcessingException e) {
            throw new BusinessException(500, "数据序列化失败");
        }

        mapper.insert(event);

        AlertIngestResponse resp = new AlertIngestResponse();
        resp.setAlertId(event.getId());
        resp.setStatus("unhandled");
        return resp;
    }

    private String resolveLevel(String alertType, String requestedLevel) {
        ScoreConfig config = scoreConfigMapper.findByType(alertType);
        if (config != null && VALID_LEVELS.contains(config.getLevel())) return config.getLevel();
        return VALID_LEVELS.contains(requestedLevel) ? requestedLevel : "warning";
    }

    private void validatePath(String path, String fieldName) {
        if (path == null) return;
        if (!path.startsWith("/")) {
            throw new BusinessException(400, fieldName + " 必须以 / 开头");
        }
        if (path.contains("://") || path.contains("..")) {
            throw new BusinessException(400, fieldName + " 不允许包含 :// 或 ..");
        }
    }
}
