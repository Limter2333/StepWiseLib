export interface Action {
  name: string;
  args: string[];
}

export function parseAction(text: string): Action | null {
  const lines = text.split("\n");
  for (const line of lines) {
    if (line.startsWith("行动：")) {
      const actionStr = line.replace("行动：", "").trim();
      // 格式：函数名(参数1, 参数2, ...)
      const match = actionStr.match(/^(\w+)\((.+)\)$/);
      if (match) {
        const name = match[1];
        // 简单解析参数，按逗号分割，并去除引号和空格
        const args = match[2].split(",").map(arg =>
          arg.trim().replace(/^["']|["']$/g, "") // 去除首尾引号
        );
        return { name, args };
      }
    }
  }
  return null;
}