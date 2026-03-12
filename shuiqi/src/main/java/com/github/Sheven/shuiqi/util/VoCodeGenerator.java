package com.github.Sheven.shuiqi.util;

import com.github.Sheven.shuiqi.entity.FieldInfo;
import lombok.extern.slf4j.Slf4j;
import org.apache.velocity.VelocityContext;
import org.apache.velocity.app.VelocityEngine;
import org.apache.velocity.runtime.RuntimeConstants;
import org.apache.velocity.util.introspection.SecureUberspector;
import org.springframework.stereotype.Component;

import java.io.StringWriter;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;

/**
 * VO 代码生成器
 * 根据字段信息生成 Java VO 类代码
 */
@Slf4j
@Component
public class VoCodeGenerator {

    private final VelocityEngine velocityEngine;

    public VoCodeGenerator() {
        this.velocityEngine = initVelocityEngine();
    }

    /**
     * 初始化 Velocity 引擎
     */
    private VelocityEngine initVelocityEngine() {
        Properties props = new Properties();
        props.setProperty(RuntimeConstants.UBERSPECT_CLASSNAME, SecureUberspector.class.getName());
        props.setProperty(RuntimeConstants.RUNTIME_LOG_REFERENCE_LOG_INVALID, "false");
        
        VelocityEngine engine = new VelocityEngine();
        engine.init(props);
        return engine;
    }

    /**
     * 生成 VO 类代码
     * @param className 类名
     * @param fieldInfos 字段信息列表
     * @return VO 类代码
     */
    public String generateVoCode(String className, List<FieldInfo> fieldInfos) {
        try {
            VelocityContext context = new VelocityContext();
            context.put("className", className);
            context.put("packageName", "com.github.Sheven.shuiqi.vo");
            context.put("fields", convertToFieldModels(fieldInfos));
            context.put("date", java.time.LocalDate.now().toString());

            StringWriter writer = new StringWriter();
            velocityEngine.evaluate(context, writer, "voTemplate", getVoTemplate());

            return writer.toString();

        } catch (Exception e) {
            log.error("生成 VO 代码失败：{}", e.getMessage());
            // 如果 Velocity 模板渲染失败，使用手动拼接方式
            return generateVoCodeManual(className, fieldInfos);
        }
    }

    /**
     * 手动生成 VO 代码（备用方案）
     */
    private String generateVoCodeManual(String className, List<FieldInfo> fieldInfos) {
        StringBuilder sb = new StringBuilder();

        // 包声明
        sb.append("package com.github.Sheven.shuiqi.vo;\n\n");

        // 导入语句
        sb.append("import lombok.Data;\n");
        sb.append("import java.io.Serializable;\n");
        sb.append("import java.math.BigDecimal;\n");
        sb.append("import java.time.LocalDateTime;\n");
        sb.append("import java.util.Date;\n\n");

        // 类注释
        sb.append("/**\n");
        sb.append(" * ").append(className).append("\n");
        sb.append(" * 自动生成于 ").append(java.time.LocalDateTime.now()).append("\n");
        sb.append(" */\n");

        // 类声明
        sb.append("@Data\n");
        sb.append("public class ").append(className).append(" implements Serializable {\n\n");

        // 生成字段
        sb.append("    private static final long serialVersionUID = 1L;\n\n");

        for (FieldInfo info : fieldInfos) {
            String fieldName = toCamelCase(info.getEnglishName());
            String fieldType = mapJavaType(info.getFieldType());

            // 字段注释
            if (info.getDescription() != null && !info.getDescription().isEmpty()) {
                sb.append("    /**\n");
                sb.append("     * ").append(info.getDescription()).append("\n");
                sb.append("     */\n");
            }

            // 字段声明
            sb.append("    private ").append(fieldType).append(" ").append(fieldName).append(";\n\n");
        }

        sb.append("}\n");

        return sb.toString();
    }

    /**
     * 将数据库类型映射为 Java 类型
     */
    private String mapJavaType(String dbType) {
        if (dbType == null || dbType.isEmpty()) {
            return "String";
        }

        String type = dbType.toUpperCase();

        if (type.contains("INT") && !type.contains("POINT")) {
            if (type.contains("BIGINT")) {
                return "Long";
            } else if (type.contains("SMALLINT")) {
                return "Integer";
            } else if (type.contains("TINYINT")) {
                return "Integer";
            } else {
                return "Integer";
            }
        } else if (type.contains("DECIMAL") || type.contains("NUMERIC")) {
            return "BigDecimal";
        } else if (type.contains("FLOAT") || type.contains("DOUBLE")) {
            return "Double";
        } else if (type.contains("DATETIME") || type.contains("TIMESTAMP")) {
            return "LocalDateTime";
        } else if (type.contains("DATE")) {
            return "LocalDate";
        } else if (type.contains("TIME")) {
            return "LocalTime";
        } else if (type.contains("BOOLEAN") || type.contains("BIT")) {
            return "Boolean";
        } else if (type.contains("BLOB") || type.contains("BINARY")) {
            return "byte[]";
        } else {
            return "String";
        }
    }

    /**
     * 将蛇形命名转换为驼峰命名
     */
    private String toCamelCase(String snakeCase) {
        if (snakeCase == null || snakeCase.isEmpty()) {
            return "";
        }

        String[] parts = snakeCase.toLowerCase().split("_");
        StringBuilder result = new StringBuilder(parts[0]);

        for (int i = 1; i < parts.length; i++) {
            if (!parts[i].isEmpty()) {
                result.append(Character.toUpperCase(parts[i].charAt(0)))
                      .append(parts[i].substring(1));
            }
        }

        return result.toString();
    }

    /**
     * 转换为字段模型列表
     */
    private List<FieldModel> convertToFieldModels(List<FieldInfo> fieldInfos) {
        List<FieldModel> models = new ArrayList<>();
        for (FieldInfo info : fieldInfos) {
            FieldModel model = new FieldModel();
            model.setFieldName(toCamelCase(info.getEnglishName()));
            model.setFieldType(mapJavaType(info.getFieldType()));
            model.setOriginalName(info.getEnglishName());
            model.setDescription(info.getDescription());
            model.setDbType(info.getFieldType());
            models.add(model);
        }
        return models;
    }

    /**
     * 获取 VO 模板
     */
    private String getVoTemplate() {
        return "#set( $CLASS_NAME = $className )\n" +
               "#set( $PACKAGE_NAME = $packageName )\n" +
               "\n" +
               "package ${PACKAGE_NAME};\n" +
               "\n" +
               "import lombok.Data;\n" +
               "import java.io.Serializable;\n" +
               "import java.math.BigDecimal;\n" +
               "import java.time.LocalDateTime;\n" +
               "import java.util.Date;\n" +
               "\n" +
               "/**\n" +
               " * ${CLASS_NAME}\n" +
               " * 自动生成于 $date\n" +
               " */\n" +
               "@Data\n" +
               "public class ${CLASS_NAME} implements Serializable {\n" +
               "\n" +
               "    private static final long serialVersionUID = 1L;\n" +
               "\n" +
               "#foreach( $field in $fields )\n" +
               "#if( $field.description )\n" +
               "    /**\n" +
               "     * ${field.description}\n" +
               "     */\n" +
               "#end\n" +
               "    private ${field.fieldType} ${field.fieldName};\n" +
               "\n" +
               "#end\n" +
               "}\n";
    }

    /**
     * 字段模型类
     */
    public static class FieldModel {
        private String fieldName;
        private String fieldType;
        private String originalName;
        private String description;
        private String dbType;

        public String getFieldName() { return fieldName; }
        public void setFieldName(String fieldName) { this.fieldName = fieldName; }

        public String getFieldType() { return fieldType; }
        public void setFieldType(String fieldType) { this.fieldType = fieldType; }

        public String getOriginalName() { return originalName; }
        public void setOriginalName(String originalName) { this.originalName = originalName; }

        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }

        public String getDbType() { return dbType; }
        public void setDbType(String dbType) { this.dbType = dbType; }
    }
}
