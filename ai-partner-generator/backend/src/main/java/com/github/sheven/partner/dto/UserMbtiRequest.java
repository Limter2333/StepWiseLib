package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * 用户信息提交请求 - MBTI 类型
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserMbtiRequest {
    
    /**
     * 用户唯一标识
     */
    private String userUuid;
    
    /**
     * MBTI 类型 (如 INTJ, ENFP 等)
     */
    private String mbtiType;
}
