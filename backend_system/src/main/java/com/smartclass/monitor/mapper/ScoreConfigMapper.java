package com.smartclass.monitor.mapper;

import com.smartclass.monitor.entity.ScoreConfig;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface ScoreConfigMapper {

    @Select("SELECT * FROM score_config ORDER BY alert_type")
    List<ScoreConfig> findAll();

    @Select("SELECT * FROM score_config WHERE alert_type = #{alertType}")
    ScoreConfig findByType(@Param("alertType") String alertType);

    @Select("SELECT * FROM score_config WHERE id = #{id}")
    ScoreConfig findById(@Param("id") Long id);

    @Insert("INSERT INTO score_config (alert_type, label, level, score, note) " +
            "VALUES (#{alertType}, #{label}, #{level}, #{score}, #{note})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(ScoreConfig config);

    @Update("UPDATE score_config SET label=#{label}, level=#{level}, score=#{score}, note=#{note} WHERE id=#{id}")
    int update(ScoreConfig config);

    @Delete("TRUNCATE TABLE score_config")
    void truncate();
}
