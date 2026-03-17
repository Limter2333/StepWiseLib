package com.github.sheven.partner.service;

import com.alibaba.fastjson.JSON;
import com.github.sheven.partner.dto.*;
import com.github.sheven.partner.mapper.GenerationRecordMapper;
import com.github.sheven.partner.mapper.UserMapper;
import com.github.sheven.partner.model.GenerationRecord;
import com.github.sheven.partner.model.User;
import com.github.sheven.partner.util.ZodiacUtil;
import org.springframework.ai.dashscope.api.DashScopeApi;
import org.springframework.ai.dashscope.api.ImageGenerationResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.UUID;

/**
 * AI 伴侣生成服务
 */
@Service
public class PartnerGenerationService {
    
    private final DashScopeApi dashScopeApi;
    
    private final UserMapper userMapper;
    
    private final GenerationRecordMapper generationRecordMapper;
    
    @Value("${spring.application.name:ai-partner-generator}")
    private String applicationName;
    
    @Value("${app.cors.allowed-origins:http://localhost:3000}")
    private String allowedOrigins;
    
    // 上传目录
    private static final String UPLOAD_DIR = "uploads/";
    
    // 图片保存根目录
    private static final String IMAGE_SAVE_DIR = "images/";
    
    public PartnerGenerationService(
            @Value("${spring.ai.dashscope.api-key}") String apiKey,
            UserMapper userMapper,
            GenerationRecordMapper generationRecordMapper) {
        this.dashScopeApi = new DashScopeApi(apiKey);
        this.userMapper = userMapper;
        this.generationRecordMapper = generationRecordMapper;
    }
    
    /**
     * 生成 AI 伴侣图片
     */
    public GenerateResponse generatePartnerImage(GenerateRequest request) {
        try {
            // 1. 保存或更新用户信息
            User user = saveOrUpdateUser(request);
            
            // 2. 构建提示词
            String prompt = buildPrompt(request);
            
            // 3. 调用通义万相生成图片
            ImageGenerationResponse response = dashScopeApi.imageGenerations()
                    .create(b -> b
                            .prompt(prompt)
                            .model("wanx-v1")
                            .n(1)
                            .size("1024x1024")
                    );
            
            if (response != null && response.getImages() != null && !response.getImages().isEmpty()) {
                String imageUrl = response.getImages().get(0).getUrl();
                String description = buildDescription(request);
                
                // 4. 下载并保存图片到本地
                String localImagePath = saveImageToLocal(imageUrl, user.getId());
                String accessUrl = "/api/images/" + localImagePath.substring(IMAGE_SAVE_DIR.length());
                
                // 5. 保存生成记录
                saveGenerationRecord(user, localImagePath, accessUrl, prompt, description, request);
                
                return GenerateResponse.success(accessUrl, description);
            } else {
                return GenerateResponse.error("图片生成失败，请重试");
            }
            
        } catch (Exception e) {
            e.printStackTrace();
            return GenerateResponse.error("生成失败：" + e.getMessage());
        }
    }
    
    /**
     * 构建 AI 绘画提示词
     */
    private String buildPrompt(GenerateRequest request) {
        StringBuilder prompt = new StringBuilder();
        
        prompt.append("一位理想的伴侣形象，");
        
        // 根据用户信息推断可能的偏好
        if ("male".equals(request.getGender())) {
            prompt.append("女性，");
        } else if ("female".equals(request.getGender())) {
            prompt.append("男性，");
        } else {
            prompt.append("人物，");
        }
        
        // 添加星座特征
        if (request.getZodiacSign() != null && !request.getZodiacSign().isEmpty() && !"未知".equals(request.getZodiacSign())) {
            prompt.append(request.getZodiacSign()).append("座气质，");
        }
        
        // 添加 MBTI 相关特征
        if (request.getMbtiType() != null && !request.getMbtiType().isEmpty()) {
            prompt.append(getMbtiCharacteristics(request.getMbtiType())).append(",");
        }
        
        // 添加兴趣爱好
        if (request.getInterests() != null && !request.getInterests().isEmpty()) {
            prompt.append("兴趣包括").append(String.join("、", request.getInterests())).append(",");
        }
        
        // 添加自定义特征
        if (request.getCustomFeatures() != null && !request.getCustomFeatures().isEmpty()) {
            prompt.append(request.getCustomFeatures()).append(",");
        }
        
        prompt.append("高质量肖像照，专业摄影，精美细节，柔和光线，温馨氛围");
        
        return prompt.toString();
    }
    
    /**
     * 根据 MBTI 类型获取特征描述
     */
    private String getMbtiCharacteristics(String mbti) {
        // 简化的 MBTI 特征映射
        return switch (mbti.toUpperCase()) {
            case "INTJ" -> "理性智慧，深邃眼神";
            case "INTP" -> "思考者气质，专注神情";
            case "ENTJ" -> "领导者风范，自信微笑";
            case "ENTP" -> "创新活力，灵动表情";
            case "INFJ" -> "温柔体贴，善解人意";
            case "INFP" -> "浪漫理想，温暖笑容";
            case "ENFJ" -> "热情开朗，感染力强";
            case "ENFP" -> "活泼可爱，充满好奇";
            case "ISTJ" -> "稳重可靠，认真严谨";
            case "ISFJ" -> "细心关怀，温和亲切";
            case "ESTJ" -> "务实干练，果断坚定";
            case "ESFJ" -> "友善热心，乐于助人";
            case "ISTP" -> "冷静沉着，动手能力强";
            case "ISFP" -> "艺术气质，敏感细腻";
            case "ESTP" -> "冒险精神，活力四射";
            case "ESFP" -> "表演天赋，魅力十足";
            default -> "独特个性";
        };
    }
    
    /**
     * 构建描述文本
     */
    private String buildDescription(GenerateRequest request) {
        StringBuilder desc = new StringBuilder();
        desc.append("根据您的信息为您生成的理想伴侣形象\n");
        desc.append("星座：").append(request.getZodiacSign()).append("\n");
        if (request.getMbtiType() != null) {
            desc.append("MBTI: ").append(request.getMbtiType()).append("\n");
        }
        if (request.getInterests() != null && !request.getInterests().isEmpty()) {
            desc.append("兴趣：").append(String.join(", ", request.getInterests()));
        }
        return desc.toString();
    }
    
    /**
     * 处理图片上传
     */
    public String uploadImage(MultipartFile file) throws IOException {
        if (file.isEmpty()) {
            throw new IOException("上传的文件为空");
        }
        
        // 创建上传目录
        Path uploadPath = Paths.get(UPLOAD_DIR);
        if (!Files.exists(uploadPath)) {
            Files.createDirectories(uploadPath);
        }
        
        // 生成唯一文件名
        String fileName = UUID.randomUUID().toString() + "_" + file.getOriginalFilename();
        Path filePath = uploadPath.resolve(fileName);
        
        // 保存文件
        Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);
        
        // 返回访问 URL（实际项目中应该使用对象存储或 CDN）
        return "/api/uploads/" + fileName;
    }
    
    /**
     * 保存或更新用户信息
     */
    private User saveOrUpdateUser(GenerateRequest request) {
        // 根据 UUID 查询用户
        User existingUser = userMapper.selectByUserUuid(request.getUserUuid());
        
        if (existingUser != null) {
            // 更新现有用户信息
            existingUser.setGender(request.getGender());
            existingUser.setMbtiType(request.getMbtiType());
            existingUser.setBirthDate(request.getBirthDate());
            existingUser.setZodiacSign(request.getZodiacSign());
            existingUser.setBirthTime(request.getBirthTime());
            existingUser.setBirthPlace(request.getBirthPlace());
            existingUser.setCurrentResidence(request.getCurrentResidence());
            existingUser.setInterests(JSON.toJSONString(request.getInterests()));
            existingUser.setCustomFeatures(request.getCustomFeatures());
            
            userMapper.updateById(existingUser);
            return existingUser;
        } else {
            // 创建新用户
            User newUser = new User();
            newUser.setUserUuid(request.getUserUuid());
            newUser.setGender(request.getGender());
            newUser.setMbtiType(request.getMbtiType());
            newUser.setBirthDate(request.getBirthDate());
            newUser.setZodiacSign(request.getZodiacSign());
            newUser.setBirthTime(request.getBirthTime());
            newUser.setBirthPlace(request.getBirthPlace());
            newUser.setCurrentResidence(request.getCurrentResidence());
            newUser.setInterests(JSON.toJSONString(request.getInterests()));
            newUser.setCustomFeatures(request.getCustomFeatures());
            
            userMapper.insert(newUser);
            return newUser;
        }
    }
    
    /**
     * 下载并保存图片到本地
     */
    private String saveImageToLocal(String imageUrl, Long userId) throws IOException {
        // 创建保存目录（按用户 ID 和日期分类）
        String dateDir = java.time.LocalDate.now().toString().replace("-", "");
        String userDir = IMAGE_SAVE_DIR + "user_" + userId + "/" + dateDir + "/";
        
        Path savePath = Paths.get(userDir);
        if (!Files.exists(savePath)) {
            Files.createDirectories(savePath);
        }
        
        // 生成唯一文件名
        String fileName = UUID.randomUUID().toString() + ".jpg";
        Path filePath = savePath.resolve(fileName);
        
        // 下载图片
        URL url = new URL(imageUrl);
        try (var inputStream = url.openStream()) {
            Files.copy(inputStream, filePath, StandardCopyOption.REPLACE_EXISTING);
        }
        
        return userDir + fileName;
    }
    
    /**
     * 保存生成记录
     */
    private void saveGenerationRecord(User user, String imagePath, String imageUrl, 
                                     String prompt, String description, GenerateRequest request) {
        GenerationRecord record = new GenerationRecord();
        record.setUserId(user.getId());
        record.setUserUuid(user.getUserUuid());
        record.setImagePath(imagePath);
        record.setImageUrl(imageUrl);
        record.setPrompt(prompt);
        record.setDescription(description);
        record.setRequestData(JSON.toJSONString(request));
        
        generationRecordMapper.insert(record);
    }
    
    // ==================== 分步保存用户信息方法 ====================
    
    /**
     * 保存性别信息
     */
    public ApiResponse<User> saveGender(UserGenderRequest request) {
        try {
            User user = getOrCreateUser(request.getUserUuid());
            user.setGender(request.getGender());
            
            if (user.getId() == null) {
                userMapper.insert(user);
            } else {
                userMapper.updateById(user);
            }
            
            return ApiResponse.success(user);
        } catch (Exception e) {
            e.printStackTrace();
            return ApiResponse.error("保存失败：" + e.getMessage());
        }
    }
    
    /**
     * 保存 MBTI 类型
     */
    public ApiResponse<User> saveMbti(UserMbtiRequest request) {
        try {
            User user = userMapper.selectByUserUuid(request.getUserUuid());
            if (user == null) {
                return ApiResponse.error(404, "用户不存在，请先填写基本信息");
            }
            
            user.setMbtiType(request.getMbtiType());
            userMapper.updateById(user);
            
            return ApiResponse.success(user);
        } catch (Exception e) {
            e.printStackTrace();
            return ApiResponse.error("保存失败：" + e.getMessage());
        }
    }
    
    /**
     * 保存出生日期和时间（自动计算星座）
     */
    public ApiResponse<User> saveBirthDate(UserBirthDateRequest request) {
        try {
            User user = userMapper.selectByUserUuid(request.getUserUuid());
            if (user == null) {
                return ApiResponse.error(404, "用户不存在，请先填写基本信息");
            }
            
            user.setBirthDate(request.getBirthDate());
            user.setBirthTime(request.getBirthTime());
            
            // 自动计算星座
            String zodiacSign = ZodiacUtil.getZodiacFromDate(request.getBirthDate());
            user.setZodiacSign(zodiacSign);
            
            userMapper.updateById(user);
            
            return ApiResponse.success(user);
        } catch (Exception e) {
            e.printStackTrace();
            return ApiResponse.error("保存失败：" + e.getMessage());
        }
    }
    
    /**
     * 保存地理位置信息
     */
    public ApiResponse<User> saveLocation(UserLocationRequest request) {
        try {
            User user = userMapper.selectByUserUuid(request.getUserUuid());
            if (user == null) {
                return ApiResponse.error(404, "用户不存在，请先填写基本信息");
            }
            
            user.setBirthPlace(request.getBirthPlace());
            user.setCurrentResidence(request.getCurrentResidence());
            userMapper.updateById(user);
            
            return ApiResponse.success(user);
        } catch (Exception e) {
            e.printStackTrace();
            return ApiResponse.error("保存失败：" + e.getMessage());
        }
    }
    
    /**
     * 保存兴趣爱好和自定义特征
     */
    public ApiResponse<User> saveInterests(UserInterestsRequest request) {
        try {
            User user = userMapper.selectByUserUuid(request.getUserUuid());
            if (user == null) {
                return ApiResponse.error(404, "用户不存在，请先填写基本信息");
            }
            
            user.setInterests(JSON.toJSONString(request.getInterests()));
            user.setCustomFeatures(request.getCustomFeatures());
            userMapper.updateById(user);
            
            return ApiResponse.success(user);
        } catch (Exception e) {
            e.printStackTrace();
            return ApiResponse.error("保存失败：" + e.getMessage());
        }
    }
    
    /**
     * 获取或创建用户
     */
    private User getOrCreateUser(String userUuid) {
        User existingUser = userMapper.selectByUserUuid(userUuid);
        
        if (existingUser != null) {
            return existingUser;
        }
        
        User newUser = new User();
        newUser.setUserUuid(userUuid);
        return newUser;
    }
    
    /**
     * 获取当前步骤信息
     */
    public StepInfo getStepInfo(String userUuid) {
        User user = userMapper.selectByUserUuid(userUuid);
        
        if (user == null) {
            return new StepInfo(1, 5, "性别", false, "请选择您的性别");
        }
        
        // 检查每一步的完成情况
        if (user.getGender() == null || user.getGender().isEmpty()) {
            return new StepInfo(1, 5, "性别", false, "请选择您的性别");
        }
        
        if (user.getMbtiType() == null || user.getMbtiType().isEmpty()) {
            return new StepInfo(2, 5, "MBTI 类型", false, "请选择或输入您的 MBTI 类型");
        }
        
        if (user.getBirthDate() == null || user.getBirthDate().isEmpty()) {
            return new StepInfo(3, 5, "出生日期", false, "请选择您的出生日期");
        }
        
        if (user.getBirthPlace() == null || user.getBirthPlace().isEmpty()) {
            return new StepInfo(4, 5, "出生地点", false, "请输入您的出生地点和当前居住地");
        }
        
        if (user.getInterests() == null || user.getInterests().isEmpty()) {
            return new StepInfo(5, 5, "兴趣爱好", false, "请选择您的兴趣爱好");
        }
        
        // 所有步骤完成
        return new StepInfo(6, 5, "完成", true, "所有信息已填写完毕，可以开始生成 AI 伴侣了！");
    }
}
