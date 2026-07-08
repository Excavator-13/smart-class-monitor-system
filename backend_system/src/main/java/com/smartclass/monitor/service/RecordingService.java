package com.smartclass.monitor.service;

import com.smartclass.monitor.common.response.PageResult;
import com.smartclass.monitor.entity.RecordingFile;
import com.smartclass.monitor.mapper.RecordingFileMapper;
import com.smartclass.monitor.vo.RecordingVO;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class RecordingService {

    private static final DateTimeFormatter DTF = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final RecordingFileMapper mapper;

    public RecordingService(RecordingFileMapper mapper) {
        this.mapper = mapper;
    }

    public PageResult<RecordingVO> listRecordings(String streamId, String eventId,
                                                   String startTime, String endTime,
                                                   int page, int pageSize) {
        LocalDateTime start = null, end = null;
        if (startTime != null && !startTime.isEmpty()) start = LocalDateTime.parse(startTime, DTF);
        if (endTime != null && !endTime.isEmpty()) end = LocalDateTime.parse(endTime, DTF);

        int offset = (page - 1) * pageSize;
        List<RecordingFile> files = mapper.findRecordings(streamId, eventId, start, end, offset, pageSize);
        long total = mapper.countRecordings(streamId, eventId, start, end);

        List<RecordingVO> records = files.stream().map(f -> {
            RecordingVO vo = new RecordingVO();
            vo.setId(f.getId());
            vo.setStreamId(f.getStreamId());
            vo.setFileName(f.getFileName());
            vo.setFilePath(f.getFilePath());
            vo.setFileExt(f.getFileExt());
            vo.setFileSize(f.getFileSize());
            if (f.getStartedAt() != null) vo.setStartedAt(f.getStartedAt().format(DTF));
            if (f.getEndedAt() != null) vo.setEndedAt(f.getEndedAt().format(DTF));
            vo.setDurationSeconds(f.getDurationSeconds());
            vo.setSourceType(f.getSourceType());
            // available: has path and not expired (within 7 days)
            vo.setAvailable(f.getFilePath() != null
                    && f.getStartedAt() != null
                    && f.getStartedAt().isAfter(LocalDateTime.now().minusDays(7)));
            return vo;
        }).collect(Collectors.toList());

        return PageResult.of(records, page, pageSize, total);
    }
}
