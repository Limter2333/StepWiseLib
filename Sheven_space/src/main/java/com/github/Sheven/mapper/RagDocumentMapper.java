package com.github.Sheven.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.github.Sheven.entity.RagDocument;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * RAG 文档 Mapper
 */
@Mapper
public interface RagDocumentMapper extends BaseMapper<RagDocument> {

    /**
     * 基于关键词检索相关文档（全文搜索）
     * @param keywords 关键词
     * @param topK 返回数量
     * @return 文档列表
     */
    List<RagDocument> searchByKeywords(@Param("keywords") String keywords,
                                        @Param("topK") Integer topK,
                                        @Param("similarityThreshold") Double similarityThreshold,
                                        @Param("docTypes") List<String> docTypes);

    /**
     * 基于标题和内容模糊搜索
     */
    List<RagDocument> searchByKeyword(@Param("keyword") String keyword,
                                       @Param("topK") Integer topK);
}
