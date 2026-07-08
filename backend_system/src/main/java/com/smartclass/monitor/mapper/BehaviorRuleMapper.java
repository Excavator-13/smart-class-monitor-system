package com.smartclass.monitor.mapper;

import com.smartclass.monitor.entity.BehaviorRule;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface BehaviorRuleMapper {

    @Select("<script>" +
            "SELECT * FROM behavior_rule WHERE deleted_at IS NULL " +
            "<if test='ruleType != null and ruleType != \"\"'>AND rule_type = #{ruleType}</if>" +
            "ORDER BY rule_type" +
            "</script>")
    List<BehaviorRule> findAll(@Param("ruleType") String ruleType);

    @Select("SELECT * FROM behavior_rule WHERE id = #{id} AND deleted_at IS NULL")
    BehaviorRule findById(@Param("id") Long id);

    @Insert("INSERT INTO behavior_rule (rule_type, rule_name, enabled, threshold_seconds, " +
            "confidence_threshold, cooldown_seconds, level, config_json) " +
            "VALUES (#{ruleType}, #{ruleName}, #{enabled}, #{thresholdSeconds}, " +
            "#{confidenceThreshold}, #{cooldownSeconds}, #{level}, #{configJson})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(BehaviorRule rule);

    @Update("UPDATE behavior_rule SET rule_name=#{ruleName}, enabled=#{enabled}, " +
            "threshold_seconds=#{thresholdSeconds}, confidence_threshold=#{confidenceThreshold}, " +
            "cooldown_seconds=#{cooldownSeconds}, level=#{level}, config_json=#{configJson} " +
            "WHERE id=#{id}")
    int update(BehaviorRule rule);

    @Update("UPDATE behavior_rule SET deleted_at=NOW() WHERE id=#{id}")
    int softDelete(@Param("id") Long id);
}
