package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * 步骤信息响应
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class StepInfo {
    
    /**
     * 当前步骤
     */
    private Integer currentStep;
    
    /**
     * 总步骤数
     */
    private Integer totalSteps;
    
    /**
     * 步骤名称
     */
    private String stepName;
    
    /**
     * 是否完成
     */
    private Boolean isComplete;
    
    /**
     * 下一步提示
     */
    private String nextHint;
}
