package com.github.Sheven.shuiqi.service;

import com.github.Sheven.shuiqi.entity.FieldInfo;
import com.github.Sheven.shuiqi.entity.FieldMapping;
import com.github.Sheven.shuiqi.entity.FieldMappingResult;

import java.util.List;

/**
 * 字段映射服务接口
 */
public interface FieldMappingService {

    /**
     * 根据中文字段名列表查询并处理字段映射
     * @param chineseNames 中文字段名列表
     * @return 字段映射结果
     */
    FieldMappingResult processFieldMappings(List<String> chineseNames);

    /**
     * 根据中文字段名查询英文字段（带 AI 去重）
     * @param chineseName 中文字段名
     * @return 去重后的字段信息列表
     */
    List<FieldInfo> queryFieldsWithDeduplication(String chineseName);

    /**
     * 调用 MCP 服务获取字段详细信息
     * @param englishName 英文字段名
     * @param tableName 表名
     * @return 字段详细信息
     */
    FieldInfo fetchFieldInfoFromMcp(String englishName, String tableName);
}
