package com.github.Sheven.shuiqi.dto;

import lombok.Data;
import java.util.List;

/**
 * 字段映射请求 DTO
 */
@Data
public class FieldMappingRequest {

    /**
     * 中文字段名列表
     */
    private List<String> chineseNames;

    /**
     * 生成的 VO 类名（可选，默认使用 FieldVO）
     */
    private String voClassName;

    /**
     * 是否导出 Excel（默认 true）
     */
    private Boolean exportExcel = true;

    /**
     * 是否生成 VO 代码（默认 true）
     */
    private Boolean generateVoCode = true;

    /**
     * Excel 文件名（可选）
     */
    private String excelFileName;
}
