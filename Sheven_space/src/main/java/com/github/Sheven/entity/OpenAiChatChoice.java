package com.github.Sheven.entity;

import lombok.Data;

@Data
public class OpenAiChatChoice {
    private int index;
    private OpenAiMessage message;
    private String finish_reason;
}