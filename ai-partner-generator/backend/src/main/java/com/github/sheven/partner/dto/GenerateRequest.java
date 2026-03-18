package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.util.List;

/**
 * 生成请求 DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class GenerateRequest {
    
    /**
     * 用户唯一标识（用于关联用户）
     */
    private String userUuid;
    
    /**
     * 用户名
     */
    private String username;
    
    /**
     * 性别
     */
    private String gender;
    
    /**
     * 目标性别（希望的对象性别）
     */
    private String targetGender;
    
    /**
     * MBTI 类型
     */
    private String mbtiType;
    
    /**
     * 出生日期（公历）
     */
    private String birthDate;
    
    /**
     * 星座
     */
    private String zodiacSign;
    
    /**
     * 出生时间
     */
    private String birthTime;
    
    /**
     * 出生地点
     */
    private String birthPlace;
    
    /**
     * 当前居住地
     */
    private String currentResidence;
    
    /**
     * 兴趣爱好
     */
    private List<String> interests;
    
    /**
     * 自定义特征描述
     */
    private String customFeatures;
}
