package com.smartclass.monitor;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class SmartClassMonitorApplication {

    public static void main(String[] args) {
        SpringApplication.run(SmartClassMonitorApplication.class, args);
    }
}
