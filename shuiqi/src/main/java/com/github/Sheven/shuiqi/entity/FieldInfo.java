package com.github.Sheven.shuiqi.entity;

import lombok.Data;

/**
 * 字段信息 DTO
 * 用于封装从 MCP 服务获取的字段详细信息
 */
@Data
public class FieldInfo {

    /**
     * 中文字段名
     */
    private String chineseName;

    /**
     * 英文字段名
     */
    private String englishName;

    /**
     * 字段类型
     */
    private String fieldType;

    /**
     * 字段长度
     */
    private Integer fieldLength;

    /**
     * 是否主键
     */
    private Boolean primaryKey;

    /**
     * 是否可为空
     */
    private Boolean nullable;

    /**
     * 默认值
     */
    private String defaultValue;

    /**
     * 字段描述
     */
    private String description;

    /**
     * 表名
     */
    private String tableName;

    /**
     * 数据库名
     */
    private String databaseName;

    /**
     * 索引信息
     */
    private String indexInfo;

    /**
     * 约束信息
     */
    private String constraintInfo;

    /**
     * 示例数据
     */
    private String sampleData;

    /**
     * 数据来源 (MCP 服务返回的原始数据)
     */
    private Object rawData;
}
