package com.smartclass.monitor.config;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import org.springframework.boot.autoconfigure.jackson.Jackson2ObjectMapperBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.TimeZone;

/**
 * Jackson 序列化配置：snake_case 命名、Asia/Shanghai 时区、yyyy-MM-dd HH:mm:ss 日期格式。
 */
@Configuration
public class JacksonConfig {

    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jacksonCustomizer() {
        return builder -> {
            builder.propertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
            builder.timeZone(TimeZone.getTimeZone("Asia/Shanghai"));
            builder.simpleDateFormat("yyyy-MM-dd HH:mm:ss");
        };
    }
}
