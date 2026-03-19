package com.github.sheven.partner.controller;

import com.github.sheven.partner.dto.*;
import com.github.sheven.partner.mapper.GenerationRecordMapper;
import com.github.sheven.partner.model.GenerationRecord;
import com.github.sheven.partner.model.User;
import com.github.sheven.partner.service.PartnerGenerationService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * AI 伴侣生成控制器
 */
@Slf4j
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "${app.cors.allowed-origins:http://localhost:3000}")
public class PartnerGenerationController {
    
    @Autowired
    private PartnerGenerationService generationService;
    
    @Autowired
    private GenerationRecordMapper generationRecordMapper;
    
    /**
     * 生成 AI 伴侣图片（使用通义万相）
     */
    @PostMapping("/generate")
    public ResponseEntity<GenerateResponse> generate(@RequestBody GenerateRequest request) {
        GenerateResponse response = generationService.generatePartnerImage(request);
        return ResponseEntity.ok(response);
    }
    
    /**
     * 生成 AI 伴侣图片（使用 Nano Banana Pro Model - Gemini API）
     */
    @PostMapping("/generate/nano-banana")
    public ResponseEntity<GenerateResponse> generateNanoBanana(@RequestBody GenerateRequest request) {
        GenerateResponse response = generationService.generateNanoBananaImage(request);
        return ResponseEntity.ok(response);
    }
    
    /**
     * 上传参考图片
     */
    @PostMapping("/upload")
    public ResponseEntity<Map<String, String>> uploadImage(
            @RequestParam("file") MultipartFile file) {
        try {
            String imageUrl = generationService.uploadImage(file);
            Map<String, String> result = new HashMap<>();
            result.put("imageUrl", imageUrl);
            result.put("message", "上传成功");
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, String> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(error);
        }
    }
    
    /**
     * 计算星座
     */
    @GetMapping("/zodiac")
    public ResponseEntity<Map<String, String>> calculateZodiac(
            @RequestParam("date") String date) {
        Map<String, String> result = new HashMap<>();
        String zodiac = com.github.sheven.partner.util.ZodiacUtil.getZodiacFromDate(date);
        result.put("zodiacSign", zodiac);
        return ResponseEntity.ok(result);
    }
    
    /**
     * 查询用户的生成记录
     */
    @GetMapping("/records")
    public ResponseEntity<RecordResponse> getRecords(
            @RequestParam("userUuid") String userUuid) {
        try {
            // 根据 UUID 查询记录
            List<GenerationRecord> records = generationRecordMapper.selectByUserUuid(userUuid);
            
            // 转换为 DTO
            List<RecordItem> recordItems = records.stream()
                    .map(record -> new RecordItem(
                            record.getId(),
                            record.getImageUrl(),
                            record.getPrompt(),
                            record.getDescription(),
                            record.getCreateTime()
                    ))
                    .collect(Collectors.toList());
            
            RecordData data = new RecordData();
            if (!records.isEmpty()) {
                data.setUserId(records.get(0).getUserId());
            }
            data.setUserUuid(userUuid);
            data.setRecords(recordItems);
            
            return ResponseEntity.ok(RecordResponse.success(data));
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.badRequest().body(RecordResponse.error("查询失败：" + e.getMessage()));
        }
    }
    
    // ==================== 分步保存用户信息接口 ====================
    
    /**
     * 获取当前步骤信息
     */
    @GetMapping("/user/step-info")
    public ResponseEntity<ApiResponse<StepInfo>> getStepInfo(
            @RequestParam("userUuid") String userUuid) {
        StepInfo stepInfo = generationService.getStepInfo(userUuid);
        return ResponseEntity.ok(ApiResponse.success(stepInfo));
    }
    
    /**
     * 保存性别信息
     */
    @PostMapping("/user/gender")
    public ResponseEntity<ApiResponse<User>> saveGender(
            @RequestBody UserGenderRequest request) {
        ApiResponse<User> response = generationService.saveGender(request);
        return ResponseEntity.ok(response);
    }
    
    /**
     * 保存 MBTI 类型
     */
    @PostMapping("/user/mbti")
    public ResponseEntity<ApiResponse<User>> saveMbti(
            @RequestBody UserMbtiRequest request) {
        ApiResponse<User> response = generationService.saveMbti(request);
        return ResponseEntity.ok(response);
    }
    
    /**
     * 保存出生日期和时间（自动计算星座）
     */
    @PostMapping("/user/birth-date")
    public ResponseEntity<ApiResponse<User>> saveBirthDate(
            @RequestBody UserBirthDateRequest request) {
        ApiResponse<User> response = generationService.saveBirthDate(request);
        return ResponseEntity.ok(response);
    }
    
    /**
     * 保存出生地点
     */
    @PostMapping("/user/birth-place")
    public ResponseEntity<ApiResponse<User>> saveBirthPlace(
            @RequestBody UserBirthPlaceRequest request) {
        ApiResponse<User> response = generationService.saveBirthPlace(request);
        return ResponseEntity.ok(response);
    }
    
    /**
     * 保存当前居住地
     */
    @PostMapping("/user/current-residence")
    public ResponseEntity<ApiResponse<User>> saveCurrentResidence(
            @RequestBody UserCurrentResidenceRequest request) {
        ApiResponse<User> response = generationService.saveCurrentResidence(request);
        return ResponseEntity.ok(response);
    }
    
    /**
     * 保存兴趣爱好和自定义特征
     */
    @PostMapping("/user/interests")
    public ResponseEntity<ApiResponse<User>> saveInterests(
            @RequestBody UserInterestsRequest request) {
        ApiResponse<User> response = generationService.saveInterests(request);
        return ResponseEntity.ok(response);
    }
    
    /**
     * 保存用户步骤信息（包含用户名）
     */
    @PostMapping("/user/step")
    public ResponseEntity<ApiResponse<User>> saveUserStep(
            @RequestBody UserStepRequest request) {
        ApiResponse<User> response = generationService.saveUserStep(request);
        return ResponseEntity.ok(response);
    }
}
