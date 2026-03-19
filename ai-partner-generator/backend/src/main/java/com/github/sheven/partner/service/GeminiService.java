package com.github.sheven.partner.service;

import com.google.genai.Client;
import com.google.genai.types.Content;
import com.google.genai.types.GenerateContentConfig;
import com.google.genai.types.GenerateContentResponse;
import com.google.genai.types.Part;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.ConnectException;
import java.net.UnknownHostException;
import java.net.http.HttpTimeoutException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Base64;

/**
 * Gemini AI 服务（使用 Google 官方 SDK）
 * 提供文本到图像、文本 + 图像到图像的生成功能
 */
@Slf4j
@Service
public class GeminiService {

    private final Client geminiClient;

    @Value("${spring.ai.gemini.chat.options.model:gemini-2.0-flash-exp}")
    private String model;

    @Value("${spring.ai.gemini.read-timeout:600000}")
    private Integer readTimeout;

    @Autowired
    public GeminiService(Client geminiClient) {
        this.geminiClient = geminiClient;
        if (geminiClient == null) {
            log.warn("Gemini Client 未初始化，Gemini 相关功能将不可用");
        }
    }

    /**
     * 根据文本描述生成图片
     * 
     * @param prompt 文本描述
     * @return 生成的图片数据（Base64 编码）
     */
    public byte[] generateImageFromText(String prompt) {
        if (geminiClient == null) {
            log.error("Gemini Client 未初始化，无法生成图片");
            throw new IllegalStateException("Gemini API 未配置，请先配置 GEMINI_API_KEY");
        }
        
        try {
            log.info("开始使用 Gemini 生成图片，提示词：{}", prompt);
            log.info("当前模型：{}，超时配置：connect=30s, read=600s, write=600s", model);

            // 配置响应模式为生成图像
            GenerateContentConfig config = GenerateContentConfig.builder()
                    .responseModalities("TEXT", "IMAGE")
                    .build();

            // 创建内容（仅文本提示）
            Content content = Content.fromParts(Part.fromText(prompt));

            // 调用 Gemini API 生成内容
            GenerateContentResponse response = geminiClient.models.generateContent(model, content, config);

            // 提取生成的图片
            log.debug("开始解析 Gemini 响应...");
            for (Part part : response.parts()) {
                if (part.inlineData().isPresent()) {
                    var blob = part.inlineData().get();
                    if (blob.data().isPresent()) {
                        byte[] imageData = blob.data().get();
                        log.info("图片生成成功，大小：{} bytes", imageData.length);
                        return imageData;
                    }
                }
            }

            log.warn("Gemini API 未返回图片数据，响应内容：{}", response.text());
            return null;

        } catch (Exception e) {
            log.error("Gemini 图片生成失败：{}", e.getMessage(), e);
            throw new RuntimeException("图片生成失败：" + e.getMessage(), e);
        }
    }

    /**
     * 根据文本描述和参考图片生成新图片
     * 
     * @param prompt 文本描述
     * @param imagePath 参考图片路径
     * @param mimeType 参考图片 MIME 类型（如 image/jpeg）
     * @return 生成的图片数据（Base64 编码）
     */
    public byte[] generateImageFromTextAndImage(String prompt, String imagePath, String mimeType) {
        if (geminiClient == null) {
            log.error("Gemini Client 未初始化，无法生成图片");
            throw new IllegalStateException("Gemini API 未配置，请先配置 GEMINI_API_KEY");
        }
        
        try {
            log.info("开始使用 Gemini 基于参考图片生成新图片，提示词：{}，参考图：{}", prompt, imagePath);

            // 读取参考图片
            Path imageFile = Paths.get(imagePath);
            byte[] imageBytes = Files.readAllBytes(imageFile);

            // 配置响应模式为生成图像
            GenerateContentConfig config = GenerateContentConfig.builder()
                    .responseModalities("TEXT", "IMAGE")
                    .build();

            // 创建内容（文本提示 + 参考图片）
            Content content = Content.fromParts(
                    Part.fromText(prompt),
                    Part.fromBytes(imageBytes, mimeType)
            );

            // 调用 Gemini API 生成内容
            GenerateContentResponse response = geminiClient.models.generateContent(model, content, config);

            // 提取生成的图片
            for (Part part : response.parts()) {
                if (part.inlineData().isPresent()) {
                    var blob = part.inlineData().get();
                    if (blob.data().isPresent()) {
                        byte[] imageData = blob.data().get();
                        log.info("图片生成成功，大小：{} bytes", imageData.length);
                        return imageData;
                    }
                }
            }

            log.warn("Gemini API 未返回图片数据");
            return null;

        } catch (IOException e) {
            log.error("读取参考图片失败", e);
            throw new RuntimeException("读取图片失败：" + e.getMessage(), e);
        } catch (Exception e) {
            log.error("Gemini 图片生成失败", e);
            throw new RuntimeException("图片生成失败：" + e.getMessage(), e);
        }
    }

    /**
     * 根据文本描述生成图片并保存为 Base64 字符串
     * 
     * @param prompt 文本描述
     * @return Base64 编码的图片字符串
     */
    public String generateImageAsBase64(String prompt) {
        byte[] imageData = generateImageFromText(prompt);
        if (imageData != null) {
            return Base64.getEncoder().encodeToString(imageData);
        }
        return null;
    }

    /**
     * 根据文本描述生成图片并保存到本地文件
     * 
     * @param prompt 文本描述
     * @param outputPath 输出文件路径
     * @return 保存的文件路径
     */
    public String generateImageAndSave(String prompt, String outputPath) {
        try {
            byte[] imageData = generateImageFromText(prompt);
            if (imageData != null) {
                Path outputFile = Paths.get(outputPath);
                Files.write(outputFile, imageData);
                log.info("图片已保存到：{}", outputPath);
                return outputPath;
            }
            return null;
        } catch (IOException e) {
            log.error("保存图片失败", e);
            throw new RuntimeException("保存图片失败：" + e.getMessage(), e);
        }
    }
}
