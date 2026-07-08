package com.smartclass.monitor.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * SpringDoc OpenAPI 配置。
 * 不使用显式分组，所有端点通过 @Tag 注解自然组织。
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
                        ));
    }
}
