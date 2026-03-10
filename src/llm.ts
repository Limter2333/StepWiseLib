import OpenAI from "openai";
import dotenv from "dotenv";

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function callLLM(messages: any[]): Promise<string> {
  const response = await openai.chat.completions.create({
    model: "gpt-4", // 或 "gpt-3.5-turbo"
    messages,
    temperature: 0,
  });
  return response.choices[0].message.content || "";
}