package com.github.Sheven.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * RAG 响应 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RagResponse {

    /**
     * AI 生成的回答
     */
    private String answer;

    /**
     * 参考的文档片段
     */
    private List<ReferenceDocument> references;

    /**
     * 是否使用了 RAG 增强
     */
    private Boolean ragEnhanced;

    /**
     * 响应元数据
     */
    private ResponseMetadata metadata;

    /**
     * 参考文档
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ReferenceDocument {
        private Long id;
        private String title;
        private String content;
        private String docType;
        private Double similarityScore;
        private String source;
    }

    /**
     * 响应元数据
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ResponseMetadata {
        private Integer totalReferences;
        private Long queryTimeMs;
        private String model;
    }
}
