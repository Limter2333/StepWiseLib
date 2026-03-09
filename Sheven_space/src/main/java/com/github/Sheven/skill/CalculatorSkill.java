package com.github.Sheven.skill;

import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

@Component
public class CalculatorSkill {

    @Tool(description = "执行基本的数学计算")
    public String calculate(
            @ToolParam(description = "第一个数字") double num1,
            @ToolParam(description = "第二个数字") double num2,
            @ToolParam(description = "运算符：+、-、*、/") String operator
    ) {
        return switch (operator) {
            case "+" -> String.format("%.2f", num1 + num2);
            case "-" -> String.format("%.2f", num1 - num2);
            case "*" -> String.format("%.2f", num1 * num2);
            case "/" -> {
                if (num2 == 0) {
                    yield "错误：除数不能为零";
                }
                yield String.format("%.2f", num1 / num2);
            }
            default -> "错误：不支持的运算符 " + operator;
        };
    }

    @Tool(description = "计算圆的面积")
    public String calculateCircleArea(
            @ToolParam(description = "圆的半径") double radius
    ) {
        if (radius <= 0) {
            return "错误：半径必须大于零";
        }
        double area = Math.PI * radius * radius;
        return String.format("半径为 %.2f 的圆面积为：%.2f", radius, area);
    }
}
