package com.github.sheven.partner.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.util.List;

/**
 * 生成记录响应 DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RecordResponse {
    
    /**
     * 状态码
     */
    private Integer code;
    
    /**
     * 消息
     */
    private String message;
    
    /**
     * 数据
     */
    private RecordData data;
    
    /**
     * 成功响应
     */
    public static RecordResponse success(RecordData data) {
        return new RecordResponse(200, "success", data);
    }
    
    /**
     * 错误响应
     */
    public static RecordResponse error(String message) {
        return new RecordResponse(500, message, null);
    }
}
