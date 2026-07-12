package com.smartclass.monitor.service;

import com.smartclass.monitor.common.exception.BusinessException;
import com.smartclass.monitor.entity.ScoreConfig;
import com.smartclass.monitor.mapper.ScoreConfigMapper;
import com.smartclass.monitor.vo.ScoreConfigVO;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ScoreConfigService {

    private final ScoreConfigMapper mapper;

    public ScoreConfigService(ScoreConfigMapper mapper) {
        this.mapper = mapper;
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

    public ScoreConfigVO updateConfig(Long id, String label, Integer score, String note) {
        ScoreConfig entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "评分配置不存在");
        if (label != null) entity.setLabel(label);
        if (score != null) entity.setScore(score);
        if (note != null) entity.setNote(note);
        mapper.update(entity);
        return toVO(entity);
    }

    private ScoreConfigVO toVO(ScoreConfig e) {
        return new ScoreConfigVO(e.getId(), e.getAlertType(), e.getLabel(), e.getScore(), e.getNote());
    }
}