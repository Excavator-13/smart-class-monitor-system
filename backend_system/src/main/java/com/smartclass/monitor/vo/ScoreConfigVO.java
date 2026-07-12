package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "告警评分配置")
public class ScoreConfigVO {

    @Schema(description = "主键", example = "1")
    private Long id;

    @Schema(description = "告警类型", example = "fire")
    private String alertType;

    @Schema(description = "显示名称", example = "明火")
    private String label;

    @Schema(description = "评分权重 0-100", example = "92")
    private Integer score;

    @Schema(description = "说明")
    private String note;

    public ScoreConfigVO() {}

    public ScoreConfigVO(Long id, String alertType, String label, Integer score, String note) {
        this.id = id;
        this.alertType = alertType;
        this.label = label;
        this.score = score;
        this.note = note;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getAlertType() { return alertType; }
    public void setAlertType(String alertType) { this.alertType = alertType; }
    public String getLabel() { return label; }
    public void setLabel(String label) { this.label = label; }
    public Integer getScore() { return score; }
    public void setScore(Integer score) { this.score = score; }
    public String getNote() { return note; }
    public void setNote(String note) { this.note = note; }
}