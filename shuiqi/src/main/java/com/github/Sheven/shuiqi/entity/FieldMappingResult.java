package com.github.Sheven.shuiqi.entity;

import lombok.Data;
import java.util.List;

/**
 * 字段映射结果
 * 包含完整的映射处理结果
 */
@Data
public class FieldMappingResult {

    /**
     * 请求 ID
     */
    private String requestId;

    /**
     * 输入的中文字段列表
     */
    private List<String> inputChineseNames;

    /**
     * 匹配成功的字段信息列表
     */
    private List<FieldInfo> matchedFields;

    /**
     * 未匹配的中文名称列表
     */
    private List<String> unmatchedNames;

    /**
     * AI 去重说明
     */
    private String aiDeduplicationNote;

    /**
     * Excel 文件路径
     */
    private String excelFilePath;

    /**
     * VO 代码内容
     */
    private String voCode;

    /**
     * 处理状态
     */
    private String status;

    /**
     * 错误信息
     */
    private String errorMessage;

    /**
     * 处理时间 (毫秒)
     */
    private Long processingTime;
}
