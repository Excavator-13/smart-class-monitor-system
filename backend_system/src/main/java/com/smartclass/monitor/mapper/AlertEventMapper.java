package com.smartclass.monitor.mapper;

import com.smartclass.monitor.entity.AlertEvent;
import org.apache.ibatis.annotations.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Mapper
public interface AlertEventMapper {

    @Select("SELECT * FROM alert_event WHERE event_id = #{eventId}")
    AlertEvent findByEventId(@Param("eventId") String eventId);

    @Insert("INSERT INTO alert_event (event_id, stream_id, student_id, alert_type, alert_name, " +
            "level, status, confidence, duration_seconds, zone_id, target_info, snapshot_path, " +
            "record_path, event_time_offset, extra, occurred_at) " +
            "VALUES (#{eventId}, #{streamId}, #{studentId}, #{alertType}, #{alertName}, " +
            "#{level}, #{status}, #{confidence}, #{durationSeconds}, #{zoneId}, #{targetInfo}, " +
            "#{snapshotPath}, #{recordPath}, #{eventTimeOffset}, #{extra}, #{occurredAt})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(AlertEvent event);

    // === 前端查询 ===

    @Select("<script>" +
            "SELECT a.*, vs.stream_name, s.name AS student_name " +
            "FROM alert_event a " +
            "LEFT JOIN video_stream vs ON a.stream_id = vs.stream_id AND vs.deleted_at IS NULL " +
            "LEFT JOIN student s ON a.student_id = s.id AND s.deleted_at IS NULL " +
            "WHERE 1=1 " +
            "<if test='streamId != null and streamId != \"\"'>AND a.stream_id = #{streamId}</if>" +
            "<if test='alertType != null and alertType != \"\"'>AND a.alert_type = #{alertType}</if>" +
            "<if test='status != null and status != \"\"'>AND a.status = #{status}</if>" +
            "<if test='level != null and level != \"\"'>AND a.level = #{level}</if>" +
            "<if test='startTime != null'>AND a.occurred_at >= #{startTime}</if>" +
            "<if test='endTime != null'>AND a.occurred_at &lt;= #{endTime}</if>" +
            "ORDER BY a.occurred_at DESC " +
            "LIMIT #{offset}, #{limit}" +
            "</script>")
    List<Map<String, Object>> findAlerts(@Param("streamId") String streamId,
                                          @Param("alertType") String alertType,
                                          @Param("status") String status,
                                          @Param("level") String level,
                                          @Param("startTime") LocalDateTime startTime,
                                          @Param("endTime") LocalDateTime endTime,
                                          @Param("offset") int offset,
                                          @Param("limit") int limit);

    @Select("<script>" +
            "SELECT COUNT(*) FROM alert_event WHERE 1=1 " +
            "<if test='streamId != null and streamId != \"\"'>AND stream_id = #{streamId}</if>" +
            "<if test='alertType != null and alertType != \"\"'>AND alert_type = #{alertType}</if>" +
            "<if test='status != null and status != \"\"'>AND status = #{status}</if>" +
            "<if test='level != null and level != \"\"'>AND level = #{level}</if>" +
            "<if test='startTime != null'>AND occurred_at >= #{startTime}</if>" +
            "<if test='endTime != null'>AND occurred_at &lt;= #{endTime}</if>" +
            "</script>")
    long countAlerts(@Param("streamId") String streamId,
                     @Param("alertType") String alertType,
                     @Param("status") String status,
                     @Param("level") String level,
                     @Param("startTime") LocalDateTime startTime,
                     @Param("endTime") LocalDateTime endTime);

    @Select("SELECT a.*, vs.stream_name, s.name AS student_name " +
            "FROM alert_event a " +
            "LEFT JOIN video_stream vs ON a.stream_id = vs.stream_id AND vs.deleted_at IS NULL " +
            "LEFT JOIN student s ON a.student_id = s.id AND s.deleted_at IS NULL " +
            "WHERE a.id = #{id}")
    Map<String, Object> findAlertDetail(@Param("id") Long id);

    // === 状态更新 ===

    @Update("UPDATE alert_event SET status=#{status}, handler_id=#{handlerId}, " +
            "remark=#{remark}, handled_at=#{handledAt} WHERE id=#{id}")
    int updateStatus(@Param("id") Long id, @Param("status") String status,
                     @Param("handlerId") Long handlerId, @Param("remark") String remark,
                     @Param("handledAt") LocalDateTime handledAt);

    // === 统计 ===

    @Select("SELECT COUNT(*) FROM alert_event WHERE DATE(occurred_at) = CURDATE()")
    long countTodayAlerts();

    @Select("SELECT COUNT(*) FROM alert_event WHERE status = 'unhandled'")
    long countUnhandled();

    @Select("SELECT alert_type, COUNT(*) AS cnt FROM alert_event " +
            "WHERE DATE(occurred_at) = CURDATE() GROUP BY alert_type")
    List<Map<String, Object>> countByTypeToday();

    @Delete("TRUNCATE TABLE alert_event")
    void truncate();
}