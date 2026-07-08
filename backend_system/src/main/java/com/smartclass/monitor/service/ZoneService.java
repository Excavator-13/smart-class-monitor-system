package com.smartclass.monitor.service;

import com.smartclass.monitor.common.exception.BusinessException;
import com.smartclass.monitor.dto.ZoneCreateRequest;
import com.smartclass.monitor.dto.ZoneUpdateRequest;
import com.smartclass.monitor.entity.DangerZone;
import com.smartclass.monitor.integration.AiClient;
import com.smartclass.monitor.mapper.DangerZoneMapper;
import com.smartclass.monitor.vo.ZoneVO;
import org.springframework.stereotype.Service;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class ZoneService {

    private static final DateTimeFormatter DTF = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final List<String> RELOAD_ITEMS = List.of("zones");

    private final DangerZoneMapper mapper;
    private final AiClient aiClient;

    public ZoneService(DangerZoneMapper mapper, AiClient aiClient) {
        this.mapper = mapper;
        this.aiClient = aiClient;
    }

    public List<ZoneVO> listZones(String streamId, String zoneType) {
        return mapper.findAll(streamId, zoneType).stream().map(this::toVO).collect(Collectors.toList());
    }

    public ZoneVO createZone(ZoneCreateRequest req) {
        DangerZone entity = new DangerZone();
        entity.setStreamId(req.getStreamId());
        entity.setZoneName(req.getZoneName());
        entity.setZoneType(req.getZoneType());
        entity.setShapeType("polygon");
        entity.setCoordinates(req.getCoordinates());
        entity.setThresholdSeconds(req.getThresholdSeconds());
        entity.setSafeDistance(req.getSafeDistance());
        entity.setEnabled(true);
        mapper.insert(entity);

        aiClient.reloadConfig(req.getStreamId(), RELOAD_ITEMS);
        return toVO(entity);
    }

    public ZoneVO getZoneById(Long id) {
        DangerZone entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "区域不存在");
        return toVO(entity);
    }

    public void updateZone(Long id, ZoneUpdateRequest req) {
        DangerZone entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "区域不存在");

        if (req.getZoneName() != null) entity.setZoneName(req.getZoneName());
        if (req.getCoordinates() != null) entity.setCoordinates(req.getCoordinates());
        if (req.getThresholdSeconds() != null) entity.setThresholdSeconds(req.getThresholdSeconds());
        if (req.getSafeDistance() != null) entity.setSafeDistance(req.getSafeDistance());
        if (req.getEnabled() != null) entity.setEnabled(req.getEnabled());
        mapper.update(entity);

        aiClient.reloadConfig(entity.getStreamId(), RELOAD_ITEMS);
    }

    public void deleteZone(Long id) {
        DangerZone entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "区域不存在");
        mapper.softDelete(id);

        aiClient.reloadConfig(entity.getStreamId(), RELOAD_ITEMS);
    }

    public List<ZoneVO> getZonesByStreamId(String streamId) {
        return mapper.findByStreamId(streamId).stream().map(this::toVO).collect(Collectors.toList());
    }

    private ZoneVO toVO(DangerZone e) {
        ZoneVO vo = new ZoneVO();
        vo.setId(e.getId());
        vo.setStreamId(e.getStreamId());
        vo.setZoneName(e.getZoneName());
        vo.setZoneType(e.getZoneType());
        vo.setShapeType(e.getShapeType());
        vo.setCoordinates(e.getCoordinates());
        vo.setThresholdSeconds(e.getThresholdSeconds());
        vo.setSafeDistance(e.getSafeDistance());
        vo.setEnabled(e.getEnabled());
        if (e.getCreatedAt() != null) vo.setCreatedAt(e.getCreatedAt().format(DTF));
        return vo;
    }
}
