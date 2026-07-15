package com.smartclass.monitor.config;

import com.smartclass.monitor.security.CurrentUserResolver;
import com.smartclass.monitor.security.InternalTokenInterceptor;
import com.smartclass.monitor.security.JwtAuthenticationInterceptor;
import com.smartclass.monitor.security.RequireRoleInterceptor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.List;

@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    private final InternalTokenInterceptor internalTokenInterceptor;
    private final JwtAuthenticationInterceptor jwtInterceptor;
    private final RequireRoleInterceptor requireRoleInterceptor;
    private final CurrentUserResolver currentUserResolver;

    public WebMvcConfig(InternalTokenInterceptor internalTokenInterceptor,
                        JwtAuthenticationInterceptor jwtInterceptor,
                        RequireRoleInterceptor requireRoleInterceptor,
                        CurrentUserResolver currentUserResolver) {
        this.internalTokenInterceptor = internalTokenInterceptor;
        this.jwtInterceptor = jwtInterceptor;
        this.requireRoleInterceptor = requireRoleInterceptor;
        this.currentUserResolver = currentUserResolver;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(internalTokenInterceptor)
                .addPathPatterns("/**");
        registry.addInterceptor(jwtInterceptor)
                .addPathPatterns("/**");
        registry.addInterceptor(requireRoleInterceptor)
                .addPathPatterns("/**");
    }

    @Override
    public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
        resolvers.add(currentUserResolver);
    }
}