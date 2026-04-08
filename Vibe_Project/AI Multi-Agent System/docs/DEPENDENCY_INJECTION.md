# 依赖注入使用指南

## 概述
core/dependencies.py 提供了依赖注入函数，用于替换全局单例模式。

## 使用方法

### 在API路由中使用

**旧方式 (全局单例):**

    from memory.short_term import short_term_memory
    stats = short_term_memory.get_stats()

**新方式 (依赖注入):**

    from core.dependencies import get_short_term_memory

    @router.get("/example")
    async def example_route():
        memory = get_short_term_memory()
        stats = memory.get_stats()
        return stats

### 可用的注入函数

| 函数 | 返回类型 | 用途 |
|------|----------|------|
| get_guardrails() | Guardrails | 安全护栏检查 |
| get_token_manager() | TokenManager | Token管理 |
| get_short_term_memory() | ShortTermMemory | 短期记忆 |
| get_long_term_memory() | LongTermMemory | 长期记忆 |
| get_rag_pipeline() | RAGPipeline | RAG处理管道 |
| get_chroma_handler() | ChromaDBHandler | ChromaDB向量存储 |
| get_task_router() | TaskRouter | 任务路由 |
| get_conversation_agent() | ConversationAgent | 对话代理 |
| get_dev_agent() | DevAgent | 开发代理 |
| get_doc_agent() | DocAgent | 文档代理 |
| get_test_agent() | TestAgent | 测试代理 |
| get_rag_agent() | RAGAgent | RAG代理 |
| get_pm_agent() | PMAgent | 项目管理代理 |
| get_error_logger() | ErrorLogger | 错误日志 |

### 异步获取RAG管道

    from core.dependencies import get_rag_pipeline

    async def async_route():
        rag = await get_rag_pipeline()
        result = await rag.query(question="...", use_knowledge=True)
        return result

## 注意事项
1. 所有注入函数都使用 @lru_cache() 缓存结果
2. 异步函数使用 asyncio.Lock 保证线程安全
3. 替换是一个渐进过程，不需要一次性全部替换