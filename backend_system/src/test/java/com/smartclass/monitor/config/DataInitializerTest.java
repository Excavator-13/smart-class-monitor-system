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
        BehaviorRuleMapper rules = mock(BehaviorRuleMapper.class);
        ScoreConfigMapper scoreConfigs = mock(ScoreConfigMapper.class);
        PasswordEncoder encoder = mock(PasswordEncoder.class);
        JdbcTemplate jdbcTemplate = new JdbcTemplate() {
            @Override
            public <T> T queryForObject(String sql, Class<T> requiredType) {
                return requiredType.cast(1);
            }
        };

        DataInitializer initializer = new DataInitializer(
                users, streams, rules, scoreConfigs, encoder, jdbcTemplate);

        initializer.run();

        verify(users, never()).truncate();
        verify(streams, never()).truncate();
        verify(rules, never()).truncate();
        verify(scoreConfigs, never()).truncate();
    }
}