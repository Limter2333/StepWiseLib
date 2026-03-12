import { HumanMessage, AIMessage, BaseMessage } from "@langchain/core/messages";
import { qwenLLM } from "./llm.js";
import { tools } from "./tools.js";
import { tool } from "@langchain/core/tools";

interface AgentState {
  messages: BaseMessage[];
  intermediateSteps: Array<{
    thought: string;
    action: string;
    observation: string;
  }>;
}

export class SimpleReActAgent {
  private llm: typeof qwenLLM;
  private tools: Map<string, ReturnType<typeof tool>>;
  private systemPrompt: string;

  constructor(llm: typeof qwenLLM, tools: ReturnType<typeof tool>[]) {
    this.llm = llm;
    this.tools = new Map(tools.map(t => [t.name, t]));
    
    // 构建系统提示词
    const toolsDesc = tools.map(t => 
      `- ${t.name}: ${t.description}，参数：${JSON.stringify(t.schema)}`
    ).join('\n');
    
    this.systemPrompt = `你是一个智能助手，可以通过思考和调用工具来回答问题。

可用工具：
${toolsDesc}

请按以下格式回复：
思考：你现在的推理...
行动：工具名称(参数)
观察：工具返回的结果
...（可重复多轮）
最终回答：对用户的最终回复

注意：
1. 如果不需要工具，直接给出最终回答
2. 工具参数必须是JSON格式
3. 每轮只输出一个行动`;
  }

  async invoke(userInput: string): Promise<string> {
    const state: AgentState = {
      messages: [new HumanMessage(userInput)],
      intermediateSteps: [],
    };

    const maxIterations = 5;
    for (let i = 0; i < maxIterations; i++) {
      // 构建当前对话上下文
      const messages = [
        { role: "system", content: this.systemPrompt },
        ...state.messages.map(m => ({
          role: m._getType() === "human" ? "user" : "assistant",
          content: m.content as string,
        })),
      ];

      // 调用千问API
      const response = await this.llm.invoke(messages);
      const content = response.content as string;
      
      console.log(`\n[第${i+1}轮] AI响应：\n${content}`);
      state.messages.push(new AIMessage(content));

      // 解析响应
      if (content.includes("最终回答：")) {
        const finalAnswer = content.split("最终回答：")[1].trim();
        return finalAnswer;
      }

      // 解析行动
      const actionMatch = content.match(/行动：(\w+)\(([^)]+)\)/);
      if (!actionMatch) {
        continue; // 没有行动，继续下一轮
      }

      const [, toolName, argsStr] = actionMatch;
      const tool = this.tools.get(toolName);
      
      if (!tool) {
        state.messages.push(new HumanMessage(`观察：未知工具${toolName}`));
        continue;
      }

      // 执行工具
      try {
        // 解析参数（简化版，实际应使用JSON.parse）
        const args = JSON.parse(`{${argsStr}}`);
        const observation = await tool.invoke(args);
        
        console.log(`[工具] ${toolName} 返回：${observation}`);
        state.messages.push(new HumanMessage(`观察：${observation}`));
        state.intermediateSteps.push({
          thought: content,
          action: toolName,
          observation,
        });
      } catch (error) {
        state.messages.push(new HumanMessage(`观察：工具执行错误 - ${error}`));
      }
    }

    return "已达到最大迭代次数，任务可能未完成。";
  }
}