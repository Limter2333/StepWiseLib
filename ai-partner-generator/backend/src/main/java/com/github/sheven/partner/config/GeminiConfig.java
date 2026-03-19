package com.github.sheven.partner.config;

import com.google.genai.Client;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.image.ImageModel;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

/**
 * Gemini AI 配置类
 * 配置 Nano Banana Pro Model 用于 AI 伴侣图片生成
 * 
 * 使用 Google 官方 Gemini SDK: com.google.genai
 */
@Slf4j
@Configuration
public class GeminiConfig {

    @Value("${spring.ai.gemini.api-key:}")
    private String apiKeyProperty;

    @Value("${spring.ai.gemini.base-url:https://generativelanguage.googleapis.com}")
    private String baseUrl;

    @Value("${spring.ai.gemini.chat.options.model:gemini-2.0-flash-exp}")
    private String model;



    /**
     * 获取实际的 API Key（处理未配置的情况）
     */
    private String getApiKey() {
        if (apiKeyProperty == null || apiKeyProperty.trim().isEmpty() ||
                apiKeyProperty.startsWith("${") && apiKeyProperty.endsWith("}")) {
            return null;
        }
        return apiKeyProperty;
    }

    /**
     * 创建 Gemini Client Bean（Google 官方 SDK）
     * 如果 API Key 为空，则返回 null
     */
    @Bean
    public Client geminiClient() {
        String apiKey = getApiKey();
        
        if (apiKey == null) {
            log.warn("未配置 GEMINI_API_KEY，Gemini Client 将不可用");
            log.info("请在 .env 文件中配置 GEMINI_API_KEY=your-api-key，或在 application.yml 中配置 spring.ai.gemini.api-key");
            return null;
        }
        
        log.info("初始化 Gemini Client，模型：{}，API 地址：{}", model, baseUrl);
        try {
            // Google Gemini SDK 的 Client.Builder 目前不支持自定义超时配置
            // 超时将通过 JVM 系统属性或 HTTP 客户端默认配置生效
            Client.Builder builder = new Client.Builder()
                    .apiKey(apiKey);
            
            return builder.build();
        } catch (Exception e) {
            log.error("创建 Gemini Client 失败：{}", e.getMessage(), e);
            return null;
        }
    }

    /**
     * 创建 Nano Banana Pro Image Model（占位符）
     * 用于 AI 伴侣图片生成
     * 
     * TODO: 实现基于 Google Gemini SDK 的 ImageModel 适配器
     * 当前可通过 GeminiService 直接调用 Gemini API
     */
    @Bean
    @Primary
    public ImageModel nanoBananaProImageModel() {
        log.warn("Nano Banana Pro Image Model 暂未实现 - 请使用 GeminiService 直接调用");
        log.info("当前将使用 DashScope ImageModel 作为默认图像生成服务");
        return null;
    }
}
