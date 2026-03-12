package com.github.Sheven.shuiqi.dto;

import com.github.Sheven.shuiqi.entity.FieldInfo;
import lombok.Data;
import java.util.List;

/**
 * 字段映射响应 DTO
 */
@Data
public class FieldMappingResponse {

    /**
     * 请求 ID
     */
    private String requestId;

    /**
     * 处理状态
     */
    private String status;

    /**
     * 错误信息
     */
    private String errorMessage;

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
     * 处理时间 (毫秒)
     */
    private Long processingTime;

    /**
     * 成功响应构造
     */
    public static FieldMappingResponse success(String requestId, List<FieldInfo> matchedFields,
                                               List<String> unmatchedNames, String excelPath,
                                               String voCode, Long processingTime) {
        FieldMappingResponse response = new FieldMappingResponse();
        response.setRequestId(requestId);
        response.setStatus("success");
        response.setMatchedFields(matchedFields);
        response.setUnmatchedNames(unmatchedNames);
        response.setAiDeduplicationNote("已使用 AI 对同一中文名的多个英文字段进行语义分析和去重");
        response.setExcelFilePath(excelPath);
        response.setVoCode(voCode);
        response.setProcessingTime(processingTime);
        return response;
    }

    /**
     * 失败响应构造
     */
    public static FieldMappingResponse error(String requestId, String errorMessage) {
        FieldMappingResponse response = new FieldMappingResponse();
        response.setRequestId(requestId);
        response.setStatus("error");
        response.setErrorMessage(errorMessage);
        return response;
    }
}
