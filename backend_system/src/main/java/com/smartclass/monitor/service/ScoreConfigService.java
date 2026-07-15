package com.smartclass.monitor.service;

import com.smartclass.monitor.common.exception.BusinessException;
import com.smartclass.monitor.entity.ScoreConfig;
import com.smartclass.monitor.integration.AiClient;
import com.smartclass.monitor.mapper.ScoreConfigMapper;
import com.smartclass.monitor.vo.ScoreConfigVO;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class ScoreConfigService {

    private final ScoreConfigMapper mapper;
    private final AiClient aiClient;
    private static final Set<String> VALID_LEVELS = Set.of("info", "warning", "high");

    public ScoreConfigService(ScoreConfigMapper mapper, AiClient aiClient) {
        this.mapper = mapper;
        this.aiClient = aiClient;
    }

    public List<ScoreConfigVO> listAll() {
        return mapper.findAll().stream().map(this::toVO).collect(Collectors.toList());
    }

    public ScoreConfigVO updateScore(Long id, Integer score) {
        ScoreConfig entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "评分配置不存在");
        entity.setScore(score);
        mapper.update(entity);
        return toVO(entity);
    }

    public ScoreConfigVO updateConfig(Long id, String label, String level, Integer score, String note) {
        ScoreConfig entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "评分配置不存在");
        if (label != null) entity.setLabel(label);
        if (level != null) {
            if (!VALID_LEVELS.contains(level)) throw new BusinessException(400, "无效的告警等级");
            entity.setLevel(level);
        }
        if (score != null) entity.setScore(score);
        if (note != null) entity.setNote(note);
        mapper.update(entity);
        aiClient.reloadConfig(null, List.of("event_configs"));
        return toVO(entity);
    }

    private ScoreConfigVO toVO(ScoreConfig e) {
        return new ScoreConfigVO(e.getId(), e.getAlertType(), e.getLabel(), e.getLevel(), e.getScore(), e.getNote());
    }
}
