package com.smartclass.monitor.security;

import com.smartclass.monitor.common.exception.BusinessException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.Arrays;
import java.util.Set;

@Component
public class RequireRoleInterceptor implements HandlerInterceptor {

    private static final Logger log = LoggerFactory.getLogger(RequireRoleInterceptor.class);

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) {
        if (!(handler instanceof HandlerMethod handlerMethod)) {
            return true;
        }

        RequireRole methodAnnotation = handlerMethod.getMethodAnnotation(RequireRole.class);
        RequireRole classAnnotation = handlerMethod.getBeanType().getAnnotation(RequireRole.class);

        RequireRole effective = methodAnnotation != null ? methodAnnotation : classAnnotation;

        if (effective == null) {
            return true;
        }

        String currentRole = (String) request.getAttribute("currentRole");
        if (currentRole == null) {
            throw new BusinessException(403, "权限不足");
        }

        Set<String> allowedRoles = Set.of(effective.value());
        if (!allowedRoles.contains(currentRole)) {
            log.debug("Role check failed: currentRole={}, required={}", currentRole, Arrays.toString(effective.value()));
            throw new BusinessException(403, "权限不足");
        }

        return true;
    }
}