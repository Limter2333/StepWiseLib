package com.github.sheven.partner.service;

import com.alibaba.fastjson.JSON;
import com.github.sheven.partner.dto.*;
import com.github.sheven.partner.mapper.GenerationRecordMapper;
import com.github.sheven.partner.mapper.UserMapper;
import com.github.sheven.partner.model.GenerationRecord;
import com.github.sheven.partner.model.User;
import com.github.sheven.partner.util.ZodiacUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.image.ImageModel;
import org.springframework.ai.image.ImagePrompt;
import org.springframework.ai.image.ImageResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
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
@Slf4j
@Service
public class PartnerGenerationService {
    
    private final ImageModel imageModel;
    
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
            @Autowired @Qualifier("dashScopeImageModel") ImageModel imageModel,
            UserMapper userMapper,
            GenerationRecordMapper generationRecordMapper) {
        this.imageModel = imageModel;
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
            ImagePrompt imagePrompt = new ImagePrompt(prompt);
            ImageResponse response = imageModel.call(imagePrompt);
            
            if (response != null && response.getResults() != null && !response.getResults().isEmpty()) {
                String imageUrl = response.getResults().get(0).getOutput().getUrl();
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
        log.info("保存或更新用户信息：userUuid={}, username={}", request.getUserUuid(), request.getUsername());
        
        // 根据 UUID 查询用户
        User existingUser = userMapper.selectByUserUuid(request.getUserUuid());
        
        if (existingUser != null) {
            log.info("更新现有用户信息，ID: {}", existingUser.getId());
            // 更新现有用户信息
            existingUser.setUsername(request.getUsername());
            existingUser.setGender(request.getGender());
            existingUser.setTargetGender(request.getTargetGender());
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
            log.info("创建新用户");
            // 创建新用户
            User newUser = new User();
            newUser.setUserUuid(request.getUserUuid());
            newUser.setUsername(request.getUsername());
            newUser.setGender(request.getGender());
            newUser.setTargetGender(request.getTargetGender());
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
     * 保存出生地点
     */
    public ApiResponse<User> saveBirthPlace(UserBirthPlaceRequest request) {
        try {
            User user = userMapper.selectByUserUuid(request.getUserUuid());
            if (user == null) {
                return ApiResponse.error(404, "用户不存在，请先填写基本信息");
            }
            
            user.setBirthPlace(request.getBirthPlace());
            userMapper.updateById(user);
            
            return ApiResponse.success(user);
        } catch (Exception e) {
            e.printStackTrace();
            return ApiResponse.error("保存失败：" + e.getMessage());
        }
    }
    
    /**
     * 保存当前居住地
     */
    public ApiResponse<User> saveCurrentResidence(UserCurrentResidenceRequest request) {
        try {
            User user = userMapper.selectByUserUuid(request.getUserUuid());
            if (user == null) {
                return ApiResponse.error(404, "用户不存在，请先填写基本信息");
            }
            
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
     * 保存用户步骤信息（包含用户名）
     */
    public ApiResponse<User> saveUserStep(UserStepRequest request) {
        try {
            log.info("保存用户步骤信息：username={}, step={}, userUuid={}", 
                    request.getUsername(), request.getStep(), request.getUserUuid());
            
            String userUuid;
            
            // 如果前端传递了 userUuid，则使用已有的 UUID
            if (request.getUserUuid() != null && !request.getUserUuid().isEmpty()) {
                userUuid = request.getUserUuid();
                log.info("使用已有的 userUuid: {}", userUuid);
            } else {
                // 否则生成新的 UUID
                userUuid = generateUserUuid(request.getUsername());
                log.info("生成新的 userUuid: {}", userUuid);
            }
            
            User user = userMapper.selectByUserUuid(userUuid);
            
            // 如果用户不存在，创建新用户
            if (user == null) {
                log.info("创建新用户：uuid={}, username={}", userUuid, request.getUsername());
                user = new User();
                user.setUserUuid(userUuid);
                user.setUsername(request.getUsername());
                
                // 从步骤数据中提取并保存用户信息
                extractAndSetUserData(user, request.getData());
                
                userMapper.insert(user);
                log.info("新用户创建成功，ID: {}", user.getId());
            } else {
                // 如果已存在，更新用户信息
                log.info("更新现有用户：id={}, uuid={}", user.getId(), userUuid);
                user.setUsername(request.getUsername());
                
                // 从步骤数据中提取并更新用户信息
                extractAndSetUserData(user, request.getData());
                
                userMapper.updateById(user);
                log.info("用户信息更新成功");
            }
            
            log.info("保存用户步骤信息成功，返回 userUuid: {}", user.getUserUuid());
            return ApiResponse.success(user);
        } catch (Exception e) {
            log.error("保存用户步骤信息失败", e);
            return ApiResponse.error("保存失败：" + e.getMessage());
        }
    }
    
    /**
     * 从步骤数据中提取并设置用户信息
     */
    @SuppressWarnings("unchecked")
    private void extractAndSetUserData(User user, Object data) {
        if (data == null) {
            return;
        }
        
        try {
            // 将 data 转换为 Map 进行处理
            if (data instanceof java.util.Map) {
                java.util.Map<String, Object> dataMap = (java.util.Map<String, Object>) data;
                
                // 提取基本信息
                String gender = (String) dataMap.get("gender");
                if (gender != null) {
                    user.setGender(gender);
                }
                
                String targetGender = (String) dataMap.get("targetGender");
                if (targetGender != null) {
                    user.setTargetGender(targetGender);
                }
                
                String mbtiType = (String) dataMap.get("mbtiType");
                if (mbtiType != null) {
                    user.setMbtiType(mbtiType);
                }
                
                String birthDate = (String) dataMap.get("birthDate");
                if (birthDate != null) {
                    user.setBirthDate(birthDate);
                }
                
                String zodiacSign = (String) dataMap.get("zodiacSign");
                if (zodiacSign != null) {
                    user.setZodiacSign(zodiacSign);
                }
                
                String birthTime = (String) dataMap.get("birthTime");
                if (birthTime != null) {
                    user.setBirthTime(birthTime);
                }
                
                String birthPlace = (String) dataMap.get("birthPlace");
                if (birthPlace != null) {
                    user.setBirthPlace(birthPlace);
                }
                
                String currentResidence = (String) dataMap.get("currentResidence");
                if (currentResidence != null) {
                    user.setCurrentResidence(currentResidence);
                }
                
                // 兴趣爱好（JSON 格式）
                Object interestsObj = dataMap.get("interests");
                if (interestsObj != null) {
                    user.setInterests(JSON.toJSONString(interestsObj));
                }
                
                // 自定义特征
                String customFeatures = (String) dataMap.get("customFeatures");
                if (customFeatures != null) {
                    user.setCustomFeatures(customFeatures);
                }
                
                log.info("提取用户数据完成：gender={}, targetGender={}, mbtiType={}", 
                        user.getGender(), user.getTargetGender(), user.getMbtiType());
            }
        } catch (Exception e) {
            log.warn("从步骤数据提取用户信息时发生异常：{}", e.getMessage());
        }
    }
    
    /**
     * 根据用户名生成唯一 UUID
     */
    private String generateUserUuid(String username) {
        // 使用用户名 + 时间戳生成唯一的 UUID
        return UUID.nameUUIDFromBytes((username + System.currentTimeMillis()).getBytes()).toString();
    }
    
    /**
     * 获取当前步骤信息
     */
    public StepInfo getStepInfo(String userUuid) {
        User user = userMapper.selectByUserUuid(userUuid);
        
        if (user == null) {
            return new StepInfo(1, 6, "性别", false, "请选择您的性别");
        }
        
        // 检查每一步的完成情况
        if (user.getGender() == null || user.getGender().isEmpty()) {
            return new StepInfo(1, 6, "性别", false, "请选择您的性别");
        }
        
        if (user.getMbtiType() == null || user.getMbtiType().isEmpty()) {
            return new StepInfo(2, 6, "MBTI 类型", false, "请选择或输入您的 MBTI 类型");
        }
        
        if (user.getBirthDate() == null || user.getBirthDate().isEmpty()) {
            return new StepInfo(3, 6, "出生日期", false, "请选择您的出生日期");
        }
        
        if (user.getBirthPlace() == null || user.getBirthPlace().isEmpty()) {
            return new StepInfo(4, 6, "出生地点", false, "请输入您的出生地点");
        }
        
        if (user.getCurrentResidence() == null || user.getCurrentResidence().isEmpty()) {
            return new StepInfo(5, 6, "当前居住地", false, "请输入您的当前居住地");
        }
        
        if (user.getInterests() == null || user.getInterests().isEmpty()) {
            return new StepInfo(6, 6, "兴趣爱好", false, "请选择您的兴趣爱好");
        }
        
        // 所有步骤完成
        return new StepInfo(7, 6, "完成", true, "所有信息已填写完毕，可以开始生成 AI 伴侣了！");
    }
}
