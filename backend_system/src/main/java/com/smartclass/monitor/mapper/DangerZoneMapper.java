package com.smartclass.monitor.mapper;

import com.smartclass.monitor.entity.DangerZone;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface DangerZoneMapper {

    @Select("<script>" +
            "SELECT * FROM danger_zone WHERE deleted_at IS NULL " +
            "<if test='streamId != null and streamId != \"\"'>AND stream_id = #{streamId}</if>" +
            "<if test='zoneType != null and zoneType != \"\"'>AND zone_type = #{zoneType}</if>" +
            "ORDER BY created_at DESC" +
            "</script>")
    List<DangerZone> findAll(@Param("streamId") String streamId, @Param("zoneType") String zoneType);

    @Select("SELECT * FROM danger_zone WHERE id = #{id} AND deleted_at IS NULL")
    DangerZone findById(@Param("id") Long id);

    @Select("SELECT * FROM danger_zone WHERE stream_id = #{streamId} AND deleted_at IS NULL AND enabled = 1")
    List<DangerZone> findByStreamId(@Param("streamId") String streamId);

    @Insert("INSERT INTO danger_zone (stream_id, zone_name, zone_type, shape_type, coordinates, " +
            "threshold_seconds, safe_distance, enabled, config_json) " +
            "VALUES (#{streamId}, #{zoneName}, #{zoneType}, #{shapeType}, #{coordinates}, " +
            "#{thresholdSeconds}, #{safeDistance}, #{enabled}, #{configJson})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(DangerZone zone);

    @Update("UPDATE danger_zone SET zone_name=#{zoneName}, zone_type=#{zoneType}, " +
            "coordinates=#{coordinates}, threshold_seconds=#{thresholdSeconds}, " +
            "safe_distance=#{safeDistance}, enabled=#{enabled}, config_json=#{configJson} WHERE id=#{id}")
    int update(DangerZone zone);

    @Update("UPDATE danger_zone SET deleted_at=NOW() WHERE id=#{id}")
    int softDelete(@Param("id") Long id);

    @Delete("TRUNCATE TABLE danger_zone")
    void truncate();
}