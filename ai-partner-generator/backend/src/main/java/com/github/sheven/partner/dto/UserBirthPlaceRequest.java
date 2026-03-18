package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * 用户信息提交请求 - 出生地点
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserBirthPlaceRequest {
    
    /**
     * 用户唯一标识
     */
    private String userUuid;
    
    /**
     * 出生地点
     */
    private String birthPlace;
}
