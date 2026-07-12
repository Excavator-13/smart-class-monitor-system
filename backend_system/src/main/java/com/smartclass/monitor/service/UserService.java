package com.smartclass.monitor.service;

import com.smartclass.monitor.common.exception.BusinessException;
import com.smartclass.monitor.common.response.PageResult;
import com.smartclass.monitor.dto.UserRoleUpdateRequest;
import com.smartclass.monitor.dto.UserStatusUpdateRequest;
import com.smartclass.monitor.dto.UserUpdateRequest;
import com.smartclass.monitor.entity.User;
import com.smartclass.monitor.mapper.UserMapper;
import com.smartclass.monitor.vo.UserVO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class UserService {

    private static final Logger log = LoggerFactory.getLogger(UserService.class);

    private final UserMapper userMapper;

    public UserService(UserMapper userMapper) {
        this.userMapper = userMapper;
    }

    public PageResult<UserVO> listUsers(String role, String status, int page, int pageSize) {
        long offset = (long) (page - 1) * pageSize;
        List<User> users;
        long total;

        if (role != null && status != null) {
            users = userMapper.findByRole(role, offset, pageSize);
            total = userMapper.countByRole(role);
        } else if (role != null) {
            users = userMapper.findByRole(role, offset, pageSize);
            total = userMapper.countByRole(role);
        } else if (status != null) {
            users = userMapper.findByStatus(status, offset, pageSize);
            total = userMapper.countByStatus(status);
        } else {
            users = userMapper.findAll(offset, pageSize);
            total = userMapper.countActive();
        }

        List<UserVO> voList = users.stream().map(this::toVO).toList();
        return PageResult.of(voList, page, pageSize, total);
    }

    public UserVO getUser(Long id) {
        User user = userMapper.findById(id);
        if (user == null || user.getDeletedAt() != null) {
            throw new BusinessException(404, "用户不存在");
        }
        return toVO(user);
    }

    public UserVO updateUser(Long id, UserUpdateRequest request) {
        User user = userMapper.findById(id);
        if (user == null || user.getDeletedAt() != null) {
            throw new BusinessException(404, "用户不存在");
        }

        if (request.getNickname() != null) {
            user.setNickname(request.getNickname());
        }
        if (request.getAvatarUrl() != null) {
            user.setAvatarUrl(request.getAvatarUrl());
        }
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.update(user);

        return toVO(userMapper.findById(id));
    }

    public void updateRole(Long id, UserRoleUpdateRequest request, Long currentUserId) {
        if (id.equals(currentUserId)) {
            throw new BusinessException(400, "不能修改自己的角色");
        }
        User user = userMapper.findById(id);
        if (user == null || user.getDeletedAt() != null) {
            throw new BusinessException(404, "用户不存在");
        }
        int rows = userMapper.updateRole(id, request.getRole());
        if (rows == 0) {
            throw new BusinessException(404, "用户不存在");
        }
        log.info("User role updated: userId={}, newRole={}, operatorId={}", id, request.getRole(), currentUserId);
    }

    public void updateStatus(Long id, UserStatusUpdateRequest request, Long currentUserId) {
        if (id.equals(currentUserId)) {
            throw new BusinessException(400, "不能禁用自己");
        }
        User user = userMapper.findById(id);
        if (user == null || user.getDeletedAt() != null) {
            throw new BusinessException(404, "用户不存在");
        }
        int rows = userMapper.updateStatus(id, request.getStatus());
        if (rows == 0) {
            throw new BusinessException(404, "用户不存在");
        }
        log.info("User status updated: userId={}, newStatus={}, operatorId={}", id, request.getStatus(), currentUserId);
    }

    public void deleteUser(Long id, Long currentUserId) {
        if (id.equals(currentUserId)) {
            throw new BusinessException(400, "不能删除自己");
        }
        int rows = userMapper.softDelete(id);
        if (rows == 0) {
            throw new BusinessException(404, "用户不存在");
        }
        log.info("User soft deleted: userId={}, operatorId={}", id, currentUserId);
    }

    private UserVO toVO(User user) {
        UserVO vo = new UserVO();
        vo.setId(user.getId());
        vo.setUsername(user.getUsername());
        vo.setRole(user.getRole());
        vo.setNickname(user.getNickname());
        vo.setAvatarUrl(user.getAvatarUrl());
        vo.setStatus(user.getStatus());
        vo.setLastLoginAt(user.getLastLoginAt());
        vo.setCreatedAt(user.getCreatedAt());
        return vo;
    }
}