package com.github.Sheven.shuiqi;

import io.github.cdimascio.dotenv.Dotenv;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * ShuiQi 应用主启动类
 * 字段映射 Agent 服务 - 自动匹配中文字段到英文字段，调用 MCP 服务获取字段信息
 */
@SpringBootApplication
public class ShuiQiApplication {

    private static final Logger log = LoggerFactory.getLogger(ShuiQiApplication.class);

    public static void main(String[] args) {
        // 加载 .env 文件（在项目根目录查找）
        Dotenv dotenv = Dotenv.load();

        // 将 .env 中的变量设置到系统环境变量中
        dotenv.entries().forEach(entry -> {
            System.setProperty(entry.getKey(), entry.getValue());
            log.info("加载环境变量：{} = {}", entry.getKey(), entry.getValue());
        });

        SpringApplication.run(ShuiQiApplication.class, args);
        log.info("========================================");
        log.info("    ShuiQi 应用启动成功！");
        log.info("    字段映射 Agent 服务已就绪");
        log.info("========================================");
    }
}
