package com.smartclass.monitor.service;

import com.smartclass.monitor.common.exception.BusinessException;
import com.smartclass.monitor.common.response.PageResult;
import com.smartclass.monitor.dto.StudentCreateRequest;
import com.smartclass.monitor.dto.StudentUpdateRequest;
import com.smartclass.monitor.entity.Student;
import com.smartclass.monitor.mapper.StudentMapper;
import com.smartclass.monitor.vo.StudentVO;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class StudentService {

    private static final DateTimeFormatter DTF = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final StudentMapper mapper;

    public StudentService(StudentMapper mapper) {
        this.mapper = mapper;
    }

    public PageResult<StudentVO> listStudents(String className, String keyword,
                                               Boolean faceRegistered, int page, int pageSize) {
        List<Student> all = mapper.findAll(className, keyword, faceRegistered);
        int total = all.size();
        int from = Math.min((page - 1) * pageSize, total);
        int to = Math.min(from + pageSize, total);
        List<StudentVO> records = all.subList(from, to).stream().map(this::toVO).collect(Collectors.toList());
        return PageResult.of(records, page, pageSize, total);
    }

    public StudentVO createStudent(StudentCreateRequest req) {
        Student entity = new Student();
        entity.setStudentNo(req.getStudentNo());
        entity.setName(req.getName());
        entity.setClassName(req.getClassName());
        entity.setFaceRegistered(false);
        entity.setStatus("enabled");

        try {
            mapper.insert(entity);
        } catch (DuplicateKeyException e) {
            throw new BusinessException(409, "student_no 已存在");
        }
        return toVO(entity);
    }

    public StudentVO getStudentById(Long id) {
        Student entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "人员不存在");
        return toVO(entity);
    }

    public void updateStudent(Long id, StudentUpdateRequest req) {
        Student entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "人员不存在");

        if (req.getName() != null) entity.setName(req.getName());
        if (req.getClassName() != null) entity.setClassName(req.getClassName());
        if (req.getStatus() != null) entity.setStatus(req.getStatus());
        if (req.getRemark() != null) entity.setRemark(req.getRemark());
        mapper.update(entity);
    }

    public void deleteStudent(Long id) {
        Student entity = mapper.findById(id);
        if (entity == null) throw new BusinessException(404, "人员不存在");
        mapper.softDelete(id);
    }

    private StudentVO toVO(Student e) {
        StudentVO vo = new StudentVO();
        vo.setId(e.getId());
        vo.setStudentNo(e.getStudentNo());
        vo.setName(e.getName());
        vo.setClassName(e.getClassName());
        vo.setGender(e.getGender());
        vo.setPhone(e.getPhone());
        vo.setFaceRegistered(e.getFaceRegistered());
        vo.setStatus(e.getStatus());
        vo.setRemark(e.getRemark());
        if (e.getCreatedAt() != null) vo.setCreatedAt(e.getCreatedAt().format(DTF));
        return vo;
    }
}
