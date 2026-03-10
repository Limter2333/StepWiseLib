package com.github.Sheven;

import io.github.cdimascio.dotenv.Dotenv;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class StepWiseLibApplication {

    private static final Logger log = LoggerFactory.getLogger(StepWiseLibApplication.class);

    public static void main(String[] args) {
        // 加载 .env 文件（在项目根目录查找）
        Dotenv dotenv = Dotenv.load();

        // 将 .env 中的变量设置到系统环境变量中
        dotenv.entries().forEach(entry -> {
            System.setProperty(entry.getKey(), entry.getValue());
            log.info("加载环境变量：{} = {}", entry.getKey(),
                    entry.getValue());
        });

        SpringApplication.run(StepWiseLibApplication.class, args);

    }
}
