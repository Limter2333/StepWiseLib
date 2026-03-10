package com.github.Sheven.controller;

import com.github.Sheven.dto.RagRequest;
import com.github.Sheven.dto.RagResponse;
import com.github.Sheven.entity.RagDocument;
import com.github.Sheven.service.RagService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.annotation.Resource;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * RAG 智能问答控制器
 */
@RestController
@RequestMapping("/rag")
@CrossOrigin(origins = "*")
public class RagController {

    private static final Logger log = LoggerFactory.getLogger(RagController.class);

    @Resource
    private RagService ragService;

    /**
     * RAG 智能问答接口
     * @param request 请求参数
     * @return AI 回答
     */
    @PostMapping("/query")
    public ResponseEntity<RagResponse> query(@RequestBody RagRequest request) {
        log.info("收到 RAG 查询请求：{}", request.getQuestion());
        
        if (request.getQuestion() == null || request.getQuestion().trim().isEmpty()) {
            return ResponseEntity.badRequest().build();
        }

        try {
            RagResponse response = ragService.query(request);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("RAG 查询失败", e);
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * 获取所有文档
     */
    @GetMapping("/documents")
    public ResponseEntity<List<RagDocument>> listDocuments() {
        try {
            List<RagDocument> documents = ragService.listAll();
            return ResponseEntity.ok(documents);
        } catch (Exception e) {
            log.error("获取文档列表失败", e);
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * 添加文档到知识库
     */
    @PostMapping("/document")
    public ResponseEntity<Map<String, Object>> addDocument(@RequestBody RagDocument document) {
        log.info("添加文档：{}", document.getTitle());
        
        Map<String, Object> result = new HashMap<>();
        try {
            boolean success = ragService.saveDocument(document);
            result.put("success", success);
            result.put("message", success ? "文档添加成功" : "文档添加失败");
            
            if (success) {
                result.put("data", document);
            }
            
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("添加文档失败", e);
            result.put("success", false);
            result.put("message", "添加文档失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(result);
        }
    }

    /**
     * 批量导入文档
     */
    @PostMapping("/documents/batch")
    public ResponseEntity<Map<String, Object>> batchAddDocuments(@RequestBody List<RagDocument> documents) {
        log.info("批量导入 {} 篇文档", documents.size());
        
        Map<String, Object> result = new HashMap<>();
        try {
            int count = ragService.batchSaveDocuments(documents);
            result.put("success", true);
            result.put("count", count);
            result.put("message", "成功导入 " + count + " 篇文档");
            
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("批量导入文档失败", e);
            result.put("success", false);
            result.put("message", "批量导入失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(result);
        }
    }

    /**
     * 删除文档
     */
    @DeleteMapping("/document/{id}")
    public ResponseEntity<Map<String, Object>> deleteDocument(@PathVariable Long id) {
        log.info("删除文档 ID: {}", id);
        
        Map<String, Object> result = new HashMap<>();
        try {
            boolean success = ragService.deleteDocument(id);
            result.put("success", success);
            result.put("message", success ? "删除成功" : "删除失败");
            
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("删除文档失败", e);
            result.put("success", false);
            result.put("message", "删除失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(result);
        }
    }

    /**
     * 健康检查
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        Map<String, String> result = new HashMap<>();
        result.put("status", "UP");
        result.put("service", "RAG Service");
        return ResponseEntity.ok(result);
    }
}
