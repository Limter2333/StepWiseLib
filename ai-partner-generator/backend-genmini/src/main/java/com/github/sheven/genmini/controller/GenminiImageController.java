package com.github.sheven.genmini.controller;

import com.github.sheven.genmini.dto.ImageGenerationRequest;
import com.github.sheven.genmini.dto.ImageGenerationResponse;
import com.github.sheven.genmini.service.GenminiImageService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Base64;
import java.util.List;

/**
 * Genmini 图片生成控制器
 * 提供与 Genmini 模型图片生成接口
 */
@Slf4j
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class GenminiImageController {

    @Autowired
    private GenminiImageService imageService;

    /**
     * 图片生成接口
     * 
     * @param request 图片生成请求
     * @return 图片生成响应
     */
    @PostMapping("/image")
    public ResponseEntity<ImageGenerationResponse> generateImage(
            @RequestBody ImageGenerationRequest request) {
        
        log.info("收到图片生成请求：prompt={}, model={}, count={}", 
            request.getPrompt(), 
            request.getModel() != null ? request.getModel() : "default",
            request.getCount());
        
        ImageGenerationResponse response = imageService.generateImage(request);
        
        if (response.isSuccess()) {
            return ResponseEntity.ok(response);
        } else {
            return ResponseEntity.badRequest().body(response);
        }
    }

    /**
     * 获取单张图片（Base64 解码）
     * 
     * @param index 图片索引（从 0 开始）
     * @return 图片二进制数据
     */
    @GetMapping("/image/{index}")
    public ResponseEntity<byte[]> getImage(
            @RequestParam String prompt,
            @RequestParam(required = false) String model,
            @PathVariable int index) {
        
        log.info("收到图片获取请求：prompt={}, model={}, index={}", prompt, model, index);
        
        // 创建请求
        ImageGenerationRequest request = new ImageGenerationRequest();
        request.setPrompt(prompt);
        request.setModel(model);
        request.setCount(index + 1);
        
        // 调用服务生成图片
        ImageGenerationResponse response = imageService.generateImage(request);
        
        if (!response.isSuccess() || response.getImages() == null || response.getImages().isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        
        // 获取指定索引的图片
        if (index >= response.getImages().size()) {
            return ResponseEntity.notFound().build();
        }
        
        String base64Image = response.getImages().get(index);
        
        try {
            // 解码 Base64 图片
            byte[] imageBytes = Base64.getDecoder().decode(base64Image);
            
            // 设置响应头
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.IMAGE_PNG);
            headers.setContentLength(imageBytes.length);
            
            return new ResponseEntity<>(imageBytes, headers, HttpStatus.OK);
        } catch (IllegalArgumentException e) {
            log.error("Base64 解码失败", e);
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * 健康检查接口
     */
    @GetMapping("/image/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("Genmini Image Service is running");
    }
}
