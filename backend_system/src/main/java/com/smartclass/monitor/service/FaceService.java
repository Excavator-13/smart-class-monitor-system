package com.smartclass.monitor.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.smartclass.monitor.common.exception.BusinessException;
import com.smartclass.monitor.entity.FaceFeature;
import com.smartclass.monitor.entity.Student;
import com.smartclass.monitor.integration.AiClient;
import com.smartclass.monitor.mapper.FaceFeatureMapper;
import com.smartclass.monitor.mapper.StudentMapper;
import com.smartclass.monitor.vo.FaceFeatureFullVO;
import com.smartclass.monitor.vo.FaceFeatureVO;
import com.smartclass.monitor.vo.FaceRegisterResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class FaceService {

    private static final Logger log = LoggerFactory.getLogger(FaceService.class);
    private static final DateTimeFormatter DTF = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final ObjectMapper objectMapper = new ObjectMapper();

    private final StudentMapper studentMapper;
    private final FaceFeatureMapper faceFeatureMapper;
    private final AiClient aiClient;

    public FaceService(StudentMapper studentMapper, FaceFeatureMapper faceFeatureMapper, AiClient aiClient) {
        this.studentMapper = studentMapper;
        this.faceFeatureMapper = faceFeatureMapper;
        this.aiClient = aiClient;
    }

    public FaceRegisterResponse registerFace(Long studentId, String base64Image) {
        // 1. 校验学生存在
        Student student = studentMapper.findById(studentId);
        if (student == null) throw new BusinessException(404, "人员不存在");
        if ("disabled".equals(student.getStatus())) throw new BusinessException(400, "人员已禁用");

        // 2. 调 AI 提取特征
        AiClient.FaceExtractResult aiResult = aiClient.extractFeature(base64Image,
                String.valueOf(student.getStudentNo()));

        // 3. 校验 face_count == 1
        if (aiResult.faceCount == 0) throw new BusinessException(400, "未检测到人脸");
        if (aiResult.faceCount > 1) throw new BusinessException(400, "检测到多个人脸，请上传单人照片");

        // 4. 写入 face_feature
        FaceFeature feature = new FaceFeature();
        feature.setStudentId(studentId);
        feature.setFeatureDim(aiResult.featureDim);
        try {
            feature.setFeatureVector(objectMapper.writeValueAsString(aiResult.featureVector));
            feature.setQualityJson(objectMapper.writeValueAsString(Map.of(
                    "score", aiResult.qualityScore,
                    "brightness", aiResult.brightness != null ? aiResult.brightness : "normal",
                    "blur", aiResult.blur != null ? aiResult.blur : "low"
            )));
            feature.setBboxJson(objectMapper.writeValueAsString(aiResult.bbox));
        } catch (JsonProcessingException e) {
            throw new BusinessException(500, "特征数据序列化失败");
        }
        feature.setQualityScore(aiResult.qualityScore);
        feature.setVersion(1);
        feature.setEnabled(true);

        faceFeatureMapper.insert(feature);

        // 5. 更新 student.face_registered
        studentMapper.updateFaceRegistered(studentId, true);

        // 6. 通知 AI 刷新（失败不阻断）
        aiClient.reloadFeatures();

        // 7. 返回结果
        FaceRegisterResponse resp = new FaceRegisterResponse();
        resp.setFaceCount(aiResult.faceCount);
        resp.setFeatureDim(aiResult.featureDim);
        resp.setQualityScore(aiResult.qualityScore);
        resp.setBbox(aiResult.bbox);
        return resp;
    }

    public List<FaceFeatureVO> getFaceFeatures(Long studentId) {
        List<FaceFeature> features = faceFeatureMapper.findByStudentId(studentId);
        return features.stream().map(f -> {
            FaceFeatureVO vo = new FaceFeatureVO();
            vo.setId(f.getId());
            vo.setImagePath(f.getImagePath());
            vo.setQualityScore(f.getQualityScore());
            vo.setQualityJson(f.getQualityJson());
            vo.setBboxJson(f.getBboxJson());
            vo.setFeatureDim(f.getFeatureDim());
            vo.setVersion(f.getVersion());
            if (f.getCreatedAt() != null) vo.setCreatedAt(f.getCreatedAt().format(DTF));
            return vo;
        }).collect(Collectors.toList());
    }

    @SuppressWarnings("unchecked")
    public List<FaceFeatureFullVO> getAllFaceFeatures() {
        List<Map<String, Object>> rows = faceFeatureMapper.findAllEnabledWithStudent();
        List<FaceFeatureFullVO> result = new ArrayList<>();
        for (Map<String, Object> row : rows) {
            FaceFeatureFullVO vo = new FaceFeatureFullVO();
            vo.setStudentId((String) row.get("student_id"));
            vo.setStudentName((String) row.get("student_name"));
            vo.setClassName((String) row.get("class_name"));
            vo.setFeatureDim((Integer) row.get("feature_dim"));
            vo.setEnabled((Boolean) row.get("enabled"));

            // feature_vector 是 MySQL JSON 列，MyBatis 返回 String
            Object fv = row.get("feature_vector");
            try {
                if (fv instanceof String) {
                    vo.setFeatureVector(objectMapper.readValue((String) fv, List.class));
                } else if (fv instanceof List) {
                    vo.setFeatureVector((List<Double>) fv);
                }
            } catch (JsonProcessingException e) {
                log.warn("Failed to parse feature_vector: {}", e.getMessage());
            }
            result.add(vo);
        }
        return result;
    }
}
