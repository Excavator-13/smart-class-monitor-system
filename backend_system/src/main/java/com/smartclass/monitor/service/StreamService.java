package com.smartclass.monitor.service;

import com.smartclass.monitor.common.exception.BusinessException;
import com.smartclass.monitor.common.response.PageResult;
import com.smartclass.monitor.dto.StreamCreateRequest;
import com.smartclass.monitor.dto.StreamUpdateRequest;
import com.smartclass.monitor.entity.VideoStream;
import com.smartclass.monitor.integration.NginxClient;
import com.smartclass.monitor.mapper.VideoStreamMapper;
import com.smartclass.monitor.vo.StreamPreviewVO;
import com.smartclass.monitor.vo.StreamStatusVO;
import com.smartclass.monitor.vo.StreamVO;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class StreamService {

    private static final DateTimeFormatter DTF = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final VideoStreamMapper mapper;
    private final NginxClient nginxClient;
    private final String aiBaseUrl;

    public StreamService(VideoStreamMapper mapper, NginxClient nginxClient, @Value("${ai.base-url}") String aiBaseUrl) {
        this.mapper = mapper;
        this.nginxClient = nginxClient;
        this.aiBaseUrl = aiBaseUrl;
    }

    public PageResult<StreamVO> listStreams(String status, String keyword, int page, int pageSize,
                                            boolean includeRtmp) {
        List<VideoStream> all = mapper.findAll(status, keyword);
        int total = all.size();
        int from = Math.min((page - 1) * pageSize, total);
        int to = Math.min(from + pageSize, total);
        List<StreamVO> records = all.subList(from, to).stream()
                .map(item -> toVO(item, includeRtmp))
                .collect(Collectors.toList());
        return PageResult.of(records, page, pageSize, total);
    }

    public StreamVO createStream(StreamCreateRequest req) {
        VideoStream entity = new VideoStream();
        entity.setStreamId(req.getStreamId());
        entity.setStreamName(req.getStreamName());
        entity.setRtmpUrl(req.getRtmpUrl());
        entity.setStatus("enabled");
        entity.setRemark(req.getRemark());

        try {
            mapper.insert(entity);
        } catch (DuplicateKeyException e) {
            throw new BusinessException(409, "stream_id 已存在");
        }
        return toVO(entity, true);
    }

    public StreamVO getStreamById(Long id, boolean includeRtmp) {
        VideoStream entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "视频源不存在");
        return toVO(entity, includeRtmp);
    }

    public void updateStream(Long id, StreamUpdateRequest req) {
        VideoStream entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "视频源不存在");

        if (req.getStreamName() != null) entity.setStreamName(req.getStreamName());
        if (req.getRtmpUrl() != null) entity.setRtmpUrl(req.getRtmpUrl());
        if (req.getStatus() != null) entity.setStatus(req.getStatus());
        if (req.getRemark() != null) entity.setRemark(req.getRemark());
        mapper.update(entity);
    }

    public void deleteStream(Long id) {
        VideoStream entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "视频源不存在");
        mapper.softDelete(id);
    }

    public List<StreamVO> getEnabledStreams(boolean includeRtmp) {
        return mapper.findEnabled().stream()
                .map(item -> toVO(item, includeRtmp))
                .collect(Collectors.toList());
    }

    public StreamStatusVO getStreamStatus(String streamId) {
        VideoStream entity = mapper.findByStreamId(streamId);
        if (entity == null) throw new BusinessException(404, "视频源不存在");
        return nginxClient.getStreamStatus(streamId);
    }

    public StreamPreviewVO getPreviewUrl(String streamId, boolean includeRtmp) {
        VideoStream entity = mapper.findByStreamId(streamId);
        if (entity == null) throw new BusinessException(404, "视频源不存在");

        StreamPreviewVO vo = new StreamPreviewVO();
        vo.setMjpegUrl(aiBaseUrl + "/video_feed/" + streamId);
        if (includeRtmp) vo.setRtmpUrl(entity.getRtmpUrl());
        vo.setHlsUrl(entity.getHlsUrl());
        return vo;
    }

    private StreamVO toVO(VideoStream e, boolean includeRtmp) {
        StreamVO vo = new StreamVO();
        vo.setId(e.getId());                        // id 必须返回
        vo.setStreamId(e.getStreamId());            // stream_id 必须返回
        vo.setStreamName(e.getStreamName());
        if (includeRtmp) vo.setRtmpUrl(e.getRtmpUrl());
        vo.setStatus(e.getStatus());
        vo.setLocation(e.getLocation());
        vo.setRemark(e.getRemark());
        if (e.getCreatedAt() != null) vo.setCreatedAt(e.getCreatedAt().format(DTF));
        return vo;
    }
}
