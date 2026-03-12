package com.github.Sheven.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 字段信息响应 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FieldInfoResponse {

    /**
     * 英文字段名
     */
    private String nameS;

    /**
     * 中文字段名（查询不到时为 null）
     */
    private String nameCn;

    /**
     * 项目编号（查询不到时为 null）
     */
    private String itemNo;

    /**
     * 自定义字段 1（查询不到时为 null）
     */
    private String f1;

    /**
     * 自定义字段 2（查询不到时为 null）
     */
    private String f2;

    /**
     * 自定义字段 3（查询不到时为 null）
     */
    private String f3;

    /**
     * 自定义字段 4（查询不到时为 null）
     */
    private String f4;

    /**
     * 是否找到匹配记录
     */
    private Boolean found;
}
