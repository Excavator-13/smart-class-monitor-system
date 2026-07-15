package com.smartclass.monitor.controller;

import com.smartclass.monitor.common.response.ApiResponse;
import com.smartclass.monitor.common.response.PageResult;
import com.smartclass.monitor.dto.StudentCreateRequest;
import com.smartclass.monitor.dto.StudentUpdateRequest;
import com.smartclass.monitor.security.RequireRole;
import com.smartclass.monitor.service.StudentService;
import com.smartclass.monitor.vo.StudentVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@Tag(name = "frontend-api", description = "前端业务接口")
public class StudentController {

    private final StudentService studentService;

    public StudentController(StudentService studentService) {
        this.studentService = studentService;
    }

    @GetMapping("/students")
    @Operation(summary = "查询人员列表", description = "按班级、关键词、人脸注册状态分页查询人员")
    public ApiResponse<PageResult<StudentVO>> list(
            @RequestParam(required = false) String className,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) Boolean faceRegistered,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int pageSize) {
        return ApiResponse.success(studentService.listStudents(className, keyword, faceRegistered, page, pageSize));
    }

    @PostMapping("/students")
    @Operation(summary = "新增人员", description = "创建人员基础信息，student_no 必须唯一")
    @RequireRole("admin")
    public ApiResponse<StudentVO> create(@Valid @RequestBody StudentCreateRequest request) {
        return ApiResponse.success(studentService.createStudent(request));
    }

    @GetMapping("/students/{id}")
    @Operation(summary = "人员详情", description = "根据主键 id 查询人员详细信息")
    public ApiResponse<StudentVO> detail(@PathVariable Long id) {
        return ApiResponse.success(studentService.getStudentById(id));
    }

    @PutMapping("/students/{id}")
    @Operation(summary = "编辑人员", description = "更新人员姓名、班级、状态、备注")
    @RequireRole("admin")
    public ApiResponse<Void> update(@PathVariable Long id, @RequestBody StudentUpdateRequest request) {
        studentService.updateStudent(id, request);
        return ApiResponse.success();
    }

    @DeleteMapping("/students/{id}")
    @Operation(summary = "删除人员", description = "软删除人员，保留历史告警关联")
    @RequireRole("admin")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        studentService.deleteStudent(id);
        return ApiResponse.success();
    }
}