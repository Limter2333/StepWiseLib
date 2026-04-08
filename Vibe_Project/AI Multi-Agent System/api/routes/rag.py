"""
RAG API 路由
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json

from knowledge.rag_pipeline import RAGPipeline, RAGConfig
from knowledge.vectorstore.chromadb_handler import ChromaDBHandler
from core.llm import get_llm
from logs.error_logs import error_logger, ErrorLevel
from core.response_cache import get_response_cache

router = APIRouter()

# 全局RAG管道实例
_rag_pipeline: Optional[RAGPipeline] = None
_response_cache = None


def get_rag_pipeline() -> RAGPipeline:
    """获取RAG管道实例"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


def get_cache():
    """获取响应缓存实例"""
    global _response_cache
    if _response_cache is None:
        _response_cache = get_response_cache()
    return _response_cache


class IndexRequest(BaseModel):
    """索引请求模型"""
    file_url: Optional[str] = None
    file_type: Optional[str] = None


class QueryRequest(BaseModel):
    """查询请求模型"""
    question: str
    session_id: Optional[str] = None
    top_k: Optional[int] = 5
    use_knowledge: bool = True


@router.post("/documents")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """上传并索引文档

    支持格式: PDF, Word, TXT, MD, HTML
    """
    try:
        # 保存上传文件
        import tempfile
        import os

        suffix = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # 后台索引
        background_tasks.add_task(index_document_background, tmp_path, file.filename)

        return {
            "status": "accepted",
            "message": f"Document {file.filename} queued for indexing",
            "filename": file.filename
        }

    except Exception as e:
        error_logger.log(
            error_type="UploadError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


async def index_document_background(file_path: str, filename: str):
    """后台索引任务"""
    try:
        rag = get_rag_pipeline()
        # 加载文档
        doc = rag.load_document(source=file_path)
        # 索引文档
        result = rag.index_documents(documents=[doc])
        error_logger.log(
            error_type="IndexComplete",
            message=f"Indexed {filename}: {result}",
            level=ErrorLevel.INFO
        )
    except Exception as e:
        error_logger.log(
            error_type="IndexError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
    finally:
        import os
        os.unlink(file_path)


@router.post("/query")
async def query_knowledge(
    question: str,
    session_id: Optional[str] = None,
    top_k: Optional[int] = 5,
    use_knowledge: bool = True,
    use_cache: bool = True
):
    """查询知识库

    Args:
        question: 问题
        session_id: 会话ID
        top_k: 返回数量
        use_knowledge: 是否使用知识库检索
        use_cache: 是否使用缓存（默认True）
    """
    # 输入验证
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if top_k is not None and top_k < 1:
        raise HTTPException(status_code=422, detail="top_k must be >= 1")

    try:
        cache = get_cache()

        # 生成缓存键（基于问题）
        cache_key = f"rag:query:{question.strip()}:{use_knowledge}"

        # 尝试从缓存获取
        if use_cache:
            cached_result, hit = cache.get(cache_key)
            if hit:
                return {
                    "success": True,
                    "answer": cached_result["answer"],
                    "sources": cached_result.get("sources", []),
                    "source_count": len(cached_result.get("sources", [])),
                    "used_rag": cached_result.get("used_rag", True),
                    "is_identity_answer": cached_result.get("is_identity_answer", False),
                    "cached": True
                }

        rag = get_rag_pipeline()

        # 调用RAG查询
        result = await rag.query(
            question=question,
            session_id=session_id,
            use_knowledge=use_knowledge
        )

        if result.get("error"):
            return {
                "success": False,
                "answer": result.get("answer", "Error processing request"),
                "sources": []
            }

        # 缓存结果
        if use_cache and not result.get("error"):
            cache.set(cache_key, result, ttl_seconds=1800)  # 30分钟缓存

        return {
            "success": True,
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "source_count": len(result.get("sources", [])),
            "used_rag": result.get("used_rag", True),
            "is_identity_answer": result.get("is_identity_answer", False),
            "cached": False
        }

    except Exception as e:
        error_logger.log(
            error_type="QueryError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


class QueryStreamRequest(BaseModel):
    """流式查询请求"""
    question: str
    session_id: Optional[str] = None
    top_k: Optional[int] = 5
    use_knowledge: bool = True


@router.post("/query-stream")
async def query_knowledge_stream(request: QueryStreamRequest):
    """流式查询知识库

    返回SSE格式的流式响应，包含：
    - 每个chunk的字符
    - 完成后返回sources和token_usage
    """
    async def generate():
        try:
            # 输入验证
            if not request.question or not request.question.strip():
                yield f"data: {json.dumps({'error': 'Question cannot be empty', 'type': 'error'})}\n\n"
                return

            rag = get_rag_pipeline()

            # 执行RAG查询
            result = await rag.query(
                question=request.question,
                session_id=request.session_id,
                use_knowledge=request.use_knowledge
            )

            response_text = result.get("answer", "Sorry, I couldn't process your request.")
            sources = result.get("sources", [])
            token_usage = result.get("token_usage", {})

            # 流式发送每个字符
            for char in response_text:
                yield f"data: {json.dumps({'content': char, 'type': 'chunk'})}\n\n"
                await asyncio.sleep(0.01)  # 10ms延迟控制速度

            # 发送完成信号
            yield f"data: {json.dumps({
                'type': 'done',
                'sources': sources,
                'source_count': len(sources),
                'token_usage': token_usage,
                'is_identity_answer': result.get('is_identity_answer', False)
            })}\n\n"

        except Exception as e:
            error_logger.log(
                error_type="StreamQueryError",
                message=str(e),
                level=ErrorLevel.ERROR
            )
            yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/documents")
async def list_documents():
    """列出已索引的文档"""
    try:
        rag = get_rag_pipeline()
        stats = rag.get_stats()

        return {
            "total_documents": stats["vectorstore"].get("count", 0),
            "stats": stats
        }

    except Exception as e:
        error_logger.log(
            error_type="ListError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    try:
        rag = get_rag_pipeline()
        vectorstore = rag.vectorstore

        # 使用doc_id作为chunk_id删除
        success = vectorstore.delete_document(doc_id)

        if success:
            return {
                "status": "deleted",
                "doc_id": doc_id,
                "message": "Document deleted successfully"
            }
        else:
            return {
                "status": "not_found",
                "doc_id": doc_id,
                "message": "Document not found or already deleted"
            }

    except Exception as e:
        error_logger.log(
            error_type="DeleteError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """获取RAG系统统计"""
    try:
        rag = get_rag_pipeline()
        stats = rag.get_stats()
        return stats

    except Exception as e:
        error_logger.log(
            error_type="StatsError",
            message=str(e),
            level=ErrorLevel.ERROR
        )


@router.get("/cache/stats")
async def get_cache_stats():
    """获取RAG查询缓存统计"""
    try:
        cache = get_cache()
        stats = cache.get_stats()
        return {
            "success": True,
            "cache_stats": stats
        }
    except Exception as e:
        error_logger.log(
            error_type="CacheStatsError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/clear")
async def clear_cache(prefix: Optional[str] = None):
    """清空RAG查询缓存

    Args:
        prefix: 可选的前缀，只清空匹配的键
    """
    try:
        cache = get_cache()
        count = cache.clear(prefix=f"rag:query:{prefix}" if prefix else None)
        return {
            "success": True,
            "message": f"Cleared {count} cache entries"
        }
    except Exception as e:
        error_logger.log(
            error_type="CacheClearError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


# ========== Multi-hop Reasoning API ==========

from knowledge.multihop_reasoner import get_multihop_reasoner, MultiHopReasoner

_multihop_reasoner: Optional[MultiHopReasoner] = None


def get_reasoner() -> MultiHopReasoner:
    """获取多跳推理器实例"""
    global _multihop_reasoner
    if _multihop_reasoner is None:
        _multihop_reasoner = get_multihop_reasoner()
        # 关联RAG管道
        _multihop_reasoner.set_rag_pipeline(get_rag_pipeline())
    return _multihop_reasoner


class MultiHopQueryRequest(BaseModel):
    """多跳查询请求"""
    question: str
    use_knowledge: bool = True
    max_hops: Optional[int] = 5


@router.post("/multihop")
async def multihop_query(request: MultiHopQueryRequest):
    """多跳推理查询

    将复杂问题分解为多个子问题，逐步检索并合并答案。

    Args:
        question: 复杂问题
        use_knowledge: 是否使用知识库检索
        max_hops: 最大跳数

    Returns:
        推理结果，包含分解的子问题和最终答案
    """
    try:
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        reasoner = get_reasoner()
        if request.max_hops:
            reasoner.max_hops = request.max_hops

        result = await reasoner.reason(
            question=request.question,
            use_knowledge=request.use_knowledge
        )

        return {
            "success": True,
            "original_question": result.original_question,
            "reasoning_type": result.reasoning_type.value,
            "hops": result.hops,
            "confidence": result.confidence,
            "final_answer": result.final_answer,
            "steps": [
                {
                    "step_id": s.step_id,
                    "question": s.question,
                    "answer": s.answer,
                    "confidence": s.confidence,
                    "is_final": s.is_final,
                    "sources_count": len(s.sources)
                }
                for s in result.steps
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        error_logger.log(
            error_type="MultiHopError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multihop/decompose")
async def decompose_question(question: str):
    """分解问题（不执行推理）

    预览复杂问题会被分解成哪些子问题。

    Args:
        question: 要分解的问题

    Returns:
        分解结果：子问题列表和推理类型
    """
    try:
        if not question or not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        from knowledge.multihop_reasoner import QuestionDecomposer
        decomposer = QuestionDecomposer()
        sub_questions, reasoning_type = decomposer.decompose(question)

        return {
            "success": True,
            "original_question": question,
            "sub_questions": sub_questions,
            "reasoning_type": reasoning_type.value,
            "step_count": len(sub_questions)
        }

    except HTTPException:
        raise
    except Exception as e:
        error_logger.log(
            error_type="DecomposeError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
