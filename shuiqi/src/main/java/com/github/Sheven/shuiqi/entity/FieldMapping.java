package com.github.Sheven.shuiqi.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 字段映射实体类
 * 存储中文名与英文字段的映射关系
 */
@Data
@TableName("field_mapping")
public class FieldMapping {

    /**
     * 主键 ID
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 中文字段名
     */
    private String chineseName;

    /**
     * 英文字段名
     */
    private String englishName;

    /**
     * 字段类型 (VARCHAR, INT, DATETIME 等)
     */
    private String fieldType;

    /**
     * 字段长度
     */
    private Integer fieldLength;

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
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;
}
