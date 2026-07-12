package com.smartclass.monitor.controller;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.dto.ZoneCreateRequest;
import com.smartclass.monitor.dto.ZoneUpdateRequest;
import com.smartclass.monitor.service.ZoneService;
import com.smartclass.monitor.vo.ZoneVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@Tag(name = "frontend-api", description = "前端业务接口")
public class ZoneController {

    private final ZoneService zoneService;

    public ZoneController(ZoneService zoneService) {
        this.zoneService = zoneService;
    }

    @GetMapping("/zones")
    @Operation(summary = "查询区域配置", description = "按 stream_id 和 zone_type 筛选区域列表")
    public ApiResponse<List<ZoneVO>> list(
            @RequestParam(required = false) String streamId,
            @RequestParam(required = false) String zoneType) {
        return ApiResponse.success(zoneService.listZones(streamId, zoneType));
    }

    @PostMapping("/zones")
    @Operation(summary = "新增区域", description = "创建区域配置，coordinates 为 0-1 归一化坐标 JSON")
    public ApiResponse<ZoneVO> create(@Valid @RequestBody ZoneCreateRequest request) {
        return ApiResponse.success(zoneService.createZone(request));
    }

    @GetMapping("/zones/{id}")
    @Operation(summary = "区域详情", description = "根据主键 id 查询区域详情")
    public ApiResponse<ZoneVO> detail(@PathVariable Long id) {
        return ApiResponse.success(zoneService.getZoneById(id));
    }

    @PutMapping("/zones/{id}")
    @Operation(summary = "修改区域", description = "更新区域配置，修改后自动通知 AI 刷新")
    public ApiResponse<Void> update(@PathVariable Long id, @RequestBody ZoneUpdateRequest request) {
        zoneService.updateZone(id, request);
        return ApiResponse.success();
    }

    @DeleteMapping("/zones/{id}")
    @Operation(summary = "删除区域", description = "软删除区域，删除后自动通知 AI 刷新")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        zoneService.deleteZone(id);
        return ApiResponse.success();
    }

    @PutMapping("/zones/{id}/toggle")
    @Operation(summary = "切换区域开关", description = "仅切换 enabled 状态，teacher 可调用")
    public ApiResponse<Void> toggle(@PathVariable Long id, @RequestParam boolean enabled) {
        zoneService.toggleZone(id, enabled);
        return ApiResponse.success();
    }

    @GetMapping("/streams/{stream_id}/zones")
    @Operation(summary = "获取视频源全部区域", description = "查询指定 stream_id 下的所有已启用区域")
    public ApiResponse<List<ZoneVO>> zonesByStream(@PathVariable("stream_id") String streamId) {
        return ApiResponse.success(zoneService.getZonesByStreamId(streamId));
    }
}