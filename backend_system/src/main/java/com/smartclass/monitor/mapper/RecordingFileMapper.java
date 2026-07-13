package com.smartclass.monitor.mapper;

import com.smartclass.monitor.entity.RecordingFile;
import org.apache.ibatis.annotations.*;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface RecordingFileMapper {

    @Select("<script>" +
            "SELECT * FROM recording_file WHERE deleted_at IS NULL " +
            "<if test='streamId != null and streamId != \"\"'>AND stream_id = #{streamId}</if>" +
            "<if test='eventId != null and eventId != \"\"'>AND event_id = #{eventId}</if>" +
            "<if test='startTime != null'>AND started_at >= #{startTime}</if>" +
            "<if test='endTime != null'>AND started_at &lt;= #{endTime}</if>" +
            "ORDER BY started_at DESC " +
            "LIMIT #{offset}, #{limit}" +
            "</script>")
    List<RecordingFile> findRecordings(@Param("streamId") String streamId,
                                        @Param("eventId") String eventId,
                                        @Param("startTime") LocalDateTime startTime,
                                        @Param("endTime") LocalDateTime endTime,
                                        @Param("offset") int offset,
                                        @Param("limit") int limit);

    @Select("<script>" +
            "SELECT COUNT(*) FROM recording_file WHERE deleted_at IS NULL " +
            "<if test='streamId != null and streamId != \"\"'>AND stream_id = #{streamId}</if>" +
            "<if test='eventId != null and eventId != \"\"'>AND event_id = #{eventId}</if>" +
            "<if test='startTime != null'>AND started_at >= #{startTime}</if>" +
            "<if test='endTime != null'>AND started_at &lt;= #{endTime}</if>" +
            "</script>")
    long countRecordings(@Param("streamId") String streamId,
                          @Param("eventId") String eventId,
                          @Param("startTime") LocalDateTime startTime,
                          @Param("endTime") LocalDateTime endTime);

    @Select("SELECT * FROM recording_file WHERE deleted_at IS NULL " +
            "AND stream_id = #{streamId} " +
            "AND started_at <= #{timestamp} " +
            "AND (ended_at IS NULL OR ended_at >= #{timestamp}) " +
            "ORDER BY started_at DESC LIMIT 1")
    RecordingFile findContainingRecording(@Param("streamId") String streamId,
                                           @Param("timestamp") LocalDateTime timestamp);

    @Delete("TRUNCATE TABLE recording_file")
    void truncate();
}