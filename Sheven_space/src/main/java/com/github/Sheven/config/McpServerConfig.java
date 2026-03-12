package com.github.Sheven.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import okhttp3.OkHttpClient;
import java.util.concurrent.TimeUnit;

/**
 * MCP Server 配置
 */
@Configuration
public class McpServerConfig {

    @Bean
    public OkHttpClient mcpOkHttpClient() {
        return new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .build();
    }
}
