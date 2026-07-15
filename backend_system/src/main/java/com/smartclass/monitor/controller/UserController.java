package com.smartclass.monitor.controller;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.common.response.PageResult;
import com.smartclass.monitor.dto.UserRoleUpdateRequest;
import com.smartclass.monitor.dto.UserStatusUpdateRequest;
import com.smartclass.monitor.dto.UserUpdateRequest;
import com.smartclass.monitor.security.CurrentUser;
import com.smartclass.monitor.security.RequireRole;
import com.smartclass.monitor.service.UserService;
import com.smartclass.monitor.vo.UserVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/users")
@Tag(name = "system-api", description = "用户管理接口")
@RequireRole("admin")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping
    @Operation(summary = "查询用户列表", description = "分页查询用户，支持按角色和状态筛选")
    public ApiResponse<PageResult<UserVO>> list(
            @RequestParam(required = false) String role,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int pageSize) {
        return ApiResponse.success(userService.listUsers(role, status, page, pageSize));
    }

    @GetMapping("/{id}")
    @Operation(summary = "用户详情", description = "根据主键 id 查询用户信息")
    public ApiResponse<UserVO> detail(@PathVariable Long id) {
        return ApiResponse.success(userService.getUser(id));
    }

    @PutMapping("/{id}")
    @Operation(summary = "编辑用户", description = "更新用户昵称、头像")
    public ApiResponse<UserVO> update(@PathVariable Long id, @RequestBody UserUpdateRequest request) {
        return ApiResponse.success(userService.updateUser(id, request));
    }

    @PutMapping("/{id}/role")
    @Operation(summary = "变更用户角色", description = "修改用户角色（admin/teacher），不能修改自己的角色")
    public ApiResponse<Void> updateRole(@PathVariable Long id,
                                        @Valid @RequestBody UserRoleUpdateRequest request,
                                        @CurrentUser Long currentUserId) {
        userService.updateRole(id, request, currentUserId);
        return ApiResponse.success();
    }

    @PutMapping("/{id}/status")
    @Operation(summary = "变更用户状态", description = "启用/禁用用户，不能禁用自己")
    public ApiResponse<Void> updateStatus(@PathVariable Long id,
                                          @Valid @RequestBody UserStatusUpdateRequest request,
                                          @CurrentUser Long currentUserId) {
        userService.updateStatus(id, request, currentUserId);
        return ApiResponse.success();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除用户", description = "软删除用户，不能删除自己")
    public ApiResponse<Void> delete(@PathVariable Long id,
                                    @CurrentUser Long currentUserId) {
        userService.deleteUser(id, currentUserId);
        return ApiResponse.success();
    }
}