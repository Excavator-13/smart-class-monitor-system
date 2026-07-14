package com.smartclass.monitor.config;

import com.smartclass.monitor.mapper.*;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;

import static org.mockito.Mockito.*;

class DataInitializerTest {

    @Test
    void startupDoesNotClearOrSeedBusinessEventData() {
        UserMapper users = mock(UserMapper.class);
        VideoStreamMapper streams = mock(VideoStreamMapper.class);
        StudentMapper students = mock(StudentMapper.class);
        BehaviorRuleMapper rules = mock(BehaviorRuleMapper.class);
        DangerZoneMapper zones = mock(DangerZoneMapper.class);
        AlertEventMapper alerts = mock(AlertEventMapper.class);
        FaceFeatureMapper faces = mock(FaceFeatureMapper.class);
        RecordingFileMapper recordings = mock(RecordingFileMapper.class);
        OperationLogMapper logs = mock(OperationLogMapper.class);
        ScoreConfigMapper eventConfigs = mock(ScoreConfigMapper.class);
        PasswordEncoder encoder = mock(PasswordEncoder.class);
        JdbcTemplate jdbcTemplate = new JdbcTemplate() {
            @Override
            public <T> T queryForObject(String sql, Class<T> requiredType) {
                return requiredType.cast(1);
            }
        };

        DataInitializer initializer = new DataInitializer(
                users, streams, students, rules, zones, alerts, faces,
                recordings, logs, eventConfigs, encoder, jdbcTemplate);

        initializer.run();

        verify(users, never()).truncate();
        verify(streams, never()).truncate();
        verify(students, never()).truncate();
        verify(rules, never()).truncate();
        verify(zones, never()).truncate();
        verify(alerts, never()).truncate();
        verify(faces, never()).truncate();
        verify(recordings, never()).truncate();
        verify(logs, never()).truncate();
        verify(eventConfigs, never()).truncate();
        verifyNoInteractions(students, zones, alerts, faces, recordings, logs);
    }
}
