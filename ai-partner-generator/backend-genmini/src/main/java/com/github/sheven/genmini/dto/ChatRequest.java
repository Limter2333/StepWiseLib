package com.github.sheven.genmini.dto;

import lombok.Data;

import jakarta.validation.constraints.NotBlank;

/**
 * 聊天请求 DTO
 */
@Data
public class ChatRequest {

    /**
     * 用户输入的消息
     */
    @NotBlank(message = "消息内容不能为空")
    private String message;

    /**
     * 使用的模型名称（可选，默认从配置文件读取）
     */
    private String model;

    /**
     * 对话历史（可选）
     */
    private ChatHistory history;
}
