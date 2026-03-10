type Weather = "sunny" | "rainy" | "snowy";

// 模拟感知函数
async function senseWeather(city: string): Promise<Weather> {
  // 这里可以替换为真实的天气 API 调用
  const weathers: Weather[] = ["sunny", "rainy", "snowy"];
  return weathers[Math.floor(Math.random() * weathers.length)];
}

// 基于规则的思考函数
function think(weather: Weather): string {
  switch (weather) {
    case "rainy":
      return "带伞";
    case "snowy":
      return "穿羽绒服";
    case "sunny":
      return "戴太阳镜";
  }
}

// 行动函数
function act(decision: string): void {
  console.log(`建议：${decision}`);
}

// 主循环
async function runAgent() {
  while (true) {
    const weather = await senseWeather("北京");
    const decision = think(weather);
    act(decision);
    await new Promise(resolve => setTimeout(resolve, 5000)); // 每5秒执行一次
  }
}

// runAgent();