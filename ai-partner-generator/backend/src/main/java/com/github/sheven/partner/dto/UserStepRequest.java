package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * 用户步骤信息提交请求
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserStepRequest {
    
    /**
     * 用户名
     */
    private String username;
    
    /**
     * 当前步骤
     */
    private Integer step;
    
    /**
     * 步骤数据（包含所有表单信息）
     */
    private Object data;
    
    /**
     * 用户 UUID（可选，用于后续步骤更新同一用户）
     */
    private String userUuid;
}
