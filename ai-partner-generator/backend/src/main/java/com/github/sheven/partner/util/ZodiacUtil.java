package com.github.sheven.partner.util;

import java.util.Calendar;
import java.util.Date;

/**
 * 星座计算工具类
 */
public class ZodiacUtil {
    
    /**
     * 根据公历日期计算星座
     * @param year 年
     * @param month 月
     * @param day 日
     * @return 星座名称
     */
    public static String getZodiacSign(int year, int month, int day) {
        // 检查是否有效日期
        if (!isValidDate(year, month, day)) {
            return "未知";
        }
        
        // 星座日期分界点
        int[] dates = {20, 19, 21, 20, 21, 22, 23, 23, 23, 24, 22, 22};
        String[] signs = {"摩羯座", "水瓶座", "双鱼座", "白羊座", "金牛座", "双子座",
                         "巨蟹座", "狮子座", "处女座", "天秤座", "天蝎座", "射手座", "摩羯座"};
        
        // 如果日期小于分界点，则是上一个星座
        if (day < dates[month - 1]) {
            return signs[month - 1];
        } else {
            return signs[month];
        }
    }
    
    /**
     * 验证日期是否有效
     */
    private static boolean isValidDate(int year, int month, int day) {
        if (year < 1900 || year > Calendar.getInstance().get(Calendar.YEAR)) {
            return false;
        }
        if (month < 1 || month > 12) {
            return false;
        }
        
        Calendar cal = Calendar.getInstance();
        cal.set(year, month - 1, 1);
        int maxDay = cal.getActualMaximum(Calendar.DAY_OF_MONTH);
        
        return day >= 1 && day <= maxDay;
    }
    
    /**
     * 从日期字符串获取星座（格式：yyyy-MM-dd）
     */
    public static String getZodiacFromDate(String dateStr) {
        try {
            String[] parts = dateStr.split("-");
            int year = Integer.parseInt(parts[0]);
            int month = Integer.parseInt(parts[1]);
            int day = Integer.parseInt(parts[2]);
            return getZodiacSign(year, month, day);
        } catch (Exception e) {
            return "未知";
        }
    }
}
