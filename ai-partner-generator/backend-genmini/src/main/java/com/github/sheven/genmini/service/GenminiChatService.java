package com.github.sheven.genmini.service;

import com.alibaba.fastjson.JSON;
import com.github.sheven.genmini.config.GenminiProperties;
import com.github.sheven.genmini.dto.ChatHistory;
import com.github.sheven.genmini.dto.ChatRequest;
import com.github.sheven.genmini.dto.ChatResponse;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Genmini 聊天服务
 * 提供与本地 Genmini 模型聊天接口交互的功能
 */
@Slf4j
@Service
public class GenminiChatService {

    @Autowired
    private GenminiProperties properties;

    @Autowired
    private OkHttpClient okHttpClient;

    /**
     * 发送聊天消息
     * 
     * @param request 聊天请求
     * @return 聊天响应
     */
    public ChatResponse chat(ChatRequest request) {
        try {
            // 构建请求 URL
            String url = properties.getBaseUrl() + properties.getChatEndpoint();
            
            // 确定使用的模型
            String model = request.getModel() != null ? request.getModel() : properties.getDefaultChatModel();

            // 构建请求体
            Map<String, Object> requestBody = buildRequestBody(request, model);

            // 打印请求日志
            log.info("========== Genmini Chat API 调用开始 ==========");
            log.info("[请求] URL: {}", url);
            log.info("[请求] 模型：{}", model);
            log.info("[请求] 消息内容：{}", request.getMessage());
            log.info("[请求] 请求体：{}", JSON.toJSONString(requestBody));
            log.info("============================================");

            // 创建 HTTP 请求
            RequestBody body = RequestBody.create(
                JSON.toJSONString(requestBody),
                MediaType.parse("application/json")
            );

            Request httpRequest = new Request.Builder()
                    .url(url)
                    .post(body)
                    .addHeader("Content-Type", "application/json")
                    .build();

            // 执行请求
            log.info("[调用] 正在调用 Genmini Chat API...");
            long startTime = System.currentTimeMillis();
            
            try (Response response = okHttpClient.newCall(httpRequest).execute()) {
                long endTime = System.currentTimeMillis();
                log.info("[调用] API 调用完成，耗时：{} ms", (endTime - startTime));

                // 检查响应状态
                if (!response.isSuccessful()) {
                    String errorBody = response.body() != null ? response.body().string() : "未知错误";
                    log.error("[响应] 请求失败，状态码：{}, 错误：{}", response.code(), errorBody);
                    return ChatResponse.error("API 调用失败：" + errorBody);
                }

                // 解析响应
                String responseBody = response.body().string();
                log.info("[响应] 响应体：{}", responseBody);

                // 解析 JSON 响应
                Map<String, Object> responseMap = JSON.parseObject(responseBody, Map.class);
                
                // 提取响应消息（根据实际 API 响应格式调整）
                String message = extractMessageFromResponse(responseMap);
                
                log.info("========== Genmini Chat API 调用成功 ==========");
                log.info("[响应] 消息内容：{}", message);
                
                return ChatResponse.success(message, model);
            }

        } catch (IOException e) {
            log.error("========== Genmini Chat API 调用异常 ==========");
            log.error("[异常] 类型：{}", e.getClass().getName());
            log.error("[异常] 消息：{}", e.getMessage());
            log.error("[异常] 堆栈跟踪:", e);
            log.error("==========================================");
            return ChatResponse.error("聊天服务调用失败：" + e.getMessage());
        }
    }

    /**
     * 构建请求体
     */
    private Map<String, Object> buildRequestBody(ChatRequest request, String model) {
        Map<String, Object> body = new HashMap<>();
        body.put("model", model);
        body.put("message", request.getMessage());

        // 如果有历史对话，添加历史记录
        if (request.getHistory() != null) {
            ChatHistory history = request.getHistory();
            
            if (history.getSystemPrompt() != null) {
                body.put("system_prompt", history.getSystemPrompt());
            }
            
            if (history.getMessages() != null && !history.getMessages().isEmpty()) {
                List<Map<String, String>> messages = new ArrayList<>();
                for (ChatHistory.Message msg : history.getMessages()) {
                    Map<String, String> messageMap = new HashMap<>();
                    messageMap.put("role", msg.getRole());
                    messageMap.put("content", msg.getContent());
                    messages.add(messageMap);
                }
                body.put("messages", messages);
            }
        }

        return body;
    }

    /**
     * 从响应中提取消息（根据实际 API 响应格式调整）
     */
    private String extractMessageFromResponse(Map<String, Object> responseMap) {
        // 尝试常见的响应格式
        if (responseMap.containsKey("message")) {
            return (String) responseMap.get("message");
        }
        if (responseMap.containsKey("content")) {
            return (String) responseMap.get("content");
        }
        if (responseMap.containsKey("reply")) {
            return (String) responseMap.get("reply");
        }
        if (responseMap.containsKey("response")) {
            return (String) responseMap.get("response");
        }
        if (responseMap.containsKey("data")) {
            Object data = responseMap.get("data");
            if (data instanceof Map) {
                Map<?, ?> dataMap = (Map<?, ?>) data;
                if (dataMap.containsKey("message")) {
                    return (String) dataMap.get("message");
                }
                if (dataMap.containsKey("content")) {
                    return (String) dataMap.get("content");
                }
            }
            return data.toString();
        }
        
        // 如果都不匹配，返回整个响应的 JSON 字符串
        return JSON.toJSONString(responseMap);
    }

    /**
     * 带流式响应的聊天（返回 ResponseBody，由 Controller 处理流式输出）
     * 
     * @param request 聊天请求
     * @return OkHttp Response（需要手动关闭）
     */
    public okhttp3.Response chatStream(ChatRequest request) throws IOException {
        // 构建请求 URL
        String url = properties.getBaseUrl() + properties.getChatEndpoint() + "/stream";
        
        // 确定使用的模型
        String model = request.getModel() != null ? request.getModel() : properties.getDefaultChatModel();

        // 构建请求体
        Map<String, Object> requestBody = buildRequestBody(request, model);

        log.info("========== Genmini Chat Stream API 调用开始 ==========");
        log.info("[请求] URL: {}", url);
        log.info("[请求] 模型：{}", model);
        log.info("============================================");

        // 创建 HTTP 请求
        RequestBody body = RequestBody.create(
            JSON.toJSONString(requestBody),
            MediaType.parse("application/json")
        );

        Request httpRequest = new Request.Builder()
                .url(url)
                .post(body)
                .addHeader("Content-Type", "application/json")
                .build();

        // 执行请求（异步，返回 Response）
        return okHttpClient.newCall(httpRequest).execute();
    }
}
