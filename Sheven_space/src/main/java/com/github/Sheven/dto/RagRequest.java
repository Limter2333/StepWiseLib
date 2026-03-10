package com.github.Sheven.dto;

import lombok.Data;

import java.util.List;

/**
 * RAG 请求 DTO
 */
@Data
public class RagRequest {

    /**
     * 用户问题
     */
    private String question;

    /**
     * 检索数量（默认 3）
     */
    private Integer topK = 3;

    /**
     * 相似度阈值（0-1，默认 0.5）
     */
    private Double similarityThreshold = 0.5;

    /**
     * 文档类型过滤（可选）
     */
    private List<String> docTypes;
}
