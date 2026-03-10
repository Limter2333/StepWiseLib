package com.github.Sheven.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 文档知识库实体
 */
@Data
@TableName("rag_document")
public class RagDocument {

    /**
     * 主键 ID
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 文档标题
     */
    private String title;

    /**
     * 文档内容
     */
    private String content;

    /**
     * 文档类型（article:文章，faq:问答，manual:手册，other:其他）
     */
    private String docType;

    /**
     * 关键词标签（逗号分隔）
     */
    private String keywords;

    /**
     * 文档来源/URL
     */
    private String source;

    /**
     * 相似度分数（用于检索排序）
     */
    @TableField(exist = false)
    private Double similarityScore;

    /**
     * 创建时间
     */
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
