"""
RAG多跳推理系统 - Multi-hop Reasoning System
============================================

【功能】
1. 问题分解 - 将复杂问题分解为子问题
2. 链式推理 - 逐步检索，每步结果支撑下一步
3. 答案合并 - 聚合多个子问题的答案

【使用场景】
- "Alice的工作地天气如何？" → 需要先知道Alice工作地，再查天气
- "这篇文档的核心观点是什么？" → 需要多段落综合
- "项目使用了哪些技术栈？" → 需要跨多个知识源聚合
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class ReasoningType(Enum):
    """推理类型"""
    CHAIN = "chain"           # 链式：Step1 → Step2 → ... → Answer
    PARALLEL = "parallel"     # 并行：Step1 || Step2 || ... → Combine
    TREE = "tree"            # 树形：分支探索


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_id: int
    question: str
    answer: Optional[str] = None
    sources: List[Dict] = None
    confidence: float = 0.0
    is_final: bool = False

    def __post_init__(self):
        if self.sources is None:
            self.sources = []


@dataclass
class MultiHopResult:
    """多跳推理结果"""
    original_question: str
    reasoning_type: ReasoningType
    steps: List[ReasoningStep]
    final_answer: str
    confidence: float
    hops: int

    def to_dict(self) -> Dict:
        return {
            "original_question": self.original_question,
            "reasoning_type": self.reasoning_type.value,
            "final_answer": self.final_answer,
            "confidence": self.confidence,
            "hops": self.hops,
            "steps": [
                {
                    "step_id": s.step_id,
                    "question": s.question,
                    "answer": s.answer,
                    "sources": s.sources,
                    "confidence": s.confidence,
                    "is_final": s.is_final
                }
                for s in self.steps
            ]
        }


class QuestionDecomposer:
    """问题分解器

    将复杂问题分解为可检索的子问题
    """

    # 问题类型模式
    QUESTION_PATTERNS = {
        # 比较类：需要多源信息比较
        r"比较.*和.*": "compare",
        r".*vs\.?.*": "compare",
        r".*与.*区别": "compare",

        # 原因类：需要追溯原因
        r"为什么": "cause",
        r"原因.*是": "cause",
        r".*导致.*": "cause",

        # 影响类：需要分析后果
        r".*影响.*": "effect",
        r".*结果.*": "effect",
        r".*导致.*": "effect",

        # 推理类：需要多步推导
        r"如果.*那么": "inference",
        r".*说明.*": "inference",

        # 聚合类：需要多源汇总
        r".*有哪些": "aggregate",
        r"列举.*": "aggregate",
        r".*包括.*": "aggregate",

        # 验证类：需要核实多个点
        r"是否.*": "verify",
        r".*真假": "verify",
    }

    # 实体提取模式
    ENTITY_PATTERNS = {
        r"(Alice|Bob|Charlie|David|Eve)\s*(?:的|住在|工作|在)": "person",
        r"(北京|上海|深圳|东京|纽约)\s*(?:的|天气|温度|位置)": "city",
    }

    def decompose(self, question: str) -> Tuple[List[str], ReasoningType]:
        """分解问题

        Args:
            question: 原始问题

        Returns:
            (子问题列表, 推理类型)
        """
        question = question.strip()
        reasoning_type = ReasoningType.CHAIN

        # 检测问题类型
        detected_types = []
        for pattern, qtype in self.QUESTION_PATTERNS.items():
            if re.search(pattern, question):
                detected_types.append(qtype)

        # 根据问题结构判断推理类型
        if "compare" in detected_types:
            reasoning_type = ReasoningType.PARALLEL
            return self._decompose_compare(question)
        elif "aggregate" in detected_types:
            reasoning_type = ReasoningType.PARALLEL
            return self._decompose_aggregate(question)
        elif self._has_sequential_dependency(question):
            reasoning_type = ReasoningType.CHAIN
            return self._decompose_chain(question)
        elif "verify" in detected_types:
            reasoning_type = ReasoningType.PARALLEL
            return self._decompose_verify(question)
        else:
            # 默认链式
            return self._decompose_simple_chain(question)

    def _decompose_compare(self, question: str) -> Tuple[List[str], ReasoningType]:
        """分解比较问题"""
        # "比较A和B" → ["A的特点", "B的特点", "对比总结"]
        parts = re.split(r"\s*(?:和|vs\.?|与)\s*", question)
        if len(parts) >= 2:
            sub_questions = [
                f"{parts[0]}的特点是什么？",
                f"{parts[1]}的特点是什么？",
                f"比较{parts[0]}和{parts[1]}的主要区别"
            ]
            return sub_questions, ReasoningType.PARALLEL
        return [question], ReasoningType.CHAIN

    def _decompose_aggregate(self, question: str) -> Tuple[List[str], ReasoningType]:
        """分解聚合问题"""
        # "项目使用了哪些技术栈？" → ["使用了哪些编程语言", "使用了哪些框架", "使用了哪些工具"]
        sub_questions = [
            question.replace("哪些", "哪些编程语言"),
            question.replace("哪些", "哪些框架"),
            question.replace("哪些", "哪些数据库和工具"),
        ]
        return sub_questions, ReasoningType.PARALLEL

    def _has_sequential_dependency(self, question: str) -> bool:
        """检查是否有顺序依赖"""
        sequential_keywords = ["首先", "然后", "接着", "最后", "首先", "其次"]
        return any(kw in question for kw in sequential_keywords)

    def _decompose_chain(self, question: str) -> Tuple[List[str], ReasoningType]:
        """分解链式问题"""
        # "首先找A，然后找B与A的关系" → 分步骤
        sub_questions = []
        steps = re.split(r"\s*(?:首先|然后|接着|最后|其次)\s*", question)
        for step in steps:
            if step.strip():
                sub_questions.append(step.strip())
        return sub_questions if sub_questions else [question], ReasoningType.CHAIN

    def _decompose_simple_chain(self, question: str) -> Tuple[List[str], ReasoningType]:
        """分解简单链式问题"""
        # 尝试提取实体，然后链式查询
        sub_questions = [question]

        # 检查是否包含"谁的"类型问题
        who_match = re.search(r"(.*)的(.+)是什么", question)
        if who_match:
            entity = who_match.group(1)
            attr = who_match.group(2)
            # 第一步：找实体
            sub_questions = [
                f"{entity}是什么？",
                question  # 原始问题作为最终问题
            ]

        # 检查天气类问题
        weather_match = re.search(r"(.*)的天气.*", question)
        if weather_match:
            location = weather_match.group(1)
            sub_questions = [
                f"{location}在哪里？",
                f"{location}的天气怎么样？"
            ]

        return sub_questions if len(sub_questions) > 1 else [question], ReasoningType.CHAIN

    def _decompose_verify(self, question: str) -> Tuple[List[str], ReasoningType]:
        """分解验证问题"""
        # "A是否是正确的？" → ["A是什么", "A的定义是什么", "判断A是否正确"]
        sub_questions = [
            question.replace("是否", ""),
            question.replace("是真的吗", ""),
            f"判断以上答案是否正确"
        ]
        return sub_questions, ReasoningType.PARALLEL


class MultiHopReasoner:
    """多跳推理器

    协调问题分解、检索、答案合并
    """

    def __init__(self, rag_pipeline=None):
        self.decomposer = QuestionDecomposer()
        self.rag_pipeline = rag_pipeline
        self.max_hops = 5  # 最大跳数限制

    def set_rag_pipeline(self, rag_pipeline):
        """设置RAG管道"""
        self.rag_pipeline = rag_pipeline

    async def reason(
        self,
        question: str,
        use_knowledge: bool = True
    ) -> MultiHopResult:
        """执行多跳推理

        Args:
            question: 问题
            use_knowledge: 是否使用知识库检索

        Returns:
            MultiHopResult: 推理结果
        """
        # 1. 分解问题
        sub_questions, reasoning_type = self.decomposer.decompose(question)

        if len(sub_questions) == 1:
            # 单跳问题，直接查询
            answer, sources = await self._single_hop_query(sub_questions[0], use_knowledge)
            step = ReasoningStep(
                step_id=0,
                question=question,
                answer=answer,
                sources=sources,
                is_final=True
            )
            return MultiHopResult(
                original_question=question,
                reasoning_type=reasoning_type,
                steps=[step],
                final_answer=answer,
                confidence=0.9,
                hops=1
            )

        # 2. 多跳推理
        steps = []
        context = ""

        for i, sub_q in enumerate(sub_questions):
            # 如果有前置答案，加入上下文
            if context:
                sub_q_with_context = f"基于以下信息回答：{context}\n\n问题：{sub_q}"
            else:
                sub_q_with_context = sub_q

            # 查询
            answer, sources = await self._single_hop_query(sub_q_with_context, use_knowledge)

            step = ReasoningStep(
                step_id=i,
                question=sub_q,
                answer=answer,
                sources=sources,
                confidence=0.8 if i < len(sub_questions) - 1 else 0.9,
                is_final=(i == len(sub_questions) - 1)
            )
            steps.append(step)

            # 更新上下文
            if answer:
                context += f"\n[{i+1}] {sub_q} -> {answer}"

        # 3. 生成最终答案
        final_answer = self._combine_answers(steps, question)

        # 计算置信度
        confidence = sum(s.confidence for s in steps) / len(steps) if steps else 0.0

        return MultiHopResult(
            original_question=question,
            reasoning_type=reasoning_type,
            steps=steps,
            final_answer=final_answer,
            confidence=confidence,
            hops=len(steps)
        )

    async def _single_hop_query(
        self,
        question: str,
        use_knowledge: bool
    ) -> Tuple[str, List[Dict]]:
        """单跳查询"""
        if self.rag_pipeline and use_knowledge:
            try:
                result = self.rag_pipeline.query(
                    question=question,
                    use_knowledge=True
                )
                return result.get("answer", ""), result.get("sources", [])
            except Exception:
                pass

        # 如果没有RAG管道或查询失败，返回模拟答案
        return f"基于问题「{question}」的推理答案", []

    def _combine_answers(
        self,
        steps: List[ReasoningStep],
        original_question: str
    ) -> str:
        """合并答案"""
        if not steps:
            return "无法回答该问题"

        last_step = steps[-1]
        if last_step.answer:
            return last_step.answer

        # 如果最后一步没有答案，汇总所有步骤
        answers = []
        for i, step in enumerate(steps):
            if step.answer:
                answers.append(f"{i+1}. {step.question}\n   答案：{step.answer}")

        if answers:
            return "推理过程：\n" + "\n".join(answers)
        return "无法生成最终答案"


# ========== 全局实例 ==========

_multihop_reasoner: Optional[MultiHopReasoner] = None


def get_multihop_reasoner() -> MultiHopReasoner:
    """获取多跳推理器实例"""
    global _multihop_reasoner
    if _multihop_reasoner is None:
        _multihop_reasoner = MultiHopReasoner()
    return _multihop_reasoner


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 获取推理器
reasoner = get_multihop_reasoner()

# 2. 设置RAG管道（可选）
reasoner.set_rag_pipeline(rag_pipeline)

# 3. 执行多跳推理
result = await reasoner.reason("Alice的工作地天气如何？")

print(f"问题: {result.original_question}")
print(f"推理类型: {result.reasoning_type}")
print(f"跳数: {result.hops}")
print(f"置信度: {result.confidence}")
print(f"最终答案: {result.final_answer}")

for step in result.steps:
    print(f"\n步骤 {step.step_id}: {step.question}")
    print(f"答案: {step.answer}")
    print(f"来源: {step.sources}")

# 4. 字典输出
print(result.to_dict())
"""
