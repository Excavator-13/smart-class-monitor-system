package com.smartclass.monitor.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

/**
 * 安全相关 Bean 配置。初版仅提供 BCryptPasswordEncoder。
 * 不引入 Spring Security 框架，鉴权由 JwtAuthenticationInterceptor 完成。
 */
@Configuration
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
