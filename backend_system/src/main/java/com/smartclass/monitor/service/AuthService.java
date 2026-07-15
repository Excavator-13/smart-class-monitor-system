package com.smartclass.monitor.service;

import com.smartclass.monitor.common.exception.BusinessException;
import com.smartclass.monitor.entity.User;
import com.smartclass.monitor.mapper.UserMapper;
import com.smartclass.monitor.security.JwtTokenProvider;
import com.smartclass.monitor.vo.LoginResponse;
import com.smartclass.monitor.vo.UserInfoVO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class AuthService {

    private static final Logger log = LoggerFactory.getLogger(AuthService.class);

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;

    public AuthService(UserMapper userMapper,
                       PasswordEncoder passwordEncoder,
                       JwtTokenProvider jwtTokenProvider) {
        this.userMapper = userMapper;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenProvider = jwtTokenProvider;
    }

    public LoginResponse login(String username, String password) {
        User user = userMapper.findByUsername(username);
        if (user == null) {
            throw new BusinessException(400, "用户名或密码错误");
        }

        if (!passwordEncoder.matches(password, user.getPasswordHash())) {
            throw new BusinessException(400, "用户名或密码错误");
        }

        if ("disabled".equals(user.getStatus())) {
            throw new BusinessException(403, "账户已禁用");
        }

        // 更新最后登录时间
        userMapper.updateLastLoginAt(user.getId(), LocalDateTime.now());

        String token = jwtTokenProvider.generate(user.getId(), user.getUsername(), user.getRole());

        LoginResponse resp = new LoginResponse();
        resp.setToken(token);
        resp.setUserId(user.getId());
        resp.setUsername(user.getUsername());
        resp.setRole(user.getRole());
        resp.setNickname(user.getNickname());
        resp.setAvatarUrl(user.getAvatarUrl());
        return resp;
    }

    public LoginResponse register(String username, String password, String nickname) {
        User existing = userMapper.findByUsername(username);
        if (existing != null) {
            throw new BusinessException(409, "用户名已存在");
        }

        User user = new User();
        user.setUsername(username);
        user.setPasswordHash(passwordEncoder.encode(password));
        user.setRole(userMapper.countActive() == 0 ? "admin" : "teacher");
        user.setNickname(nickname);
        user.setStatus("enabled");

        userMapper.insert(user);

        String token = jwtTokenProvider.generate(user.getId(), user.getUsername(), user.getRole());

        LoginResponse resp = new LoginResponse();
        resp.setToken(token);
        resp.setUserId(user.getId());
        resp.setUsername(user.getUsername());
        resp.setRole(user.getRole());
        resp.setNickname(user.getNickname());
        resp.setAvatarUrl(user.getAvatarUrl());
        return resp;
    }

    public UserInfoVO getCurrentUser(Long userId) {
        User user = userMapper.findById(userId);
        if (user == null) {
            throw new BusinessException(404, "用户不存在");
        }

        UserInfoVO vo = new UserInfoVO();
        vo.setUserId(user.getId());
        vo.setUsername(user.getUsername());
        vo.setRole(user.getRole());
        vo.setNickname(user.getNickname());
        vo.setAvatarUrl(user.getAvatarUrl());
        return vo;
    }
}