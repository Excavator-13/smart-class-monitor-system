package com.smartclass.monitor.controller;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.dto.LoginRequest;
import com.smartclass.monitor.security.CurrentUser;
import com.smartclass.monitor.service.AuthService;
import com.smartclass.monitor.vo.LoginResponse;
import com.smartclass.monitor.vo.UserInfoVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Tag(name = "frontend-api", description = "前端业务接口")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/auth/login")
    @Operation(summary = "用户登录", description = "使用用户名和密码登录，返回 JWT Token 和用户信息")
    public ApiResponse<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        LoginResponse result = authService.login(request.getUsername(), request.getPassword());
        return ApiResponse.success(result);
    }

    @GetMapping("/auth/info")
    @Operation(summary = "获取当前用户信息", description = "根据请求头中的 JWT Token 返回当前登录用户信息")
    public ApiResponse<UserInfoVO> info(@CurrentUser Long userId) {
        UserInfoVO result = authService.getCurrentUser(userId);
        return ApiResponse.success(result);
    }

    @PostMapping("/auth/logout")
    @Operation(summary = "退出登录", description = "初版空实现，前端直接清除 Token 即可")
    public ApiResponse<Void> logout(@CurrentUser Long userId) {
        return ApiResponse.success();
    }
}
