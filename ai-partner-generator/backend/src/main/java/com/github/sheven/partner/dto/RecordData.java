package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.util.List;

/**
 * 记录数据 DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RecordData {
    
    /**
     * 用户 ID
     */
    private Long userId;
    
    /**
     * 用户 UUID
     */
    private String userUuid;
    
    /**
     * 生成记录列表
     */
    private List<RecordItem> records;
}
