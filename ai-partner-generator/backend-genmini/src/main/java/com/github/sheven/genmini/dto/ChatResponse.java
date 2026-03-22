package com.github.sheven.genmini.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 聊天响应 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatResponse {

    /**
     * 是否成功
     */
    private boolean success;

    /**
     * 响应消息
     */
    private String message;

    /**
     * 使用的模型
     */
    private String model;

    /**
     * 错误信息（如果失败）
     */
    private String error;

    /**
     * 创建成功响应
     */
    public static ChatResponse success(String message, String model) {
        return ChatResponse.builder()
                .success(true)
                .message(message)
                .model(model)
                .build();
    }

    /**
     * 创建失败响应
     */
    public static ChatResponse error(String error) {
        return ChatResponse.builder()
                .success(false)
                .error(error)
                .build();
    }
}
