package com.smartclass.monitor.mapper;

import com.smartclass.monitor.entity.OperationLog;
import org.apache.ibatis.annotations.*;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface OperationLogMapper {

    @Select("<script>" +
            "SELECT * FROM operation_log WHERE 1=1 " +
            "<if test='userId != null'>AND user_id = #{userId}</if>" +
            "<if test='action != null and action != \"\"'>AND action = #{action}</if>" +
            "<if test='targetType != null and targetType != \"\"'>AND target_type = #{targetType}</if>" +
            "<if test='targetId != null and targetId != \"\"'>AND target_id = #{targetId}</if>" +
            "<if test='startTime != null'>AND created_at >= #{startTime}</if>" +
            "<if test='endTime != null'>AND created_at &lt;= #{endTime}</if>" +
            "ORDER BY created_at DESC " +
            "LIMIT #{offset}, #{limit}" +
            "</script>")
    List<OperationLog> findLogs(@Param("userId") Long userId,
                                 @Param("action") String action,
                                 @Param("targetType") String targetType,
                                 @Param("targetId") String targetId,
                                 @Param("startTime") LocalDateTime startTime,
                                 @Param("endTime") LocalDateTime endTime,
                                 @Param("offset") int offset,
                                 @Param("limit") int limit);

    @Select("<script>" +
            "SELECT COUNT(*) FROM operation_log WHERE 1=1 " +
            "<if test='userId != null'>AND user_id = #{userId}</if>" +
            "<if test='action != null and action != \"\"'>AND action = #{action}</if>" +
            "<if test='targetType != null and targetType != \"\"'>AND target_type = #{targetType}</if>" +
            "<if test='targetId != null and targetId != \"\"'>AND target_id = #{targetId}</if>" +
            "<if test='startTime != null'>AND created_at >= #{startTime}</if>" +
            "<if test='endTime != null'>AND created_at &lt;= #{endTime}</if>" +
            "</script>")
    long countLogs(@Param("userId") Long userId,
                    @Param("action") String action,
                    @Param("targetType") String targetType,
                    @Param("targetId") String targetId,
                    @Param("startTime") LocalDateTime startTime,
                    @Param("endTime") LocalDateTime endTime);

    @Insert("INSERT INTO operation_log (user_id, username, action, target_type, target_id, " +
            "method, request_uri, request_ip, request_body, result_code, result_message) " +
            "VALUES (#{userId}, #{username}, #{action}, #{targetType}, #{targetId}, " +
            "#{method}, #{requestUri}, #{requestIp}, #{requestBody}, #{resultCode}, #{resultMessage})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(OperationLog log);
}
