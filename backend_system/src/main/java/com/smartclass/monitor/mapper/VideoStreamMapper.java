package com.smartclass.monitor.mapper;

import com.smartclass.monitor.entity.VideoStream;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface VideoStreamMapper {

    @Select("<script>" +
            "SELECT * FROM video_stream WHERE deleted_at IS NULL " +
            "<if test='status != null and status != \"\"'>AND status = #{status}</if>" +
            "<if test='keyword != null and keyword != \"\"'>AND (stream_name LIKE CONCAT('%',#{keyword},'%') OR stream_id LIKE CONCAT('%',#{keyword},'%'))</if>" +
            "ORDER BY created_at DESC" +
            "</script>")
    List<VideoStream> findAll(@Param("status") String status, @Param("keyword") String keyword);

    @Select("SELECT * FROM video_stream WHERE stream_id = #{streamId} AND deleted_at IS NULL")
    VideoStream findByStreamId(@Param("streamId") String streamId);

    @Select("SELECT * FROM video_stream WHERE id = #{id} AND deleted_at IS NULL")
    VideoStream findById(@Param("id") Long id);

    @Select("SELECT * FROM video_stream WHERE status = 'enabled' AND deleted_at IS NULL ORDER BY stream_name")
    List<VideoStream> findEnabled();

    @Insert("INSERT INTO video_stream (stream_id, stream_name, rtmp_url, preview_mjpeg_url, hls_url, location, status, remark) " +
            "VALUES (#{streamId}, #{streamName}, #{rtmpUrl}, #{previewMjpegUrl}, #{hlsUrl}, #{location}, #{status}, #{remark})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(VideoStream stream);

    @Update("UPDATE video_stream SET stream_name=#{streamName}, rtmp_url=#{rtmpUrl}, status=#{status}, " +
            "preview_mjpeg_url=#{previewMjpegUrl}, hls_url=#{hlsUrl}, location=#{location}, remark=#{remark} WHERE id=#{id}")
    int update(VideoStream stream);

    @Update("UPDATE video_stream SET deleted_at=NOW() WHERE id=#{id}")
    int softDelete(@Param("id") Long id);

    @Delete("TRUNCATE TABLE video_stream")
    void truncate();
}