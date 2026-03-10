package com.github.Sheven.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.github.Sheven.dto.RagRequest;
import com.github.Sheven.dto.RagResponse;
import com.github.Sheven.entity.RagDocument;
import com.github.Sheven.mapper.RagDocumentMapper;
import com.github.Sheven.service.RagService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import jakarta.annotation.Resource;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * RAG 服务实现
 */
@Service
public class RagServiceImpl extends ServiceImpl<RagDocumentMapper, RagDocument> implements RagService {

    private static final Logger log = LoggerFactory.getLogger(RagServiceImpl.class);

    @Resource
    private ChatModel chatModel;

    @Resource
    private RagDocumentMapper ragDocumentMapper;

    // 系统提示词模板
    private static final String SYSTEM_PROMPT = """
            你是一个基于知识库的智能问答助手。请根据以下参考文档回答用户的问题。
            
            要求：
            1. 优先基于参考文档中的信息回答问题
            2. 如果参考文档中没有相关信息，请诚实告知用户
            3. 回答要准确、简洁、有条理
            4. 可以在回答末尾列出参考的文档来源
            
            参考文档：
            {context}
            
            用户问题：{question}
            
            请回答：
            """;

    @Override
    public RagResponse query(RagRequest request) {
        long startTime = System.currentTimeMillis();
        
        String question= request.getQuestion();
        Integer topK = request.getTopK() != null ? request.getTopK() : 3;
        Double similarityThreshold = request.getSimilarityThreshold() != null ? request.getSimilarityThreshold() : 0.5;
        
        log.info("RAG 查询 - 问题：{}, topK: {}, threshold: {}", question, topK, similarityThreshold);

        // 1. 从问题中提取关键词（简单实现：分词）
        String keywords = extractKeywords(question);
        log.debug("提取的关键词：{}", keywords);

        // 2. 检索相关文档
        List<RagDocument> documents = ragDocumentMapper.searchByKeywords(
                keywords, 
                topK, 
                similarityThreshold,
                request.getDocTypes()
        );
        
        log.info("检索到 {} 篇相关文档", documents.size());

        // 3. 构建上下文
        String context = buildContext(documents);

        // 4. 调用 AI 模型生成回答
        String answer;
        boolean ragEnhanced = !documents.isEmpty();
        
        if (ragEnhanced) {
            // 使用 RAG 增强
            String prompt = SYSTEM_PROMPT
                    .replace("{context}", context)
                    .replace("{question}", question);
            answer= chatModel.call(prompt);
        } else {
            // 没有参考文档，直接让 AI 回答
            answer = chatModel.call(question);
        }

        // 5. 构建响应
        long queryTime = System.currentTimeMillis() - startTime;
        
        List<RagResponse.ReferenceDocument> references = documents.stream()
                .map(doc -> RagResponse.ReferenceDocument.builder()
                        .id(doc.getId())
                        .title(doc.getTitle())
                        .content(truncateContent(doc.getContent(), 200))
                        .docType(doc.getDocType())
                        .similarityScore(doc.getSimilarityScore())
                        .source(doc.getSource())
                        .build())
                .collect(Collectors.toList());

        RagResponse.ResponseMetadata metadata = RagResponse.ResponseMetadata.builder()
                .totalReferences(documents.size())
                .queryTimeMs(queryTime)
                .model("qwen")
                .build();

        return RagResponse.builder()
                .answer(answer)
                .references(references)
                .ragEnhanced(ragEnhanced)
                .metadata(metadata)
                .build();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean saveDocument(RagDocument document) {
        log.info("保存文档：{}", document.getTitle());
        return save(document);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int batchSaveDocuments(List<RagDocument> documents) {
        log.info("批量导入 {} 篇文档", documents.size());
        
        int count = 0;
        for (RagDocument document : documents) {
            if (save(document)) {
                count++;
            }
        }
        return count;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteDocument(Long id) {
        log.info("删除文档 ID: {}", id);
        return removeById(id);
    }

    @Override
    public List<RagDocument> listAll() {
        return list(new LambdaQueryWrapper<RagDocument>()
                .orderByDesc(RagDocument::getUpdateTime));
    }

    /**
     * 从问题中提取关键词（简单实现）
     */
    private String extractKeywords(String question) {
        // 简单实现：移除标点符号和停用词
        String cleaned = question.replaceAll("[\\p{P}\\p{S}]", " ");
        
        // 中文停用词（可以扩展）
        String[] stopwords = {"的", "了", "是", "在", "和", "就", "都", "而", "及", "与", "或", "怎么", "如何", "什么", "哪里", "哪"};
        
        for (String stopword : stopwords) {
            cleaned = cleaned.replace(stopword, " ");
        }
        
        return cleaned.trim().replaceAll("\\s+", " ");
    }

    /**
     * 构建上下文文本
     */
    private String buildContext(List<RagDocument> documents) {
        StringBuilder sb = new StringBuilder();
        
        for (int i = 0; i < documents.size(); i++) {
            RagDocument doc = documents.get(i);
            sb.append("【参考文档 ").append(i + 1).append("】\n");
            sb.append("标题：").append(doc.getTitle()).append("\n");
            sb.append("类型：").append(doc.getDocType()).append("\n");
            if (doc.getSource() != null) {
                sb.append("来源：").append(doc.getSource()).append("\n");
            }
            sb.append("内容：").append(doc.getContent()).append("\n\n");
        }
        
        return sb.toString();
    }

    /**
     * 截断内容
     */
    private String truncateContent(String content, int maxLength) {
        if (content == null) {
            return null;
        }
        if (content.length() <= maxLength) {
            return content;
        }
        return content.substring(0, maxLength) + "...";
    }
}
