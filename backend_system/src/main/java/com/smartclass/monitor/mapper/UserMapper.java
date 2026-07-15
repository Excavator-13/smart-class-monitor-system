package com.smartclass.monitor.mapper;

import com.smartclass.monitor.entity.User;
import org.apache.ibatis.annotations.*;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface UserMapper {

    @Select("SELECT * FROM user WHERE username = #{username} AND deleted_at IS NULL")
    User findByUsername(@Param("username") String username);

    @Select("SELECT * FROM user WHERE id = #{id} AND deleted_at IS NULL")
    User findById(@Param("id") Long id);

    @Insert("INSERT INTO user (username, password_hash, role, nickname, avatar_url, status) " +
            "VALUES (#{username}, #{passwordHash}, #{role}, #{nickname}, #{avatarUrl}, #{status})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(User user);

    @Update("UPDATE user SET last_login_at = #{time} WHERE id = #{id}")
    int updateLastLoginAt(@Param("id") Long id, @Param("time") LocalDateTime time);

    @Delete("TRUNCATE TABLE user")
    void truncate();

    @Select("SELECT COUNT(*) FROM user WHERE deleted_at IS NULL")
    long countActive();

    @Select("SELECT * FROM user WHERE deleted_at IS NULL ORDER BY id DESC LIMIT #{offset}, #{size}")
    List<User> findAll(@Param("offset") long offset, @Param("size") int size);

    @Select("SELECT * FROM user WHERE role = #{role} AND deleted_at IS NULL ORDER BY id DESC LIMIT #{offset}, #{size}")
    List<User> findByRole(@Param("role") String role, @Param("offset") long offset, @Param("size") int size);

    @Select("SELECT * FROM user WHERE status = #{status} AND deleted_at IS NULL ORDER BY id DESC LIMIT #{offset}, #{size}")
    List<User> findByStatus(@Param("status") String status, @Param("offset") long offset, @Param("size") int size);

    @Select("SELECT COUNT(*) FROM user WHERE role = #{role} AND deleted_at IS NULL")
    long countByRole(@Param("role") String role);

    @Select("SELECT COUNT(*) FROM user WHERE status = #{status} AND deleted_at IS NULL")
    long countByStatus(@Param("status") String status);

    @Update("UPDATE user SET role = #{role}, updated_at = NOW() WHERE id = #{id} AND deleted_at IS NULL")
    int updateRole(@Param("id") Long id, @Param("role") String role);

    @Update("UPDATE user SET status = #{status}, updated_at = NOW() WHERE id = #{id} AND deleted_at IS NULL")
    int updateStatus(@Param("id") Long id, @Param("status") String status);

    @Update("UPDATE user SET deleted_at = NOW() WHERE id = #{id} AND deleted_at IS NULL")
    int softDelete(@Param("id") Long id);

    @Update("UPDATE user SET nickname = #{nickname}, avatar_url = #{avatarUrl}, updated_at = #{updatedAt} WHERE id = #{id} AND deleted_at IS NULL")
    int update(User user);
}