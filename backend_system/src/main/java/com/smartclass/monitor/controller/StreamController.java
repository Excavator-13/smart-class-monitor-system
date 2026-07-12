package com.smartclass.monitor.controller;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.common.response.PageResult;
import com.smartclass.monitor.dto.StreamCreateRequest;
import com.smartclass.monitor.dto.StreamUpdateRequest;
import com.smartclass.monitor.security.RequireRole;
import com.smartclass.monitor.service.StreamService;
import com.smartclass.monitor.vo.StreamPreviewVO;
import com.smartclass.monitor.vo.StreamStatusVO;
import com.smartclass.monitor.vo.StreamVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@Tag(name = "frontend-api", description = "前端业务接口")
public class StreamController {

    private final StreamService streamService;

    public StreamController(StreamService streamService) {
        this.streamService = streamService;
    }

    @GetMapping("/streams")
    @Operation(summary = "查询视频源列表", description = "返回视频源分页列表，每个 record 包含 id 和 stream_id")
    public ApiResponse<PageResult<StreamVO>> list(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String keyword,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int pageSize) {
        return ApiResponse.success(streamService.listStreams(status, keyword, page, pageSize));
    }

    @PostMapping("/streams")
    @Operation(summary = "新增视频源", description = "创建新的视频源，stream_id 必须唯一且与推流端 Stream Key 一致")
    @RequireRole("admin")
    public ApiResponse<StreamVO> create(@Valid @RequestBody StreamCreateRequest request) {
        return ApiResponse.success(streamService.createStream(request));
    }

    @GetMapping("/streams/enabled")
    @Operation(summary = "获取已启用的视频源", description = "返回 status=enabled 的视频源列表，供首页下拉和 AI 同步使用")
    public ApiResponse<List<StreamVO>> enabled() {
        return ApiResponse.success(streamService.getEnabledStreams());
    }

    @GetMapping("/streams/{id}")
    @Operation(summary = "视频源详情", description = "根据数据库主键 id 查询视频源详情")
    public ApiResponse<StreamVO> detail(@PathVariable Long id) {
        return ApiResponse.success(streamService.getStreamById(id));
    }

    @PutMapping("/streams/{id}")
    @Operation(summary = "编辑视频源", description = "根据数据库主键 id 更新视频源")
    @RequireRole("admin")
    public ApiResponse<Void> update(@PathVariable Long id, @RequestBody StreamUpdateRequest request) {
        streamService.updateStream(id, request);
        return ApiResponse.success();
    }

    @DeleteMapping("/streams/{id}")
    @Operation(summary = "删除视频源", description = "软删除视频源，有关联告警时不会物理删除")
    @RequireRole("admin")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        streamService.deleteStream(id);
        return ApiResponse.success();
    }

    @GetMapping("/streams/{stream_id}/status")
    @Operation(summary = "查询推流状态", description = "通过 Nginx /stat XML 判断视频源在线状态。路径参数为 stream_id（业务标识）")
    public ApiResponse<StreamStatusVO> status(@PathVariable("stream_id") String streamId) {
        return ApiResponse.success(streamService.getStreamStatus(streamId));
    }

    @GetMapping("/streams/{stream_id}/preview-url")
    @Operation(summary = "获取播放地址", description = "返回 MJPEG、RTMP、HLS 地址，不代理视频流。路径参数为 stream_id（业务标识）")
    public ApiResponse<StreamPreviewVO> previewUrl(@PathVariable("stream_id") String streamId) {
        return ApiResponse.success(streamService.getPreviewUrl(streamId));
    }
}