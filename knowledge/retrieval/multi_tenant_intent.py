"""
意图识别模块 - Intent Recognition
===============================

【完美体验设计】

1. 多层次意图理解
   - 显式意图：用户明确表达的需求
   - 隐式意图：根据上下文推断
   - 情感倾向：积极/消极/中性

2. 意图分类体系
   - inquiry: 知识问答
   - task_execution: 任务执行
   - document_management: 文档管理
   - conversation: 对话闲聊
   - chitchat: 闲聊
   - clarification: 需求澄清

3. 上下文追踪
   - 多轮对话意图连贯性
   - 话题切换检测
   - 指代消解

4. 降级策略
   - 有模型：使用深度学习模型
   - 无模型：使用规则匹配
"""

from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import json


class IntentType(Enum):
    """意图类型"""
    # 主要意图
    INQUIRY = "inquiry"               # 知识问答
    TASK_EXECUTION = "task_execution" # 任务执行
    DOCUMENT_MANAGEMENT = "document_management"  # 文档管理
    CONVERSATION = "conversation"     # 对话闲聊
    CLARIFICATION = "clarification"    # 需求澄清

    # 辅助意图
    GREETING = "greeting"             # 问候
    GOODBYE = "goodbye"               # 告别
    THANKS = "thanks"                 # 感谢
    CHITCHAT = "chitchat"             # 闲聊
    UNKNOWN = "unknown"               # 未知


class Sentiment(Enum):
    """情感倾向"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class Intent:
    """意图"""
    intent_type: IntentType
    confidence: float          # 置信度 0.0-1.0
    entities: Dict = field(default_factory=dict)  # 提取的实体
    metadata: Dict = field(default_factory=dict)
    parent_intent: Optional[str] = None  # 父意图（用于子意图）


@dataclass
class IntentCandidate:
    """意图候选"""
    intent_type: IntentType
    confidence: float
    matched_keywords: List[str]
    pattern: str


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    user_id: Optional[str] = None
    history: List[Intent] = field(default_factory=list)
    current_topic: Optional[str] = None
    topic_history: List[str] = field(default_factory=list)
    last_intent: Optional[Intent] = None
    entities: Dict = field(default_factory=dict)  # 累积实体


class KeywordIntentRecognizer:
    """基于关键词的意图识别

    【适用场景】
    - 快速原型
    - 无NLP模型的降级方案
    - 高频意图识别
    """

    # 意图关键词库
    INTENT_PATTERNS = {
        IntentType.INQUIRY: {
            "keywords": [
                "什么", "怎么", "如何", "为什么", "哪里", "谁",
                "what", "how", "why", "where", "who", "which",
                "解释", "定义", "说明", "介绍", "了解", "知道",
                "是", "是不是", "有没有", "能不能"
            ],
            "weight": 1.0
        },
        IntentType.TASK_EXECUTION: {
            "keywords": [
                "执行", "完成", "做", "生成", "创建", "编写",
                "生成", "开发", "实现", "运行", "处理",
                "execute", "do", "create", "generate", "build", "run",
                "帮我", "请", "能不能", "可以帮"
            ],
            "weight": 1.0
        },
        IntentType.DOCUMENT_MANAGEMENT: {
            "keywords": [
                "上传", "添加", "删除", "更新", "修改",
                "索引", "导入", "导出", "下载",
                "upload", "add", "delete", "update", "modify",
                "索引", "搜索", "查询", "检索"
            ],
            "weight": 1.0
        },
        IntentType.CONVERSATION: {
            "keywords": [
                "你好", "嗨", "哈喽", "在吗", "在不在",
                "hello", "hi", "hey",
                "聊聊", "说说话", "对话"
            ],
            "weight": 0.9
        },
        IntentType.GREETING: {
            "keywords": [
                "你好", "嗨", "哈喽", "早上好", "下午好", "晚上好",
                "hi", "hello", "good morning", "good afternoon"
            ],
            "weight": 1.0
        },
        IntentType.GOODBYE: {
            "keywords": [
                "再见", "拜拜", "下次见", "走了",
                "bye", "goodbye", "see you"
            ],
            "weight": 1.0
        },
        IntentType.THANKS: {
            "keywords": [
                "谢谢", "感谢", "多谢", "Thanks", "thank you"
            ],
            "weight": 1.0
        },
        IntentType.CLARIFICATION: {
            "keywords": [
                "具体", "详细", "更多", "举个例子", "说明白",
                "clarify", "specifically", "more details"
            ],
            "weight": 0.8
        }
    }

    def __init__(self):
        # 编译正则
        self._compile_patterns()

    def _compile_patterns(self):
        """编译匹配模式"""
        self.patterns = {}
        for intent_type, config in self.INTENT_PATTERNS.items():
            keywords = config["keywords"]
            # 构建正则模式
            pattern = "|".join(re.escape(kw) for kw in keywords)
            self.patterns[intent_type] = re.compile(pattern, re.IGNORECASE)

    def recognize(
        self,
        query: str,
        context: Optional[ConversationContext] = None
    ) -> List[IntentCandidate]:
        """识别意图

        Args:
            query: 用户查询
            context: 对话上下文（可选）

        Returns:
            意图候选列表，按置信度排序
        """
        candidates = []
        if not query or not query.strip():
            return candidates

        query_lower = query.lower()

        for intent_type, config in self.INTENT_PATTERNS.items():
            pattern = self.patterns[intent_type]
            matches = pattern.findall(query_lower)

            if matches:
                # 计算置信度：基于匹配数量和关键词权重
                match_count = len(matches)
                base_confidence = min(match_count * 0.3, 1.0) * config["weight"]

                candidates.append(IntentCandidate(
                    intent_type=intent_type,
                    confidence=base_confidence,
                    matched_keywords=list(set(matches)),
                    pattern=pattern.pattern
                ))

        # 按置信度排序
        candidates.sort(key=lambda x: x.confidence, reverse=True)

        return candidates

    def add_keywords(self, intent_type: IntentType, keywords: List[str]) -> None:
        """添加关键词到指定意图类型

        Args:
            intent_type: 意图类型
            keywords: 关键词列表
        """
        if intent_type not in self.INTENT_PATTERNS:
            self.INTENT_PATTERNS[intent_type] = {"keywords": [], "weight": 1.0}

        # 添加新关键词
        for kw in keywords:
            if kw.lower() not in [k.lower() for k in self.INTENT_PATTERNS[intent_type]["keywords"]]:
                self.INTENT_PATTERNS[intent_type]["keywords"].append(kw)

        # 重新编译模式
        self._compile_patterns()

    def update_keyword_weight(self, intent_type: IntentType, weight: float) -> None:
        """更新意图类型的关键词权重

        Args:
            intent_type: 意图类型
            weight: 新权重 (0.0-1.0)
        """
        if intent_type in self.INTENT_PATTERNS:
            self.INTENT_PATTERNS[intent_type]["weight"] = max(0.0, min(1.0, weight))

    def learn_from_feedback(
        self,
        query: str,
        correct_intent: IntentType,
        feedback_type: str = "correct"
    ) -> None:
        """从反馈中学习（在线学习）

        Args:
            query: 用户查询
            correct_intent: 正确的意图类型
            feedback_type: 反馈类型 ("correct", "incorrect")
        """
        if feedback_type == "correct":
            # 增加该意图类型的置信度
            self.update_keyword_weight(correct_intent, min(1.0,
                self.INTENT_PATTERNS.get(correct_intent, {}).get("weight", 1.0) + 0.05))
        else:
            # 降低该意图类型的置信度
            self.update_keyword_weight(correct_intent, max(0.1,
                self.INTENT_PATTERNS.get(correct_intent, {}).get("weight", 1.0) - 0.1))

    def export_patterns(self) -> Dict:
        """导出当前模式（用于持久化）"""
        return {
            intent_type.value: config
            for intent_type, config in self.INTENT_PATTERNS.items()
        }

    def import_patterns(self, patterns: Dict) -> None:
        """导入模式（用于加载）"""
        for intent_value, config in patterns.items():
            try:
                intent_type = IntentType(intent_value)
                self.INTENT_PATTERNS[intent_type] = config
            except ValueError:
                pass  # 忽略无效的意图类型
        self._compile_patterns()


class SentimentAnalyzer:
    """情感分析器

    【简化实现】
    - 基于关键词的情感分析
    - 实际生产中应使用专门的情感分析模型
    """

    POSITIVE_WORDS = [
        "好", "棒", "优秀", "完美", "喜欢", "感谢",
        "good", "great", "excellent", "perfect", "love", "thanks",
        "太棒了", "太好了", "谢谢", "不错", "优秀"
    ]

    NEGATIVE_WORDS = [
        "差", "烂", "垃圾", "讨厌", "不满",
        "bad", "terrible", "hate", "worst", "awful",
        "不好", "糟糕", "失望", "愤怒"
    ]

    def analyze(self, text: str) -> Sentiment:
        """分析情感"""
        text_lower = text.lower()

        pos_count = sum(1 for w in self.POSITIVE_WORDS if w in text_lower)
        neg_count = sum(1 for w in self.NEGATIVE_WORDS if w in text_lower)

        if pos_count > neg_count:
            return Sentiment.POSITIVE
        elif neg_count > pos_count:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL


class EntityExtractor:
    """实体提取器

    【功能】
    - 从文本中提取关键实体
    - 支持：时间、数量、邮箱、URL、文件类型、编程语言等
    """

    def __init__(self):
        # 时间表达式
        self.time_patterns = [
            (r'\d{4}年\d{1,2}月\d{1,2}日', 'date'),
            (r'\d{1,2}月\d{1,2}日', 'date'),
            (r'今天|明天|后天|昨天', 'relative_date'),
            (r'\d{1,2}点\d{1,2}分', 'time'),
            (r'下个?\w*期', 'weekday'),
            (r'本周|下周|上周', 'week'),
        ]

        # 数字表达式
        self.number_patterns = [
            (r'\d+个?', 'quantity'),
            (r'\d+\.\d+', 'decimal'),
            (r'第一|第二|第三|第一', 'ordinal'),
        ]

        # 邮箱表达式
        self.email_patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email'),
        ]

        # URL表达式
        self.url_patterns = [
            (r'https?://[^\s]+', 'url'),
            (r'www\.[^\s]+', 'url'),
        ]

        # 文件类型表达式
        self.file_type_patterns = [
            (r'\.pdf|\.docx?|\.txt|\.md|\.csv|\.xlsx?|\.pptx?', 'file_type'),
            (r'PDF|DOCX?|TXT|MD|CSV|XLSX?|PPTX', 'file_type'),
        ]

        # 编程语言表达式
        self.language_patterns = [
            (r'Python|JavaScript|TypeScript|Java|C\+\+|Go|Rust|PHP|Ruby|Swift|Kotlin', 'language'),
            (r'python|javascript|typescript|java|go|rust|php', 'language'),
        ]

    def extract(self, text: str) -> Dict[str, List[str]]:
        """提取实体

        Returns:
            {"type": [values]}
        """
        entities = {}

        # 提取时间
        time_entities = []
        for pattern, entity_type in self.time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                time_entities.extend(matches)
        if time_entities:
            entities["time"] = time_entities

        # 提取数字
        number_entities = []
        for pattern, entity_type in self.number_patterns:
            matches = re.findall(pattern, text)
            if matches:
                number_entities.extend(matches)
        if number_entities:
            entities["number"] = number_entities

        # 提取邮箱
        email_entities = []
        for pattern, entity_type in self.email_patterns:
            matches = re.findall(pattern, text)
            if matches:
                email_entities.extend(matches)
        if email_entities:
            entities["email"] = email_entities

        # 提取URL
        url_entities = []
        for pattern, entity_type in self.url_patterns:
            matches = re.findall(pattern, text)
            if matches:
                url_entities.extend(matches)
        if url_entities:
            entities["url"] = url_entities

        # 提取文件类型
        file_entities = []
        for pattern, entity_type in self.file_type_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                file_entities.extend(matches)
        if file_entities:
            entities["file_type"] = file_entities

        # 提取编程语言
        language_entities = []
        for pattern, entity_type in self.language_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                language_entities.extend(matches)
        if language_entities:
            entities["language"] = language_entities

        return entities


class IntentRecognitionPipeline:
    """意图识别管道

    【完美体验设计】
    1. 多策略融合
       - 关键词匹配（快速）
       - 规则匹配（可解释）
       - 上下文推断（智能）

    2. 置信度校准
       - 基于匹配数量
       - 基于上下文
       - 基于历史

    3. 结果验证
       - 意图一致性检查
       - 歧义消解
    """

    def __init__(self):
        self.keyword_recognizer = KeywordIntentRecognizer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.entity_extractor = EntityExtractor()

        # 上下文存储
        self.contexts: Dict[str, ConversationContext] = {}

    def get_or_create_context(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> ConversationContext:
        """获取或创建对话上下文"""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id
            )
        return self.contexts[session_id]

    def recognize(
        self,
        query: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Intent:
        """识别意图

        Args:
            query: 用户查询
            session_id: 会话ID
            user_id: 用户ID（可选）

        Returns:
            最终意图
        """
        # 获取上下文
        context = self.get_or_create_context(session_id, user_id)

        # 1. 关键词意图识别
        candidates = self.keyword_recognizer.recognize(query, context)

        if not candidates:
            # 无匹配，返回未知
            return Intent(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                entities={},
                metadata={"reason": "no_match"}
            )

        # 2. 取最高置信度的候选
        top_candidate = candidates[0]

        # 3. 提取实体
        entities = self.entity_extractor.extract(query)

        # 4. 分析情感
        sentiment = self.sentiment_analyzer.analyze(query)

        # 5. 上下文推断（调整置信度）
        confidence = self._adjust_confidence(
            top_candidate,
            context
        )

        # 6. 构建意图
        intent = Intent(
            intent_type=top_candidate.intent_type,
            confidence=confidence,
            entities=entities,
            metadata={
                "sentiment": sentiment.value,
                "matched_keywords": top_candidate.matched_keywords,
                "all_candidates": [
                    {"type": c.intent_type.value, "confidence": c.confidence}
                    for c in candidates[:3]
                ]
            }
        )

        # 7. 更新上下文
        self._update_context(context, intent, query)

        return intent

    def _adjust_confidence(
        self,
        candidate: IntentCandidate,
        context: ConversationContext
    ) -> float:
        """根据上下文调整置信度"""
        confidence = candidate.confidence

        # 如果上一轮是同类意图，增加置信度（意图延续）
        if context.last_intent:
            if context.last_intent.intent_type == candidate.intent_type:
                confidence = min(confidence * 1.2, 1.0)

        # 如果上下文中有相关实体，增加置信度
        if context.entities:
            entity_count = len(context.entities)
            confidence = min(confidence + entity_count * 0.05, 1.0)

        return confidence

    def _update_context(
        self,
        context: ConversationContext,
        intent: Intent,
        query: str
    ):
        """更新对话上下文"""
        # 添加到历史
        context.history.append(intent)
        context.last_intent = intent

        # 累积实体
        if intent.entities:
            for entity_type, values in intent.entities.items():
                if entity_type not in context.entities:
                    context.entities[entity_type] = []
                context.entities[entity_type].extend(values)

        # 检测话题切换
        # 简化：如果意图类型大幅变化，认为切换话题
        if len(context.history) >= 2:
            prev_intent = context.history[-2]
            if prev_intent.intent_type != intent.intent_type:
                context.topic_history.append(prev_intent.intent_type.value)

    def clear_context(self, session_id: str):
        """清除会话上下文"""
        if session_id in self.contexts:
            del self.contexts[session_id]

    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """获取会话上下文"""
        return self.contexts.get(session_id)


# 全局实例
_intent_recognizer: Optional[IntentRecognitionPipeline] = None


def get_intent_recognizer() -> IntentRecognitionPipeline:
    """获取意图识别器实例"""
    global _intent_recognizer
    if _intent_recognizer is None:
        _intent_recognizer = IntentRecognitionPipeline()
    return _intent_recognizer


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 获取实例
recognizer = get_intent_recognizer()

# 2. 识别意图
intent = recognizer.recognize(
    query="如何上传文档到知识库？",
    session_id="user_123_session_1",
    user_id="user_123"
)

print(f"意图: {intent.intent_type.value}")
print(f"置信度: {intent.confidence:.2f}")
print(f"实体: {intent.entities}")
print(f"情感: {intent.metadata.get('sentiment')}")

# 3. 多轮对话
# 第二轮：追问
intent2 = recognizer.recognize(
    query="支持哪些格式？",
    session_id="user_123_session_1"
)

# 因为在同一会话中，系统会理解这是追问
print(f"意图: {intent2.intent_type.value}")
# 如果置信度提高，说明系统识别到了延续

# 4. 获取上下文
context = recognizer.get_context("user_123_session_1")
print(f"历史意图数: {len(context.history)}")
print(f"累积实体: {context.entities}")

# 5. 清除上下文（开始新话题）
recognizer.clear_context("user_123_session_1")
"""


class TaskRouter:
    """任务路由器

    根据意图将请求路由到对应的处理模块
    """

    def __init__(self):
        self.handlers: Dict[IntentType, Callable] = {}

    def register_handler(
        self,
        intent_type: IntentType,
        handler: Callable
    ):
        """注册意图处理器"""
        self.handlers[intent_type] = handler

    def route(self, intent: Intent, query: str, context: ConversationContext) -> Dict:
        """路由任务

        Args:
            intent: 识别出的意图
            query: 用户查询
            context: 对话上下文

        Returns:
            路由结果
        """
        handler = self.handlers.get(intent.intent_type)

        if handler:
            return handler(intent, query, context)
        else:
            return {
                "success": False,
                "message": f"No handler for intent: {intent.intent_type.value}",
                "intent": intent.intent_type.value
            }


# ========== 快速路由示例 ==========
"""
【意图到处理的快速映射】

INQUIRY (知识问答)
  → RAG搜索 → 返回知识库答案

TASK_EXECUTION (任务执行)
  → Dev Agent / Test Agent → 返回任务结果

DOCUMENT_MANAGEMENT (文档管理)
  → RAG Agent索引/删除 → 返回操作结果

CONVERSATION (对话闲聊)
  → Conversation Agent → 返回对话响应

CLARIFICATION (需求澄清)
  → 生成澄清问题 → 返回追问
"""
