package com.smartclass.monitor.config;

import com.smartclass.monitor.mapper.*;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;

import static org.mockito.Mockito.*;

class TestDataInitializerTest {

    @Test
    void startupTruncatesAllAndSeedsTestData() {
        UserMapper users = mock(UserMapper.class);
        VideoStreamMapper streams = mock(VideoStreamMapper.class);
        StudentMapper students = mock(StudentMapper.class);
        BehaviorRuleMapper rules = mock(BehaviorRuleMapper.class);
        DangerZoneMapper zones = mock(DangerZoneMapper.class);
        AlertEventMapper alerts = mock(AlertEventMapper.class);
        FaceFeatureMapper faces = mock(FaceFeatureMapper.class);
        RecordingFileMapper recordings = mock(RecordingFileMapper.class);
        OperationLogMapper logs = mock(OperationLogMapper.class);
        ScoreConfigMapper scoreConfigs = mock(ScoreConfigMapper.class);
        PasswordEncoder encoder = mock(PasswordEncoder.class);
        JdbcTemplate jdbcTemplate = new JdbcTemplate() {
            @Override
            public <T> T queryForObject(String sql, Class<T> requiredType) {
                return requiredType.cast(1);
            }
        };

        TestDataInitializer initializer = new TestDataInitializer(
                users, streams, students, rules, zones, alerts, faces,
                recordings, logs, scoreConfigs, encoder, jdbcTemplate);

        initializer.run();

        verify(alerts).truncate();
        verify(faces).truncate();
        verify(recordings).truncate();
        verify(logs).truncate();
        verify(zones).truncate();
        verify(rules).truncate();
        verify(scoreConfigs).truncate();
        verify(students).truncate();
        verify(streams).truncate();
        verify(users).truncate();

        verify(students, atLeastOnce()).insert(any());
        verify(zones, atLeastOnce()).insert(any());
        verify(alerts, atLeastOnce()).insert(any());
    }
}