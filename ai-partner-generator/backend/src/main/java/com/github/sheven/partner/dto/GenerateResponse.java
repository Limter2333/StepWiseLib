package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * 生成响应 DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class GenerateResponse {
    
    /**
     * 生成的图片 URL
     */
    private String imageUrl;
    
    /**
     * 生成描述
     */
    private String description;
    
    /**
     * 是否成功
     */
    private boolean success;
    
    /**
     * 错误信息
     */
    private String errorMessage;
    
    public static GenerateResponse success(String imageUrl, String description) {
        return new GenerateResponse(imageUrl, description, true, null);
    }
    
    public static GenerateResponse error(String errorMessage) {
        return new GenerateResponse(null, errorMessage, false, errorMessage);
    }
}
