package com.github.sheven.partner.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.github.sheven.partner.model.GenerationRecord;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 生成记录 Mapper 接口
 */
@Mapper
public interface GenerationRecordMapper extends BaseMapper<GenerationRecord> {
    
    /**
     * 查询用户的所有生成记录
     */
    List<GenerationRecord> selectByUserId(@Param("userId") Long userId);
    
    /**
     * 查询用户的所有生成记录（按 UUID）
     */
    List<GenerationRecord> selectByUserUuid(@Param("userUuid") String userUuid);
}
