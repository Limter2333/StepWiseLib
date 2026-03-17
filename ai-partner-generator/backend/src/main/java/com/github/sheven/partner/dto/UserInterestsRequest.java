package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.util.List;

/**
 * 用户信息提交请求 - 兴趣爱好和特征
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserInterestsRequest {
    
    /**
     * 用户唯一标识
     */
    private String userUuid;
    
    /**
     * 兴趣爱好列表
     */
    private List<String> interests;
    
    /**
     * 自定义特征描述（可选）
     */
    private String customFeatures;
}
