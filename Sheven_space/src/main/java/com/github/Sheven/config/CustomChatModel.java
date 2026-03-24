package com.github.Sheven.config;


import org.apache.logging.log4j.message.Message;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.model.Generation;

import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

@Component
public class CustomChatModel implements ChatModel {

    private final RestTemplate restTemplate = new RestTemplate();
    private final String localModelUrl = "http://localhost:8001/predict"; // 你的本地模型 API

    @Override
    public ChatResponse call(Prompt prompt) {
        // 1. 从 Prompt 提取用户消息
        UserMessage userMessage = prompt.getUserMessage();
        String userContent = userMessage.getText();

        // 2. 构造你本地模型所需的请求体（根据你的 API 修改！）
        Map<String, Object> localRequest = Map.of(
                "prompt", userContent,
                "max_new_tokens", 512,
                "temperature", 0.7
        );

        // 3. 调用本地模型
        Map response = restTemplate.postForObject(localModelUrl, localRequest, Map.class);
        if (response == null) {
            throw new RuntimeException("Local model returned null");
        }

        // 4. 解析响应（假设你的模型返回 {"generated_text": "..."}）
        String generatedText = (String) response.get("generated_text");


        // 5. 构造 Spring AI 的 ChatResponse
        AssistantMessage assistantMessage = new AssistantMessage(generatedText);
        Generation generation = new Generation(assistantMessage);
        return new ChatResponse(List.of(generation));
    }
}