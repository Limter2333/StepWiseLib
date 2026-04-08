"""
Model Context Protocol (MCP)
===========================

【学习要点】
1. 什么是MCP?
   - 管理AI模型上下文窗口的协议
   - 解决长对话超出token限制的问题
   - 智能压缩和扩展上下文

2. 核心问题
   - LLM有固定上下文窗口(如4K, 16K, 100K tokens)
   - 长对话会超出限制
   - 需要智能管理上下文

3. MCP策略
   - Context Window: 固定窗口滑动
   - Context Compression: 压缩重要信息
   - Context Expansion: 动态扩展窗口
   - Priority-based: 按优先级保留

4. 压缩技术
   - 摘要压缩: 保留核心要点
   - 关键信息提取: 只保留关键实体
   - 对话摘要: 定期汇总对话
"""

from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class ContextPriority(Enum):
    """上下文优先级"""
    CRITICAL = 3   # 必须保留（系统指令、关键实体）
    HIGH = 2      # 优先保留（用户明确要求、重要上下文）
    MEDIUM = 1    # 可压缩（一般对话内容）
    LOW = 0       # 可丢弃（闲聊、历史日志）


@dataclass
class ContextSegment:
    """上下文片段

    【结构】
    - id: 唯一标识
    - content: 内容文本
    - priority: 优先级
    - tokens: token数量（估算）
    - timestamp: 创建时间
    - metadata: 元数据
    """
    id: str
    content: str
    priority: ContextPriority = ContextPriority.MEDIUM
    tokens: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.tokens == 0:
            # 简单估算: 中文≈2 tokens/字, 英文≈1.3 tokens/词
            if self.is_chinese():
                self.tokens = len(self.content) // 2
            else:
                self.tokens = len(self.content.split()) * 4 // 3

    def is_chinese(self) -> bool:
        """判断是否包含中文"""
        return any('\u4e00' <= char <= '\u9fff' for char in self.content)


@dataclass
class ContextWindow:
    """上下文窗口

    【概念】
    - max_tokens: 最大token数
    - segments: 当前窗口内的片段
    - total_tokens: 当前总token数
    """
    max_tokens: int
    segments: List[ContextSegment] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return sum(s.tokens for s in self.segments)

    @property
    def available_tokens(self) -> int:
        return max(0, self.max_tokens - self.total_tokens)

    def is_full(self) -> bool:
        return self.total_tokens >= self.max_tokens

    def add(self, segment: ContextSegment) -> bool:
        """添加片段，成功返回True"""
        if self.total_tokens + segment.tokens > self.max_tokens:
            return False
        self.segments.append(segment)
        return True

    def remove(self, segment_id: str) -> bool:
        """移除片段"""
        for i, seg in enumerate(self.segments):
            if seg.id == segment_id:
                self.segments.pop(i)
                return True
        return False

    def clear(self):
        """清空窗口"""
        self.segments.clear()

    def get_all_content(self) -> str:
        """获取窗口内所有内容"""
        return "\n".join(seg.content for seg in self.segments)


class CompressionStrategy:
    """压缩策略基类"""

    def compress(self, segments: List[ContextSegment]) -> List[ContextSegment]:
        """压缩片段列表"""
        raise NotImplementedError


class PriorityCompression(CompressionStrategy):
    """基于优先级的压缩

    【策略】
    1. 先删除LOW优先级
    2. 再压缩MEDIUM优先级
    3. 最后才考虑HIGH
    4. CRITICAL永不删除
    """

    def __init__(self, target_tokens: int):
        self.target_tokens = target_tokens

    def compress(self, segments: List[ContextSegment]) -> List[ContextSegment]:
        if not segments:
            return []

        # 按优先级分组
        by_priority = {p: [] for p in ContextPriority}
        for seg in segments:
            by_priority[seg.priority].append(seg)

        result = []

        # 1. 先保留CRITICAL
        critical = by_priority[ContextPriority.CRITICAL]
        critical_tokens = sum(s.tokens for s in critical)
        result.extend(critical)

        # 2. 再处理HIGH
        high = by_priority[ContextPriority.HIGH]
        high_tokens = sum(s.tokens for s in high)
        if critical_tokens + high_tokens <= self.target_tokens:
            result.extend(high)
        else:
            # 部分保留
            remaining = self.target_tokens - critical_tokens
            result.extend(self._fit_segments(high, remaining))

        # 3. 然后MEDIUM
        if result:
            current_tokens = sum(s.tokens for s in result)
            remaining = self.target_tokens - current_tokens
            if remaining > 0:
                medium = by_priority[ContextPriority.MEDIUM]
                result.extend(self._fit_segments(medium, remaining))

        # 4. 最后LOW
        if result:
            current_tokens = sum(s.tokens for s in result)
            remaining = self.target_tokens - current_tokens
            if remaining > 0:
                low = by_priority[ContextPriority.LOW]
                result.extend(self._fit_segments(low, remaining))

        return result

    def _fit_segments(self, segments: List[ContextSegment], max_tokens: int) -> List[ContextSegment]:
        """选择能放入的片段"""
        result = []
        total = 0
        for seg in segments:
            if total + seg.tokens <= max_tokens:
                result.append(seg)
                total += seg.tokens
        return result


class SummarizeCompression(CompressionStrategy):
    """摘要压缩

    【策略】
    - 对低优先级内容生成摘要
    - 保留关键实体和意图
    - 大幅减少token数
    """

    def __init__(self, summarizer: Optional[Callable] = None):
        self.summarizer = summarizer or self._simple_summarize

    def _simple_summarize(self, content: str, max_length: int = 200) -> str:
        """简单摘要 - 保留首尾句+关键信息"""
        if len(content) <= max_length:
            return content

        # 提取关键句子（简化版）
        sentences = content.replace('!', '.').replace('?', '.').split('.')
        if len(sentences) <= 3:
            return content

        # 保留首句和尾句
        summary = sentences[0].strip()
        if len(sentences) > 1:
            summary += ". " + sentences[-1].strip()

        return summary + f" (内容已摘要，原长度{len(content)}字符)"

    def compress(self, segments: List[ContextSegment]) -> List[ContextSegment]:
        compressed = []
        for seg in segments:
            if seg.priority in [ContextPriority.LOW, ContextPriority.MEDIUM]:
                # 压缩
                new_content = self._simple_summarize(seg.content)
                new_tokens = len(new_content) // 2
                compressed.append(ContextSegment(
                    id=f"{seg.id}_compressed",
                    content=new_content,
                    priority=seg.priority,
                    tokens=new_tokens,
                    metadata={**seg.metadata, "compressed": True}
                ))
            else:
                # 保留
                compressed.append(seg)
        return compressed


class ContextManager:
    """上下文管理器

    【核心功能】
    1. 维护上下文窗口
    2. 智能添加新内容
    3. 自动压缩超限内容
    4. 支持多种压缩策略

    【使用流程】
    1. 初始化: 设置max_tokens和策略
    2. 添加: add_context() 添加新内容
    3. 压缩: compress() 当超出限制
    4. 获取: get_context() 获取当前上下文
    """

    def __init__(
        self,
        max_tokens: int = 4000,
        compression_strategy: Optional[CompressionStrategy] = None
    ):
        self.max_tokens = max_tokens
        self.window = ContextWindow(max_tokens=max_tokens)
        self.compression_strategy = compression_strategy or PriorityCompression(max_tokens // 2)

        # 历史记录（用于追踪）
        self.history: List[Dict] = []

        # 统计
        self.stats = {
            "total_adds": 0,
            "total_compressions": 0,
            "total_tokens_saved": 0
        }

    def add_context(
        self,
        content: str,
        priority: ContextPriority = ContextPriority.MEDIUM,
        metadata: Optional[Dict] = None
    ) -> str:
        """添加上下文

        Returns:
            context_id: 添加的上下文的ID
        """
        segment = ContextSegment(
            id=f"ctx_{len(self.history)}",
            content=content,
            priority=priority,
            metadata=metadata or {}
        )

        # 检查是否需要压缩
        if self.window.total_tokens + segment.tokens > self.max_tokens:
            self._compress()

        # 添加到窗口
        self.window.add(segment)

        # 记录历史
        self.history.append({
            "action": "add",
            "segment_id": segment.id,
            "tokens": segment.tokens,
            "timestamp": datetime.now().isoformat()
        })

        self.stats["total_adds"] += 1
        return segment.id

    def _compress(self):
        """压缩上下文"""
        original_tokens = self.window.total_tokens

        # 使用策略压缩
        compressed = self.compression_strategy.compress(self.window.segments)

        # 计算节省的token
        saved_tokens = original_tokens - sum(s.tokens for s in compressed)

        # 更新窗口
        self.window.clear()
        for seg in compressed:
            self.window.add(seg)

        # 记录
        self.history.append({
            "action": "compress",
            "original_tokens": original_tokens,
            "new_tokens": sum(s.tokens for s in compressed),
            "saved_tokens": saved_tokens,
            "timestamp": datetime.now().isoformat()
        })

        self.stats["total_compressions"] += 1
        self.stats["total_tokens_saved"] += saved_tokens

    def get_context(self) -> str:
        """获取当前上下文"""
        return self.window.get_all_content()

    def get_context_with_metadata(self) -> List[Dict]:
        """获取带元数据的上下文"""
        return [
            {
                "id": seg.id,
                "content": seg.content,
                "priority": seg.priority.name,
                "tokens": seg.tokens,
                "metadata": seg.metadata
            }
            for seg in self.window.segments
        ]

    def clear(self):
        """清空上下文"""
        self.window.clear()
        self.history.append({
            "action": "clear",
            "timestamp": datetime.now().isoformat()
        })

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "current_tokens": self.window.total_tokens,
            "max_tokens": self.max_tokens,
            "utilization": f"{self.window.total_tokens / self.max_tokens * 100:.1f}%",
            "segment_count": len(self.window.segments)
        }

    def get_history_summary(self, limit: int = 10) -> List[Dict]:
        """获取历史摘要"""
        return self.history[-limit:]


# 全局实例
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """获取上下文管理器实例"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 初始化
from mcp import ContextManager, ContextPriority

manager = ContextManager(max_tokens=4000)

# 2. 添加不同优先级的上下文
manager.add_context(
    "系统指令：你是一个有帮助的AI助手",
    priority=ContextPriority.CRITICAL
)

manager.add_context(
    "用户：帮我写一段Python代码",
    priority=ContextPriority.HIGH
)

manager.add_context(
    "用户：昨天天气不错",
    priority=ContextPriority.LOW
)

# 3. 获取当前上下文
context = manager.get_context()
print(f"当前上下文: {context}")

# 4. 获取统计
stats = manager.get_stats()
print(f"Token使用: {stats['utilization']}")
print(f"压缩次数: {stats['total_compressions']}")

# 5. 切换压缩策略
from mcp import SummarizeCompression
manager.compression_strategy = SummarizeCompression()
"""


class MCPServer:
    """MCP服务器

    【概念】
    提供上下文管理服务
    支持多客户端
    """

    def __init__(self, max_tokens: int = 4000):
        self.manager = ContextManager(max_tokens=max_tokens)
        self.clients: Dict[str, ContextManager] = {}

    def create_client_context(self, client_id: str) -> ContextManager:
        """为客户端创建独立上下文"""
        client_ctx = ContextManager(max_tokens=self.manager.max_tokens)
        self.clients[client_id] = client_ctx
        return client_ctx

    def get_client_context(self, client_id: str) -> Optional[ContextManager]:
        """获取客户端上下文"""
        return self.clients.get(client_id)

    def close_client(self, client_id: str):
        """关闭客户端"""
        if client_id in self.clients:
            del self.clients[client_id]
