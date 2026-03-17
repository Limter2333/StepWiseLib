package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * 用户信息提交请求 - 出生日期和时间
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserBirthDateRequest {
    
    /**
     * 用户唯一标识
     */
    private String userUuid;
    
    /**
     * 出生日期（公历，格式：yyyy-MM-dd）
     */
    private String birthDate;
    
    /**
     * 出生时间（可选，格式：HH:mm）
     */
    private String birthTime;
}
