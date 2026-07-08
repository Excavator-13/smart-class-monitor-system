package com.smartclass.monitor.controller.ai;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.service.FaceService;
import com.smartclass.monitor.vo.FaceFeatureFullVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * AI 内部接口 —— 禁止前端访问。
 * 放在 controller.ai 包中，Swagger 分组为 ai-internal-api。
 */
@RestController
@Tag(name = "ai-internal-api", description = "AI 服务调用 SpringBoot 的内部接口")
public class AiFaceFeatureController {

    private final FaceService faceService;

    public AiFaceFeatureController(FaceService faceService) {
        this.faceService = faceService;
    }

    @GetMapping("/students/face-features")
    @Operation(summary = "获取全量人脸特征", description = "AI 内部调用，返回包含 feature_vector 的完整特征数据。禁止前端访问")
    public ApiResponse<List<FaceFeatureFullVO>> allFaceFeatures() {
        return ApiResponse.success(faceService.getAllFaceFeatures());
    }
}
