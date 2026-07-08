package com.smartclass.monitor.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class Student {
    private Long id;
    private String studentNo;
    private String name;
    private String className;
    private String gender;
    private String phone;
    private Boolean faceRegistered;
    private String status;
    private String remark;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private LocalDateTime deletedAt;
}
