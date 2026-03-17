package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.time.LocalDateTime;

/**
 * 记录项 DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RecordItem {
    
    /**
     * 记录 ID
     */
    private Long id;
    
    /**
     * 图片 URL
     */
    private String imageUrl;
    
    /**
     * 提示词
     */
    private String prompt;
    
    /**
     * 描述文本
     */
    private String description;
    
    /**
     * 创建时间
     */
    private LocalDateTime createTime;
}
