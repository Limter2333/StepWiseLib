#!/usr/bin/env python3
"""
LLM调用测试脚本
快速验证API连接是否正常
"""

import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 检查API Key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key or api_key == "your_minimax_api_key_here":
    print("[X] API Key not configured!")
    print("    Please set ANTHROPIC_API_KEY=your_actual_key in .env file")
    exit(1)

print(f"[OK] API Key configured: {api_key[:8]}...")

# 测试LLM调用
async def test_llm():
    try:
        from core.llm.llm_provider import get_llm, LLMProvider, LLMWrapper

        print("\n[*] Testing MiniMax LLM call...")

        # 初始化LLM (使用.env配置)
        llm = get_llm()
        print(f"   Provider: {llm.provider.value}")
        print(f"   Model: {llm.model}")

        # 简单对话测试
        response = await llm.generate(
            prompt="请回复: 1+1等于几?",
            system_prompt="你是一个简洁的数学助手，只回答数字。"
        )

        print(f"\n[OK] LLM call successful!")
        print(f"    Model: {response.model}")
        print(f"    Response: {response.content}")
        print(f"    Tokens: {response.usage}")

        return True

    except Exception as e:
        print(f"\n[X] LLM call failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_llm())
    exit(0 if result else 1)
