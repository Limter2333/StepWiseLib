"""
流式输出美化器 - Stream Output Beautifier
==========================================

【功能】
1. Markdown渲染 - 实时识别并标记Markdown元素
2. 词组流式 - 按词组发送而非逐字，更自然
3. 元数据流式 - 实时显示token计数、速度
4. 代码块缓冲 - 完整代码块后再发送

【使用场景】
- 聊天流式输出美化
- RAG查询流式输出
- Agent执行结果流式展示
"""

from typing import Dict, List, Optional, Any, Callable, AsyncIterator
from dataclasses import dataclass
from datetime import datetime
import re
import json
import asyncio


@dataclass
class StreamConfig:
    """流式配置"""
    chunk_by: str = "word"  # "char" | "word" | "sentence"
    word_delimiter: str = " "
    markdown_enabled: bool = True
    code_block_buffer: int = 3  # 代码块缓冲行数
    emit_speed_metrics: bool = True
    emit_token_count: bool = True


class MarkdownTokenizer:
    """Markdown语法识别器

    识别Markdown元素以便前端渲染
    """

    # Markdown元素模式
    PATTERNS = {
        "code_block": re.compile(r"^```(\w*)$"),  # 代码块开始
        "code_block_end": re.compile(r"^```$"),   # 代码块结束
        "header": re.compile(r"^(#{1,6})\s+(.+)$"),  # 标题
        "bold": re.compile(r"\*\*(.+?)\*\*"),     # 粗体
        "italic": re.compile(r"\*(.+?)\*"),       # 斜体
        "code": re.compile(r"`([^`]+)`"),         # 行内代码
        "link": re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),  # 链接
        "list_item": re.compile(r"^[-*]\s+(.+)$"),  # 列表项
        "numbered_list": re.compile(r"^\d+\.\s+(.+)$"),  # 数字列表
        "blockquote": re.compile(r"^>\s+(.+)$"),   # 引用
        "hr": re.compile(r"^---+$"),              # 分隔线
    }

    @classmethod
    def tokenize(cls, text: str) -> List[Dict[str, Any]]:
        """标记化文本，识别Markdown元素

        Returns:
            List of tokens with type and content
        """
        tokens = []
        lines = text.split('\n')

        in_code_block = False
        code_block_lang = ""

        for line in lines:
            # 代码块状态
            code_end_match = cls.PATTERNS["code_block_end"].match(line)
            code_match = cls.PATTERNS["code_block"].match(line)

            # 如果在代码块内，先检查是否结束
            if in_code_block:
                if code_end_match:
                    in_code_block = False
                    tokens.append({
                        "type": "code_block_end",
                        "content": line
                    })
                    continue
                else:
                    # 代码块内直接添加
                    tokens.append({
                        "type": "code_line",
                        "content": line
                    })
                    continue

            # 不在代码块内，检查是否开始
            if code_match:
                in_code_block = True
                code_block_lang = code_match.group(1)
                tokens.append({
                    "type": "code_block_start",
                    "content": line,
                    "lang": code_block_lang
                })
                continue

            # 检查标题
            header_match = cls.PATTERNS["header"].match(line)
            if header_match:
                tokens.append({
                    "type": "header",
                    "level": len(header_match.group(1)),
                    "content": header_match.group(2)
                })
                continue

            # 检查引用
            quote_match = cls.PATTERNS["blockquote"].match(line)
            if quote_match:
                tokens.append({
                    "type": "blockquote",
                    "content": quote_match.group(1)
                })
                continue

            # 检查列表
            list_match = cls.PATTERNS["list_item"].match(line)
            if list_match:
                tokens.append({
                    "type": "list_item",
                    "content": list_match.group(1)
                })
                continue

            num_match = cls.PATTERNS["numbered_list"].match(line)
            if num_match:
                tokens.append({
                    "type": "numbered_item",
                    "content": num_match.group(1)
                })
                continue

            # 检查分隔线
            if cls.PATTERNS["hr"].match(line):
                tokens.append({
                    "type": "hr",
                    "content": line
                })
                continue

            # 普通文本行
            if line.strip():
                tokens.append({
                    "type": "paragraph",
                    "content": line
                })

        return tokens


class StreamBeautifier:
    """流式美化器"""

    def __init__(self, config: Optional[StreamConfig] = None):
        self.config = config or StreamConfig()

    def chunk_text(self, text: str) -> List[str]:
        """将文本分块"""
        if self.config.chunk_by == "char":
            return list(text)

        elif self.config.chunk_by == "word":
            # 按空格分割，保留标点
            words = []
            current = ""

            for char in text:
                current += char
                if char in " \t\n":
                    if current.strip():
                        words.append(current)
                    current = ""

            if current.strip():
                words.append(current)

            return words if words else [text]

        elif self.config.chunk_by == "sentence":
            # 按句子分割
            sentences = re.split(r"([.!?。！？]+)", text)
            result = []
            for i in range(0, len(sentences) - 1, 2):
                result.append(sentences[i] + sentences[i + 1])
            if sentences[-1].strip():
                result.append(sentences[-1])
            return result if result else [text]

        return [text]

    async def stream_text(
        self,
        text: str,
        speed: float = 0.02,
        progress_callback: Optional[Callable] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式发送文本

        Args:
            text: 要发送的文本
            speed: 每次发送的延迟（秒）
            progress_callback: 进度回调

        Yields:
            流式数据字典
        """
        chunks = self.chunk_text(text)
        total = len(chunks)
        start_time = datetime.now()
        chars_streamed = 0

        for i, chunk in enumerate(chunks):
            # 发送块
            token_type = "text"
            if self.config.markdown_enabled:
                tokens = MarkdownTokenizer.tokenize(chunk)
                if tokens:
                    token_type = tokens[0].get("type", "text")

            yield {
                "type": "chunk",
                "content": chunk,
                "chunk_type": token_type,
                "progress": (i + 1) / total,
                "chars_streamed": chars_streamed
            }

            chars_streamed += len(chunk)

            # 发送速度指标
            if self.config.emit_speed_metrics and i > 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > 0:
                    chars_per_sec = chars_streamed / elapsed
                    yield {
                        "type": "metrics",
                        "chars_per_second": round(chars_per_sec, 1),
                        "elapsed_seconds": round(elapsed, 2),
                        "progress_percent": round((i + 1) / total * 100, 1)
                    }

            if progress_callback:
                await progress_callback(i + 1, total)

            # 延迟控制速度
            await asyncio.sleep(speed)

        # 发送完成
        yield {
            "type": "done",
            "total_chars": chars_streamed,
            "total_chunks": len(chunks)
        }

    def format_stream_event(self, data: Dict) -> str:
        """格式化SSE事件"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    async def stream_to_sse(
        self,
        text: str,
        speed: float = 0.02
    ) -> AsyncIterator[str]:
        """流式生成SSE格式数据"""
        async for data in self.stream_text(text, speed=speed):
            yield self.format_stream_event(data)


class CodeBlockBuffer:
    """代码块缓冲区

    缓冲代码块内容，完整后再发送以避免前端闪烁
    """

    def __init__(self, buffer_lines: int = 3):
        self.buffer_lines = buffer_lines
        self.reset()

    def reset(self):
        """重置缓冲区"""
        self.in_code_block = False
        self.buffer = []
        self.language = ""

    def process_line(self, line: str) -> Optional[List[Dict]]:
        """处理一行文本

        Returns:
            如果返回None表示需要缓冲，如果返回列表表示可以发送
        """
        # 代码块开始
        code_start = re.match(r"^```(\w*)$", line)
        if code_start and not self.in_code_block:
            self.in_code_block = True
            self.language = code_start.group(1)
            self.buffer = [line]
            return None  # 需要更多缓冲

        # 代码块结束
        if re.match(r"^```$", line) and self.in_code_block:
            self.buffer.append(line)
            self.in_code_block = False
            result = [{"type": "code_block", "lines": self.buffer, "lang": self.language}]
            self.buffer = []
            return result

        # 代码块内
        if self.in_code_block:
            self.buffer.append(line)
            # 缓冲满后可以发送
            if len(self.buffer) >= self.buffer_lines:
                return [{"type": "code_block", "lines": self.buffer, "lang": self.language}]
            return None

        # 非代码内容直接发送
        return [{"type": "text", "content": line}]

    def flush(self) -> List[Dict]:
        """冲刷缓冲区"""
        if self.in_code_block and self.buffer:
            result = [{"type": "code_block", "lines": self.buffer, "lang": self.language}]
            self.buffer = []
            return result
        return []


# ========== 流式事件类型定义 ==========

class StreamEventType:
    """流式事件类型"""
    CHUNK = "chunk"           # 文本块
    METRICS = "metrics"       # 速度指标
    PROGRESS = "progress"      # 进度
    SOURCE = "source"          # 来源添加
    THINKING = "thinking"      # 思考中状态
    DONE = "done"             # 完成
    ERROR = "error"           # 错误


# ========== 全局实例 ==========

_default_beautifier: Optional[StreamBeautifier] = None


def get_stream_beautifier(config: Optional[StreamConfig] = None) -> StreamBeautifier:
    """获取流式美化器实例"""
    global _default_beautifier
    if _default_beautifier is None:
        _default_beautifier = StreamBeautifier(config)
    return _default_beautifier


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 创建美化器
config = StreamConfig(
    chunk_by="word",        # 按词组流式
    markdown_enabled=True,  # 启用Markdown识别
    emit_speed_metrics=True  # 显示速度指标
)
beautifier = StreamBeautifier(config)

# 2. 流式发送文本
async def example():
    text = "## 你好世界\n\n这是一段包含**粗体**的文本。\n\n```python\nprint('hello')\n```"

    async for event in beautifier.stream_text(text, speed=0.03):
        print(event)
        # {type: "chunk", content: "##", chunk_type: "header", ...}
        # {type: "chunk", content: " 你好世界", chunk_type: "header", ...}
        # {type: "metrics", chars_per_second: 25.0, ...}

# 3. 代码块缓冲
buffer = CodeBlockBuffer(buffer_lines=5)
for line in code_lines:
    result = buffer.process_line(line)
    if result:
        for item in result:
            yield item

# 4. SSE格式输出
async for sse in beautifier.stream_to_sse(text):
    yield sse
    # data: {"type": "chunk", "content": "...", ...}\n\n
"""
