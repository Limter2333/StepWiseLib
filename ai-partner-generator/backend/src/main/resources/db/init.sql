-- AI Partner Generator 数据库初始化脚本
-- 数据库名：ai-partner-generator

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS `ai-partner-generator` 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

USE `ai-partner-generator`;

-- 用户信息表
DROP TABLE IF EXISTS `user_profile`;
CREATE TABLE `user_profile` (
    `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
    `user_uuid` VARCHAR(64) NOT NULL COMMENT '用户唯一标识',
    `gender` VARCHAR(10) DEFAULT NULL COMMENT '性别',
    `mbti_type` VARCHAR(10) DEFAULT NULL COMMENT 'MBTI 类型',
    `birth_date` VARCHAR(20) DEFAULT NULL COMMENT '出生日期（公历）',
    `zodiac_sign` VARCHAR(20) DEFAULT NULL COMMENT '星座',
    `birth_time` VARCHAR(20) DEFAULT NULL COMMENT '出生时间',
    `birth_place` VARCHAR(100) DEFAULT NULL COMMENT '出生地点',
    `current_residence` VARCHAR(100) DEFAULT NULL COMMENT '当前居住地',
    `interests` TEXT DEFAULT NULL COMMENT '兴趣爱好（JSON 格式）',
    `custom_features` TEXT DEFAULT NULL COMMENT '自定义特征描述',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_uuid` (`user_uuid`),
    KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户信息表';

-- AI 伴侣生成记录表
DROP TABLE IF EXISTS `generation_record`;
CREATE TABLE `generation_record` (
    `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
    `user_id` BIGINT(20) NOT NULL COMMENT '用户 ID',
    `user_uuid` VARCHAR(64) NOT NULL COMMENT '用户唯一标识',
    `image_path` VARCHAR(500) NOT NULL COMMENT '生成的图片路径（本地路径）',
    `image_url` VARCHAR(500) NOT NULL COMMENT '生成的图片 URL（访问路径）',
    `prompt` TEXT DEFAULT NULL COMMENT '提示词',
    `description` TEXT DEFAULT NULL COMMENT '描述文本',
    `request_data` TEXT DEFAULT NULL COMMENT '请求参数（JSON 格式）',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_user_uuid` (`user_uuid`),
    KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 伴侣生成记录表';
