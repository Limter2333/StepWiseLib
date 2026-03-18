package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * 用户信息提交请求 - 当前居住地
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserCurrentResidenceRequest {
    
    /**
     * 用户唯一标识
     */
    private String userUuid;
    
    /**
     * 当前居住地
     */
    private String currentResidence;
}
