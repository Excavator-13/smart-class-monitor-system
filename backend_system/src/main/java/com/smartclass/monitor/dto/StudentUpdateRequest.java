package com.smartclass.monitor.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "编辑人员请求")
public class StudentUpdateRequest {

    @Schema(description = "姓名", example = "张三")
    private String name;

    @Schema(description = "班级", example = "软件工程1班")
    private String className;

    @Schema(description = "状态", example = "enabled")
    private String status;

    @Schema(description = "备注")
    private String remark;

    public String getName() { return name; }
    public void setName(String v) { this.name = v; }
    public String getClassName() { return className; }
    public void setClassName(String v) { this.className = v; }
    public String getStatus() { return status; }
    public void setStatus(String v) { this.status = v; }
    public String getRemark() { return remark; }
    public void setRemark(String v) { this.remark = v; }
}
