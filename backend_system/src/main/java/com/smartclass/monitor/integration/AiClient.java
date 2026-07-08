package com.smartclass.monitor.integration;

import com.smartclass.monitor.common.exception.BusinessException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Component
public class AiClient {

    private static final Logger log = LoggerFactory.getLogger(AiClient.class);

    private final RestTemplate restTemplate;
    private final String baseUrl;

    public AiClient(@Value("${ai.base-url}") String baseUrl,
                    @Value("${ai.connect-timeout-ms:3000}") int connectTimeout,
                    @Value("${ai.read-timeout-ms:10000}") int readTimeout) {
        this.baseUrl = baseUrl;
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(connectTimeout);
        factory.setReadTimeout(readTimeout);
        this.restTemplate = new RestTemplate(factory);
    }

    @SuppressWarnings("unchecked")
    public FaceExtractResult extractFeature(String base64Image, String studentId) {
        String url = baseUrl + "/face/feature/extract";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("student_id", studentId);
        body.put("image", base64Image);
        body.put("image_type", "base64");

        try {
            Map<String, Object> resp = restTemplate.postForObject(url, new HttpEntity<>(body, headers), Map.class);
            if (resp == null) throw new BusinessException(500, "AI 服务返回为空");

            int code = ((Number) resp.getOrDefault("code", -1)).intValue();
            if (code != 0) {
                String msg = (String) resp.getOrDefault("message", "AI 处理失败");
                throw new BusinessException(400, msg);
            }

            Map<String, Object> data = (Map<String, Object>) resp.get("data");
            FaceExtractResult result = new FaceExtractResult();
            result.faceCount = ((Number) data.get("face_count")).intValue();
            result.featureDim = ((Number) data.get("feature_dim")).intValue();
            result.featureVector = (List<Double>) data.get("feature_vector");

            Map<String, Object> quality = (Map<String, Object>) data.get("quality");
            if (quality != null) {
                result.qualityScore = quality.get("score") != null ? ((Number) quality.get("score")).doubleValue() : 0;
                result.brightness = (String) quality.getOrDefault("brightness", "normal");
                result.blur = (String) quality.getOrDefault("blur", "low");
            }

            List<Integer> bboxList = (List<Integer>) data.get("bbox");
            if (bboxList != null) result.bbox = bboxList;

            return result;
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("AI /face/feature/extract failed: {}", e.getMessage());
            throw new BusinessException(500, "AI 服务不可用");
        }
    }

    /** 通用健康检查：GET /model/status */
    public boolean checkHealth() {
        try {
            String url = baseUrl + "/model/status";
            Map<String, Object> resp = restTemplate.getForObject(url, Map.class);
            return resp != null && ((Number) resp.getOrDefault("code", -1)).intValue() == 0;
        } catch (Exception e) {
            log.warn("AI health check failed: {}", e.getMessage());
            return false;
        }
    }

    public void reloadFeatures() {
        String url = baseUrl + "/face/features/reload";
        try {
            Map<String, Object> body = new LinkedHashMap<>();
            body.put("scope", "all");
            body.put("student_id", null);
            restTemplate.postForObject(url, body, Map.class);
            log.info("AI /face/features/reload success");
        } catch (Exception e) {
            log.warn("AI /face/features/reload failed (non-blocking): {}", e.getMessage());
        }
    }

    public static class FaceExtractResult {
        public int faceCount;
        public int featureDim;
        public List<Double> featureVector;
        public double qualityScore;
        public String brightness;
        public String blur;
        public List<Integer> bbox;
    }

    public void reloadConfig(String streamId, List<String> reloadItems) {
        String url = baseUrl + "/config/reload";
        try {
            Map<String, Object> body = new LinkedHashMap<>();
            body.put("stream_id", streamId);
            body.put("reload_items", reloadItems);
            restTemplate.postForObject(url, body, Map.class);
            log.info("AI /config/reload success for stream={}", streamId);
        } catch (Exception e) {
            log.warn("AI /config/reload failed (non-blocking) for stream={}: {}", streamId, e.getMessage());
        }
    }
}
