import { testConnection } from "./llm.js";
import { SimpleReActAgent } from "./reactAgent.js";
import { qwenLLM } from "./llm.js";
import { tools } from "./tools.js";
import { runAgent as runLangGraphAgent } from "./langgraphAgent.js";

async function main() {
  console.log("=== 测试千问API连接 ===");
  await testConnection();

  console.log("\n=== 测试简易ReAct Agent ===");
  const simpleAgent = new SimpleReActAgent(qwenLLM, tools);
  const result1 = await simpleAgent.invoke("北京天气怎么样？");
  console.log("最终回答：", result1);

  console.log("\n=== 测试LangGraph Agent ===");
  const result2 = await runLangGraphAgent("计算 123 + 456 等于多少？");
  console.log("最终回答：", result2);
}

main().catch(console.error);