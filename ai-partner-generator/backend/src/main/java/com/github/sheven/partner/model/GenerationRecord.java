package com.github.sheven.partner.model;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.time.LocalDateTime;

/**
 * AI 伴侣生成记录实体类
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@TableName("generation_record")
public class GenerationRecord {
    
    /**
     * 主键 ID
     */
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;
    
    /**
     * 用户 ID
     */
    @TableField("user_id")
    private Long userId;
    
    /**
     * 用户唯一标识
     */
    @TableField("user_uuid")
    private String userUuid;
    
    /**
     * 生成的图片路径（本地路径）
     */
    @TableField("image_path")
    private String imagePath;
    
    /**
     * 生成的图片 URL（访问路径）
     */
    @TableField("image_url")
    private String imageUrl;
    
    /**
     * 提示词
     */
    @TableField("prompt")
    private String prompt;
    
    /**
     * 描述文本
     */
    @TableField("description")
    private String description;
    
    /**
     * 请求参数（JSON 格式）
     */
    @TableField("request_data")
    private String requestData;
    
    /**
     * 创建时间
     */
    @TableField(value = "create_time", fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    
    /**
     * 更新时间
     */
    @TableField(value = "update_time", fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
