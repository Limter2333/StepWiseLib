package com.github.Sheven.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.github.Sheven.entity.FieldManager;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 字段管理 Mapper
 */
@Mapper
public interface FieldManagerMapper extends BaseMapper<FieldManager> {

    /**
     * 根据多个英文字段名批量查询字段信息
     * @param nameSList 英文字段名列表
     * @return 字段信息列表
     */
    @Select("<script>" +
            "SELECT * FROM field_manager " +
            "WHERE NAME_S IN " +
            "<foreach item='nameS' collection='nameSList' open='(' separator=',' close=')'>" +
            "#{nameS}" +
            "</foreach>" +
            "</script>")
    List<FieldManager> selectByNames(@Param("nameSList") List<String> nameSList);
}
