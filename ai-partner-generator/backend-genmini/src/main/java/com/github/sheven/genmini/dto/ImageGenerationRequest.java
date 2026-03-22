package com.github.sheven.genmini.dto;

import lombok.Data;

import jakarta.validation.constraints.NotBlank;

/**
 * 图片生成请求 DTO
 */
@Data
public class ImageGenerationRequest {

    /**
     * 图片描述提示词
     */
    @NotBlank(message = "提示词不能为空")
    private String prompt;

    /**
     * 使用的模型名称（可选，默认从配置文件读取）
     */
    private String model;

    /**
     * 参考图片的 Base64 数据（可选）
     */
    private String referenceImage;

    /**
     * 参考图片的 MIME 类型（如 image/jpeg）
     */
    private String referenceImageType;

    /**
     * 生成图片的数量（可选，默认 1）
     */
    private Integer count = 1;

    /**
     * 图片宽度（可选，取决于模型支持）
     */
    private Integer width;

    /**
     * 图片高度（可选，取决于模型支持）
     */
    private Integer height;
}
