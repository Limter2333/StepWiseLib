# ShuiQi

> **字段映射 Agent 服务** - 智能匹配中文字段到英文字段，自动生成 VO 代码  
> 基于 Spring AI Alibaba + MyBatis-Plus + Apache POI

---

## 📦 项目概述

**ShuiQi** 是一个智能字段映射 Java Agent 项目，主要功能包括：

1. **中文转英文字段映射**：接收中文字段名，从数据库查询对应的英文字段
2. **AI 智能去重**：同一中文名可能对应多个英文字段，使用 AI 判断语义，去除重复项
3. **MCP 服务集成**：调用 MCP 服务获取字段的详细信息（类型、约束、索引等）
4. **Excel 结构化导出**：将字段信息导出为格式化的 Excel 文件
5. **VO 代码自动生成**：根据字段信息自动生成 Java VO 类代码

---

## 🏗️ 技术架构

### 核心技术栈
- ☕ **Java 17**
- 🍃 **Spring Boot 3.5.8**
- 🤖 **Spring AI Alibaba** (通义千问 Qwen)
- 💾 **MyBatis-Plus** (数据访问层)
- 📊 **Apache POI + EasyExcel** (Excel 操作)
- 🏗️ **Apache Velocity** (代码生成模板引擎)
- 🔌 **OkHttp** (MCP 服务调用)

### 项目结构
```
ShuiQi/
├── src/main/java/com/github/Sheven/shuiqi/
│   ├── ShuiQiApplication.java       # 主启动类
│   ├── agent/                       # AI Agent 工具类
│   │   └── FieldMappingAgent.java
│   ├── config/                      # 配置类
│   │   └── DatabaseConfig.java
│   ├── controller/                  # REST 控制器
│   │   └── FieldMappingController.java
│   ├── dto/                         # 数据传输对象
│   │   ├── FieldMappingRequest.java
│   │   └── FieldMappingResponse.java
│   ├── entity/                      # 实体类
│   │   ├── FieldMapping.java
│   │   ├── FieldInfo.java
│   │   └── FieldMappingResult.java
│   ├── mapper/                      # MyBatis Mapper
│   │   └── FieldMappingMapper.java
│   ├── mcp/                         # MCP 客户端
│   │   └── McpClient.java
│   ├── service/                     # 业务服务层
│   │   ├── FieldMappingService.java
│   │   └── impl/
│   │       └── FieldMappingServiceImpl.java
│   └── util/                        # 工具类
│       ├── ExcelExportUtil.java
│       └── VoCodeGenerator.java
├── src/main/resources/
│   ├── application.yml              # 应用配置
│   ├── mapper/
│   │   └── FieldMappingMapper.xml   # MyBatis XML
│   └── schema.sql                   # 数据库初始化脚本
├── pom.xml                          # Maven 配置
├── .env.example                     # 环境变量示例
└── README.md                        # 项目说明
```

---

## ⚙️ 快速开始

### 1️⃣ 环境准备

- **JDK 17+**
- **Maven 3.6+**
- **MySQL 8.0+**
- **DashScope API Key** (通义千问)

### 2️⃣ 克隆项目

```bash
cd "d:\projectFile\StepWiseLib - 副本\ShuiQi"
```

### 3️⃣ 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
# DashScope API 配置
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_MODEL=qwen-plus
DASHSCOPE_TEMPERATURE=0.3
DASHSCOPE_MAX_TOKENS=2048

# MySQL 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=field_mapping_db
DB_USERNAME=root
DB_PASSWORD=root

# MCP 服务配置
MCP_SERVER_URL=http://localhost:8080
MCP_TIMEOUT=30000

# Excel 导出路径
EXCEL_EXPORT_PATH=./exports
```

### 4️⃣ 初始化数据库

```bash
mysql -u root -p < src/main/resources/schema.sql
```

### 5️⃣ 编译项目

```bash
mvn clean package -DskipTests
```

### 6️⃣ 启动应用

**方式一：Maven 直接运行**
```bash
mvn spring-boot:run
```

**方式二：运行 JAR**
```bash
java -jar target/ShuiQi-1.0.0.jar
```

启动成功后，服务运行在 `http://localhost:8689`

---

## 📡 API 接口

### 1. 健康检查

```http
GET /api/field-mapping/health
```

**响应示例：**
```
ShuiQi Field Mapping Service is running
```

---

### 2. 处理字段映射（主接口）

```http
POST /api/field-mapping/process
Content-Type: application/json
```

**请求体：**
```json
{
  "chineseNames": ["用户 ID", "用户名", "创建时间", "状态"],
  "voClassName": "UserVO",
  "exportExcel": true,
  "generateVoCode": true,
  "excelFileName": "用户字段映射"
}
```

**响应示例：**
```json
{
  "requestId": "uuid-here",
  "status": "success",
  "inputChineseNames": ["用户 ID", "用户名", "创建时间", "状态"],
  "matchedFields": [
    {
      "chineseName": "用户 ID",
      "englishName": "user_id",
      "tableName": "t_user",
      "fieldType": "BIGINT",
      "description": "用户唯一标识"
    }
    // ... 更多字段
  ],
  "unmatchedNames": [],
  "aiDeduplicationNote": "已使用 AI 对同一中文名的多个英文字段进行语义分析和去重",
  "excelFilePath": "./exports/用户字段映射_20260312_143025.xlsx",
  "voCode": "package com.github.Sheven.shuiqi.vo;\n\nimport lombok.Data;...",
  "processingTime": 1523
}
```

---

### 3. 查询单个字段

```http
GET /api/field-mapping/query/{chineseName}
```

**示例：**
```http
GET /api/field-mapping/query/用户 ID
```

---

### 4. 批量查询字段

```http
GET /api/field-mapping/query?chineseNames=用户 ID，用户名，创建时间
```

---

## 🤖 AI 去重逻辑

当同一中文名对应多个英文字段时（如"用户 ID"对应 `user_id`, `uid`, `user_uuid`），系统会：

1. **收集候选字段**：从数据库查询所有匹配的英文字段
2. **构建 AI 提示词**：包含中文字段名、候选英文字段、表信息等
3. **调用 AI 分析**：AI 判断这些英文字段是否表示相同语义
4. **去重筛选**：保留语义不重复的字段
5. **返回结果**：输出去重后的字段列表

**AI 提示词示例：**
```
你是一个数据库字段映射专家。

任务：对于中文名称「用户 ID」，有以下候选英文字段名：
user_id, uid, user_uuid

这些字段来自不同的表：
- user_id (表：t_user, 类型：BIGINT)
- uid (表：t_user_profile, 类型：BIGINT)
- user_uuid (表：t_user_account, 类型：VARCHAR)

请分析这些英文字段名是否表示相同的语义。
如果多个字段名表示相同的含义（如 user_id, uid, userId 都表示用户 ID），只保留最规范的一个。
如果字段名虽然相似但实际含义不同（如 create_time 和 update_time），则都保留。

请直接返回一个 JSON 数组，包含推荐保留的英文字段名，不要有其他说明。
格式：["field1", "field2", ...]
```

---

## 📊 Excel 导出示例

导出的 Excel 文件包含以下列：

| 序号 | 中文字段名 | 英文字段名 | 表名 | 数据库名 | 字段类型 | 长度 | 主键 | 可空 | 默认值 | 描述 | 索引信息 | 约束信息 | 示例数据 |
|------|-----------|-----------|------|---------|---------|------|------|------|--------|------|---------|---------|---------|

---

## 💻 VO 代码生成示例

**输入：**
```json
{
  "chineseNames": ["用户 ID", "用户名", "邮箱", "创建时间"]
}
```

**生成的 VO 代码：**
```java
package com.github.Sheven.shuiqi.vo;

import lombok.Data;
import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * UserVO
 * 自动生成于 2026-03-12
 */
@Data
public class UserVO implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 用户唯一标识
     */
    private Long userId;

    /**
     * 用户登录名
     */
    private String username;

    /**
     * 用户邮箱地址
     */
    private String email;

    /**
     * 记录创建时间
     */
    private LocalDateTime createTime;
}
```

---

## 🔧 MCP 服务集成

项目通过 `McpClient` 调用外部 MCP 服务获取字段详细信息。

**MCP 服务 API 约定：**

```http
GET /api/fields/{tableName}/{fieldName}
```

**响应格式：**
```json
{
  "field_name": "user_id",
  "field_type": "BIGINT",
  "field_length": 20,
  "table_name": "t_user",
  "database_name": "field_mapping_db",
  "is_primary_key": true,
  "is_nullable": false,
  "default_value": null,
  "description": "用户唯一标识",
  "index_info": "PRIMARY KEY",
  "constraint_info": "NOT NULL",
  "sample_data": "100001"
}
```

如果没有 MCP 服务，可以：
1. 部署一个 mock 服务
2. 或者在 `FieldMappingServiceImpl` 中跳过 MCP 调用步骤

---

## 🛠️ 开发指南

### 添加新的字段映射

在数据库中插入新记录：
```sql
INSERT INTO field_mapping (chinese_name, english_name, field_type, description, table_name)
VALUES ('订单号', 'order_no', 'VARCHAR', '订单编号', 't_order');
```

### 自定义 AI 模型参数

修改 `.env` 文件：
```bash
DASHSCOPE_MODEL=qwen-max        # 使用更高性能的模型
DASHSCOPE_TEMPERATURE=0.5       # 调整创造性
```

### 扩展 Excel 导出列

修改 `ExcelExportUtil.java` 中的 `createHeader()` 方法。

---

## 🐛 常见问题

### 1. API Key 无效
确保 `.env` 文件中的 `DASHSCOPE_API_KEY` 配置正确。

### 2. 数据库连接失败
检查 MySQL 服务是否启动，数据库 `field_mapping_db` 是否已创建。

### 3. MCP 服务调用失败
- 检查 `MCP_SERVER_URL` 配置
- 确认 MCP 服务已启动
- 查看日志了解详细错误信息

### 4. Excel 导出路径不存在
确保 `EXCEL_EXPORT_PATH` 目录存在且有写权限。

---

## 📝 最佳实践

1. **字段命名规范**：建议使用统一的命名规范（如下划线命名法）
2. **数据库索引**：为常用查询字段建立索引
3. **AI 温度调整**：生产环境建议使用较低的温度值（0.2-0.3）
4. **批量处理**：大批量字段映射建议分批处理

---

## 📞 技术支持

- 📖 Spring AI Alibaba 文档：https://java2ai.com/
- 🐛 问题反馈：在项目 Issues 中提交

---

<div align="center">

**ShuiQi** · Made with 💖 and ☕  
*让字段映射更智能！* 🚀

[参考项目：Sheven_space](../Sheven_space/README.md)

</div>
