package com.github.Sheven.shuiqi.util;

import com.github.Sheven.shuiqi.entity.FieldInfo;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.streaming.SXSSFSheet;
import org.apache.poi.xssf.streaming.SXSSFWorkbook;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * Excel 导出工具类
 * 将字段信息结构化导出到 Excel 文件
 */
@Slf4j
@Component
public class ExcelExportUtil {

    @Value("${excel.export.path:./exports}")
    private String exportPath;

    /**
     * 导出字段信息到 Excel
     * @param fieldInfos 字段信息列表
     * @return 生成的 Excel 文件路径
     */
    public String exportFieldInfo(List<FieldInfo> fieldInfos) throws IOException {
        return exportFieldInfo(fieldInfos, "字段映射结果");
    }

    /**
     * 导出字段信息到 Excel（指定文件名）
     * @param fieldInfos 字段信息列表
     * @param fileName 文件名（不含扩展名）
     * @return 生成的 Excel 文件路径
     */
    public String exportFieldInfo(List<FieldInfo> fieldInfos, String fileName) throws IOException {
        // 确保导出目录存在
        File directory = new File(exportPath);
        if (!directory.exists()) {
            directory.mkdirs();
        }

        // 生成文件名（带时间戳）
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
        String fullFileName = fileName + "_" + timestamp + ".xlsx";
        String filePath = new File(exportPath, fullFileName).getAbsolutePath();

        try (Workbook workbook = new SXSSFWorkbook(100)) {
            // 创建工作表
            SXSSFSheet sheet =  (SXSSFSheet)workbook.createSheet("字段信息");

            // 创建表头
            createHeader(sheet);

            // 跟踪所有需要自动调整列宽的列（0-13 共 14 列）
            trackColumnsForAutoResize(sheet, 14);

            // 填充数据
            fillData(sheet, fieldInfos);

            // 自动调整列宽
            autoSizeColumns(sheet);

            // 写入文件
            try (FileOutputStream fos = new FileOutputStream(filePath)) {
                workbook.write(fos);
            }

            log.info("Excel 文件导出成功：{}", filePath);
            return filePath;
        }
    }

    /**
     * 创建表头
     */
    private void createHeader(Sheet sheet) {
        Row headerRow = sheet.createRow(0);

        String[] headers = {
                "序号", "中文字段名", "英文字段名", "表名", "数据库名",
                "字段类型", "长度", "主键", "可空", "默认值",
                "描述", "索引信息", "约束信息", "示例数据"
        };

        CellStyle headerStyle = createHeaderStyle(sheet.getWorkbook());

        for (int i = 0; i < headers.length; i++) {
            Cell cell = headerRow.createCell(i);
            cell.setCellValue(headers[i]);
            cell.setCellStyle(headerStyle);
        }
    }

    /**
     * 跟踪需要自动调整大小的列
     * @param sheet 工作表
     * @param columnCount 列数
     */
    private void trackColumnsForAutoResize(SXSSFSheet sheet, int columnCount) {
        // 方法 1：跟踪所有列（推荐）
        sheet.trackAllColumnsForAutoSizing();
    }

    /**
     * 创建表头样式
     */
    private CellStyle createHeaderStyle(Workbook workbook) {
        CellStyle style = workbook.createCellStyle();
        Font font = workbook.createFont();
        font.setBold(true);
        font.setFontHeightInPoints((short) 11);
        style.setFont(font);
        style.setFillForegroundColor(IndexedColors.GREY_25_PERCENT.getIndex());
        style.setFillPattern(FillPatternType.SOLID_FOREGROUND);
        style.setBorderBottom(BorderStyle.THIN);
        style.setBorderTop(BorderStyle.THIN);
        style.setBorderLeft(BorderStyle.THIN);
        style.setBorderRight(BorderStyle.THIN);
        style.setAlignment(HorizontalAlignment.CENTER);
        style.setVerticalAlignment(VerticalAlignment.CENTER);
        style.setWrapText(true);
        return style;
    }

    /**
     * 填充数据
     */
    private void fillData(Sheet sheet, List<FieldInfo> fieldInfos) {
        CellStyle dataStyle = createDataStyle(sheet.getWorkbook());
        CellStyle centerStyle = createCenterStyle(sheet.getWorkbook());

        int rowNum = 1;
        for (int i = 0; i < fieldInfos.size(); i++) {
            FieldInfo info = fieldInfos.get(i);
            Row row = sheet.createRow(rowNum++);

            createCell(row, 0, i + 1, centerStyle);
            createCell(row, 1, info.getChineseName(), dataStyle);
            createCell(row, 2, info.getEnglishName(), dataStyle);
            createCell(row, 3, info.getTableName(), dataStyle);
            createCell(row, 4, info.getDatabaseName(), dataStyle);
            createCell(row, 5, info.getFieldType(), dataStyle);
            createCell(row, 6, info.getFieldLength() != null ? info.getFieldLength() : "-", centerStyle);
            createCell(row, 7, info.getPrimaryKey() != null ? (info.getPrimaryKey() ? "是" : "否") : "-", centerStyle);
            createCell(row, 8, info.getNullable() != null ? (info.getNullable() ? "是" : "否") : "-", centerStyle);
            createCell(row, 9, info.getDefaultValue() != null ? info.getDefaultValue() : "-", dataStyle);
            createCell(row, 10, info.getDescription() != null ? info.getDescription() : "-", dataStyle);
            createCell(row, 11, info.getIndexInfo() != null ? info.getIndexInfo() : "-", dataStyle);
            createCell(row, 12, info.getConstraintInfo() != null ? info.getConstraintInfo() : "-", dataStyle);
            createCell(row, 13, info.getSampleData() != null ? info.getSampleData() : "-", dataStyle);
        }

        // 冻结首行
        sheet.createFreezePane(0, 1);
    }

    /**
     * 创建单元格
     */
    private void createCell(Row row, int column, Object value, CellStyle style) {
        Cell cell = row.createCell(column);
        if (value instanceof String) {
            cell.setCellValue((String) value);
        } else if (value instanceof Integer) {
            cell.setCellValue((Integer) value);
        } else if (value instanceof Boolean) {
            cell.setCellValue((Boolean) value);
        } else {
            cell.setCellValue(value != null ? value.toString() : "");
        }
        cell.setCellStyle(style);
    }

    /**
     * 创建数据样式
     */
    private CellStyle createDataStyle(Workbook workbook) {
        CellStyle style = workbook.createCellStyle();
        style.setBorderBottom(BorderStyle.THIN);
        style.setBorderTop(BorderStyle.THIN);
        style.setBorderLeft(BorderStyle.THIN);
        style.setBorderRight(BorderStyle.THIN);
        style.setVerticalAlignment(VerticalAlignment.CENTER);
        style.setWrapText(true);
        return style;
    }

    /**
     * 创建居中样式
     */
    private CellStyle createCenterStyle(Workbook workbook) {
        CellStyle style = createDataStyle(workbook);
        style.setAlignment(HorizontalAlignment.CENTER);
        return style;
    }

    /**
     * 自动调整列宽
     */
    private void autoSizeColumns(Sheet sheet) {
        for (int i = 0; i < 14; i++) {
            sheet.autoSizeColumn(i);
            // 设置最大列宽，避免过宽
            int maxWidth = 50;
            int currentWidth = sheet.getColumnWidth(i);
            if (currentWidth > maxWidth * 256) {
                sheet.setColumnWidth(i, maxWidth * 256);
            }
        }
    }
}
