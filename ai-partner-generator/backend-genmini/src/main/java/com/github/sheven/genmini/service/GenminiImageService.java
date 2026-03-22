package com.github.sheven.genmini.service;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.sheven.genmini.config.GenminiProperties;
import com.github.sheven.genmini.dto.GeminiRequest;
import com.github.sheven.genmini.dto.ImageGenerationRequest;
import com.github.sheven.genmini.dto.ImageGenerationResponse;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import okio.Buffer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Genmini 图片生成服务
 * 提供与本地 Genmini 模型图片生成接口交互的功能
 */
@Slf4j
@Service
public class GenminiImageService {

    @Autowired
    private GenminiProperties properties;

    @Autowired
    private OkHttpClient okHttpClient;

    private static final ObjectMapper mapper = new ObjectMapper();

    /**
     * 生成图片
     *
     * @param request 图片生成请求
     * @return 图片生成响应
     */
    public ImageGenerationResponse generateImage(ImageGenerationRequest request) {
        try {

            // 构建请求 URL
            String url = properties.getBaseUrl() + properties.getImageEndpoint();

            String apiKey = properties.getApiKey();

            // 确定使用的模型
            String model = request.getModel() != null ? request.getModel() : properties.getDefaultImageModel();

            String tarGender = "female";

            String info = "";
            // 构建 POJO
            GeminiRequest geminiRequest = new GeminiRequest();
            geminiRequest.contents = List.of(new GeminiRequest.Content(buildText(info, tarGender)));
            geminiRequest.generationConfig = new GeminiRequest.GenerationConfig();

            // 序列化为 JSON
            String jsonBody = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(geminiRequest);
            log.info("请求体:\n{}", jsonBody);

            // 发送请求
            OkHttpClient client = new OkHttpClient.Builder()
                    .readTimeout(300, TimeUnit.SECONDS)
                    .build();

            RequestBody body = RequestBody.create(jsonBody, MediaType.parse("application/json"));

            Request httpRequest = new Request.Builder()
                    .url(url)
                    .method("POST", body)
                    .addHeader("x-goog-api-key", apiKey)
                    .addHeader("Content-Type", "application/json")
                    .build();

            // 执行请求
            log.info("[调用] 正在调用 Genmini Image API... request -> {}", requestToJson(httpRequest));
            long startTime = System.currentTimeMillis();


            try (Response response = client.newCall(httpRequest).execute()) {
                long endTime = System.currentTimeMillis();
                log.info("[调用] API 调用完成，耗时：{} ms", (endTime - startTime));

                // 检查响应状态
                if (!response.isSuccessful()) {
                    String errorBody = response.body() != null ? response.body().string() : "未知错误";
                    log.error("[响应] 请求失败，状态码：{}, 错误：{}", response.code(), errorBody);
                    return ImageGenerationResponse.error("API 调用失败：" + errorBody);
                }

                // 解析响应
                String responseBody = response.body().string();
                log.info("[响应] 响应体大小：{} bytes", responseBody.length());
                log.debug("[响应] 响应体：{}", responseBody);

                // 解析 JSON 响应
                Map<String, Object> responseMap = JSON.parseObject(responseBody, Map.class);

                // 提取生成的图片
                List<String> images = extractImagesFromResponse(responseMap);

                if (images == null || images.isEmpty()) {
                    log.warn("[响应] 未找到图片数据");
                    return ImageGenerationResponse.error("未生成图片");
                }

                log.info("========== Genmini Image API 调用成功 ==========");
                log.info("[响应] 生成图片数量：{}", images.size());
                log.info("[响应] 第一张图片大小：{} bytes", images.get(0).length());

                return ImageGenerationResponse.success(images, model);
            }

        } catch (IOException e) {
            log.error("========== Genmini Image API 调用异常 ==========");
            log.error("[异常] 类型：{}", e.getClass().getName());
            log.error("[异常] 消息：{}", e.getMessage());
            log.error("[异常] 堆栈跟踪:", e);
            log.error("==========================================");
            return ImageGenerationResponse.error("图片生成失败：" + e.getMessage());
        }
    }

    private static String buildText(String info, String targetGender) {
        return String.format(
                "请通过用户的描述揣测用户可能喜欢的形象，以下是一个用户的描述\\n %s,%s，喜欢$s。中国人，符合中国人审美，尽可能好看。",
                info, targetGender
        );
    }

    public String requestToJson(Request request) {
        JSONObject json = new JSONObject();

        // 基本信息
        json.put("method", request.method());
        json.put("url", request.url().toString());

        // 解析 URL 参数
        JSONObject urlParams = new JSONObject();
        HttpUrl url = request.url();
        for (int i = 0; i < url.querySize(); i++) {
            urlParams.put(url.queryParameterName(i), url.queryParameterValue(i));
        }
        json.put("queryParams", urlParams);

        // Headers
        JSONObject headers = new JSONObject();
        for (String name : request.headers().names()) {
            headers.put(name, request.header(name));
        }
        json.put("headers", headers);

        // Body (如果有)
        if (request.body() != null) {
            json.put("body", bodyToString(request));
        }

        return json.toString(); // 格式化输出
    }

    private String bodyToString(Request request) {
        try {
            Request copy = request.newBuilder().build();
            Buffer buffer = new Buffer();
            if (copy.body() != null) {
                copy.body().writeTo(buffer);
                return buffer.readUtf8();
            }
        } catch (IOException e) {
            return "无法读取 body: " + e.getMessage();
        }
        return "";
    }

    /**
     * 构建请求体
     */
    private Map<String, Object> buildRequestBody(ImageGenerationRequest request, String model) {
        Map<String, Object> body = new HashMap<>();
        body.put("model", model);
        body.put("prompt", request.getPrompt());

        // 如果有参考图片，添加到请求中
        if (request.getReferenceImage() != null && !request.getReferenceImage().isEmpty()) {
            Map<String, String> image = new HashMap<>();
            image.put("data", request.getReferenceImage());
            if (request.getReferenceImageType() != null) {
                image.put("type", request.getReferenceImageType());
            }
            body.put("reference_image", image);
        }

        // 添加生成参数
        if (request.getCount() != null && request.getCount() > 1) {
            body.put("count", request.getCount());
        }

        if (request.getWidth() != null) {
            body.put("width", request.getWidth());
        }

        if (request.getHeight() != null) {
            body.put("height", request.getHeight());
        }

        return body;
    }

    /**
     * 从响应中提取图片（根据实际 API 响应格式调整）
     */
    @SuppressWarnings("unchecked")
    private List<String> extractImagesFromResponse(Map<String, Object> responseMap) {
        List<String> images = new ArrayList<>();

        // 尝试常见的响应格式
        
        // 格式 1: { "images": ["base64...", ...] }
        if (responseMap.containsKey("images")) {
            Object imagesObj = responseMap.get("images");
            if (imagesObj instanceof List) {
                for (Object img : (List<?>) imagesObj) {
                    if (img instanceof String) {
                        images.add((String) img);
                    } else if (img instanceof Map) {
                        // { "data": "base64..." }
                        Map<?, ?> imgMap = (Map<?, ?>) img;
                        if (imgMap.containsKey("data") || imgMap.containsKey("base64")) {
                            images.add((String) (imgMap.containsKey("data") ? imgMap.get("data") : imgMap.get("base64")));
                        }
                    }
                }
            }
            return images;
        }

        // 格式 2: { "image": "base64..." } 或 { "data": "base64..." }
        if (responseMap.containsKey("image")) {
            Object img = responseMap.get("image");
            if (img instanceof String) {
                images.add((String) img);
                return images;
            }
        }
        
        if (responseMap.containsKey("data")) {
            Object data = responseMap.get("data");
            if (data instanceof String) {
                images.add((String) data);
                return images;
            } else if (data instanceof Map) {
                // { "data": { "image": "base64..." } }
                Map<?, ?> dataMap = (Map<?, ?>) data;
                if (dataMap.containsKey("image")) {
                    images.add((String) dataMap.get("image"));
                    return images;
                }
                if (dataMap.containsKey("base64")) {
                    images.add((String) dataMap.get("base64"));
                    return images;
                }
            }
        }

        // 格式 3: { "result": { "images": [...] } }
        if (responseMap.containsKey("result")) {
            Object result = responseMap.get("result");
            if (result instanceof Map) {
                Map<?, ?> resultMap = (Map<?, ?>) result;
                if (resultMap.containsKey("images")) {
                    Object imagesObj = resultMap.get("images");
                    if (imagesObj instanceof List) {
                        for (Object img : (List<?>) imagesObj) {
                            if (img instanceof String) {
                                images.add((String) img);
                            }
                        }
                        return images;
                    }
                }
            }
        }

        // 如果都不匹配，返回空列表
        return images;
    }
}
