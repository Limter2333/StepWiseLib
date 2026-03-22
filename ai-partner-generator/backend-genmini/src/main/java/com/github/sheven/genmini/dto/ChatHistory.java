package com.github.sheven.genmini.dto;

import lombok.Data;
import java.util.List;

/**
 * 对话历史 DTO
 */
@Data
public class ChatHistory {

    /**
     * 系统提示词
     */
    private String systemPrompt;

    /**
     * 历史消息列表
     */
    private List<Message> messages;

    @Data
    public static class Message {
        /**
         * 角色：user 或 assistant
         */
        private String role;

        /**
         * 消息内容
         */
        private String content;
    }
}
