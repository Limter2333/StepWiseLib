import { ChatOpenAI } from "@langchain/openai";
import dotenv from "dotenv";

dotenv.config();

// 千问API通过OpenAI兼容模式接入
export const qwenLLM = new ChatOpenAI({
  apiKey: process.env.QWEN_API_KEY,
  configuration: {
    baseURL: process.env.QWEN_BASE_URL,
  },
  model: process.env.QWEN_MODEL || "qwen-max",
  temperature: 0,
  maxTokens: 2000,
});

// 测试连接
export async function testConnection() {
  try {
    const response = await qwenLLM.invoke("你好，请简单介绍一下你自己");
    console.log("千问API连接成功：", response.content);
  } catch (error) {
    console.error("连接失败：", error);
  }
}