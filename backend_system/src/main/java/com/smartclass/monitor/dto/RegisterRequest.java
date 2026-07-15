package com.smartclass.monitor.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

@Schema(description = "注册请求")
public class RegisterRequest {

    @NotBlank(message = "用户名不能为空")
    @Size(min = 2, max = 64, message = "用户名长度需在2-64之间")
    @Schema(description = "用户名", example = "newuser")
    private String username;

    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 128, message = "密码长度需在6-128之间")
    @Schema(description = "密码", example = "123456")
    private String password;

    @Size(max = 64, message = "昵称长度不能超过64")
    @Schema(description = "昵称（可选）", example = "新用户")
    private String nickname;

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getNickname() {
        return nickname;
    }

    public void setNickname(String nickname) {
        this.nickname = nickname;
    }
}