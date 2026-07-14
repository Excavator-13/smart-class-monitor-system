package com.smartclass.monitor.service;

import com.smartclass.monitor.common.exception.BusinessException;
import com.smartclass.monitor.dto.RuleCreateRequest;
import com.smartclass.monitor.dto.RuleUpdateRequest;
import com.smartclass.monitor.entity.BehaviorRule;
import com.smartclass.monitor.integration.AiClient;
import com.smartclass.monitor.mapper.BehaviorRuleMapper;
import com.smartclass.monitor.vo.RuleVO;
import org.springframework.stereotype.Service;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class RuleService {

    private static final DateTimeFormatter DTF = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final List<String> RELOAD_ITEMS = List.of("rules");

    private final BehaviorRuleMapper mapper;
    private final AiClient aiClient;

    public RuleService(BehaviorRuleMapper mapper, AiClient aiClient) {
        this.mapper = mapper;
        this.aiClient = aiClient;
    }

    public List<RuleVO> listRules(String ruleType) {
        return mapper.findAll(ruleType).stream().map(this::toVO).collect(Collectors.toList());
    }

    public RuleVO createRule(RuleCreateRequest req) {
        BehaviorRule entity = new BehaviorRule();
        entity.setRuleType(req.getRuleType());
        entity.setRuleName(req.getRuleName());
        entity.setEnabled(req.getEnabled() != null ? req.getEnabled() : true);
        entity.setThresholdSeconds(req.getThresholdSeconds());
        entity.setConfidenceThreshold(req.getConfidenceThreshold());
        entity.setCooldownSeconds(req.getCooldownSeconds());
        entity.setConfigJson(req.getConfigJson());
        mapper.insert(entity);

        aiClient.reloadConfig(null, RELOAD_ITEMS);
        return toVO(entity);
    }

    public RuleVO getRuleById(Long id) {
        BehaviorRule entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "规则不存在");
        return toVO(entity);
    }

    public void updateRule(Long id, RuleUpdateRequest req) {
        BehaviorRule entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "规则不存在");

        if (req.getRuleName() != null) entity.setRuleName(req.getRuleName());
        if (req.getThresholdSeconds() != null) entity.setThresholdSeconds(req.getThresholdSeconds());
        if (req.getConfidenceThreshold() != null) entity.setConfidenceThreshold(req.getConfidenceThreshold());
        if (req.getCooldownSeconds() != null) entity.setCooldownSeconds(req.getCooldownSeconds());
        if (req.getEnabled() != null) entity.setEnabled(req.getEnabled());
        if (req.getConfigJson() != null) entity.setConfigJson(req.getConfigJson());
        mapper.update(entity);

        aiClient.reloadConfig(null, RELOAD_ITEMS);
    }

    public void deleteRule(Long id) {
        BehaviorRule entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "规则不存在");
        mapper.softDelete(id);
        aiClient.reloadConfig(null, RELOAD_ITEMS);
    }

    public void toggleRule(Long id, boolean enabled) {
        BehaviorRule entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "规则不存在");
        entity.setEnabled(enabled);
        mapper.update(entity);
        aiClient.reloadConfig(null, RELOAD_ITEMS);
    }

    private RuleVO toVO(BehaviorRule e) {
        RuleVO vo = new RuleVO();
        vo.setId(e.getId());
        vo.setRuleType(e.getRuleType());
        vo.setRuleName(e.getRuleName());
        vo.setEnabled(e.getEnabled());
        vo.setThresholdSeconds(e.getThresholdSeconds());
        vo.setConfidenceThreshold(e.getConfidenceThreshold());
        vo.setCooldownSeconds(e.getCooldownSeconds());
        vo.setConfigJson(e.getConfigJson());
        if (e.getCreatedAt() != null) vo.setCreatedAt(e.getCreatedAt().format(DTF));
        return vo;
    }
}
