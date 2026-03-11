package com.github.Sheven.service;


import com.github.Sheven.dto.ChatRequest;
import com.github.Sheven.dto.ChatResponse;
import reactor.core.publisher.Flux;

public interface SkillService {

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
