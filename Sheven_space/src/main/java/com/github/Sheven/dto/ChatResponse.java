package com.github.Sheven.dto;

import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ChatResponse {
    private String content;
    private String conversationId;
    private long timestamp;
    private String model;

    public ChatResponse(String content, String conversationId, String model) {
        this.content = content;
        this.conversationId = conversationId;
        this.model = model;
        this.timestamp = System.currentTimeMillis();
    }
}