package com.github.Sheven.shuiqi.agent;

import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

/**
 * 字段映射 Agent
 * 提供 AI 工具方法用于字段名称的智能判断和去重
 */
@Component
public class FieldMappingAgent {

    /**
     * 判断同一中文名称对应的多个英文字段是否重复
     * @param chineseName 中文字段名
     * @param englishNames 英文字段名列表（JSON 数组格式）
     * @return 去重后的英文字段名（JSON 数组格式）
     */
    @Tool(description = "判断同一中文名称对应的多个英文字段是否重复，返回不重复的英文字段列表")
    public String deduplicateFields(
            @ToolParam(description = "中文字段名") String chineseName,
            @ToolParam(description = "英文字段名列表，JSON 数组格式，如 [\"user_id\",\"uid\",\"userId\"]") String englishNames
    ) {
        // 这个方法由 AI 自动调用，实际逻辑由 AI 模型处理
        // AI 会分析这些英文字段名是否表示相同的含义
        // 如果含义相同则保留一个，如果含义不同则都保留
        return englishNames;
    }

    /**
     * 选择最合适的英文字段名
     * @param chineseName 中文字段名
     * @param candidates 候选英文字段名列表（JSON 数组格式）
     * @return 最合适的英文字段名
     */
    @Tool(description = "从候选英文字段名中选择最合适的一个")
    public String selectBestFieldName(
            @ToolParam(description = "中文字段名") String chineseName,
            @ToolParam(description = "候选英文字段名列表，JSON 数组格式") String candidates
    ) {
        // AI 会根据命名规范、通用习惯等选择最合适的字段名
        return candidates;
    }

    /**
     * 验证字段映射的合理性
     * @param chineseName 中文字段名
     * @param englishName 英文字段名
     * @param context 上下文信息（表名、字段类型等）
     * @return 验证结果（合理/不合理及原因）
     */
    @Tool(description = "验证中文名到英文名的映射是否合理")
    public String validateFieldMapping(
            @ToolParam(description = "中文字段名") String chineseName,
            @ToolParam(description = "英文字段名") String englishName,
            @ToolParam(description = "上下文信息，JSON 格式，包含表名、字段类型等") String context
    ) {
        // AI 会验证映射是否符合业务语义和技术规范
        return "valid";
    }
}
