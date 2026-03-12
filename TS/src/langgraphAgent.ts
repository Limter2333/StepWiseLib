import { StateGraph, MessagesAnnotation, END } from "@langchain/langgraph";
import { ToolNode } from "@langchain/langgraph/prebuilt";
import { qwenLLM } from "./llm.js";
import { tools } from "./tools.js";

// 绑定工具到模型
const llmWithTools = qwenLLM.bindTools(tools);

// 定义Agent节点：模型决定下一步
async function agentNode(state: typeof MessagesAnnotation.State) {
  const result = await llmWithTools.invoke(state.messages);
  return { messages: [result] };
}

// 定义路由函数：决定是调用工具还是结束
function shouldContinue(state: typeof MessagesAnnotation.State) {
  const messages = state.messages;
  const lastMessage = messages[messages.length - 1];

  // 如果模型请求调用工具，则进入tools节点
  if (lastMessage._getType() === "ai" && lastMessage.tool_calls?.length) {
    return "tools";
  }
  // 否则结束
  return END;
}

// 构建状态图
const workflow = new StateGraph(MessagesAnnotation)
  .addNode("agent", agentNode)
  .addNode("tools", new ToolNode(tools))
  .addEdge("__start__", "agent")
  .addConditionalEdges("agent", shouldContinue)
  .addEdge("tools", "agent");

// 编译为可执行应用
export const agentApp = workflow.compile();

// 使用示例
export async function runAgent(question: string) {
  const result = await agentApp.invoke({
    messages: [{ role: "user", content: question }],
  });
  
  const lastMessage = result.messages[result.messages.length - 1];
  return lastMessage.content;
}