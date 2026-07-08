package com.smartclass.monitor.security;

import com.smartclass.monitor.common.exception.BusinessException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.List;

@Component
public class JwtAuthenticationInterceptor implements HandlerInterceptor {

    private static final Logger log = LoggerFactory.getLogger(JwtAuthenticationInterceptor.class);

    /** 放行路径白名单 */
    private static final List<String> EXCLUDE_PATHS = List.of(
            "/auth/login",
            "/system/health",
            "/alerts/ai",               // 由 InternalTokenInterceptor 保护
            "/students/face-features"   // 由 InternalTokenInterceptor 保护
    );

    /** 放行前缀 */
    private static final List<String> EXCLUDE_PREFIXES = List.of(
            "/swagger-ui",
            "/v3/api-docs"
    );

    private final JwtTokenProvider jwtTokenProvider;

    public JwtAuthenticationInterceptor(JwtTokenProvider jwtTokenProvider) {
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) {
        String path = request.getRequestURI();

        // 白名单放行
        if (EXCLUDE_PATHS.contains(path)) {
            return true;
        }
        for (String prefix : EXCLUDE_PREFIXES) {
            if (path.startsWith(prefix)) {
                return true;
            }
        }

        // 提取 Token
        String header = request.getHeader("Authorization");
        if (header == null || !header.startsWith("Bearer ")) {
            throw new BusinessException(401, "未登录或 Token 缺失");
        }
        String token = header.substring(7);

        // 校验
        if (!jwtTokenProvider.validate(token)) {
            throw new BusinessException(401, "Token 无效或已过期");
        }

        // 解析用户信息，放入 Request attribute
        Long userId = jwtTokenProvider.parseUserId(token);
        String username = jwtTokenProvider.parseUsername(token);
        String role = jwtTokenProvider.parseRole(token);

        request.setAttribute("currentUserId", userId);
        request.setAttribute("currentUsername", username);
        request.setAttribute("currentRole", role);

        return true;
    }
}
