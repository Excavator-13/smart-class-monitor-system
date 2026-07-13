package com.smartclass.monitor.mapper;

import com.smartclass.monitor.entity.User;
import org.apache.ibatis.annotations.*;

import java.time.LocalDateTime;

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
}