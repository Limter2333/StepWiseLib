// 工具函数的类型：接收任意参数，返回 Promise<string>
type Tool = (...args: any[]) => Promise<string>;

// 示例工具：查询日历
export async function checkCalendar(date: string): Promise<string> {
  // 模拟日历数据
  const events: Record<string, string> = {
    "2025-04-11": "项目评审会",
    "2025-04-12": "团队同步",
  };
  return events[date] || "无会议";
}

// 示例工具：添加事件
export async function addEvent(date: string, event: string): Promise<string> {
  console.log(`[工具调用] 添加事件：${date} - ${event}`);
  // 实际可写入数据库
  return `已成功添加事件：${event} 在 ${date}`;
}

// 工具注册表
export const tools: Record<string, Tool> = {
  checkCalendar,
  addEvent,
};