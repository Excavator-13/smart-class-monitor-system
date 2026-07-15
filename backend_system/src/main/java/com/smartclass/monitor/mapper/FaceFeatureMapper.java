package com.smartclass.monitor.mapper;

import com.smartclass.monitor.entity.FaceFeature;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface FaceFeatureMapper {

    @Insert("INSERT INTO face_feature (student_id, feature_dim, feature_vector, image_path, " +
            "quality_score, quality_json, bbox_json, model_name, model_version, version, enabled) " +
            "VALUES (#{studentId}, #{featureDim}, #{featureVector}, #{imagePath}, " +
            "#{qualityScore}, #{qualityJson}, #{bboxJson}, #{modelName}, #{modelVersion}, #{version}, #{enabled})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(FaceFeature feature);

    @Select("SELECT id, student_id, feature_dim, image_path, quality_score, quality_json, " +
            "bbox_json, version, enabled, created_at FROM face_feature " +
            "WHERE student_id = #{studentId} AND deleted_at IS NULL ORDER BY created_at DESC")
    @Results({
            @Result(property = "featureVector", column = "feature_vector"),
            @Result(property = "studentId", column = "student_id"),
            @Result(property = "featureDim", column = "feature_dim"),
            @Result(property = "imagePath", column = "image_path"),
            @Result(property = "qualityScore", column = "quality_score"),
            @Result(property = "qualityJson", column = "quality_json"),
            @Result(property = "bboxJson", column = "bbox_json"),
            @Result(property = "modelName", column = "model_name"),
            @Result(property = "modelVersion", column = "model_version"),
            @Result(property = "createdAt", column = "created_at")
    })
    List<FaceFeature> findByStudentId(@Param("studentId") Long studentId);

    @Select("SELECT ff.feature_vector, ff.feature_dim, ff.enabled, " +
            "s.student_no AS student_id, s.name AS student_name, s.class_name " +
            "FROM face_feature ff JOIN student s ON ff.student_id = s.id " +
            "WHERE ff.enabled = 1 AND ff.deleted_at IS NULL AND s.deleted_at IS NULL")
    List<java.util.Map<String, Object>> findAllEnabledWithStudent();

    @Delete("TRUNCATE TABLE face_feature")
    void truncate();
}