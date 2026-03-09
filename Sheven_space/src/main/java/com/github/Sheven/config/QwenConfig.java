package com.github.Sheven.config;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class QwenConfig {

    /**
     * 配置 ChatClient Builder
     * 注意：Spring AI Alibaba 会自动配置 ChatClient.Builder，
     * 这里展示如何添加全局默认配置
     */
    @Bean
    ChatClient chatClient(ChatClient.Builder builder) {
        return builder
                .defaultSystem("请用可爱一点的语气回答用户问题。")
                .build();
    }
}
