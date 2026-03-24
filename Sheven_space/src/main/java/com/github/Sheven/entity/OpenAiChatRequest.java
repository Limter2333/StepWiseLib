package com.github.Sheven.entity;

import lombok.Data;

import java.util.List;


@Data
public class OpenAiChatRequest {
    private List<OpenAiMessage> messages;
    private String model;
    private Integer max_tokens;
    private Double temperature;
}
