"""
Token管理模块 Token Manager
===========================

【功能说明】
仅负责记录LLM API调用的token消耗量（累计计数），无预算限制，无阻塞。

【设计原则】
- 纯计数: 只记录，不限制
- 持久化: 每次调用后保存到文件
- 无状态: 不存在"耗尽"概念
"""

import json
import os
from datetime import datetime
from typing import Dict
from dataclasses import dataclass
from threading import Lock

# 持久化存储路径
TOKEN_STATS_FILE = "G:/claude_code_project/data/token_stats.json"


@dataclass
class TokenStats:
    """Token统计信息"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    request_count: int = 0

    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens


class TokenManager:
    """Token计数器 - 仅记录LLM API消耗，无预算限制"""

    def __init__(self):
        self.stats = TokenStats()
        self.lock = Lock()
        self._load_stats()

    def _load_stats(self) -> None:
        """从磁盘加载统计"""
        try:
            if os.path.exists(TOKEN_STATS_FILE):
                with open(TOKEN_STATS_FILE, 'r') as f:
                    data = json.load(f)
                    self.stats = TokenStats(
                        prompt_tokens=data.get("prompt_tokens", 0),
                        completion_tokens=data.get("completion_tokens", 0),
                        request_count=data.get("request_count", 0)
                    )
                print(f"[TokenManager] Loaded stats: {self.stats.total_tokens} tokens from {self.stats.request_count} requests")
            else:
                self.stats = TokenStats()
                self._save_stats()
                print(f"[TokenManager] No previous stats found, starting fresh")
        except Exception as e:
            self.stats = TokenStats()
            print(f"[TokenManager] Load error: {e}, starting fresh")

    def _save_stats(self) -> None:
        """保存统计到磁盘"""
        try:
            os.makedirs(os.path.dirname(TOKEN_STATS_FILE), exist_ok=True)
            with open(TOKEN_STATS_FILE, 'w') as f:
                json.dump({
                    "prompt_tokens": self.stats.prompt_tokens,
                    "completion_tokens": self.stats.completion_tokens,
                    "total_tokens": self.stats.total_tokens,
                    "request_count": self.stats.request_count,
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"[TokenManager] Save error: {e}")

    def reset(self) -> None:
        """手动重置计数"""
        with self.lock:
            old = self.stats.total_tokens
            self.stats = TokenStats()
            self._save_stats()
            print(f"[TokenManager] Reset (previous: {old} tokens)")

    async def consume(
        self,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Dict:
        """记录Token消耗 - 始终记录，不阻塞

        Args:
            prompt_tokens: 输入Token数
            completion_tokens: 输出Token数

        Returns:
            包含消耗详情的字典
        """
        with self.lock:
            self.stats.prompt_tokens += prompt_tokens
            self.stats.completion_tokens += completion_tokens
            self.stats.total_tokens += prompt_tokens + completion_tokens
            self.stats.request_count += 1
            self._save_stats()

        return {
            "success": True,
            "usage": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": prompt_tokens + completion_tokens
            },
            "stats": {
                "total_used": self.stats.total_tokens,
                "requests": self.stats.request_count
            }
        }

    def get_status(self) -> Dict:
        """获取当前统计状态"""
        return {
            "current_usage": self.stats.total_tokens,
            "prompt_tokens": self.stats.prompt_tokens,
            "completion_tokens": self.stats.completion_tokens,
            "requests": self.stats.request_count,
            "last_updated": datetime.now().isoformat()
        }


# 全局单例
token_manager = TokenManager()
