"""
测试流式输出美化器

验证用户故事 acceptance criteria
"""

import pytest
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stream_beautifier import (
    StreamBeautifier,
    StreamConfig,
    MarkdownTokenizer,
    CodeBlockBuffer,
    get_stream_beautifier
)


class TestMarkdownTokenizer:
    """Markdown标记化测试"""

    def test_tokenize_header(self):
        """用户故事: markdown tokenize识别标题"""
        text = "## Header\n"
        tokens = MarkdownTokenizer.tokenize(text)
        assert any(t["type"] == "header" and t["level"] == 2 for t in tokens)

    def test_tokenize_bold(self):
        """用户故事: markdown tokenize识别粗体"""
        text = "**bold** text"
        tokens = MarkdownTokenizer.tokenize(text)
        assert any(t["type"] == "paragraph" for t in tokens)
        # Bold markers应该出现在文本中
        text_content = "".join(t.get("content", "") for t in tokens)
        assert "**" in text_content or "bold" in text_content

    def test_tokenize_code_block(self):
        """用户故事: markdown tokenize识别代码块"""
        text = "```python\nprint(1)\n```"
        tokens = MarkdownTokenizer.tokenize(text)
        types = [t["type"] for t in tokens]
        assert "code_block_start" in types
        assert "code_line" in types
        assert "code_block_end" in types

    def test_tokenize_paragraph(self):
        """用户故事: markdown tokenize识别段落"""
        text = "这是一段普通文本"
        tokens = MarkdownTokenizer.tokenize(text)
        assert any(t["type"] == "paragraph" for t in tokens)

    def test_tokenize_empty(self):
        """空文本处理"""
        tokens = MarkdownTokenizer.tokenize("")
        assert tokens == []


class TestStreamBeautifier:
    """流式美化器测试"""

    def test_chunk_by_word(self):
        """用户故事: 按词组分块"""
        config = StreamConfig(chunk_by="word")
        beautifier = StreamBeautifier(config)
        chunks = beautifier.chunk_text("Hello World")
        # 应该按空格分割
        assert len(chunks) >= 1
        # 'Hello ' 或 'Hello World' 作为第一个词
        assert chunks[0].startswith("Hello")

    def test_chunk_by_char(self):
        """用户故事: 按字符分块"""
        config = StreamConfig(chunk_by="char")
        beautifier = StreamBeautifier(config)
        chunks = beautifier.chunk_text("Hi")
        assert chunks == ["H", "i"]

    def test_config_defaults(self):
        """默认配置"""
        beautifier = StreamBeautifier()
        assert beautifier.config.chunk_by == "word"
        assert beautifier.config.markdown_enabled is True

    def test_get_stream_beautifier_singleton(self):
        """单例模式"""
        b1 = get_stream_beautifier()
        b2 = get_stream_beautifier()
        assert b1 is b2


class TestCodeBlockBuffer:
    """代码块缓冲区测试"""

    def test_buffer_code_block_start(self):
        """用户故事: 缓冲代码块开始"""
        buffer = CodeBlockBuffer(buffer_lines=2)
        result = buffer.process_line("```python")
        assert result is None  # 还没完整，缓冲中
        assert buffer.in_code_block is True
        assert buffer.language == "python"

    def test_buffer_releases_on_end(self):
        """用户故事: 代码块结束时发送"""
        buffer = CodeBlockBuffer(buffer_lines=2)
        buffer.process_line("```python")
        buffer.process_line("print(1)")
        result = buffer.process_line("```")
        assert result is not None
        assert len(result) == 1
        assert result[0]["type"] == "code_block"
        assert result[0]["lang"] == "python"

    def test_buffer_lines_collected(self):
        """用户故事: 缓冲行被收集"""
        buffer = CodeBlockBuffer(buffer_lines=3)
        buffer.process_line("```python")
        buffer.process_line("line1")
        # buffer_lines reached (3 lines: opening + 2 lines), should emit
        result = buffer.process_line("line2")
        assert result is not None
        assert result[0]["type"] == "code_block"
        assert len(result[0]["lines"]) == 3

    def test_buffer_flush(self):
        """用户故事: 冲刷缓冲区"""
        buffer = CodeBlockBuffer(buffer_lines=2)
        buffer.process_line("```")
        buffer.process_line("x")
        # 未关闭代码块，flush应该返回空
        result = buffer.flush()
        # flush后buffer应该清空
        assert buffer.buffer == []

    def test_outside_code_block_passthrough(self):
        """代码块外文本直接通过"""
        buffer = CodeBlockBuffer()
        result = buffer.process_line("normal text")
        assert result is not None
        assert result[0]["type"] == "text"


class TestStreamEvents:
    """流式事件测试"""

    def test_format_stream_event(self):
        """用户故事: SSE格式输出"""
        beautifier = StreamBeautifier()
        data = {"type": "chunk", "content": "test"}
        formatted = beautifier.format_stream_event(data)
        assert formatted.startswith("data: ")
        assert formatted.endswith("\n\n")
        assert "test" in formatted


@pytest.mark.asyncio
class TestAsyncStreaming:
    """异步流式测试"""

    async def test_stream_text_yields_chunks(self):
        """用户故事: 流式发送文本块"""
        beautifier = StreamBeautifier(StreamConfig(chunk_by="char"))
        text = "Hi"
        chunks = []
        async for event in beautifier.stream_text(text, speed=0.001):
            if event["type"] == "chunk":
                chunks.append(event["content"])
        assert "H" in chunks
        assert "i" in chunks

    async def test_stream_text_yields_done(self):
        """用户故事: 流式发送完成信号"""
        beautifier = StreamBeautifier(StreamConfig(chunk_by="char"))
        text = "Hi"
        done_received = False
        async for event in beautifier.stream_text(text, speed=0.001):
            if event["type"] == "done":
                done_received = True
                assert "total_chars" in event
        assert done_received

    async def test_stream_yields_metrics(self):
        """用户故事: 流式发送速度指标"""
        config = StreamConfig(chunk_by="word", emit_speed_metrics=True)
        beautifier = StreamBeautifier(config)
        text = "one two three four five six seven eight nine ten"
        metrics_received = False
        async for event in beautifier.stream_text(text, speed=0.001):
            if event["type"] == "metrics":
                metrics_received = True
                assert "chars_per_second" in event
        assert metrics_received
