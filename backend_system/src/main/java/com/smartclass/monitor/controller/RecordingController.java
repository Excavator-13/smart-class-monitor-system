package com.smartclass.monitor.controller;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.common.response.PageResult;
import com.smartclass.monitor.service.RecordingService;
import com.smartclass.monitor.vo.RecordingVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

@RestController
@Tag(name = "frontend-api", description = "前端业务接口")
public class RecordingController {

    private final RecordingService recordingService;

    public RecordingController(RecordingService recordingService) {
        this.recordingService = recordingService;
    }

    @GetMapping("/recordings")
    @Operation(summary = "查询录像列表", description = "分页查询录像文件，支持按视频源、事件ID、时间范围筛选")
    public ApiResponse<PageResult<RecordingVO>> list(
            @RequestParam(required = false) String streamId,
            @RequestParam(required = false) String eventId,
            @RequestParam(required = false) String startTime,
            @RequestParam(required = false) String endTime,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int pageSize) {
        return ApiResponse.success(
                recordingService.listRecordings(streamId, eventId, startTime, endTime, page, pageSize));
    }
}
