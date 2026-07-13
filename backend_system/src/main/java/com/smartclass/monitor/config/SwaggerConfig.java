package com.smartclass.monitor.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * SpringDoc OpenAPI 配置。
 */
@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI smartClassMonitorOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("智慧教室实时行为分析与安全监测系统 API")
                        .description("SpringBoot 后端 RESTful 接口文档")
                        .version("v0.1.0")
                        .contact(new Contact()
                                .name("BJTU 小组")
                                .email("")
                        ))
                .addSecurityItem(new SecurityRequirement().addList("Bearer Authentication"))
                .components(new io.swagger.v3.oas.models.Components()
                        .addSecuritySchemes("Bearer Authentication",
                                new SecurityScheme()
                                        .type(SecurityScheme.Type.HTTP)
                                        .scheme("bearer")
                                        .bearerFormat("JWT")
                                        .description("请输入 JWT Token（不需要加 Bearer 前缀）")
                        ));
    }
}
