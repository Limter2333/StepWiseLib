package com.github.sheven.genmini.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * Genmini AI 配置属性
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "genmini")
public class GenminiProperties {

    /**
     * API 基础地址（默认本地 3000 端口）
     */
    private String baseUrl = "http://localhost:3000";

    /**
     * 聊天接口路径
     */
    private String chatEndpoint = "/api/chat";

    /**
     * 图片生成接口路径
     */
    private String imageEndpoint = "";

    /**
     * 默认聊天模型
     */
    private String defaultChatModel = "genmini-chat-v1";

    /**
     * 默认图片生成模型
     */
    private String defaultImageModel = "genmini-image-v1";

    /**
     * API Key（可选，如果 Genmini 服务需要认证）
     */
    private String apiKey;

    /**
     * API Key 请求头名称
     */
    private String apiKeyHeader = "Authorization";

    /**
     * API Key 前缀（如 Bearer）
     */
    private String apiKeyPrefix = "Bearer ";

    /**
     * 连接超时（毫秒）
     */
    private Integer connectTimeout = 30000;

    /**
     * 读取超时（毫秒）
     */
    private Integer readTimeout = 1500000;

    /**
     * 写入超时（毫秒）
     */
    private Integer writeTimeout = 600000;
}
