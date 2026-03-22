package com.github.sheven.genmini.controller;

import com.github.sheven.genmini.dto.ChatRequest;
import com.github.sheven.genmini.dto.ChatResponse;
import com.github.sheven.genmini.service.GenminiChatService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

/**
 * Genmini 聊天控制器
 * 提供与 Genmini 模型聊天的接口
 */
@Slf4j
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class GenminiChatController {

    @Autowired
    private GenminiChatService chatService;

    /**
     * 聊天接口（非流式）
     * 
     * @param request 聊天请求
     * @return 聊天响应
     */
    @PostMapping("/chat")
    public ResponseEntity<ChatResponse> chat(@RequestBody ChatRequest request) {
        log.info("收到聊天请求：message={}, model={}", 
            request.getMessage(), 
            request.getModel() != null ? request.getModel() : "default");
        
        ChatResponse response = chatService.chat(request);
        
        if (response.isSuccess()) {
            return ResponseEntity.ok(response);
        } else {
            return ResponseEntity.badRequest().body(response);
        }
    }

    /**
     * 聊天接口（流式 SSE）
     * 
     * @param request 聊天请求
     * @return SSE Emitter
     */
    @PostMapping(value = "/chat/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public ResponseEntity<SseEmitter> chatStream(@RequestBody ChatRequest request) {
        log.info("收到流式聊天请求：message={}, model={}", 
            request.getMessage(), 
            request.getModel() != null ? request.getModel() : "default");

        // 创建 SSE Emitter（超时时间设置为 5 分钟）
        SseEmitter emitter = new SseEmitter(5 * 60 * 1000L);

        // 异步执行聊天请求
        new Thread(() -> {
            try {
                // 调用流式聊天服务
                okhttp3.Response response = chatService.chatStream(request);
                
                if (!response.isSuccessful()) {
                    emitter.send(SseEmitter.event()
                        .name("error")
                        .data("API 调用失败：" + response.code()));
                    emitter.complete();
                    return;
                }

                // 读取流式响应
                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(response.body().byteStream()))) {
                    
                    String line;
                    while ((line = reader.readLine()) != null) {
                        try {
                            // 发送 SSE 事件
                            emitter.send(SseEmitter.event()
                                .name("message")
                                .data(line));
                        } catch (IOException e) {
                            log.error("发送 SSE 消息失败", e);
                            break;
                        }
                    }
                }
                
                emitter.complete();
                
            } catch (Exception e) {
                log.error("流式聊天异常", e);
                try {
                    emitter.send(SseEmitter.event()
                        .name("error")
                        .data("聊天失败：" + e.getMessage()));
                } catch (IOException ex) {
                    log.error("发送错误消息失败", ex);
                }
                emitter.complete();
            }
        }).start();

        return ResponseEntity.ok(emitter);
    }

    /**
     * 健康检查接口
     */
    @GetMapping("/chat/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("Genmini Chat Service is running");
    }
}
