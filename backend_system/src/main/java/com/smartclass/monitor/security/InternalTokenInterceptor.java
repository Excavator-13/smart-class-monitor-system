package com.smartclass.monitor.security;

import com.smartclass.monitor.common.exception.BusinessException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.List;

/**
 * AI 内部接口鉴权拦截器。
 * 仅拦截 /alerts/ai 和 /students/face-features，使用 X-Internal-Token 校验。
 */
@Component
public class InternalTokenInterceptor implements HandlerInterceptor {

    private static final List<String> AI_PATHS = List.of(
            "/alerts/ai",
            "/students/face-features"
    );

    private final String internalToken;

    public InternalTokenInterceptor(@Value("${ai.internal-token}") String internalToken) {
        this.internalToken = internalToken;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) {
        String path = request.getRequestURI();

        // 只拦截 AI 内部路径
        if (!AI_PATHS.contains(path)) {
            return true;
        }

        String token = request.getHeader("X-Internal-Token");
        if (token == null || !token.equals(internalToken)) {
            throw new BusinessException(401, "内部接口鉴权失败");
        }

        return true;
    }
}
