package com.github.Sheven.entity;

import lombok.Data;

@Data
public class OpenAiMessage {
    private String role;
    private String content;

    public OpenAiMessage() {}
    public OpenAiMessage(String role, String content) {
        this.role = role;
        this.content = content;
    }
    // getters/setters
}