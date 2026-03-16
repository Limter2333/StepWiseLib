package com.github.Sheven.shuiqi.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.Sheven.shuiqi.entity.FieldInfo;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import okhttp3.logging.HttpLoggingInterceptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.TimeUnit;
import com.fasterxml.jackson.core.type.TypeReference;

/**
 * MCP (Model Context Protocol) 客户端
 * 用于调用 MCP 服务获取字段详细信息
 */
@Slf4j
@Component
public class McpClient {

    @Value("${mcp.server.url:http://localhost:8080}")
    private String mcpServerUrl;

    @Value("${mcp.timeout:30000}")
    private int timeout;

    @Autowired
    private ObjectMapper objectMapper;

    private final OkHttpClient httpClient;

    public McpClient(@Value("${mcp.timeout:30000}") int timeout) {
        this.timeout = timeout;
        // 添加日志拦截器
        HttpLoggingInterceptor loggingInterceptor = new HttpLoggingInterceptor();
        loggingInterceptor.setLevel(HttpLoggingInterceptor.Level.BODY);
        
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(timeout, TimeUnit.MILLISECONDS)
                .readTimeout(timeout, TimeUnit.MILLISECONDS)
                .writeTimeout(timeout, TimeUnit.MILLISECONDS)
                .addInterceptor(loggingInterceptor)
                .build();
    }

    /**
     * 获取字段详细信息
     * @param fieldName 字段名
     * @param tableName 表名
     * @return 字段详细信息
     */
    public FieldInfo getFieldInfo(String fieldName, String tableName) {
        String url = String.format("%s/api/fields/%s/%s", mcpServerUrl, tableName, fieldName);

        Request request = new Request.Builder()
                .url(url)
                .get()
                .addHeader("Content-Type", "application/json")
                .addHeader("Accept", "application/json")
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                log.warn("MCP 服务返回错误：{} {}", response.code(), response.message());
                return null;
            }

            String responseBody = response.body().string();
            return parseFieldInfo(responseBody);

        } catch (IOException e) {
            log.error("调用 MCP 服务失败：{}", e.getMessage());
            throw new RuntimeException("调用 MCP 服务失败", e);
        }
    }

    /**
     * 批量获取字段信息
     * @param fields 字段列表 [tableName.fieldName]
     * @return 字段信息列表
     */
    public List<FieldInfo> batchGetFieldInfo(List<String> fields) {
        String url = String.format("%s/api/fields/batch", mcpServerUrl);

        JsonNode requestBody = objectMapper.createObjectNode()
                .set("fields", objectMapper.valueToTree(fields));

        RequestBody body = RequestBody.create(
                requestBody.toString(),
                MediaType.parse("application/json")
        );

        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .addHeader("Content-Type", "application/json")
                .addHeader("Accept", "application/json")
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                log.warn("MCP 批量查询返回错误：{} {}", response.code(), response.message());
                return Collections.emptyList();
            }

            String responseBody = response.body().string();
            JsonNode jsonNode = objectMapper.readTree(responseBody);

            return objectMapper.readValue(
                    jsonNode.get("data").toString(),
                    new TypeReference<List<FieldInfo>>() {}
            );

        } catch (IOException e) {
            log.error("批量调用 MCP 服务失败：{}", e.getMessage());
            return Collections.emptyList();
        }
    }

    /**
     * 解析字段信息 JSON
     */
    private FieldInfo parseFieldInfo(String json) throws IOException {
        JsonNode jsonNode = objectMapper.readTree(json);

        FieldInfo info = new FieldInfo();

        // 解析基本字段
        if (jsonNode.has("field_name")) {
            info.setEnglishName(jsonNode.get("field_name").asText());
        }
        if (jsonNode.has("field_type")) {
            info.setFieldType(jsonNode.get("field_type").asText());
        }
        if (jsonNode.has("field_length")) {
            info.setFieldLength(jsonNode.get("field_length").asInt());
        }
        if (jsonNode.has("description")) {
            info.setDescription(jsonNode.get("description").asText());
        }
        if (jsonNode.has("table_name")) {
            info.setTableName(jsonNode.get("table_name").asText());
        }
        if (jsonNode.has("database_name")) {
            info.setDatabaseName(jsonNode.get("database_name").asText());
        }
        if (jsonNode.has("is_primary_key")) {
            info.setPrimaryKey(jsonNode.get("is_primary_key").asBoolean());
        }
        if (jsonNode.has("is_nullable")) {
            info.setNullable(jsonNode.get("is_nullable").asBoolean());
        }
        if (jsonNode.has("default_value")) {
            info.setDefaultValue(jsonNode.get("default_value").asText());
        }
        if (jsonNode.has("index_info")) {
            info.setIndexInfo(jsonNode.get("index_info").asText());
        }
        if (jsonNode.has("constraint_info")) {
            info.setConstraintInfo(jsonNode.get("constraint_info").asText());
        }
        if (jsonNode.has("sample_data")) {
            info.setSampleData(jsonNode.get("sample_data").asText());
        }

        // 保存原始数据
        info.setRawData(jsonNode);

        return info;
    }
}
