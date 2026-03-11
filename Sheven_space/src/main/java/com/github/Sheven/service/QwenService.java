package com.github.Sheven.service;


import com.github.Sheven.dto.ChatRequest;
import com.github.Sheven.dto.ChatResponse;
import com.github.Sheven.skill.CalculatorSkill;
import com.github.Sheven.skill.DateTimeSkill;
import com.github.Sheven.skill.WeatherSkill;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

public interface QwenService {

    /**
     * 普通对话（不使用 Skills）
     */
    public ChatResponse chat(ChatRequest request);

    /**
     * 使用 Skills 的对话
     */
    public ChatResponse chatWithSkills(ChatRequest request);

    /**
     * 流式响应（使用 Skills）
     */
    public Flux<ChatResponse> streamChatWithSkills(ChatRequest request);
}
