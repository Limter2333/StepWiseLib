import dotenv from "dotenv";
dotenv.config();

export const config = {
  DASHSCOPE_API_KEY: process.env.DASHSCOPE_API_KEY || "",
  MODEL: "qwen-turbo", // 通义千问轻量版，也可换qwen-plus/qwen-max
};