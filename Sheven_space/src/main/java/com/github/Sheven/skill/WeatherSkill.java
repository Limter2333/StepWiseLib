package com.github.Sheven.skill;

import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

@Component
public class WeatherSkill {

    @Tool(description = "查询指定城市的天气信息")
    public String queryWeather(
            @ToolParam(description = "城市名称，如：北京、上海") String city
    ) {
        // 模拟天气数据，实际项目中可以调用天气 API
        return switch (city) {
            case "北京" -> "北京今天晴朗，温度 25°C，空气质量优";
            case "上海" -> "上海今天多云，温度 28°C，空气质量良好";
            case "广州" -> "广州今天有雨，温度 30°C，湿度较大";
            case "深圳" -> "深圳今天晴朗，温度 32°C，适宜户外活动";
            default -> "抱歉，暂时无法查询到 " + city + " 的天气信息";
        };
    }
}
