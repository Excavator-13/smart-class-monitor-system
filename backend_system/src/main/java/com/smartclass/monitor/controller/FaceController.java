package com.smartclass.monitor.controller;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.dto.FaceRegisterRequest;
import com.smartclass.monitor.security.RequireRole;
import com.smartclass.monitor.service.FaceService;
import com.smartclass.monitor.vo.FaceFeatureVO;
import com.smartclass.monitor.vo.FaceRegisterResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@Tag(name = "frontend-api", description = "前端业务接口")
public class FaceController {

    private final FaceService faceService;

    public FaceController(FaceService faceService) {
        this.faceService = faceService;
    }

    @PostMapping("/students/{id}/face")
    @Operation(summary = "人脸注册", description = "上传 base64 人脸图片，调 AI 提取特征并入库")
    @RequireRole("admin")
    public ApiResponse<FaceRegisterResponse> registerFace(@PathVariable Long id,
                                                           @Valid @RequestBody FaceRegisterRequest request) {
        return ApiResponse.success(faceService.registerFace(id, request.getImage()));
    }

    @GetMapping("/students/{id}/face-features")
    @Operation(summary = "查看人脸特征记录", description = "返回特征元数据（图片路径、质量评分、创建时间等），不包含完整特征向量")
    public ApiResponse<List<FaceFeatureVO>> faceFeatures(@PathVariable Long id) {
        return ApiResponse.success(faceService.getFaceFeatures(id));
    }
}