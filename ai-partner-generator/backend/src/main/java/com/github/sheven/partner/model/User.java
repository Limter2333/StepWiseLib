package com.github.sheven.partner.model;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.time.LocalDateTime;

/**
 * 用户信息实体类
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@TableName("user_profile")
public class User {
    
    /**
     * 主键 ID
     */
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;
    
    /**
     * 用户唯一标识（前端传递）
     */
    @TableField("user_uuid")
    private String userUuid;
    
    /**
     * 用户名
     */
    @TableField("username")
    private String username;
    
    /**
     * 性别
     */
    @TableField("gender")
    private String gender;
    
    /**
     * 目标性别（希望的对象性别）
     */
    @TableField("target_gender")
    private String targetGender;
    
    /**
     * MBTI 类型
     */
    @TableField("mbti_type")
    private String mbtiType;
    
    /**
     * 出生日期（公历）
     */
    @TableField("birth_date")
    private String birthDate;
    
    /**
     * 星座
     */
    @TableField("zodiac_sign")
    private String zodiacSign;
    
    /**
     * 出生时间
     */
    @TableField("birth_time")
    private String birthTime;
    
    /**
     * 出生地点
     */
    @TableField("birth_place")
    private String birthPlace;
    
    /**
     * 当前居住地
     */
    @TableField("current_residence")
    private String currentResidence;
    
    /**
     * 兴趣爱好（JSON 格式）
     */
    @TableField("interests")
    private String interests;
    
    /**
     * 自定义特征描述
     */
    @TableField("custom_features")
    private String customFeatures;
    
    /**
     * 创建时间
     */
    @TableField(value = "create_time", fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    
    /**
     * 更新时间
     */
    @TableField(value = "update_time", fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
