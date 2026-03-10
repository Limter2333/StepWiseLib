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
    @Select("SELECT *, MATCH(title, content) AGAINST(#{keywords} IN NATURAL LANGUAGE MODE) AS similarity_score " +
            "FROM rag_document " +
            "WHERE MATCH(title, content) AGAINST(#{keywords} IN NATURAL LANGUAGE MODE) >= #{similarityThreshold} " +
            "<script>" +
            "<if test='docTypes != null and docTypes.size() > 0'>" +
            "AND doc_type IN " +
            "<foreach item='type' collection='docTypes' open='(' separator=',' close=')'>" +
            "#{type}" +
            "</foreach>" +
            "</if>" +
            "</script> " +
            "ORDER BY similarity_score DESC " +
            "LIMIT #{topK}")
    List<RagDocument> searchByKeywords(@Param("keywords") String keywords,
                                        @Param("topK") Integer topK,
                                        @Param("similarityThreshold") Double similarityThreshold,
                                        @Param("docTypes") List<String> docTypes);

    /**
     * 基于标题和内容模糊搜索
     */
    @Select("SELECT * FROM rag_document " +
            "WHERE title LIKE CONCAT('%', #{keyword}, '%') " +
            "OR content LIKE CONCAT('%', #{keyword}, '%') " +
            "ORDER BY update_time DESC " +
            "LIMIT #{topK}")
    List<RagDocument> searchByKeyword(@Param("keyword") String keyword,
                                       @Param("topK") Integer topK);
}
