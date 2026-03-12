package com.github.Sheven.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 字段信息查询请求 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FieldQueryRequest {

    /**
     * 英文字段名列表
     */
    private String[] nameSList;
}
