package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * 用户信息提交请求 - 地理位置信息
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserLocationRequest {
    
    /**
     * 用户唯一标识
     */
    private String userUuid;
    
    /**
     * 出生地点
     */
    private String birthPlace;
    
    /**
     * 当前居住地
     */
    private String currentResidence;
}
