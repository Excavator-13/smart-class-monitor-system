package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "行为规则信息")
public class RuleVO {

    @Schema(description = "规则主键", example = "1")
    private Long id;

    @Schema(description = "规则类型", example = "phone_usage")
    private String ruleType;

    @Schema(description = "规则中文名", example = "手机使用检测")
    private String ruleName;

    @Schema(description = "是否启用")
    private Boolean enabled;

    @Schema(description = "持续时间阈值（秒）", example = "3")
    private Integer thresholdSeconds;

    @Schema(description = "置信度阈值", example = "0.85")
    private Double confidenceThreshold;

    @Schema(description = "冷却时间（秒）", example = "60")
    private Integer cooldownSeconds;

    @Schema(description = "默认告警等级", example = "warning")
    private String level;

    @Schema(description = "扩展配置 JSON")
    private String configJson;

    @Schema(description = "创建时间", example = "2026-07-08 10:00:00")
    private String createdAt;

    public Long getId() { return id; }
    public void setId(Long v) { this.id = v; }
    public String getRuleType() { return ruleType; }
    public void setRuleType(String v) { this.ruleType = v; }
    public String getRuleName() { return ruleName; }
    public void setRuleName(String v) { this.ruleName = v; }
    public Boolean getEnabled() { return enabled; }
    public void setEnabled(Boolean v) { this.enabled = v; }
    public Integer getThresholdSeconds() { return thresholdSeconds; }
    public void setThresholdSeconds(Integer v) { this.thresholdSeconds = v; }
    public Double getConfidenceThreshold() { return confidenceThreshold; }
    public void setConfidenceThreshold(Double v) { this.confidenceThreshold = v; }
    public Integer getCooldownSeconds() { return cooldownSeconds; }
    public void setCooldownSeconds(Integer v) { this.cooldownSeconds = v; }
    public String getLevel() { return level; }
    public void setLevel(String v) { this.level = v; }
    public String getConfigJson() { return configJson; }
    public void setConfigJson(String v) { this.configJson = v; }
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String v) { this.createdAt = v; }
}
