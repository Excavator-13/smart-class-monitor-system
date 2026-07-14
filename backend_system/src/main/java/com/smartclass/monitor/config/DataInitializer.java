package com.smartclass.monitor.config;

import com.smartclass.monitor.entity.*;
import com.smartclass.monitor.mapper.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;

@Component
public class DataInitializer implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(DataInitializer.class);

    private final UserMapper userMapper;
    private final VideoStreamMapper videoStreamMapper;
    private final StudentMapper studentMapper;
    private final BehaviorRuleMapper behaviorRuleMapper;
    private final DangerZoneMapper dangerZoneMapper;
    private final AlertEventMapper alertEventMapper;
    private final FaceFeatureMapper faceFeatureMapper;
    private final RecordingFileMapper recordingFileMapper;
    private final OperationLogMapper operationLogMapper;
    private final ScoreConfigMapper scoreConfigMapper;
    private final PasswordEncoder passwordEncoder;
    private final JdbcTemplate jdbcTemplate;

    public DataInitializer(UserMapper userMapper,
                           VideoStreamMapper videoStreamMapper,
                           StudentMapper studentMapper,
                           BehaviorRuleMapper behaviorRuleMapper,
                           DangerZoneMapper dangerZoneMapper,
                           AlertEventMapper alertEventMapper,
                           FaceFeatureMapper faceFeatureMapper,
                           RecordingFileMapper recordingFileMapper,
                           OperationLogMapper operationLogMapper,
                           ScoreConfigMapper scoreConfigMapper,
                           PasswordEncoder passwordEncoder,
                           JdbcTemplate jdbcTemplate) {
        this.userMapper = userMapper;
        this.videoStreamMapper = videoStreamMapper;
        this.studentMapper = studentMapper;
        this.behaviorRuleMapper = behaviorRuleMapper;
        this.dangerZoneMapper = dangerZoneMapper;
        this.alertEventMapper = alertEventMapper;
        this.faceFeatureMapper = faceFeatureMapper;
        this.recordingFileMapper = recordingFileMapper;
        this.operationLogMapper = operationLogMapper;
        this.scoreConfigMapper = scoreConfigMapper;
        this.passwordEncoder = passwordEncoder;
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    @Transactional
    public void run(String... args) {
        log.info("===== DataInitializer: 开始幂等补齐默认配置 =====");
        ensureSchemaCompatibility();
        seedUsers();
        seedStreams();
        seedRules();
        seedScoreConfig();
        log.info("===== DataInitializer: 默认配置检查完成 =====");
    }

    private void ensureSchemaCompatibility() {
        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM information_schema.columns " +
                        "WHERE table_schema=DATABASE() AND table_name='score_config' AND column_name='level'",
                Integer.class);
        if (count != null && count == 0) {
            jdbcTemplate.execute("ALTER TABLE score_config ADD COLUMN level VARCHAR(32) " +
                    "NOT NULL DEFAULT 'warning' COMMENT '默认告警等级：info / warning / high' AFTER label");
            log.info("score_config.level 字段已补齐");
        }
    }

    private void seedUsers() {
        log.info("插入测试用户...");
        String adminHash = passwordEncoder.encode("admin123");
        String teacherHash = passwordEncoder.encode("teacher123");

        if (userMapper.findByUsername("admin") == null) {
            User admin = new User();
            admin.setUsername("admin");
            admin.setPasswordHash(adminHash);
            admin.setRole("admin");
            admin.setNickname("管理员");
            admin.setStatus("enabled");
            userMapper.insert(admin);
        }

        if (userMapper.findByUsername("teacher") == null) {
            User teacher = new User();
            teacher.setUsername("teacher");
            teacher.setPasswordHash(teacherHash);
            teacher.setRole("teacher");
            teacher.setNickname("教师");
            teacher.setStatus("enabled");
            userMapper.insert(teacher);
        }

        log.info("测试用户: admin/admin123, teacher/teacher123");
    }

    private void seedStreams() {
        log.info("插入测试视频源...");
        VideoStream stream1 = new VideoStream();
        stream1.setStreamId("classroom_01");
        stream1.setStreamName("教室01 主摄像头");
        stream1.setRtmpUrl("rtmp://39.106.209.208:9090/live/classroom_01");
        stream1.setPreviewMjpegUrl("http://localhost:5001/video_feed/classroom_01");
        stream1.setHlsUrl("http://39.106.209.208:9092/live/classroom_01.m3u8");
        stream1.setLocation("教学楼A101");
        stream1.setStatus("enabled");
        stream1.setRemark("云服务器RTMP测试流");
        if (videoStreamMapper.findByStreamId(stream1.getStreamId()) == null) {
            videoStreamMapper.insert(stream1);
        }

        VideoStream stream2 = new VideoStream();
        stream2.setStreamId("classroom_02");
        stream2.setStreamName("教室02 后排摄像头");
        stream2.setRtmpUrl("rtmp://39.106.209.208:9090/live/classroom_02");
        stream2.setPreviewMjpegUrl("http://localhost:5001/video_feed/classroom_02");
        stream2.setHlsUrl("http://39.106.209.208:9092/live/classroom_02.m3u8");
        stream2.setLocation("教学楼B203");
        stream2.setStatus("enabled");
        stream2.setRemark("备用测试流");
        if (videoStreamMapper.findByStreamId(stream2.getStreamId()) == null) {
            videoStreamMapper.insert(stream2);
        }
    }

    private void seedStudents() {
        log.info("插入测试学生...");
        List<Student> students = Arrays.asList(
                createStudent("2026001", "张三", "计科1班", "男", true),
                createStudent("2026002", "李四", "计科1班", "男", true),
                createStudent("2026003", "王五", "计科1班", "女", true),
                createStudent("2026004", "赵六", "计科2班", "男", false),
                createStudent("2026005", "孙七", "计科2班", "女", false)
        );
        for (Student s : students) {
            studentMapper.insert(s);
        }
    }

    private Student createStudent(String studentNo, String name, String className,
                                  String gender, boolean faceRegistered) {
        Student s = new Student();
        s.setStudentNo(studentNo);
        s.setName(name);
        s.setClassName(className);
        s.setGender(gender);
        s.setFaceRegistered(faceRegistered);
        s.setStatus("enabled");
        s.setRemark(faceRegistered ? "人脸已注册" : "待采集人脸");
        return s;
    }

    private void seedRules() {
        log.info("插入测试规则...");
        List<BehaviorRule> rules = Arrays.asList(
                createRule("phone_usage", "手机违规检测", true, 5, 0.75, 30),
                createRule("flame_detected", "明火检测", true, 3, 0.80, 20),
                createRule("fall_detected", "摔倒检测", false, 4, 0.78, 20),
                createRule("head_down", "长时间低头", true, 6, 0.70, 60),
                createRule("crowd_gathering", "异常人流聚集", true, 3, 0.70, 30),
                createRule("danger_zone", "区域入侵检测", true, 5, 0.75, 30)
        );
        for (BehaviorRule r : rules) {
            if (behaviorRuleMapper.findAll(r.getRuleType()).isEmpty()) {
                behaviorRuleMapper.insert(r);
            }
        }
    }

    private BehaviorRule createRule(String ruleType, String ruleName, boolean enabled,
                                   Integer thresholdSeconds, double confidenceThreshold,
                                   Integer cooldownSeconds) {
        BehaviorRule r = new BehaviorRule();
        r.setRuleType(ruleType);
        r.setRuleName(ruleName);
        r.setEnabled(enabled);
        r.setThresholdSeconds(thresholdSeconds);
        r.setConfidenceThreshold(confidenceThreshold);
        r.setCooldownSeconds(cooldownSeconds);
        return r;
    }

    private void seedZones() {
        log.info("插入测试区域...");
        DangerZone zone = new DangerZone();
        zone.setStreamId("classroom_01");
        zone.setZoneName("讲台危险区域");
        zone.setZoneType("danger");
        zone.setShapeType("polygon");
        zone.setCoordinates("[{\"x\":0.0,\"y\":0.0},{\"x\":0.3,\"y\":0.0},{\"x\":0.3,\"y\":0.25},{\"x\":0.0,\"y\":0.25}]");
        zone.setThresholdSeconds(5);
        zone.setSafeDistance(0.05);
        zone.setEnabled(true);
        dangerZoneMapper.insert(zone);

        DangerZone phoneZone = new DangerZone();
        phoneZone.setStreamId("classroom_01");
        phoneZone.setZoneName("手机禁用区");
        phoneZone.setZoneType("phone_forbidden");
        phoneZone.setShapeType("rectangle");
        phoneZone.setCoordinates("[{\"x\":0.1,\"y\":0.3},{\"x\":0.9,\"y\":0.3},{\"x\":0.9,\"y\":0.9},{\"x\":0.1,\"y\":0.9}]");
        phoneZone.setThresholdSeconds(3);
        phoneZone.setEnabled(true);
        dangerZoneMapper.insert(phoneZone);
    }

    private void seedAlerts() {
        log.info("插入测试告警...");
        LocalDateTime now = LocalDateTime.now();

        AlertEvent alert1 = new AlertEvent();
        alert1.setEventId("evt-" + UUID.randomUUID().toString().substring(0, 8));
        alert1.setStreamId("classroom_01");
        alert1.setAlertType("head_down");
        alert1.setAlertName("长时间低头");
        alert1.setLevel("warning");
        alert1.setStatus("unhandled");
        alert1.setConfidence(0.82);
        alert1.setDurationSeconds(8.5);
        alert1.setTargetInfo("{\"track_id\":\"person_3\",\"bbox\":[0.15,0.35,0.30,0.55]}");
        alert1.setOccurredAt(now.minusMinutes(15));
        alertEventMapper.insert(alert1);

        AlertEvent alert2 = new AlertEvent();
        alert2.setEventId("evt-" + UUID.randomUUID().toString().substring(0, 8));
        alert2.setStreamId("classroom_01");
        alert2.setAlertType("danger_zone");
        alert2.setAlertName("区域入侵检测");
        alert2.setLevel("warning");
        alert2.setStatus("processing");
        alert2.setConfidence(0.76);
        alert2.setDurationSeconds(3.2);
        alert2.setTargetInfo("{\"track_id\":\"person_5\",\"bbox\":[0.05,0.05,0.25,0.20]}");
        alert2.setOccurredAt(now.minusMinutes(8));
        alertEventMapper.insert(alert2);

        AlertEvent alert3 = new AlertEvent();
        alert3.setEventId("evt-" + UUID.randomUUID().toString().substring(0, 8));
        alert3.setStreamId("classroom_01");
        alert3.setAlertType("crowd_gathering");
        alert3.setAlertName("异常人流聚集");
        alert3.setLevel("high");
        alert3.setStatus("unhandled");
        alert3.setConfidence(0.88);
        alert3.setTargetInfo("{\"track_id\":\"face_unknown_1\",\"bbox\":[0.45,0.20,0.60,0.40]}");
        alert3.setOccurredAt(now.minusMinutes(3));
        alertEventMapper.insert(alert3);

        AlertEvent alert4 = new AlertEvent();
        alert4.setEventId("evt-" + UUID.randomUUID().toString().substring(0, 8));
        alert4.setStreamId("classroom_01");
        alert4.setAlertType("head_down");
        alert4.setAlertName("长时间低头");
        alert4.setLevel("info");
        alert4.setStatus("handled");
        alert4.setConfidence(0.65);
        alert4.setDurationSeconds(5.0);
        alert4.setTargetInfo("{\"track_id\":\"person_1\",\"bbox\":[0.50,0.40,0.65,0.58]}");
        alert4.setOccurredAt(now.minusHours(2));
        alert4.setHandledAt(now.minusHours(1));
        alert4.setRemark("已确认，学生捡笔");
        alertEventMapper.insert(alert4);
    }

    private void seedScoreConfig() {
        log.info("插入告警评分配置...");
        List<ScoreConfig> configs = Arrays.asList(
                createScoreConfig("stranger_detected", "陌生人员出现", "warning", 70, "需核验人员身份"),
                createScoreConfig("danger_zone_intrusion", "危险区域入侵", "high", 78, "人员进入危险区域"),
                createScoreConfig("danger_zone_stay", "危险区域停留超时", "high", 82, "人员在危险区域持续停留"),
                createScoreConfig("danger_zone_approach", "接近危险区域", "warning", 55, "人员接近危险区域边界"),
                createScoreConfig("phone_usage", "手机违规", "info", 42, "命中已启用手机禁用区后参与评分"),
                createScoreConfig("head_down", "长时间低头", "info", 35, "课堂行为异常"),
                createScoreConfig("crowd_gathering", "异常人流聚集", "high", 76, "人员异常聚集"),
                createScoreConfig("fall_detected", "人员摔倒", "high", 86, "需立即确认人员状态"),
                createScoreConfig("leave_seat", "长时间离座", "warning", 45, "人员长时间离开座位"),
                createScoreConfig("flame_detected", "明火检测", "high", 92, "发现后立即处置"),
                createScoreConfig("spoof_detected", "活体检测异常", "high", 80, "疑似照片或回放攻击"),
                createScoreConfig("deepfake_detected", "疑似换脸攻击", "high", 90, "疑似 AI 换脸攻击"),
                createScoreConfig("abnormal_sound", "异常声学事件", "warning", 65, "检测到异常声音"),
                createScoreConfig("stream_offline", "视频流中断", "high", 75, "视频源推流中断"),
                createScoreConfig("general", "其他告警", "warning", 35, "未识别事件类型的兜底配置")
        );
        for (ScoreConfig c : configs) {
            if (scoreConfigMapper.findByType(c.getAlertType()) == null) {
                scoreConfigMapper.insert(c);
            }
        }
    }

    private ScoreConfig createScoreConfig(String alertType, String label, String level, int score, String note) {
        ScoreConfig c = new ScoreConfig();
        c.setAlertType(alertType);
        c.setLabel(label);
        c.setLevel(level);
        c.setScore(score);
        c.setNote(note);
        return c;
    }
}
