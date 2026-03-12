package com.github.Sheven.shuiqi.service.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.Sheven.shuiqi.agent.FieldMappingAgent;
import com.github.Sheven.shuiqi.entity.FieldInfo;
import com.github.Sheven.shuiqi.entity.FieldMapping;
import com.github.Sheven.shuiqi.entity.FieldMappingResult;
import com.github.Sheven.shuiqi.mapper.FieldMappingMapper;
import com.github.Sheven.shuiqi.mcp.McpClient;
import com.github.Sheven.shuiqi.service.FieldMappingService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.Message;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 字段映射服务实现类
 */
@Slf4j
@Service
public class FieldMappingServiceImpl implements FieldMappingService {

    @Autowired
    private FieldMappingMapper fieldMappingMapper;

    @Autowired
    private ChatClient chatClient;

    @Autowired
    private FieldMappingAgent fieldMappingAgent;

    @Autowired
    private McpClient mcpClient;

    @Autowired
    private ObjectMapper objectMapper;

    @Value("${spring.ai.dashscope.chat.options.model:qwen-plus}")
    private String model;

    /**
     * 构建带 AI Agent 工具的 ChatClient
     */
    private ChatClient buildAgentChatClient() {
        // 使用注入的 ChatClient，它已经配置好了工具支持
        return chatClient;
    }

    @Override
    public FieldMappingResult processFieldMappings(List<String> chineseNames) {
        long startTime = System.currentTimeMillis();
        String requestId = UUID.randomUUID().toString();

        FieldMappingResult result = new FieldMappingResult();
        result.setRequestId(requestId);
        result.setInputChineseNames(chineseNames);
        result.setStatus("processing");

        try {
            List<FieldInfo> allMatchedFields = new ArrayList<>();
            List<String> unmatchedNames = new ArrayList<>();

            // 1. 批量查询数据库获取所有可能的字段映射
            List<FieldMapping> mappings = fieldMappingMapper.selectByChineseNames(chineseNames);

            // 2. 按中文名称分组
            Map<String, List<FieldMapping>> groupedByChinese = mappings.stream()
                    .collect(Collectors.groupingBy(FieldMapping::getChineseName));

            // 3. 对每个中文名称的英文字段进行 AI 去重判断
            for (String chineseName : chineseNames) {
                List<FieldMapping> fieldMappings = groupedByChinese.getOrDefault(chineseName, Collections.emptyList());

                if (fieldMappings.isEmpty()) {
                    unmatchedNames.add(chineseName);
                    log.warn("未找到中文字段 [{}] 的映射", chineseName);
                    continue;
                }

                // 使用 AI 进行字段去重
                List<FieldInfo> deduplicatedFields = deduplicateFieldsWithAI(chineseName, fieldMappings);
                allMatchedFields.addAll(deduplicatedFields);
            }

            // 4. 调用 MCP 服务获取详细的字段信息
            for (FieldInfo fieldInfo : allMatchedFields) {
                try {
                    FieldInfo detailedInfo = mcpClient.getFieldInfo(
                            fieldInfo.getEnglishName(),
                            fieldInfo.getTableName()
                    );
                    if (detailedInfo != null) {
                        // 合并信息
                        mergeFieldInfo(fieldInfo, detailedInfo);
                    }
                } catch (Exception e) {
                    log.error("调用 MCP 服务获取字段 [{}] 信息失败：{}",
                            fieldInfo.getEnglishName(), e.getMessage());
                }
            }

            result.setMatchedFields(allMatchedFields);
            result.setUnmatchedNames(unmatchedNames);
            result.setAiDeduplicationNote("已使用 AI 对同一中文名的多个英文字段进行语义分析和去重");
            result.setStatus("success");

        } catch (Exception e) {
            log.error("处理字段映射失败", e);
            result.setStatus("error");
            result.setErrorMessage(e.getMessage());
        }

        result.setProcessingTime(System.currentTimeMillis() - startTime);
        return result;
    }

    @Override
    public List<FieldInfo> queryFieldsWithDeduplication(String chineseName) {
        List<FieldMapping> mappings = fieldMappingMapper.selectByChineseName(chineseName);
        if (mappings.isEmpty()) {
            return Collections.emptyList();
        }
        return deduplicateFieldsWithAI(chineseName, mappings);
    }

    @Override
    public FieldInfo fetchFieldInfoFromMcp(String englishName, String tableName) {
        return mcpClient.getFieldInfo(englishName, tableName);
    }

    /**
     * 使用 AI 对字段进行去重
     */
    private List<FieldInfo> deduplicateFieldsWithAI(String chineseName, List<FieldMapping> mappings) {
        try {
            // 提取所有英文字段名
            List<String> englishNames = mappings.stream()
                    .map(FieldMapping::getEnglishName)
                    .distinct()
                    .collect(Collectors.toList());

            if (englishNames.size() <= 1) {
                // 只有一个或没有英文字段，直接返回
                return mappings.stream()
                        .map(this::convertToFieldInfo)
                        .collect(Collectors.toList());
            }

            // 构建 AI 提示词
            String promptText = buildDeduplicationPrompt(chineseName, englishNames, mappings);

            Message userMessage = new UserMessage(promptText);
            Prompt prompt = new Prompt(userMessage);

            // 调用 AI 进行去重判断
            String aiResponse = chatClient.prompt(prompt)
                    .call()
                    .content();

            log.info("AI 去重响应：{}", aiResponse);

            // 解析 AI 响应，获取推荐的英文字段名
            List<String> recommendedFields = parseAIResponse(aiResponse);

            // 筛选出推荐的字段
            Set<String> recommendedSet = new HashSet<>(recommendedFields);
            return mappings.stream()
                    .filter(m -> recommendedSet.contains(m.getEnglishName()))
                    .map(this::convertToFieldInfo)
                    .collect(Collectors.toList());

        } catch (Exception e) {
            log.error("AI 去重失败，返回所有字段：{}", e.getMessage());
            // AI 失败时返回所有字段
            return mappings.stream()
                    .map(this::convertToFieldInfo)
                    .collect(Collectors.toList());
        }
    }

    /**
     * 构建去重提示词
     */
    private String buildDeduplicationPrompt(String chineseName, List<String> englishNames, List<FieldMapping> mappings) {
        StringBuilder sb = new StringBuilder();
        sb.append("你是一个数据库字段映射专家。\n\n");
        sb.append("任务：对于中文名称「").append(chineseName).append("」，有以下候选英文字段名：\n");
        sb.append(String.join(", ", englishNames)).append("\n\n");
        sb.append("这些字段来自不同的表：\n");
        for (FieldMapping mapping : mappings) {
            sb.append("- ").append(mapping.getEnglishName())
                    .append(" (表：").append(mapping.getTableName())
                    .append(", 类型：").append(mapping.getFieldType())
                    .append(")\n");
        }
        sb.append("\n请分析这些英文字段名是否表示相同的语义。\n");
        sb.append("如果多个字段名表示相同的含义（如 user_id, uid, userId 都表示用户 ID），只保留最规范的一个。\n");
        sb.append("如果字段名虽然相似但实际含义不同（如 create_time 和 update_time），则都保留。\n\n");
        sb.append("请直接返回一个 JSON 数组，包含推荐保留的英文字段名，不要有其他说明。\n");
        sb.append("格式：[\"field1\", \"field2\", ...]");

        return sb.toString();
    }

    /**
     * 解析 AI 响应，提取推荐的字段名列表
     */
    private List<String> parseAIResponse(String aiResponse) {
        try {
            // 尝试从响应中提取 JSON 数组
            String jsonContent = aiResponse.trim();

            // 如果响应包含代码块标记，提取其中的内容
            if (jsonContent.contains("```")) {
                int start = jsonContent.indexOf("```") + 3;
                // 跳过可能的语言标识
                if (jsonContent.substring(start).startsWith("json")) {
                    start += 4;
                }
                int end = jsonContent.indexOf("```", start);
                jsonContent = jsonContent.substring(start, end).trim();
            }

            // 解析 JSON 数组
            JsonNode jsonNode = objectMapper.readTree(jsonContent);
            if (jsonNode.isArray()) {
                List<String> result = new ArrayList<>();
                for (JsonNode item : jsonNode) {
                    result.add(item.asText());
                }
                return result;
            }
        } catch (JsonProcessingException e) {
            log.warn("解析 AI 响应为 JSON 失败：{}", e.getMessage());
        }

        // 如果解析失败，返回空列表（将使用所有字段）
        return Collections.emptyList();
    }

    /**
     * 将 FieldMapping 转换为 FieldInfo
     */
    private FieldInfo convertToFieldInfo(FieldMapping mapping) {
        FieldInfo info = new FieldInfo();
        info.setChineseName(mapping.getChineseName());
        info.setEnglishName(mapping.getEnglishName());
        info.setFieldType(mapping.getFieldType());
        info.setFieldLength(mapping.getFieldLength());
        info.setNullable(mapping.getNullable());
        info.setDefaultValue(mapping.getDefaultValue());
        info.setDescription(mapping.getDescription());
        info.setTableName(mapping.getTableName());
        info.setDatabaseName(mapping.getDatabaseName());
        return info;
    }

    /**
     * 合并字段信息
     */
    private void mergeFieldInfo(FieldInfo target, FieldInfo source) {
        if (source.getDescription() != null && !source.getDescription().isEmpty()) {
            target.setDescription(source.getDescription());
        }
        if (source.getIndexInfo() != null) {
            target.setIndexInfo(source.getIndexInfo());
        }
        if (source.getConstraintInfo() != null) {
            target.setConstraintInfo(source.getConstraintInfo());
        }
        if (source.getSampleData() != null) {
            target.setSampleData(source.getSampleData());
        }
        if (source.getPrimaryKey() != null) {
            target.setPrimaryKey(source.getPrimaryKey());
        }
    }
}
