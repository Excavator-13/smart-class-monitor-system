package com.smartclass.monitor.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;

@Schema(description = "人脸注册请求")
public class FaceRegisterRequest {

    @NotBlank(message = "图片不能为空")
    @Schema(description = "base64 编码的人脸图片", example = "/9j/4AAQSkZJRg...")
    private String image;

    public String getImage() { return image; }
    public void setImage(String v) { this.image = v; }
}
