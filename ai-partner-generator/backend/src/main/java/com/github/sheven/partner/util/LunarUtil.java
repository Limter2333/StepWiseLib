package com.github.sheven.partner.util;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;

/**
 * 农历工具类（简化版）
 * 实际项目中建议使用成熟的农历库如 lunar-calendar
 */
public class LunarUtil {
    
    /**
     * 将公历转换为农历（简化实现）
     * 实际生产环境建议使用完整的农历算法库
     */
    public static String solarToLunar(String solarDate) {
        try {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
            Date date = sdf.parse(solarDate);
            Calendar calendar = Calendar.getInstance();
            calendar.setTime(date);
            
            // 这里是一个简化的示例
            // 实际应该使用完整的农历转换算法
            int year = calendar.get(Calendar.YEAR);
            int month = calendar.get(Calendar.MONTH) + 1;
            int day = calendar.get(Calendar.DAY_OF_MONTH);
            
            // 返回格式：农历 YYYY 年 MM 月 DD 日
            return getLunarYear(year) + "年" + getLunarMonth(month) + "月" + getLunarDay(day);
        } catch (Exception e) {
            return solarDate;
        }
    }
    
    /**
     * 获取农历年份天干地支
     */
    private static String getLunarYear(int year) {
        String[] heavenlyStems = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"};
        String[] earthlyBranches = {"子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"};
        
        int stemIndex = (year - 4) % 10;
        int branchIndex = (year - 4) % 12;
        
        if (stemIndex < 0) stemIndex += 10;
        if (branchIndex < 0) branchIndex += 12;
        
        return heavenlyStems[stemIndex] + earthlyBranches[branchIndex];
    }
    
    /**
     * 获取农历月份（简化）
     */
    private static String getLunarMonth(int month) {
        String[] months = {"正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"};
        return months[month - 1];
    }
    
    /**
     * 获取农历日期（简化）
     */
    private static String getLunarDay(int day) {
        if (day >= 1 && day <= 10) {
            return "初" + toChineseNumber(day);
        } else if (day >= 11 && day <= 20) {
            return "十" + toChineseNumber(day - 10);
        } else if (day >= 21 && day <= 30) {
            return "廿" + toChineseNumber(day - 20);
        }
        return String.valueOf(day);
    }
    
    /**
     * 数字转中文
     */
    private static String toChineseNumber(int num) {
        String[] nums = {"", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"};
        return nums[num];
    }
}
