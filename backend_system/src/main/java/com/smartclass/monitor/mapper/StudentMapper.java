package com.smartclass.monitor.mapper;

import com.smartclass.monitor.entity.Student;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface StudentMapper {

    @Select("<script>" +
            "SELECT * FROM student WHERE deleted_at IS NULL " +
            "<if test='className != null and className != \"\"'>AND class_name = #{className}</if>" +
            "<if test='keyword != null and keyword != \"\"'>AND (name LIKE CONCAT('%',#{keyword},'%') OR student_no LIKE CONCAT('%',#{keyword},'%'))</if>" +
            "<if test='faceRegistered != null'>AND face_registered = #{faceRegistered}</if>" +
            "ORDER BY created_at DESC" +
            "</script>")
    List<Student> findAll(@Param("className") String className,
                          @Param("keyword") String keyword,
                          @Param("faceRegistered") Boolean faceRegistered);

    @Select("SELECT * FROM student WHERE id = #{id} AND deleted_at IS NULL")
    Student findById(@Param("id") Long id);

    @Insert("INSERT INTO student (student_no, name, class_name, gender, phone, face_registered, status, remark) " +
            "VALUES (#{studentNo}, #{name}, #{className}, #{gender}, #{phone}, #{faceRegistered}, #{status}, #{remark})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Student student);

    @Update("UPDATE student SET name=#{name}, class_name=#{className}, gender=#{gender}, " +
            "phone=#{phone}, status=#{status}, remark=#{remark} WHERE id=#{id}")
    int update(Student student);

    @Update("UPDATE student SET deleted_at=NOW() WHERE id=#{id}")
    int softDelete(@Param("id") Long id);

    @Update("UPDATE student SET face_registered = #{registered} WHERE id = #{id}")
    int updateFaceRegistered(@Param("id") Long id, @Param("registered") boolean registered);

    @Delete("TRUNCATE TABLE student")
    void truncate();
}