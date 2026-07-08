package com.smartclass.monitor.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;

@Schema(description = "新增人员请求")
public class StudentCreateRequest {

    @NotBlank(message = "学号不能为空")
    @Schema(description = "学号或人员编号", example = "2024001")
    private String studentNo;

    @NotBlank(message = "姓名不能为空")
    @Schema(description = "姓名", example = "张三")
    private String name;

    @Schema(description = "班级或分组", example = "软件工程1班")
    private String className;

    public String getStudentNo() { return studentNo; }
    public void setStudentNo(String v) { this.studentNo = v; }
    public String getName() { return name; }
    public void setName(String v) { this.name = v; }
    public String getClassName() { return className; }
    public void setClassName(String v) { this.className = v; }
}
