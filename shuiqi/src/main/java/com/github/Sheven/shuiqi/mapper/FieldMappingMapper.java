package com.github.Sheven.shuiqi.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.github.Sheven.shuiqi.entity.FieldMapping;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 字段映射 Mapper 接口
 */
@Mapper
public interface FieldMappingMapper extends BaseMapper<FieldMapping> {

    /**
     * 根据中文字段名查询所有匹配的英文字段
     * @param chineseName 中文字段名
     * @return 英文字段列表
     */
    List<FieldMapping> selectByChineseName(@Param("chineseName") String chineseName);

    /**
     * 批量根据中文字段名查询
     * @param chineseNames 中文字段名列表
     * @return 字段映射列表
     */
    List<FieldMapping> selectByChineseNames(@Param("chineseNames") List<String> chineseNames);

    /**
     * 根据表名查询所有字段映射
     * @param tableName 表名
     * @return 字段映射列表
     */
    List<FieldMapping> selectByTableName(@Param("tableName") String tableName);

    /**
     * 根据数据库名和表名查询
     * @param databaseName 数据库名
     * @param tableName 表名
     * @return 字段映射列表
     */
    List<FieldMapping> selectByDatabaseAndTable(
        @Param("databaseName") String databaseName,
        @Param("tableName") String tableName
    );
}
