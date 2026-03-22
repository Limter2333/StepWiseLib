package com.github.sheven.genmini.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 图片生成响应 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ImageGenerationResponse {

    /**
     * 是否成功
     */
    private boolean success;

    /**
     * 生成的图片列表（Base64 编码）
     */
    private List<String> images;

    /**
     * 使用的模型
     */
    private String model;

    /**
     * 错误信息（如果失败）
     */
    private String error;

    /**
     * 创建成功响应
     */
    public static ImageGenerationResponse success(List<String> images, String model) {
        return ImageGenerationResponse.builder()
                .success(true)
                .images(images)
                .model(model)
                .build();
    }

    /**
     * 创建失败响应
     */
    public static ImageGenerationResponse error(String error) {
        return ImageGenerationResponse.builder()
                .success(false)
                .error(error)
                .build();
    }
}
