package com.smartclass.monitor.config;

import com.smartclass.monitor.security.CurrentUserResolver;
import com.smartclass.monitor.security.InternalTokenInterceptor;
import com.smartclass.monitor.security.JwtAuthenticationInterceptor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.List;

@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    private final InternalTokenInterceptor internalTokenInterceptor;
    private final JwtAuthenticationInterceptor jwtInterceptor;
    private final CurrentUserResolver currentUserResolver;

    public WebMvcConfig(InternalTokenInterceptor internalTokenInterceptor,
                        JwtAuthenticationInterceptor jwtInterceptor,
                        CurrentUserResolver currentUserResolver) {
        this.internalTokenInterceptor = internalTokenInterceptor;
        this.jwtInterceptor = jwtInterceptor;
        this.currentUserResolver = currentUserResolver;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // 内部 Token 拦截器优先（只拦截 AI 路径，非 AI 路径直接放行）
        registry.addInterceptor(internalTokenInterceptor)
                .addPathPatterns("/**");
        // JWT 拦截器（已放行 AI 路径和非鉴权路径）
        registry.addInterceptor(jwtInterceptor)
                .addPathPatterns("/**");
    }

    @Override
    public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
        resolvers.add(currentUserResolver);
    }
}
