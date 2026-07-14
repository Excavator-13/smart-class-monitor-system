package com.smartclass.monitor.config;

import com.smartclass.monitor.entity.BehaviorRule;
import com.smartclass.monitor.entity.ScoreConfig;
import com.smartclass.monitor.entity.User;
import com.smartclass.monitor.entity.VideoStream;
import com.smartclass.monitor.mapper.BehaviorRuleMapper;
import com.smartclass.monitor.mapper.ScoreConfigMapper;
import com.smartclass.monitor.mapper.UserMapper;
import com.smartclass.monitor.mapper.VideoStreamMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.Arrays;
import java.util.List;

@Component
@Profile("!test")
public class DataInitializer implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(DataInitializer.class);

    private final UserMapper userMapper;
    private final VideoStreamMapper videoStreamMapper;
    private final BehaviorRuleMapper behaviorRuleMapper;
    private final ScoreConfigMapper scoreConfigMapper;
    private final PasswordEncoder passwordEncoder;
    private final JdbcTemplate jdbcTemplate;

    public DataInitializer(UserMapper userMapper,
                           VideoStreamMapper videoStreamMapper,
                           BehaviorRuleMapper behaviorRuleMapper,
                           ScoreConfigMapper scoreConfigMapper,
                           PasswordEncoder passwordEncoder,
                           JdbcTemplate jdbcTemplate) {
        this.userMapper = userMapper;
        this.videoStreamMapper = videoStreamMapper;
        this.behaviorRuleMapper = behaviorRuleMapper;
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
        log.info("补齐默认用户...");
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

        log.info("默认用户: admin/admin123, teacher/teacher123");
    }

    private void seedStreams() {
        log.info("补齐默认视频源...");
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

    private void seedRules() {
        log.info("补齐默认规则...");
        List<BehaviorRule> rules = Arrays.asList(
                createRule("phone_usage", "手机违规检测", true, 5, 0.75, 30),
                createRule("flame_detected", "明火检测", true, 3, 0.40, 20),
                createRule("fall_detected", "摔倒检测", false, 4, 0.78, 20),
                createRule("head_down", "长时间低头", true, 6, 0.70, 60),
                createRule("crowd_gathering", "异常人流聚集", true, 3, 0.70, 30),
                createRule("danger_zone", "区域入侵检测", true, 5, 0.75, 30),
                createRule("stranger_detected", "陌生人员检测", true, 0, 0.45, 10),
                createRule("leave_seat", "离座检测", false, 10, 0.60, 30),
                createRule("stream_offline", "视频流中断", true, 10, 1.0, 30),
                createRule("spoof_detected", "活体检测异常", true, 0, 0.70, 30),
                createRule("deepfake_detected", "换脸检测", false, 3, 0.70, 60),
                createRule("abnormal_sound", "异常声学事件", true, 0, 0.50, 15)
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

    private void seedScoreConfig() {
        log.info("补齐告警评分配置...");
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