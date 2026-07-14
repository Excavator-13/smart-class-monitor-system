-- user 登录用户表
CREATE TABLE IF NOT EXISTS `user` (
    `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户主键',
    `username`   VARCHAR(64)     NOT NULL COMMENT '登录名',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希（BCrypt）',
    `role`       VARCHAR(32)     NOT NULL DEFAULT 'teacher' COMMENT '角色：admin / teacher',
    `nickname`   VARCHAR(64)     DEFAULT NULL COMMENT '昵称',
    `avatar_url` VARCHAR(255)    DEFAULT NULL COMMENT '头像相对路径或外部URL',
    `status`     VARCHAR(32)     NOT NULL DEFAULT 'enabled' COMMENT 'enabled / disabled',
    `last_login_at` DATETIME     DEFAULT NULL COMMENT '最近登录时间',
    `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_at` DATETIME        DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_username` (`username`),
    KEY `idx_user_role` (`role`),
    KEY `idx_user_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='登录用户表';

-- video_stream 视频源配置表
CREATE TABLE IF NOT EXISTS `video_stream` (
    `id`                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '数据库主键',
    `stream_id`         VARCHAR(128)    NOT NULL COMMENT '业务标识，必须与推流端 Stream Key 一致',
    `stream_name`       VARCHAR(128)    NOT NULL COMMENT '展示名称',
    `rtmp_url`          VARCHAR(500)    NOT NULL COMMENT 'RTMP 推拉流地址',
    `preview_mjpeg_url` VARCHAR(500)    DEFAULT NULL COMMENT 'MJPEG 预览地址',
    `hls_url`           VARCHAR(500)    DEFAULT NULL COMMENT 'HLS 播放地址',
    `location`          VARCHAR(255)    DEFAULT NULL COMMENT '教室或摄像头位置',
    `status`            VARCHAR(32)     NOT NULL DEFAULT 'enabled' COMMENT '配置状态：enabled / disabled',
    `last_online_at`    DATETIME        DEFAULT NULL COMMENT '最近在线时间',
    `last_offline_at`   DATETIME        DEFAULT NULL COMMENT '最近离线时间',
    `remark`            VARCHAR(500)    DEFAULT NULL COMMENT '备注',
    `created_at`        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_at`        DATETIME        DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_video_stream_id` (`stream_id`),
    KEY `idx_video_stream_status` (`status`),
    KEY `idx_video_stream_name` (`stream_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频源配置表';

-- student 人员基础信息表
CREATE TABLE IF NOT EXISTS `student` (
    `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '人员主键',
    `student_no`      VARCHAR(64)     NOT NULL COMMENT '学号或人员编号',
    `name`            VARCHAR(64)     NOT NULL COMMENT '姓名',
    `class_name`      VARCHAR(128)    DEFAULT NULL COMMENT '班级或分组',
    `gender`          VARCHAR(16)     DEFAULT NULL COMMENT '性别',
    `phone`           VARCHAR(32)     DEFAULT NULL COMMENT '联系方式',
    `face_registered` TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否已注册人脸',
    `status`          VARCHAR(32)     NOT NULL DEFAULT 'enabled' COMMENT 'enabled / disabled',
    `remark`          VARCHAR(500)    DEFAULT NULL COMMENT '备注',
    `created_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_at`      DATETIME        DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_student_no` (`student_no`),
    KEY `idx_student_class_name` (`class_name`),
    KEY `idx_student_face_registered` (`face_registered`),
    KEY `idx_student_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人员基础信息表';

-- face_feature 人脸特征表
CREATE TABLE IF NOT EXISTS `face_feature` (
    `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '特征记录主键',
    `student_id`      BIGINT UNSIGNED NOT NULL COMMENT '关联 student.id',
    `feature_dim`     INT             NOT NULL COMMENT '特征维度（128 或 512）',
    `feature_vector`  JSON            NOT NULL COMMENT '特征向量，不返回给前端',
    `image_path`      VARCHAR(255)    DEFAULT NULL COMMENT '注册图片相对路径',
    `quality_score`   DECIMAL(5,4)    DEFAULT NULL COMMENT '人脸质量评分 0-1',
    `quality_json`    JSON            DEFAULT NULL COMMENT '亮度、模糊度等质量详情',
    `bbox_json`       JSON            DEFAULT NULL COMMENT 'AI 返回的人脸框 [x,y,w,h]',
    `model_name`      VARCHAR(64)     DEFAULT NULL COMMENT '特征提取模型名称',
    `model_version`   VARCHAR(64)     DEFAULT NULL COMMENT '模型版本',
    `version`         INT             NOT NULL DEFAULT 1 COMMENT '同一人员的特征版本号',
    `enabled`         TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_at`      DATETIME        DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    KEY `idx_face_feature_student` (`student_id`),
    KEY `idx_face_feature_enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人脸特征表';

-- danger_zone 区域配置表
CREATE TABLE IF NOT EXISTS `danger_zone` (
    `id`                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '区域主键',
    `stream_id`         VARCHAR(128)    NOT NULL COMMENT '关联 video_stream.stream_id',
    `zone_name`         VARCHAR(128)    NOT NULL COMMENT '区域名称',
    `zone_type`         VARCHAR(64)     NOT NULL COMMENT 'danger / phone_forbidden',
    `shape_type`        VARCHAR(32)     NOT NULL DEFAULT 'polygon' COMMENT '形状类型',
    `coordinates`       JSON            NOT NULL COMMENT '归一化坐标（0-1 比例）',
    `threshold_seconds` INT             DEFAULT NULL COMMENT '区域停留阈值（秒）',
    `safe_distance`     DECIMAL(8,6)    DEFAULT NULL COMMENT '接近预警距离阈值（归一化比例）',
    `enabled`           TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否启用',
    `config_json`       JSON            DEFAULT NULL COMMENT '扩展配置',
    `created_at`        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_at`        DATETIME        DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    KEY `idx_zone_stream` (`stream_id`),
    KEY `idx_zone_stream_type` (`stream_id`, `zone_type`),
    KEY `idx_zone_enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='区域配置表';

-- behavior_rule 行为规则表
CREATE TABLE IF NOT EXISTS `behavior_rule` (
    `id`                   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '规则主键',
    `rule_type`            VARCHAR(64)     NOT NULL COMMENT '规则类型',
    `rule_name`            VARCHAR(128)    DEFAULT NULL COMMENT '规则中文名',
    `enabled`              TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否启用',
    `threshold_seconds`    INT             DEFAULT NULL COMMENT '持续时间阈值（秒）',
    `confidence_threshold` DECIMAL(5,4)    DEFAULT NULL COMMENT '置信度阈值 0-1',
    `cooldown_seconds`     INT             DEFAULT NULL COMMENT '同类告警冷却时间（秒）',
    `level`                VARCHAR(32)     DEFAULT 'warning' COMMENT '默认告警等级',
    `config_json`          JSON            DEFAULT NULL COMMENT '扩展规则配置',
    `created_at`           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_at`           DATETIME        DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_behavior_rule_type` (`rule_type`),
    KEY `idx_behavior_rule_enabled` (`enabled`),
    KEY `idx_behavior_rule_level` (`level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='行为检测规则表';

-- alert_event 告警事件表
CREATE TABLE IF NOT EXISTS `alert_event` (
    `id`                 BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '告警主键',
    `event_id`           VARCHAR(128)    NOT NULL COMMENT 'AI 事件唯一 ID，用于幂等',
    `stream_id`          VARCHAR(128)    NOT NULL COMMENT '视频源业务 ID',
    `student_id`         BIGINT UNSIGNED DEFAULT NULL COMMENT '关联 student.id，陌生人可为空',
    `alert_type`         VARCHAR(64)     NOT NULL COMMENT '告警类型',
    `alert_name`         VARCHAR(128)    DEFAULT NULL COMMENT '告警中文名',
    `level`              VARCHAR(32)     NOT NULL COMMENT 'info / warning / high',
    `status`             VARCHAR(32)     NOT NULL DEFAULT 'unhandled' COMMENT 'unhandled/processing/handled/false_alarm/ignored',
    `confidence`         DECIMAL(5,4)    DEFAULT NULL COMMENT '置信度 0-1',
    `duration_seconds`   DECIMAL(10,3)   DEFAULT NULL COMMENT '持续时间（秒）',
    `zone_id`            BIGINT UNSIGNED DEFAULT NULL COMMENT '关联区域 ID',
    `target_info`        JSON            DEFAULT NULL COMMENT '目标信息 {track_id, bbox}',
    `snapshot_path`      VARCHAR(255)    DEFAULT NULL COMMENT '截图相对路径',
    `record_path`        VARCHAR(255)    DEFAULT NULL COMMENT '录像相对路径',
    `event_time_offset`  DECIMAL(10,3)   DEFAULT NULL COMMENT '事件在录像中的偏移秒数',
    `extra`              JSON            DEFAULT NULL COMMENT '扩展信息（模型、规则等）',
    `occurred_at`        DATETIME        NOT NULL COMMENT '发生时间',
    `handled_at`         DATETIME        DEFAULT NULL COMMENT '处理时间',
    `handler_id`         BIGINT UNSIGNED DEFAULT NULL COMMENT '处理人 user.id',
    `remark`             VARCHAR(1000)   DEFAULT NULL COMMENT '处理备注',
    `created_at`         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    `updated_at`         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_alert_event_id` (`event_id`),
    KEY `idx_alert_time` (`occurred_at`),
    KEY `idx_alert_stream_time` (`stream_id`, `occurred_at`),
    KEY `idx_alert_status_time` (`status`, `occurred_at`),
    KEY `idx_alert_type_time` (`alert_type`, `occurred_at`),
    KEY `idx_alert_level_time` (`level`, `occurred_at`),
    KEY `idx_alert_student` (`student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警事件表';

-- recording_file 录像文件索引表
CREATE TABLE IF NOT EXISTS `recording_file` (
    `id`               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '录像主键',
    `stream_id`        VARCHAR(128)    NOT NULL COMMENT '视频源业务 ID',
    `event_id`         VARCHAR(128)    DEFAULT NULL COMMENT '关联告警事件 ID',
    `file_path`        VARCHAR(255)    NOT NULL COMMENT '相对路径',
    `file_name`        VARCHAR(255)    NOT NULL COMMENT '文件名',
    `file_ext`         VARCHAR(16)     DEFAULT NULL COMMENT '文件扩展名',
    `file_size`        BIGINT UNSIGNED DEFAULT NULL COMMENT '文件大小（字节）',
    `started_at`       DATETIME        DEFAULT NULL COMMENT '录像开始时间',
    `ended_at`         DATETIME        DEFAULT NULL COMMENT '录像结束时间',
    `duration_seconds` DECIMAL(10,3)   DEFAULT NULL COMMENT '持续时长（秒）',
    `source_type`      VARCHAR(32)     NOT NULL DEFAULT 'nginx_record' COMMENT '来源: nginx_record / ai_clip',
    `created_at`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    `deleted_at`       DATETIME        DEFAULT NULL COMMENT '过期或软删除时间',
    PRIMARY KEY (`id`),
    KEY `idx_recording_stream` (`stream_id`),
    KEY `idx_recording_event` (`event_id`),
    KEY `idx_recording_time` (`started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='录像文件索引表';

-- operation_log 操作日志表
CREATE TABLE IF NOT EXISTS `operation_log` (
    `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志主键',
    `user_id`        BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人 ID',
    `username`       VARCHAR(64)     DEFAULT NULL COMMENT '操作用户名快照',
    `action`         VARCHAR(128)    NOT NULL COMMENT '操作动作',
    `target_type`    VARCHAR(64)     DEFAULT NULL COMMENT '目标类型',
    `target_id`      VARCHAR(128)    DEFAULT NULL COMMENT '目标 ID',
    `method`         VARCHAR(16)     DEFAULT NULL COMMENT 'HTTP 方法',
    `request_uri`    VARCHAR(500)    DEFAULT NULL COMMENT '请求路径',
    `request_ip`     VARCHAR(64)     DEFAULT NULL COMMENT '客户端 IP',
    `request_body`   JSON            DEFAULT NULL COMMENT '脱敏后的请求体',
    `result_code`    INT             DEFAULT NULL COMMENT '响应 code',
    `result_message` VARCHAR(500)    DEFAULT NULL COMMENT '响应摘要',
    `created_at`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    PRIMARY KEY (`id`),
    KEY `idx_operation_log_user_time` (`user_id`, `created_at`),
    KEY `idx_operation_log_action_time` (`action`, `created_at`),
    KEY `idx_operation_log_target` (`target_type`, `target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作审计日志表';

-- score_config 告警评分配置表
CREATE TABLE IF NOT EXISTS `score_config` (
    `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
    `alert_type` VARCHAR(64)     NOT NULL COMMENT '告警类型',
    `label`      VARCHAR(64)     NOT NULL COMMENT '显示名称',
    `score`      INT             NOT NULL DEFAULT 50 COMMENT '评分权重 0-100',
    `note`       VARCHAR(255)    DEFAULT NULL COMMENT '说明',
    `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_score_config_type` (`alert_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警评分配置表';