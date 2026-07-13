package com.smartclass.monitor.service;

import com.smartclass.monitor.common.exception.BusinessException;
import com.smartclass.monitor.common.response.PageResult;
import com.smartclass.monitor.dto.AlertStatusUpdateRequest;
import com.smartclass.monitor.entity.RecordingFile;
import com.smartclass.monitor.mapper.AlertEventMapper;
import com.smartclass.monitor.mapper.RecordingFileMapper;
import com.smartclass.monitor.vo.AlertStatsVO;
import com.smartclass.monitor.vo.AlertVO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Service
public class AlertService {

    private static final Logger log = LoggerFactory.getLogger(AlertService.class);
    private static final DateTimeFormatter DTF = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final Set<String> VALID_STATUSES = Set.of(
            "unhandled", "processing", "handled", "false_alarm", "ignored");

    private final AlertEventMapper mapper;
    private final RecordingFileMapper recordingMapper;

    public AlertService(AlertEventMapper mapper, RecordingFileMapper recordingMapper) {
        this.mapper = mapper;
        this.recordingMapper = recordingMapper;
    }

    public PageResult<AlertVO> listAlerts(String streamId, String alertType, String status,
                                           String level, String startTime, String endTime,
                                           int page, int pageSize) {
        LocalDateTime start = null, end = null;
        if (startTime != null && !startTime.isEmpty()) start = LocalDateTime.parse(startTime, DTF);
        if (endTime != null && !endTime.isEmpty()) end = LocalDateTime.parse(endTime, DTF);

        int offset = (page - 1) * pageSize;
        List<Map<String, Object>> rows = mapper.findAlerts(streamId, alertType, status, level,
                start, end, offset, pageSize);
        long total = mapper.countAlerts(streamId, alertType, status, level, start, end);

        List<AlertVO> records = new ArrayList<>();
        for (Map<String, Object> row : rows) {
            records.add(mapToAlertVO(row));
        }
        return PageResult.of(records, page, pageSize, total);
    }

    public AlertVO getAlertDetail(Long id) {
        Map<String, Object> row = mapper.findAlertDetail(id);
        if (row == null) throw new BusinessException(404, "告警不存在");
        return mapToAlertVO(row);
    }

    public void updateStatus(Long id, AlertStatusUpdateRequest req) {
        Map<String, Object> existing = mapper.findAlertDetail(id);
        if (existing == null) throw new BusinessException(404, "告警不存在");

        if (!VALID_STATUSES.contains(req.getStatus())) {
            throw new BusinessException(400, "无效的告警状态: " + req.getStatus());
        }

        mapper.updateStatus(id, req.getStatus(), req.getHandlerId(), req.getRemark(),
                LocalDateTime.now());
    }

    public AlertStatsVO getStats() {
        AlertStatsVO stats = new AlertStatsVO();
        stats.setTodayTotal(mapper.countTodayAlerts());
        stats.setUnhandledCount(mapper.countUnhandled());
        stats.setByType(mapper.countByTypeToday());
        return stats;
    }

    private AlertVO mapToAlertVO(Map<String, Object> row) {
        AlertVO vo = new AlertVO();
        vo.setId(toLong(row.get("id")));
        vo.setEventId((String) row.get("event_id"));
        vo.setStreamId((String) row.get("stream_id"));
        vo.setStreamName((String) row.get("stream_name"));
        vo.setStudentId(toLong(row.get("student_id")));
        vo.setStudentName((String) row.get("student_name"));
        vo.setAlertType((String) row.get("alert_type"));
        vo.setLevel((String) row.get("level"));
        vo.setStatus((String) row.get("status"));
        vo.setConfidence(toDouble(row.get("confidence")));
        vo.setSnapshotUrl((String) row.get("snapshot_path"));

        String recordPath = (String) row.get("record_path");
        Double eventTimeOffset = toDouble(row.get("event_time_offset"));

        if (recordPath != null && !recordPath.isEmpty()) {
            vo.setRecordUrl(recordPath);
            vo.setEventTimeOffset(eventTimeOffset);
        } else {
            String streamId = (String) row.get("stream_id");
            LocalDateTime occurredAt = (LocalDateTime) row.get("occurred_at");
            if (streamId != null && occurredAt != null) {
                try {
                    RecordingFile rec = recordingMapper.findContainingRecording(streamId, occurredAt);
                    if (rec != null) {
                        String urlDir = rec.getFilePath();
                        if (urlDir != null && urlDir.startsWith("/segments")) {
                            urlDir = "/records" + urlDir.substring("/segments".length());
                        }
                        if (urlDir == null || urlDir.isEmpty()) {
                            vo.setRecordUrl("/" + rec.getFileName());
                        } else {
                            vo.setRecordUrl(urlDir + "/" + rec.getFileName());
                        }
                        if (rec.getStartedAt() != null) {
                            long offsetSec = Duration.between(rec.getStartedAt(), occurredAt).getSeconds();
                            vo.setEventTimeOffset(Math.max(0, (double) offsetSec));
                        }
                    }
                } catch (Exception e) {
                    log.warn("录像查找失败 event_id={}: {}", row.get("event_id"), e.getMessage());
                }
            }
        }

        if (row.get("occurred_at") != null) {
            vo.setOccurredAt(((LocalDateTime) row.get("occurred_at")).format(DTF));
        }
        if (row.get("handled_at") != null) {
            vo.setHandledAt(((LocalDateTime) row.get("handled_at")).format(DTF));
        }
        vo.setRemark((String) row.get("remark"));
        return vo;
    }

    private Long toLong(Object v) {
        if (v == null) return null;
        if (v instanceof Number) return ((Number) v).longValue();
        return null;
    }

    private Double toDouble(Object v) {
        if (v == null) return null;
        if (v instanceof Number) return ((Number) v).doubleValue();
        return null;
    }
}