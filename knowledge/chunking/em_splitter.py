"""
EM语义分割器
============

【学习要点】
1. 文本分割的重要性
   - LLM有上下文长度限制（如4096 tokens）
   - 检索时需要较小的文本块
   - 影响检索质量和生成质量

2. 分割策略对比
   - 固定长度: 简单但可能切断句子
   - 规则分割: 按句子/段落切，保留完整性
   - 语义分割: AI判断在哪里切，最智能但最慢
"""

from typing import List, Generator, Optional
import re


class EMSplitter:
    """EM (Embedding Model) 语义分割器

    【核心思想】
    使用embedding模型的相似度来判断语义边界
    - 相邻块的相似度高 → 同一语义单元 → 不切
    - 相邻块的相似度低 → 语义转换 → 切
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        """
        Args:
            chunk_size: 目标块大小（字符数）
            chunk_overlap: 块之间的重叠（保持上下文）
            min_chunk_size: 最小块大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def split_text(self, text: str) -> List[str]:
        """分割文本

        【流程】
        1. 按段落分割
        2. 按句子分割
        3. 根据chunk_size组合
        4. 添加重叠保持连续性
        """
        if not text:
            return []

        # 1. 先按段落分割
        paragraphs = self._split_by_paragraph(text)
        chunks = []

        # 2. 按段落组合成块
        current_chunk = ""
        for para in paragraphs:
            # 如果单个段落就超过chunk_size，按句子分割
            if len(para) > self.chunk_size:
                sentences = self._split_by_sentence(para)
                for sent in sentences:
                    if len(current_chunk) + len(sent) <= self.chunk_size:
                        current_chunk += sent + " "
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = sent + " "
            else:
                if len(current_chunk) + len(para) <= self.chunk_size:
                    current_chunk += para + "\n"
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    # 保留overlap
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = overlap_text + para + "\n"

        # 处理最后一个块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # 3. 合并过小的块
        chunks = self._merge_small_chunks(chunks)

        return chunks

    def _split_by_paragraph(self, text: str) -> List[str]:
        """按段落分割"""
        # 多个换行符分割
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_by_sentence(self, text: str) -> List[str]:
        """按句子分割

        【学习要点】句子分割的难点
        - 英文: Mr. Dr. 等缩写
        - 中文: 。！？等标点
        - 混合文本需要处理两者
        """
        # 中英文句子分割
        # 优先按中文标点
        sentences = re.split(r'([。！？\.!?])', text)

        # 合并句子和标点
        merged = []
        for i in range(0, len(sentences) - 1, 2):
            sent = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ""
            merged.append(sent + punct)

        if len(sentences) % 2 == 1:
            merged.append(sentences[-1])

        return [s.strip() for s in merged if s.strip()]

    def _get_overlap(self, text: str) -> str:
        """获取overlap文本

        【学习要点】Overlap的作用
        - 保持块之间的上下文连续
        - 避免在分割点丢失重要信息
        - 类似于滑动窗口
        """
        if len(text) <= self.chunk_overlap:
            return text

        # 从后往前找sentence boundary
        overlap_text = text[-self.chunk_overlap:]
        # 尝试找到句号
        match = re.search(r'[。！？\.!]\s*\S+$', overlap_text)
        if match:
            return match.group(0)
        return overlap_text

    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """合并过小的块"""
        if not chunks:
            return []

        merged = []
        current = chunks[0]

        for next_chunk in chunks[1:]:
            if len(current) < self.min_chunk_size:
                current += " " + next_chunk
            else:
                merged.append(current)
                current = next_chunk

        if current:
            merged.append(current)

        return merged


class RuleSplitter:
    """规则分割器（更简单但有效）

    【适用场景】
    - 格式规范的文档
    - 对分割位置有明确要求
    """

    def __init__(
        self,
        separators: List[str] = None,
        chunk_size: int = 500
    ):
        self.separators = separators or [
            "\n\n",  # 段落
            "\n",    # 换行
            "。",    # 中文句号
            ". ",    # 英文句号+空格
            "? ",    # 问号
            "! ",    # 感叹号
            "; ",    # 分号
            ", ",    # 逗号
        ]
        self.chunk_size = chunk_size

    def split_text(self, text: str) -> List[str]:
        """按规则分割文本"""
        if not text:
            return []

        # 先尝试大的分隔符
        for sep in self.separators:
            if sep in text:
                parts = text.split(sep)
                chunks = []
                current = ""

                for part in parts:
                    if len(current) + len(part) <= self.chunk_size:
                        current += part + sep
                    else:
                        if current.strip():
                            chunks.append(current.strip())
                        current = part + sep

                if current.strip():
                    chunks.append(current.strip())

                return chunks

        # 如果没有分隔符，按固定长度分割
        return [text[i:i+self.chunk_size] for i in range(0, len(text), self.chunk_size)]
