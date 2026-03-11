package com.github.Sheven.service.impl;


import com.github.Sheven.dto.ChatRequest;
import com.github.Sheven.dto.ChatResponse;
import com.github.Sheven.service.SkillService;
import com.github.Sheven.skill.CalculatorSkill;
import com.github.Sheven.skill.DateTimeSkill;
import com.github.Sheven.skill.WeatherSkill;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

@Service
public class SkillServiceImpl implements SkillService {

    @Autowired
    private ChatClient chatClient;

    @Autowired
    private WeatherSkill weatherSkill;

    @Autowired
    private CalculatorSkill calculatorSkill;

    @Autowired
    private DateTimeSkill dateTimeSkill;

    /**
     * 普通对话（不使用 Skills）
     */
    @Override
    public ChatResponse chat(ChatRequest request) {
        String reply = chatClient.prompt()
                .user(request.getMessage())
                .call()
                .content();

        return ChatResponse.builder()
                .content(reply)
                .build();
    }

    /**
     * 使用 Skills 的对话
     */
    @Override
    public ChatResponse chatWithSkills(ChatRequest request) {
        String reply = chatClient.prompt()
                .user(request.getMessage())
                .tools(weatherSkill, calculatorSkill, dateTimeSkill)
                .call()
                .content();

        return ChatResponse.builder()
                .content(reply)
                .build();
    }

    /**
     * 流式响应（使用 Skills）
     */
    @Override
    public Flux<ChatResponse> streamChatWithSkills(ChatRequest request) {
        return chatClient.prompt()
                .user(request.getMessage())
                .tools(weatherSkill, calculatorSkill, dateTimeSkill)
                .stream()
                .content()
                .map(content -> ChatResponse.builder()
                        .content(content)
                        .build());
    }
}
