package com.smartclass.monitor;

import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class SmartClassMonitorApplication {

    @Value("${spring.datasource.url}")
    private String dbUrl;

    @PostConstruct
    public void showDb() {
        System.out.println("========== JDBC URL: " + dbUrl + " ==========");
    }

    public static void main(String[] args) {
        SpringApplication.run(SmartClassMonitorApplication.class, args);
    }
}
