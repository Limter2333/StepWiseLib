package com.github.Sheven.skill;


import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Component
public class DateTimeSkill {

    @Tool(description = "获取当前日期和时间")
    public String getCurrentDateTime() {
        LocalDateTime now = LocalDateTime.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        return "当前日期和时间：" + now.format(formatter);
    }

    @Tool(description = "获取当前日期")
    public String getCurrentDate() {
        LocalDate today = LocalDate.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy 年 MM 月 dd 日 EEEE");
        return "今天：" + today.format(formatter);
    }

    @Tool(description = "计算两个日期之间的天数")
    public String daysBetweenDates(
            @ToolParam(description = "起始日期，格式：yyyy-MM-dd") String startDate,
            @ToolParam(description = "结束日期，格式：yyyy-MM-dd") String endDate
    ) {
        try {
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
            LocalDate start = LocalDate.parse(startDate, formatter);
            LocalDate end = LocalDate.parse(endDate, formatter);
            long days = java.time.temporal.ChronoUnit.DAYS.between(start, end);
            return String.format("从 %s 到 %s 相差 %d 天", startDate, endDate, Math.abs(days));
        } catch (Exception e) {
            return "错误：日期格式不正确，请使用 yyyy-MM-dd 格式";
        }
    }
}
