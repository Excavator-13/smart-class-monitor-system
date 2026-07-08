package com.smartclass.monitor.integration;

import com.smartclass.monitor.vo.StreamStatusVO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.w3c.dom.Document;
import org.w3c.dom.NodeList;

import javax.xml.parsers.DocumentBuilderFactory;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;

@Component
public class NginxClient {

    private static final Logger log = LoggerFactory.getLogger(NginxClient.class);

    private final RestTemplate restTemplate;
    private final String statUrl;

    public NginxClient(@Value("${nginx.stat-url}") String statUrl) {
        this.statUrl = statUrl;
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(3000);
        factory.setReadTimeout(5000);
        this.restTemplate = new RestTemplate(factory);
    }

    /** 通用健康检查：请求 /stat 是否可达 */
    public boolean checkHealth() {
        try {
            String xml = restTemplate.getForObject(statUrl, String.class);
            return xml != null && xml.contains("<rtmp>");
        } catch (Exception e) {
            log.warn("Nginx health check failed: {}", e.getMessage());
            return false;
        }
    }

    public StreamStatusVO getStreamStatus(String streamId) {
        try {
            String xml = restTemplate.getForObject(statUrl, String.class);
            if (xml == null) {
                return offline(streamId, "unknown");
            }
            return parseStat(xml, streamId);
        } catch (Exception e) {
            log.warn("Nginx /stat request failed for stream {}: {}", streamId, e.getMessage());
            return offline(streamId, "unknown");
        }
    }

    private StreamStatusVO parseStat(String xml, String streamId) {
        try {
            Document doc = DocumentBuilderFactory.newInstance()
                    .newDocumentBuilder()
                    .parse(new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8)));

            NodeList streams = doc.getElementsByTagName("stream");
            for (int i = 0; i < streams.getLength(); i++) {
                var stream = streams.item(i);
                var nameNode = ((org.w3c.dom.Element) stream).getElementsByTagName("name").item(0);
                if (nameNode != null && streamId.equals(nameNode.getTextContent().trim())) {
                    var publishNodes = ((org.w3c.dom.Element) stream).getElementsByTagName("publish");
                    if (publishNodes.getLength() > 0) {
                        var publish = (org.w3c.dom.Element) publishNodes.item(0);
                        String active = publish.getAttribute("active");
                        if ("true".equals(active)) {
                            return online(streamId, publish.getAttribute("time"));
                        }
                    }
                    return offline(streamId, "offline");
                }
            }
            return offline(streamId, "offline");
        } catch (Exception e) {
            log.warn("Failed to parse Nginx /stat XML for stream {}: {}", streamId, e.getMessage());
            return offline(streamId, "unknown");
        }
    }

    private StreamStatusVO online(String streamId, String uptime) {
        StreamStatusVO vo = new StreamStatusVO();
        vo.setStreamId(streamId);
        vo.setOnline(true);
        vo.setUptime(uptime);
        vo.setStatus("online");
        return vo;
    }

    private StreamStatusVO offline(String streamId, String status) {
        StreamStatusVO vo = new StreamStatusVO();
        vo.setStreamId(streamId);
        vo.setOnline(false);
        vo.setUptime(null);
        vo.setStatus(status);
        return vo;
    }
}
