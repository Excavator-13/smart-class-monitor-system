package com.smartclass.monitor.security;

import com.smartclass.monitor.common.exception.BusinessException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.List;

@Component
public class JwtAuthenticationInterceptor implements HandlerInterceptor {

    private static final Logger log = LoggerFactory.getLogger(JwtAuthenticationInterceptor.class);

    private static final List<String> EXCLUDE_PATHS = List.of(
            "/auth/login",
            "/auth/register",
            "/system/health"
    );

    private static final List<String> EXCLUDE_PREFIXES = List.of(
            "/swagger-ui",
            "/v3/api-docs"
    );

    private final JwtTokenProvider jwtTokenProvider;
    private final String internalToken;

    public JwtAuthenticationInterceptor(JwtTokenProvider jwtTokenProvider,
                                        @Value("${ai.internal-token}") String internalToken) {
        this.jwtTokenProvider = jwtTokenProvider;
        this.internalToken = internalToken;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) {
        String path = request.getRequestURI();

        if (EXCLUDE_PATHS.contains(path)) {
            return true;
        }
        for (String prefix : EXCLUDE_PREFIXES) {
            if (path.startsWith(prefix)) {
                return true;
            }
        }

        String internalHeader = request.getHeader("X-Internal-Token");
        if (internalHeader != null && internalHeader.equals(internalToken)) {
            return true;
        }

        String header = request.getHeader("Authorization");
        if (header == null || !header.startsWith("Bearer ")) {
            throw new BusinessException(401, "未登录或 Token 缺失");
        }
        String token = header.substring(7);

        if (!jwtTokenProvider.validate(token)) {
            throw new BusinessException(401, "Token 无效或已过期");
        }

        Long userId = jwtTokenProvider.parseUserId(token);
        String username = jwtTokenProvider.parseUsername(token);
        String role = jwtTokenProvider.parseRole(token);

        request.setAttribute("currentUserId", userId);
        request.setAttribute("currentUsername", username);
        request.setAttribute("currentRole", role);

        return true;
    }
}