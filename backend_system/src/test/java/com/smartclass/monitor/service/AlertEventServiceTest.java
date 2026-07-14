package com.smartclass.monitor.service;

import com.smartclass.monitor.dto.AlertIngestRequest;
import com.smartclass.monitor.entity.AlertEvent;
import com.smartclass.monitor.entity.ScoreConfig;
import com.smartclass.monitor.mapper.AlertEventMapper;
import com.smartclass.monitor.mapper.ScoreConfigMapper;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.*;

class AlertEventServiceTest {

    @Test
    void configuredEventLevelOverridesAiPayload() {
        AlertEventMapper alertMapper = mock(AlertEventMapper.class);
        ScoreConfigMapper configMapper = mock(ScoreConfigMapper.class);
        ScoreConfig config = new ScoreConfig();
        config.setAlertType("flame_detected");
        config.setLevel("high");
        when(configMapper.findByType("flame_detected")).thenReturn(config);

        AlertEventService service = new AlertEventService(alertMapper, configMapper);
        AlertIngestRequest request = request("flame_detected", "info");

        service.ingestAlert(request);

        ArgumentCaptor<AlertEvent> captor = ArgumentCaptor.forClass(AlertEvent.class);
        verify(alertMapper).insert(captor.capture());
        assertEquals("high", captor.getValue().getLevel());
    }

    @Test
    void unknownEventFallsBackToWarningForInvalidPayloadLevel() {
        AlertEventMapper alertMapper = mock(AlertEventMapper.class);
        ScoreConfigMapper configMapper = mock(ScoreConfigMapper.class);
        AlertEventService service = new AlertEventService(alertMapper, configMapper);

        service.ingestAlert(request("new_event", "critical"));

        ArgumentCaptor<AlertEvent> captor = ArgumentCaptor.forClass(AlertEvent.class);
        verify(alertMapper).insert(captor.capture());
        assertEquals("warning", captor.getValue().getLevel());
    }

    private AlertIngestRequest request(String type, String level) {
        AlertIngestRequest request = new AlertIngestRequest();
        request.setEventId("evt-test-1");
        request.setStreamId("classroom_01");
        request.setAlertType(type);
        request.setAlertName(type);
        request.setLevel(level);
        request.setOccurredAt("2026-07-14T10:00:00+08:00");
        return request;
    }
}
