package com.github.sheven.genmini.config;

import lombok.extern.slf4j.Slf4j;
import okhttp3.OkHttpClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.TimeUnit;

/**
 * Genmini AI 配置类
 * 配置 HTTP 客户端和 OkHttp Interceptor
 */
@Slf4j
@Configuration
public class GenminiConfig {

    @Autowired
    private GenminiProperties properties;

    /**
     * 创建 OkHttpClient Bean（带日志拦截器和 API Key 拦截器）
     */
    @Bean
    public OkHttpClient okHttpClient() {
        log.info("========== 初始化 Genmini HTTP Client ==========");
        log.info("[配置] API 地址：{}", properties.getBaseUrl());
        log.info("[配置] 连接超时：{} ms", properties.getConnectTimeout());
        log.info("[配置] 读取超时：{} ms", properties.getReadTimeout());
        log.info("[配置] 写入超时：{} ms", properties.getWriteTimeout());
        if (properties.getApiKey() != null && !properties.getApiKey().isEmpty()) {
            log.info("[配置] API Key：已配置 (头：{}, 前缀：{})", 
                properties.getApiKeyHeader(), properties.getApiKeyPrefix());
        } else {
            log.info("[配置] API Key：未配置");
        }
        log.info("==============================================");

        // 创建日志拦截器
        okhttp3.logging.HttpLoggingInterceptor loggingInterceptor = 
            new okhttp3.logging.HttpLoggingInterceptor(message -> {
                log.debug("[HTTP] {}", message);
            });
        loggingInterceptor.setLevel(okhttp3.logging.HttpLoggingInterceptor.Level.BODY);

        // 创建 API Key 拦截器
        okhttp3.logging.HttpLoggingInterceptor authLoggingInterceptor = 
            new okhttp3.logging.HttpLoggingInterceptor(message -> {
                // 过滤掉敏感的 API Key 信息
                if (message.contains(properties.getApiKey())) {
                    log.debug("[HTTP] {}", message.replace(properties.getApiKey(), "***"));
                } else {
                    log.debug("[HTTP] {}", message);
                }
            });
        authLoggingInterceptor.setLevel(okhttp3.logging.HttpLoggingInterceptor.Level.HEADERS);

        okhttp3.Interceptor authInterceptor = chain -> {
            okhttp3.Request originalRequest = chain.request();
            okhttp3.Request.Builder requestBuilder = originalRequest.newBuilder();
            
            // 添加 API Key（如果配置了）
            String apiKey = properties.getApiKey();
            if (apiKey != null && !apiKey.isEmpty()) {
                String apiKeyValue = properties.getApiKeyPrefix() + apiKey;
                requestBuilder.addHeader(properties.getApiKeyHeader(), apiKeyValue);
                log.debug("[HTTP] 添加认证头：{} = {}", properties.getApiKeyHeader(), "***");
            }
            
            requestBuilder.method(originalRequest.method(), originalRequest.body());
            return chain.proceed(requestBuilder.build());
        };

        OkHttpClient.Builder clientBuilder = new OkHttpClient.Builder()
                .connectTimeout(properties.getConnectTimeout(), TimeUnit.MILLISECONDS)
                .readTimeout(properties.getReadTimeout(), TimeUnit.MILLISECONDS)
                .writeTimeout(properties.getWriteTimeout(), TimeUnit.MILLISECONDS)
                .addInterceptor(loggingInterceptor)
                .addInterceptor(authInterceptor);

        return clientBuilder.build();
    }
}
