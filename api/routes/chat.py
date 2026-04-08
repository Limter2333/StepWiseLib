"""
Chat API 路由
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, AsyncIterator
from datetime import datetime
import asyncio
import json

from memory.short_term import short_term_memory, MemoryType, ConversationSession
from agents.conversation_agent.conversation_agent import conversation_agent, MessageRole
from core.guardrails import guardrails
from core.llm import get_llm
from logs.error_logs import error_logger, ErrorLevel
from knowledge.rag_pipeline import RAGPipeline

router = APIRouter()

# 全局RAG管道实例
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag() -> RAGPipeline:
    """获取RAG管道实例"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


class Message(BaseModel):
    """消息模型"""
    role: str  # user / assistant
    content: str


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: str
    use_knowledge: bool = True


class ChatResponse(BaseModel):
    """聊天响应"""
    message: str
    session_id: str
    sources: List[dict] = []
    token_usage: int = 0


class SessionCreate(BaseModel):
    """创建会话"""
    user_id: Optional[str] = None
    metadata: Optional[dict] = {}


@router.post("/chat")
async def chat(request: ChatRequest):
    """聊天接口

    Args:
        request: 包含消息和会话ID的请求
    """
    try:
        # 输入检查
        guard_result = guardrails.check_input(request.message)
        if not guard_result.passed:
            raise HTTPException(status_code=400, detail=guard_result.message)

        # 记录用户消息
        await conversation_agent.send_message(
            session_id=request.session_id,
            message=request.message,
            role=MessageRole.USER
        )

        # 调用RAG管道进行知识增强回答
        rag = get_rag()
        result = await rag.query(
            question=request.message,
            session_id=request.session_id,
            use_knowledge=request.use_knowledge
        )

        response_text = result.get("answer", "Sorry, I couldn't process your request.")
        sources = result.get("sources", [])
        llm_token_usage = result.get("token_usage", {})

        # Per-session token tracking
        if request.session_id:
            session = short_term_memory.get_or_create_session(request.session_id)
            session.add_token_usage(
                prompt_tokens=llm_token_usage.get("prompt_tokens", 0),
                completion_tokens=llm_token_usage.get("completion_tokens", 0)
            )

        # 获取Token使用量（global + per-session）
        try:
            from core.token_manager import token_manager
            global_token_status = token_manager.get_status()
            global_token_usage = global_token_status.get("current_usage", 0)
        except:
            global_token_usage = 0

        # 获取per-session token使用量
        session_token_usage = short_term_memory.get_session_token_usage(request.session_id)
        session_total = session_token_usage.get("total_tokens", 0) if session_token_usage else 0

        # 记录助手回复
        await conversation_agent.send_message(
            session_id=request.session_id,
            message=response_text,
            role=MessageRole.ASSISTANT
        )

        return {
            "message": response_text,
            "session_id": request.session_id,
            "sources": sources,
            "token_usage": {
                "global_total": global_token_usage,
                "session_total": session_total,
                "this_call": llm_token_usage
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error_logger.log(
            error_type="ChatError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


class StreamChatRequest(BaseModel):
    """流式聊天请求"""
    message: str
    session_id: str
    use_knowledge: bool = True


@router.post("/chat/stream")
async def stream_chat(request: StreamChatRequest):
    """流式聊天接口

    Args:
        request: 包含消息和会话ID的请求

    Returns:
        SSE流式响应
    """
    async def generate():
        try:
            # 输入检查
            guard_result = guardrails.check_input(request.message)
            if not guard_result.passed:
                yield f"data: {json.dumps({'error': guard_result.message, 'type': 'error'})}\n\n"
                return

            # 记录用户消息
            await conversation_agent.send_message(
                session_id=request.session_id,
                message=request.message,
                role=MessageRole.USER
            )

            # 获取RAG管道
            rag = get_rag()

            # 调用RAG查询（非流式，但分块返回）
            result = await rag.query(
                question=request.message,
                session_id=request.session_id,
                use_knowledge=request.use_knowledge
            )

            response_text = result.get("answer", "Sorry, I couldn't process your request.")
            sources = result.get("sources", [])
            llm_token_usage = result.get("token_usage", {})

            # Per-session token tracking
            if request.session_id:
                session = short_term_memory.get_or_create_session(request.session_id)
                session.add_token_usage(
                    prompt_tokens=llm_token_usage.get("prompt_tokens", 0),
                    completion_tokens=llm_token_usage.get("completion_tokens", 0)
                )

            # 记录助手回复
            await conversation_agent.send_message(
                session_id=request.session_id,
                message=response_text,
                role=MessageRole.ASSISTANT
            )

            # 流式发送每个字符
            for char in response_text:
                yield f"data: {json.dumps({'content': char, 'type': 'chunk'})}\n\n"
                await asyncio.sleep(0.01)  # 10ms延迟以控制速度

            # 发送完成信号
            yield f"data: {json.dumps({
                'type': 'done',
                'sources': sources,
                'token_usage': llm_token_usage
            })}\n\n"

        except Exception as e:
            error_logger.log(
                error_type="StreamChatError",
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


@router.post("/sessions")
async def create_session(request: SessionCreate):
    """创建新会话"""
    try:
        session = await conversation_agent.create_session(
            session_id=f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=request.user_id,
            metadata=request.metadata or {}
        )

        return {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat()
        }

    except Exception as e:
        error_logger.log(
            error_type="SessionError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    """列出所有会话"""
    try:
        stats = short_term_memory.get_stats()

        return {
            "active_sessions": stats.get("active_sessions", 0),
            "total_memory_items": stats.get("total_memory_items", 0)
        }

    except Exception as e:
        error_logger.log(
            error_type="ListSessionsError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """获取会话信息"""
    try:
        session = await conversation_agent.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_active": session.last_active.isoformat(),
            "memory_items_count": len(session.memory_items)
        }

    except HTTPException:
        raise
    except Exception as e:
        error_logger.log(
            error_type="GetSessionError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_history(
    session_id: str,
    limit: int = 20
):
    """获取会话历史"""
    try:
        # 检查会话是否存在
        session = await conversation_agent.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        history = await conversation_agent.get_conversation_history(
            session_id=session_id,
            limit=limit
        )

        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in history
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        error_logger.log(
            error_type="HistoryError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/summary")
async def get_summary(session_id: str):
    """获取会话摘要"""
    try:
        # 检查会话是否存在
        session = await conversation_agent.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        summary = await conversation_agent.summarize_conversation(session_id)

        return {
            "session_id": session_id,
            "summary": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        error_logger.log(
            error_type="SummaryError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        success = await conversation_agent.clear_session(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "status": "deleted",
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        error_logger.log(
            error_type="DeleteSessionError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


class IntentDetectRequest(BaseModel):
    """意图检测请求"""
    message: str
    session_id: Optional[str] = None


class IntentEntity(BaseModel):
    """识别的实体"""
    type: str
    value: str
    confidence: float


class IntentResponse(BaseModel):
    """意图检测响应"""
    intent: str
    confidence: float
    sentiment: str
    entities: List[IntentEntity]
    keywords: List[str]


@router.post("/intent/detect", response_model=IntentResponse)
async def detect_intent(request: IntentDetectRequest):
    """检测用户意图

    使用关键词+LLM混合方式识别用户意图，支持：
    - 意图分类（问答、任务执行、文档管理、对话闲聊等）
    - 情感分析（积极、消极、中性）
    - 实体提取（时间、数量、邮箱、URL等）
    - 关键词提取

    Args:
        request: 包含消息和可选session_id的请求

    Returns:
        IntentResponse: 意图、情感、实体、关键词
    """
    try:
        message = request.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # 使用ConversationAgent的意图检测方法
        # 优先使用LLM检测，失败后回退到关键词检测
        intent_result = await conversation_agent.detect_intent_with_llm(
            message=message,
            context=""
        )

        # 基础实体提取
        entities_result = await conversation_agent.extract_entities(message)

        # 情感分析（简化实现）
        sentiment = "neutral"
        positive_words = ["好", "喜欢", "谢谢", "棒", "不错", "good", "great", "thanks", "nice"]
        negative_words = ["差", "烂", "讨厌", "不好", "bad", "hate", "terrible", "awful", "wrong"]

        msg_lower = message.lower()
        pos_count = sum(1 for w in positive_words if w in msg_lower)
        neg_count = sum(1 for w in negative_words if w in msg_lower)

        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"

        # 提取关键词（简单实现：取长度适中的词）
        words = message.replace("？", "?").replace("！", "!").split()
        keywords = [w for w in words if 2 <= len(w) <= 10][:5]

        # 构建实体列表
        entities = []
        if entities_result.get("has_question"):
            entities.append(IntentEntity(type="question_mark", value="?", confidence=1.0))
        if entities_result.get("has_number"):
            import re
            numbers = re.findall(r'\d+', message)
            for num in numbers[:3]:
                entities.append(IntentEntity(type="number", value=num, confidence=0.9))
        if "language" in entities_result:
            entities.append(IntentEntity(
                type="language",
                value=entities_result["language"],
                confidence=0.95
            ))

        return IntentResponse(
            intent=intent_result,
            confidence=0.85,
            sentiment=sentiment,
            entities=entities,
            keywords=keywords
        )

    except HTTPException:
        raise
    except Exception as e:
        error_logger.log(
            error_type="IntentDetectError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/token-usage")
async def get_token_usage():
    """获取Token使用量"""
    try:
        from core.token_manager import token_manager
        status = token_manager.get_status()
        return {
            "success": True,
            "token_usage": status.get("current_usage", 0),
            "prompt_tokens": status.get("prompt_tokens", 0),
            "completion_tokens": status.get("completion_tokens", 0),
            "requests": status.get("requests", 0),
            "last_updated": status.get("last_updated", "")
        }
    except Exception as e:
        error_logger.log(
            error_type="TokenUsageError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/token-usage/reset")
async def reset_token_usage():
    """重置Token使用量"""
    try:
        from core.token_manager import token_manager
        token_manager.reset()
        return {"success": True, "message": "Token usage reset"}
    except Exception as e:
        error_logger.log(
            error_type="TokenResetError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/token-usage")
async def get_session_token_usage(session_id: str):
    """获取指定会话的Token使用量（per-session tracking）"""
    try:
        session_token = short_term_memory.get_session_token_usage(session_id)
        if session_token is None:
            raise HTTPException(status_code=404, detail="Session not found")

        # 同时返回全局统计
        from core.token_manager import token_manager
        global_status = token_manager.get_status()

        return {
            "session_id": session_id,
            "session_tokens": session_token,
            "global_tokens": {
                "total": global_status.get("current_usage", 0),
                "prompt": global_status.get("prompt_tokens", 0),
                "completion": global_status.get("completion_tokens", 0),
                "requests": global_status.get("requests", 0)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log(
            error_type="SessionTokenUsageError",
            message=str(e),
            level=ErrorLevel.ERROR
        )
        raise HTTPException(status_code=500, detail=str(e))
