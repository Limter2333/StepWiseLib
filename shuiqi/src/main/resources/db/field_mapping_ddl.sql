-- ----------------------------
-- Table structure for field_mapping
-- ----------------------------
DROP TABLE IF EXISTS `field_mapping`;
CREATE TABLE `field_mapping` (
                                 `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
                                 `chinese_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '中文字段名',
                                 `english_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '英文字段名',
                                 `field_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '字段类型 (VARCHAR, INT, DATETIME 等)',
                                 `field_length` int DEFAULT NULL COMMENT '字段长度',
                                 `nullable` tinyint(1) DEFAULT '1' COMMENT '是否可为空 (0:否，1:是)',
                                 `default_value` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '默认值',
                                 `description` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '字段描述',
                                 `table_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '表名',
                                 `database_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '数据库名',
                                 `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                                 `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                                 PRIMARY KEY (`id`),
                                 KEY `idx_chinese_name` (`chinese_name`) USING BTREE COMMENT '中文字段名索引',
                                 KEY `idx_english_name` (`english_name`) USING BTREE COMMENT '英文字段名索引',
                                 KEY `idx_table_name` (`table_name`) USING BTREE COMMENT '表名索引',
                                 KEY `idx_create_time` (`create_time`) USING BTREE COMMENT '创建时间索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='字段映射表';