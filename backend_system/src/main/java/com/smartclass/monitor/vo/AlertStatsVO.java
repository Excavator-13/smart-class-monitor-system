package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

import java.util.List;
import java.util.Map;

@Schema(description = "告警统计数据")
public class AlertStatsVO {

    @Schema(description = "今日告警总数", example = "42")
    private long todayTotal;

    @Schema(description = "未处理告警数", example = "5")
    private long unhandledCount;

    @Schema(description = "今日各类型告警数量")
    private List<Map<String, Object>> byType;

    public long getTodayTotal() { return todayTotal; }
    public void setTodayTotal(long v) { this.todayTotal = v; }
    public long getUnhandledCount() { return unhandledCount; }
    public void setUnhandledCount(long v) { this.unhandledCount = v; }
    public List<Map<String, Object>> getByType() { return byType; }
    public void setByType(List<Map<String, Object>> v) { this.byType = v; }
}
