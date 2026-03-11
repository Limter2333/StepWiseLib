-- RAG 知识库数据库初始化脚本
-- MySQL 8.0+ 

-- 创建数据库
CREATE DATABASE IF NOT EXISTS rag_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE rag_db;

-- 创建 RAG 文档表
DROP TABLE IF EXISTS rag_document;

CREATE TABLE rag_document (
      id BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
      title VARCHAR(255) NOT NULL COMMENT '文档标题',
      content TEXT NOT NULL COMMENT '文档内容',
      doc_type VARCHAR(50) DEFAULT 'article' COMMENT '文档类型：article-文章，faq-问答，manual-手册，other-其他',
      keywords VARCHAR(1000) DEFAULT NULL COMMENT '关键词标签（逗号分隔）',
      source VARCHAR(500) DEFAULT NULL COMMENT '文档来源/URL',
      create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      PRIMARY KEY (id),
      FULLTEXT INDEX ft_title_content (title(50), content(100)) WITH PARSER ngram COMMENT '全文索引（用于中文分词搜索）',
      INDEX idx_doc_type (doc_type),
      INDEX idx_keywords (keywords(255)),
      INDEX idx_create_time (create_time),
      INDEX idx_update_time (update_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='RAG 知识库文档表';

-- 插入示例数据
INSERT INTO rag_document (title, content, doc_type, keywords, source) VALUES
('什么是 RAG 技术？', 
 'RAG（Retrieval-Augmented Generation，检索增强生成）是一种将信息检索与文本生成相结合的人工智能技术。它通过从外部知识库中检索相关信息，然后将这些信息作为上下文输入给大型语言模型，从而生成更准确、更有依据的回答。RAG 技术的核心优势在于：1. 可以减少模型的幻觉；2. 可以提供可追溯的信息来源；3. 可以及时更新知识而不需要重新训练模型。',
 'faq', 
 'RAG，人工智能，自然语言处理，检索增强生成',
 'https://example.com/rag-intro'),

('如何搭建企业知识库问答系统？',
 '搭建企业知识库问答系统通常需要以下步骤：1. 收集和整理企业内部的文档资料；2. 对文档进行清洗和结构化处理；3. 建立文档检索机制（可以使用全文检索或向量检索）；4. 集成大语言模型 API；5. 开发前后端应用界面；6. 测试和优化系统性能。关键技术包括：MyBatis-Plus 用于数据持久化，MySQL 用于存储文档，Spring Boot 用于后端开发，以及 AI 模型集成。',
 'manual',
 '知识库，问答系统，企业应用，系统架构',
 'https://example.com/knowledge-base-guide'),

('MySQL 数据库优化技巧',
 'MySQL 数据库优化的主要方法包括：1. 合理使用索引，避免索引滥用；2. 优化 SQL 查询语句，避免全表扫描；3. 使用 EXPLAIN 分析查询计划；4. 合理配置数据库参数（如 buffer_pool、query_cache 等）；5. 采用读写分离、分库分表等架构优化；6. 定期维护和监控数据库性能。对于全文检索场景，可以使用 MySQL 的 FULLTEXT 索引来提高搜索效率。',
 'article',
 'MySQL，数据库优化，索引，性能调优',
 'https://example.com/mysql-optimization'),

('MyBatis-Plus 快速入门教程',
 'MyBatis-Plus 是一个 MyBatis 的增强工具，在 MyBatis 的基础上只做增强不做改变。主要特性包括：1. 无侵入设计，只做增强不做改变；2. 强大的 CRUD 操作支持；3. 支持 Lambda 语法编写条件构造器；4. 支持主键自动生成；5. 支持 ActiveRecord 模式；6. 支持自定义全局通用 Mapper。使用 MyBatis-Plus 可以大大简化数据库开发工作，提高开发效率。',
 'article',
 'MyBatis-Plus，Java，ORM，数据库开发',
 'https://example.com/mybatis-plus-tutorial'),

('Spring Boot 项目最佳实践',
 'Spring Boot 项目最佳实践包括：1. 合理的包结构设计；2. 使用 application.yml 进行配置管理；3. 使用 Profile 区分不同环境；4. 使用 Lombok 简化代码；5. 统一异常处理和响应格式；6. 使用日志框架记录关键信息；7. 集成 MyBatis-Plus 等优秀框架；8. 编写单元测试保证代码质量；9. 使用 Git 进行版本控制。遵循这些实践可以提高项目的可维护性和可扩展性。',
 'article',
 'Spring Boot，最佳实践，项目架构，Java 开发',
 'https://example.com/spring-boot-best-practices'),

('AI Agent 开发指南',
 'AI Agent 是能够感知环境并采取行动实现目标的智能体。开发现代 AI Agent 通常需要使用 Spring AI 等框架，结合大语言模型的能力。关键组件包括：1. 对话管理能力；2. 工具调用能力（Function Calling）；3. 记忆能力；4. 规划和推理能力。Spring AI Alibaba 提供了与通义千问等模型的集成，使得开发者可以快速构建 AI 应用。',
 'manual',
 'AI Agent，智能体，Spring AI，大语言模型',
 'https://example.com/ai-agent-guide');

-- 查询示例
-- SELECT * FROM rag_document ORDER BY update_time DESC;
-- SELECT * FROM rag_document WHERE doc_type = 'faq';
-- SELECT *, MATCH(title, content) AGAINST('RAG 技术' IN NATURAL LANGUAGE MODE) AS score FROM rag_document ORDER BY score DESC;
