package com.smartclass.monitor.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "更新规则请求")
public class RuleUpdateRequest {

    @Schema(description = "规则中文名", example = "手机使用检测")
    private String ruleName;

    @Schema(description = "持续时间阈值（秒）", example = "5")
    private Integer thresholdSeconds;

    @Schema(description = "置信度阈值（0-1）", example = "0.90")
    private Double confidenceThreshold;

    @Schema(description = "冷却时间（秒）", example = "120")
    private Integer cooldownSeconds;

    @Schema(description = "默认告警等级", example = "warning")
    private String level;

    @Schema(description = "是否启用", example = "true")
    private Boolean enabled;

    @Schema(description = "扩展配置 JSON")
    private String configJson;

    public String getRuleName() { return ruleName; }
    public void setRuleName(String v) { this.ruleName = v; }
    public Integer getThresholdSeconds() { return thresholdSeconds; }
    public void setThresholdSeconds(Integer v) { this.thresholdSeconds = v; }
    public Double getConfidenceThreshold() { return confidenceThreshold; }
    public void setConfidenceThreshold(Double v) { this.confidenceThreshold = v; }
    public Integer getCooldownSeconds() { return cooldownSeconds; }
    public void setCooldownSeconds(Integer v) { this.cooldownSeconds = v; }
    public String getLevel() { return level; }
    public void setLevel(String v) { this.level = v; }
    public Boolean getEnabled() { return enabled; }
    public void setEnabled(Boolean v) { this.enabled = v; }
    public String getConfigJson() { return configJson; }
    public void setConfigJson(String v) { this.configJson = v; }
}
