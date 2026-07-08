package com.smartclass.monitor.mapper;

import com.smartclass.monitor.entity.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.time.LocalDateTime;

@Mapper
public interface UserMapper {

    @Select("SELECT * FROM user WHERE username = #{username} AND deleted_at IS NULL")
    User findByUsername(@Param("username") String username);

    @Select("SELECT * FROM user WHERE id = #{id} AND deleted_at IS NULL")
    User findById(@Param("id") Long id);

    @Update("UPDATE user SET last_login_at = #{time} WHERE id = #{id}")
    int updateLastLoginAt(@Param("id") Long id, @Param("time") LocalDateTime time);
}
