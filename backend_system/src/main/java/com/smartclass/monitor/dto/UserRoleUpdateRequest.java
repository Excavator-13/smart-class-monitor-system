package com.smartclass.monitor.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public class UserRoleUpdateRequest {

    @NotBlank(message = "角色不能为空")
    @Pattern(regexp = "^(admin|teacher)$", message = "角色必须为 admin 或 teacher")
    private String role;

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }
}