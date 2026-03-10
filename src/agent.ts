import { callLLM } from "./llm";
import { SYSTEM_PROMPT } from "./prompts";
import { tools } from "./tools";
import { parseAction } from "./parser";

export async function runAgent(userQuery: string): Promise<string> {
  const messages: any[] = [
    { role: "system", content: SYSTEM_PROMPT },
    { role: "user", content: userQuery },
  ];

  const maxSteps = 5;
  for (let step = 0; step < maxSteps; step++) {
    // 1. 调用 LLM
    const aiResponse = await callLLM(messages);
    console.log(`\n[Step ${step}] AI:\n${aiResponse}`);
    messages.push({ role: "assistant", content: aiResponse });

    // 2. 检查是否有最终回答
    if (aiResponse.includes("最终回答：")) {
      const finalAnswer = aiResponse.split("最终回答：")[1].trim();
      return finalAnswer;
    }

    // 3. 解析行动
    const action = parseAction(aiResponse);
    if (!action) {
      // 没有行动也没有最终回答，可能是模型出错了
      return "Agent 无法理解指令，请重试。";
    }

    // 4. 执行工具
    const tool = tools[action.name];
    if (!tool) {
      throw new Error(`未知工具：${action.name}`);
    }
    const observation = await tool(...action.args);
    console.log(`[工具] ${action.name} 返回：${observation}`);

    // 5. 将观察结果加入对话
    messages.push({ role: "user", content: `观察：${observation}` });
  }

  return "已达到最大步骤数，任务未完成。";
}