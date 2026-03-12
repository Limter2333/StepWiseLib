package com.github.Sheven.shuiqi.controller;

import com.github.Sheven.shuiqi.dto.FieldMappingRequest;
import com.github.Sheven.shuiqi.dto.FieldMappingResponse;
import com.github.Sheven.shuiqi.entity.FieldInfo;
import com.github.Sheven.shuiqi.entity.FieldMappingResult;
import com.github.Sheven.shuiqi.service.FieldMappingService;
import com.github.Sheven.shuiqi.util.ExcelExportUtil;
import com.github.Sheven.shuiqi.util.VoCodeGenerator;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

/**
 * 字段映射控制器
 * 提供字段映射、Excel 导出、VO 代码生成等功能
 */
@Slf4j
@RestController
@RequestMapping("/api/field-mapping")
public class FieldMappingController {

    @Autowired
    private FieldMappingService fieldMappingService;

    @Autowired
    private ExcelExportUtil excelExportUtil;

    @Autowired
    private VoCodeGenerator voCodeGenerator;

    /**
     * 健康检查接口
     */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("ShuiQi Field Mapping Service is running... We Good~");
    }

    /**
     * 处理字段映射请求
     * @param request 请求参数
     * @return 映射结果
     */
    @PostMapping("/process")
    public ResponseEntity<FieldMappingResponse> processFieldMapping(
            @RequestBody FieldMappingRequest request
    ) {
        String requestId = UUID.randomUUID().toString();
        long startTime = System.currentTimeMillis();

        try {
            log.info("收到字段映射请求：requestId={}, chineseNames={}",
                    requestId, request.getChineseNames());

            // 验证请求
            if (request.getChineseNames() == null || request.getChineseNames().isEmpty()) {
                return ResponseEntity.badRequest().body(
                        FieldMappingResponse.error(requestId, "中文字段名列表不能为空")
                );
            }

            // 1. 处理字段映射（包含 AI 去重和 MCP 调用）
            FieldMappingResult mappingResult = fieldMappingService.processFieldMappings(
                    request.getChineseNames()
            );

            if ("error".equals(mappingResult.getStatus())) {
                return ResponseEntity.internalServerError().body(
                        FieldMappingResponse.error(requestId, mappingResult.getErrorMessage())
                );
            }

            List<FieldInfo> matchedFields = mappingResult.getMatchedFields();
            List<String> unmatchedNames = mappingResult.getUnmatchedNames();

            // 2. 导出 Excel（如果请求）
            String excelFilePath = null;
            if (Boolean.TRUE.equals(request.getExportExcel()) && !matchedFields.isEmpty()) {
                try {
                    String fileName = request.getExcelFileName() != null ?
                            request.getExcelFileName() : "字段映射结果";
                    excelFilePath = excelExportUtil.exportFieldInfo(matchedFields, fileName);
                    log.info("Excel 文件导出成功：{}", excelFilePath);
                } catch (IOException e) {
                    log.error("导出 Excel 失败：{}", e.getMessage());
                }
            }

            // 3. 生成 VO 代码（如果请求）
            String voCode = null;
            if (Boolean.TRUE.equals(request.getGenerateVoCode()) && !matchedFields.isEmpty()) {
                String className = request.getVoClassName() != null ?
                        request.getVoClassName() : "FieldVO";
                voCode = voCodeGenerator.generateVoCode(className, matchedFields);
                log.info("VO 代码生成成功，类名：{}", className);
            }

            long processingTime = System.currentTimeMillis() - startTime;

            // 4. 返回响应
            FieldMappingResponse response = FieldMappingResponse.success(
                    requestId,
                    matchedFields,
                    unmatchedNames,
                    excelFilePath,
                    voCode,
                    processingTime
            );
            response.setInputChineseNames(request.getChineseNames());

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("处理字段映射失败：requestId={}", requestId, e);
            long processingTime = System.currentTimeMillis() - startTime;
            
            FieldMappingResponse response = new FieldMappingResponse();
            response.setRequestId(requestId);
            response.setStatus("error");
            response.setErrorMessage("处理失败：" + e.getMessage());
            response.setProcessingTime(processingTime);
            
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 查询单个中文字段的映射（简化接口）
     * @param chineseName 中文字段名
     * @return 字段信息列表
     */
    @GetMapping("/query/{chineseName}")
    public ResponseEntity<List<FieldInfo>> queryField(
            @PathVariable String chineseName
    ) {
        try {
            List<FieldInfo> fieldInfos = fieldMappingService.queryFieldsWithDeduplication(chineseName);
            return ResponseEntity.ok(fieldInfos);
        } catch (Exception e) {
            log.error("查询字段失败：chineseName={}", chineseName, e);
            return ResponseEntity.internalServerError().body(Collections.emptyList());
        }
    }

    /**
     * 批量查询字段映射（简化接口）
     * @param chineseNames 中文字段名列表（逗号分隔）
     * @return 字段映射结果
     */
    @GetMapping("/query")
    public ResponseEntity<FieldMappingResponse> queryFields(
            @RequestParam String chineseNames
    ) {
        String requestId = UUID.randomUUID().toString();
        
        try {
            List<String> nameList = List.of(chineseNames.split(","));
            FieldMappingResult result = fieldMappingService.processFieldMappings(nameList);
            
            FieldMappingResponse response = new FieldMappingResponse();
            response.setRequestId(requestId);
            response.setStatus(result.getStatus());
            response.setMatchedFields(result.getMatchedFields());
            response.setUnmatchedNames(result.getUnmatchedNames());
            response.setAiDeduplicationNote(result.getAiDeduplicationNote());
            response.setProcessingTime(result.getProcessingTime());
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("批量查询字段失败：chineseNames={}", chineseNames, e);
            return ResponseEntity.internalServerError().body(
                    FieldMappingResponse.error(requestId, e.getMessage())
            );
        }
    }
}
