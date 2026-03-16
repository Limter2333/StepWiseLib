package com.github.Sheven.controller;

import com.github.Sheven.service.CustomModelService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 自定义模型控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/custom-model")
@CrossOrigin(origins = "*")
public class CustomModelController {

    @Autowired
    private CustomModelService customModelService;

    /**
     * 简单对话接口
     * @param request 包含消息的请求体
     * @return 模型响应
     */
    @PostMapping("/chat")
    public ResponseEntity<Map<String, Object>> chat(@RequestBody Map<String, String> request) {
        log.info("收到自定义模型对话请求");
        
        Map<String, Object> result = new HashMap<>();
        try {
            String message = request.get("message");
            if (message == null || message.trim().isEmpty()) {
                result.put("success", false);
                result.put("message", "消息不能为空");
                return ResponseEntity.badRequest().body(result);
            }

            String response = customModelService.chat(message);
            result.put("success", true);
            result.put("data", response);
            result.put("message", "对话成功");
            
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("自定义模型对话失败", e);
            result.put("success", false);
            result.put("message", "对话失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(result);
        }
    }

    /**
     * 流式对话接口
     * @param request 包含消息的请求体
     * @return 模型响应流
     */
    @PostMapping(value = "/chat/stream", produces = "text/event-stream")
    public Mono<String> streamChat(@RequestBody Map<String, String> request) {
        log.info("收到自定义模型流式对话请求");
        
        String message = request.get("message");
        if (message == null || message.trim().isEmpty()) {
            return Mono.error(new IllegalArgumentException("消息不能为空"));
        }

        return customModelService.streamChat(message);
    }

    /**
     * 带历史记录的对话接口
     * @param request 包含消息历史列表的请求体
     * @return 模型响应
     */
    @PostMapping("/chat/history")
    public ResponseEntity<Map<String, Object>> chatWithHistory(@RequestBody Map<String, List<Map<String, String>>> request) {
        log.info("收到自定义模型带历史记录的对话请求");
        
        Map<String, Object> result = new HashMap<>();
        try {
            List<Map<String, String>> messages = request.get("messages");
            if (messages == null || messages.isEmpty()) {
                result.put("success", false);
                result.put("message", "消息历史不能为空");
                return ResponseEntity.badRequest().body(result);
            }

            String response = customModelService.chatWithHistory(messages);
            result.put("success", true);
            result.put("data", response);
            result.put("message", "对话成功");
            
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("自定义模型带历史对话失败", e);
            result.put("success", false);
            result.put("message", "对话失败：" + e.getMessage());
            return ResponseEntity.internalServerError().body(result);
        }
    }

    /**
     * 健康检查接口
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        Map<String, String> result = new HashMap<>();
        result.put("status", "UP");
        result.put("service", "Custom Model Service");
        return ResponseEntity.ok(result);
    }
}
