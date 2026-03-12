# ShuiQi API 使用示例

## 基础信息

- **服务地址**: `http://localhost:8689`
- **API 前缀**: `/api/field-mapping`

---

## 1. 健康检查

```bash
curl -X GET http://localhost:8689/api/field-mapping/health
```

**响应:**
```
ShuiQi Field Mapping Service is running
```

---

## 2. 处理字段映射（主接口）

### 请求示例

```bash
curl -X POST http://localhost:8689/api/field-mapping/process \
  -H "Content-Type: application/json" \
  -d '{
    "chineseNames": ["用户 ID", "用户名", "创建时间", "状态"],
    "voClassName": "UserVO",
    "exportExcel": true,
    "generateVoCode": true,
    "excelFileName": "用户字段映射"
  }'
```

### 完整请求参数说明

```json
{
  "chineseNames": [           // 必填：中文字段名列表
    "用户 ID",
    "用户名",
    "创建时间",
    "状态"
  ],
  "voClassName": "UserVO",    // 可选：生成的 VO 类名，默认 FieldVO
  "exportExcel": true,        // 可选：是否导出 Excel，默认 true
  "generateVoCode": true,     // 可选：是否生成 VO 代码，默认 true
  "excelFileName": "用户字段映射" // 可选：Excel 文件名
}
```

### 响应示例

```json
{
  "requestId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "inputChineseNames": ["用户 ID", "用户名", "创建时间", "状态"],
  "matchedFields": [
    {
      "chineseName": "用户 ID",
      "englishName": "user_id",
      "tableName": "t_user",
      "databaseName": "field_mapping_db",
      "fieldType": "BIGINT",
      "fieldLength": 20,
      "primaryKey": true,
      "nullable": false,
      "defaultValue": null,
      "description": "用户唯一标识",
      "indexInfo": "PRIMARY KEY",
      "constraintInfo": "NOT NULL",
      "sampleData": "100001"
    },
    {
      "chineseName": "用户名",
      "englishName": "username",
      "tableName": "t_user",
      "databaseName": "field_mapping_db",
      "fieldType": "VARCHAR",
      "fieldLength": 50,
      "primaryKey": false,
      "nullable": false,
      "defaultValue": null,
      "description": "用户登录名",
      "indexInfo": "IDX_USERNAME",
      "constraintInfo": null,
      "sampleData": "zhangsan"
    },
    {
      "chineseName": "创建时间",
      "englishName": "create_time",
      "tableName": "t_user",
      "databaseName": "field_mapping_db",
      "fieldType": "DATETIME",
      "fieldLength": null,
      "primaryKey": false,
      "nullable": false,
      "defaultValue": "CURRENT_TIMESTAMP",
      "description": "记录创建时间",
      "indexInfo": null,
      "constraintInfo": null,
      "sampleData": "2026-03-12 10:30:00"
    },
    {
      "chineseName": "状态",
      "englishName": "status",
      "tableName": "t_user",
      "databaseName": "field_mapping_db",
      "fieldType": "TINYINT",
      "fieldLength": 4,
      "primaryKey": false,
      "nullable": false,
      "defaultValue": "1",
      "description": "记录状态（0:禁用，1:启用）",
      "indexInfo": null,
      "constraintInfo": null,
      "sampleData": "1"
    }
  ],
  "unmatchedNames": [],
  "aiDeduplicationNote": "已使用 AI 对同一中文名的多个英文字段进行语义分析和去重",
  "excelFilePath": "./exports/用户字段映射_20260312_143025.xlsx",
  "voCode": "package com.github.Sheven.shuiqi.vo;\n\nimport lombok.Data;...",
  "processingTime": 1523
}
```

---

## 3. 查询单个字段

```bash
curl -X GET http://localhost:8689/api/field-mapping/query/用户 ID
```

**响应:**
```json
[
  {
    "chineseName": "用户 ID",
    "englishName": "user_id",
    "tableName": "t_user",
    "fieldType": "BIGINT",
    "description": "用户唯一标识"
  },
  {
    "chineseName": "用户 ID",
    "englishName": "uid",
    "tableName": "t_user_profile",
    "fieldType": "BIGINT",
    "description": "用户唯一标识（别名）"
  }
]
```

---

## 4. 批量查询字段（简化版）

```bash
curl -X GET "http://localhost:8689/api/field-mapping/query?chineseNames=用户 ID，用户名，创建时间"
```

---

## 5. Postman 使用示例

### 配置步骤

1. 打开 Postman
2. 创建新请求
3. 设置请求方法为 `POST`
4. 输入 URL: `http://localhost:8689/api/field-mapping/process`
5. 在 Headers 中添加: `Content-Type: application/json`
6. 在 Body 中选择 `raw` 和 `JSON`
7. 输入请求体 JSON

### Postman Collection 导入

```json
{
  "info": {
    "name": "ShuiQi API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Process Field Mapping",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"chineseNames\": [\"用户 ID\", \"用户名\", \"创建时间\"],\n  \"voClassName\": \"UserVO\",\n  \"exportExcel\": true,\n  \"generateVoCode\": true\n}"
        },
        "url": {
          "raw": "http://localhost:8689/api/field-mapping/process",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8689",
          "path": ["api", "field-mapping", "process"]
        }
      }
    },
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": {
          "raw": "http://localhost:8689/api/field-mapping/health",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8689",
          "path": ["api", "field-mapping", "health"]
        }
      }
    }
  ]
}
```

---

## 6. Java 调用示例

```java
import java.net.http.*;
import java.net.URI;
import com.fasterxml.jackson.databind.ObjectMapper;

public class ShuiQiClient {
    
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        ObjectMapper mapper = new ObjectMapper();
        
        // 构建请求
        Map<String, Object> request = new HashMap<>();
        request.put("chineseNames", List.of("用户 ID", "用户名", "创建时间"));
        request.put("voClassName", "UserVO");
        request.put("exportExcel", true);
        request.put("generateVoCode", true);
        
        String requestBody = mapper.writeValueAsString(request);
        
        // 发送请求
        HttpRequest httpRequest = HttpRequest.newBuilder()
            .uri(URI.create("http://localhost:8689/api/field-mapping/process"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(requestBody))
            .build();
        
        HttpResponse<String> response = client.send(httpRequest, 
            HttpResponse.BodyHandlers.ofString());
        
        // 解析响应
        Map<String, Object> result = mapper.readValue(response.body(), Map.class);
        System.out.println("匹配字段：" + result.get("matchedFields"));
        System.out.println("VO 代码：" + result.get("voCode"));
        System.out.println("Excel 路径：" + result.get("excelFilePath"));
    }
}
```

---

## 7. Python 调用示例

```python
import requests
import json

# API 地址
API_URL = "http://localhost:8689/api/field-mapping/process"

# 请求数据
payload = {
    "chineseNames": ["用户 ID", "用户名", "创建时间", "状态"],
    "voClassName": "UserVO",
    "exportExcel": True,
    "generateVoCode": True,
    "excelFileName": "用户字段映射"
}

# 发送请求
response = requests.post(API_URL, json=payload)

# 解析响应
if response.status_code == 200:
    result = response.json()
    print(f"请求 ID: {result['requestId']}")
    print(f"状态：{result['status']}")
    print(f"匹配字段数：{len(result['matchedFields'])}")
    print(f"未匹配字段：{result['unmatchedNames']}")
    print(f"Excel 路径：{result['excelFilePath']}")
    print(f"处理时间：{result['processingTime']}ms")
    
    # 保存 VO 代码
    if result.get('voCode'):
        with open('UserVO.java', 'w', encoding='utf-8') as f:
            f.write(result['voCode'])
        print("VO 代码已保存到 UserVO.java")
else:
    print(f"请求失败：{response.status_code}")
    print(response.text)
```

---

## 错误处理

### 常见错误码

| HTTP 状态码 | 说明 | 解决方案 |
|-----------|------|---------|
| 400 | 请求参数错误 | 检查 `chineseNames` 是否为空 |
| 500 | 服务器内部错误 | 查看日志，检查数据库连接、AI 服务等 |
| 404 | 接口不存在 | 检查 URL 是否正确 |

### 错误响应示例

```json
{
  "requestId": "uuid-here",
  "status": "error",
  "errorMessage": "数据库连接失败",
  "processingTime": 150
}
```

---

## 性能优化建议

1. **批量处理**: 尽量一次性传入所有需要处理的字段名
2. **缓存结果**: 对于相同的查询，可以缓存结果避免重复计算
3. **异步处理**: 大批量字段可以使用异步方式处理
4. **调整 AI 参数**: 降低 `temperature` 可以提高响应速度

---

<div align="center">

**ShuiQi API** · Made with 💖  
[返回 README](README.md)

</div>
