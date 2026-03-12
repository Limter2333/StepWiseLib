import { tool } from "@langchain/core/tools";
import { z } from "zod";

// 示例工具1：计算器
export const calculatorTool = tool(
  async ({ expression }) => {
    try {
      // 安全地计算表达式（仅作示例，实际应使用math.js等安全库）
      const result = eval(expression);
      return `计算结果：${result}`;
    } catch (error) {
      return `计算错误：${error}`;
    }
  },
  {
    name: "calculator",
    description: "计算数学表达式，如'2+2'、'3*5'等",
    schema: z.object({
      expression: z.string().describe("要计算的数学表达式"),
    }),
  }
);

// 示例工具2：天气查询（模拟）
export const weatherTool = tool(
  async ({ city }) => {
    // 这里可以接入真实天气API
    const weathers: Record<string, string> = {
      北京: "晴天，25℃",
      上海: "多云，22℃",
      广州: "小雨，28℃",
    };
    return `${city}的天气：${weathers[city] || "暂无数据"}`;
  },
  {
    name: "weather",
    description: "查询指定城市的天气",
    schema: z.object({
      city: z.string().describe("城市名称，如'北京'"),
    }),
  }
);

// 工具注册表
export const tools = [calculatorTool, weatherTool];