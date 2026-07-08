package com.smartclass.monitor.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class VideoStream {
    private Long id;
    private String streamId;
    private String streamName;
    private String rtmpUrl;
    private String previewMjpegUrl;
    private String hlsUrl;
    private String location;
    private String status;
    private LocalDateTime lastOnlineAt;
    private LocalDateTime lastOfflineAt;
    private String remark;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private LocalDateTime deletedAt;
}
