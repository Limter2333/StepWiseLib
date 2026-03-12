package com.github.Sheven.shuiqi.config;

import com.github.Sheven.shuiqi.agent.FieldMappingAgent;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * AI 配置类
 */
@Configuration
public class AiConfig {

    /**
     * 创建支持工具的 ChatClient Bean
     */
    @Bean
    public ChatClient chatClient(ChatModel chatModel, FieldMappingAgent fieldMappingAgent) {
        return ChatClient.builder(chatModel)
                .build();
    }
}
