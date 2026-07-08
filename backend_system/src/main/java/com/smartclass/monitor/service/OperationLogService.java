package com.smartclass.monitor.service;

import com.smartclass.monitor.common.response.PageResult;
import com.smartclass.monitor.entity.OperationLog;
import com.smartclass.monitor.mapper.OperationLogMapper;
import com.smartclass.monitor.vo.OperationLogVO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class OperationLogService {

    private static final Logger log = LoggerFactory.getLogger(OperationLogService.class);
    private static final DateTimeFormatter DTF = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final OperationLogMapper mapper;

    public OperationLogService(OperationLogMapper mapper) {
        this.mapper = mapper;
    }

    public PageResult<OperationLogVO> listLogs(Long userId, String action, String targetType,
                                                String targetId, String startTime, String endTime,
                                                int page, int pageSize) {
        LocalDateTime start = null, end = null;
        if (startTime != null && !startTime.isEmpty()) start = LocalDateTime.parse(startTime, DTF);
        if (endTime != null && !endTime.isEmpty()) end = LocalDateTime.parse(endTime, DTF);

        int offset = (page - 1) * pageSize;
        List<OperationLog> logs = mapper.findLogs(userId, action, targetType, targetId, start, end, offset, pageSize);
        long total = mapper.countLogs(userId, action, targetType, targetId, start, end);

        List<OperationLogVO> records = logs.stream().map(l -> {
            OperationLogVO vo = new OperationLogVO();
            vo.setId(l.getId());
            vo.setUserId(l.getUserId());
            vo.setUsername(l.getUsername());
            vo.setAction(l.getAction());
            vo.setTargetType(l.getTargetType());
            vo.setTargetId(l.getTargetId());
            vo.setMethod(l.getMethod());
            vo.setRequestUri(l.getRequestUri());
            vo.setRequestIp(l.getRequestIp());
            vo.setResultCode(l.getResultCode());
            vo.setResultMessage(l.getResultMessage());
            if (l.getCreatedAt() != null) vo.setCreatedAt(l.getCreatedAt().format(DTF));
            return vo;
        }).collect(Collectors.toList());

        return PageResult.of(records, page, pageSize, total);
    }

    /** 手动记录操作日志。调用方需确保 requestBody 已脱敏（不含 password/token/feature_vector） */
    public void log(Long userId, String username, String action, String targetType, String targetId,
                    String method, String requestUri, String requestIp, String requestBody,
                    int resultCode, String resultMessage) {
        OperationLog entity = new OperationLog();
        entity.setUserId(userId);
        entity.setUsername(username);
        entity.setAction(action);
        entity.setTargetType(targetType);
        entity.setTargetId(targetId);
        entity.setMethod(method);
        entity.setRequestUri(requestUri);
        entity.setRequestIp(requestIp);
        entity.setRequestBody(requestBody);
        entity.setResultCode(resultCode);
        entity.setResultMessage(resultMessage);
        mapper.insert(entity);
    }
}
