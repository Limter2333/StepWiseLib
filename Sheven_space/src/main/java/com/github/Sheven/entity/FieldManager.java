package com.github.Sheven.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 字段管理实体
 */
@Data
@TableName("field_manager")
public class FieldManager {

    /**
     * 主键 ID
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 英文字段名
     */
    private String nameS;

    /**
     * 中文字段名
     */
    private String nameCn;

    /**
     * 项目编号
     */
    private String itemNo;

    /**
     * 自定义字段 1
     */
    private String f1;

    /**
     * 自定义字段 2
     */
    private String f2;

    /**
     * 自定义字段 3
     */
    private String f3;

    /**
     * 自定义字段 4
     */
    private String f4;

    /**
     * 创建时间
     */
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
