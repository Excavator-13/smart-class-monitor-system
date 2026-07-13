package com.smartclass.monitor.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public class UserStatusUpdateRequest {

    @NotBlank(message = "状态不能为空")
    @Pattern(regexp = "^(enabled|disabled)$", message = "状态必须为 enabled 或 disabled")
    private String status;

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }
}