package com.github.Sheven.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.github.Sheven.dto.RagRequest;
import com.github.Sheven.dto.RagResponse;
import com.github.Sheven.entity.RagDocument;

import java.util.List;

/**
 * RAG 服务接口
 */
public interface RagService extends IService<RagDocument> {

    /**
     * RAG 智能问答
     * @param request 请求参数
     * @return AI 回答及参考文档
     */
    RagResponse query(RagRequest request);

    /**
     * 保存文档到知识库
     * @param document 文档
     * @return 是否成功
     */
    boolean saveDocument(RagDocument document);

    /**
     * 批量导入文档
     * @param documents 文档列表
     * @return 成功数量
     */
    int batchSaveDocuments(List<RagDocument> documents);

    /**
     * 删除文档
     * @param id 文档 ID
     * @return 是否成功
     */
    boolean deleteDocument(Long id);

    /**
     * 获取所有文档
     * @return 文档列表
     */
    List<RagDocument> listAll();
}
