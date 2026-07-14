package com.smartclass.monitor.integration;

import com.smartclass.monitor.vo.StreamStatusVO;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class NginxClientTest {

    private final NginxClient client = new NginxClient("http://localhost/stat");

    @Test
    void detectsStandardPublishingClientAsOnline() {
        String xml = """
                <rtmp><server><application><live><stream>
                  <name>classroom_01</name><time>12345</time>
                  <clients><client><id>1</id><publishing/></client></clients>
                </stream></live></application></server></rtmp>
                """;

        StreamStatusVO status = client.parseStat(xml, "classroom_01");

        assertTrue(status.isOnline());
        assertEquals("online", status.getStatus());
        assertEquals("12345", status.getUptime());
    }

    @Test
    void streamWithoutPublisherIsOffline() {
        String xml = """
                <rtmp><server><application><live><stream>
                  <name>classroom_01</name><time>12345</time>
                  <clients><client><id>2</id></client></clients>
                </stream></live></application></server></rtmp>
                """;

        StreamStatusVO status = client.parseStat(xml, "classroom_01");

        assertFalse(status.isOnline());
        assertEquals("offline", status.getStatus());
    }

    @Test
    void malformedXmlReturnsUnknown() {
        StreamStatusVO status = client.parseStat("<rtmp>", "classroom_01");

        assertFalse(status.isOnline());
        assertEquals("unknown", status.getStatus());
    }
}
