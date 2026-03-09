package com.github.Sheven.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ChatRequest {
    // 用户输入的消息
    private String message;

    // 对话ID，用于区分不同会话（实现记忆功能）
    private String conversationId;

    // 可选：系统提示词（覆盖默认）
    private String systemPrompt;
}