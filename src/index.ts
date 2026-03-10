import { runAgent } from "./agent";

async function main() {
  const query = "明天（2025-04-11）有什么安排？";
  const result = await runAgent(query);
  console.log("\n最终回答：", result);
}

main().catch(console.error);