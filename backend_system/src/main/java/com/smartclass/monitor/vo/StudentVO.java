package com.smartclass.monitor.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "人员信息")
public class StudentVO {

    @Schema(description = "人员主键", example = "1")
    private Long id;

    @Schema(description = "学号", example = "2024001")
    private String studentNo;

    @Schema(description = "姓名", example = "张三")
    private String name;

    @Schema(description = "班级", example = "软件工程1班")
    private String className;

    @Schema(description = "性别")
    private String gender;

    @Schema(description = "联系方式")
    private String phone;

    @Schema(description = "是否已注册人脸", example = "false")
    private Boolean faceRegistered;

    @Schema(description = "状态", example = "enabled")
    private String status;

    @Schema(description = "备注")
    private String remark;

    @Schema(description = "创建时间", example = "2026-07-08 10:00:00")
    private String createdAt;

    public Long getId() { return id; }
    public void setId(Long v) { this.id = v; }
    public String getStudentNo() { return studentNo; }
    public void setStudentNo(String v) { this.studentNo = v; }
    public String getName() { return name; }
    public void setName(String v) { this.name = v; }
    public String getClassName() { return className; }
    public void setClassName(String v) { this.className = v; }
    public String getGender() { return gender; }
    public void setGender(String v) { this.gender = v; }
    public String getPhone() { return phone; }
    public void setPhone(String v) { this.phone = v; }
    public Boolean getFaceRegistered() { return faceRegistered; }
    public void setFaceRegistered(Boolean v) { this.faceRegistered = v; }
    public String getStatus() { return status; }
    public void setStatus(String v) { this.status = v; }
    public String getRemark() { return remark; }
    public void setRemark(String v) { this.remark = v; }
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String v) { this.createdAt = v; }
}
