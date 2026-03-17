package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * 用户信息提交请求 - 基本信息（性别）
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserGenderRequest {
    
    /**
     * 用户唯一标识
     */
    private String userUuid;
    
    /**
     * 性别 (male/female/other)
     */
    private String gender;
}
