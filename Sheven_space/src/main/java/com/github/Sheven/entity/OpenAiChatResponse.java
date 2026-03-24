package com.github.Sheven.entity;

import lombok.Data;
import org.springframework.ai.chat.metadata.Usage;

import java.util.List;

@Data
public class OpenAiChatResponse {
    private String id;
    private String object = "chat.completion";
    private Long created;
    private String model;
    private List<OpenAiChatChoice> choices;
    private Usage usage;
}