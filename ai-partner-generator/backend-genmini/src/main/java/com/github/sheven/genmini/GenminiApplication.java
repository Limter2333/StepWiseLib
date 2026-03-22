package com.github.sheven.genmini;

import io.github.cdimascio.dotenv.Dotenv;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Genmini AI 后端应用
 * 提供与本地 Genmini 模型交互的接口
 */
@Slf4j
@SpringBootApplication
public class GenminiApplication {

    public static void main(String[] args) {
        // 加载 .env 文件（在项目根目录查找）
        Dotenv dotenv = Dotenv.load();

        // 将 .env 中的变量设置到系统环境变量中
        dotenv.entries().forEach(entry -> {
            System.setProperty(entry.getKey(), entry.getValue());
            log.info("加载环境变量：{} = {}", entry.getKey(), entry.getValue());
        });

        SpringApplication.run(GenminiApplication.class, args);
    }
}
