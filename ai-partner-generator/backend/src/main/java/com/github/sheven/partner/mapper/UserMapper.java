package com.github.sheven.partner.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.github.sheven.partner.model.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 用户信息 Mapper 接口
 */
@Mapper
public interface UserMapper extends BaseMapper<User> {
    
    /**
     * 根据 UUID 查询用户
     */
    User selectByUserUuid(@Param("userUuid") String userUuid);
}
