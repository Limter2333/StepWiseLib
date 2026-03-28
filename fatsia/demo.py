"""
Fatsia 快速演示脚本

展示如何使用 Fatsia 库与不同 AI 模型进行交互。
运行前请确保已设置相应的 API Key。
"""

import os
import sys
from dotenv import load_dotenv

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv()


def main():
    """主函数 - 演示基本使用方式"""
    print("""
    ============================================================
    
                      Fatsia 快速演示
    
                支持：千问 3 | OpenAI | Gemini
    
    ============================================================
    """)
    
    from src.fatsia import ModelConfig, FatsiaClient, logger
    
    # 检查是否有 API Key
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key or api_key == "your_qwen_api_key_here":
        print("[提示] 未设置 QWEN_API_KEY，使用测试模式演示\n")
        
        # 演示配置创建
        print("[1] 创建千问 3 配置")
        config = ModelConfig.create_qwen3_config(
            api_key="test-key",
            model_name="qwen-plus"
        )
        print("    配置创建成功")
        print(f"      - 模型类型：{config.model_type}")
        print(f"      - 模型名称：{config.model_name}")
        print(f"      - Base URL: {config.base_url}")
        
        print("\n[2] 创建 OpenAI 配置")
        openai_config = ModelConfig.create_openai_config(
            api_key="test-key",
            model_name="gpt-4o"
        )
        print("    配置创建成功")
        print(f"      - 模型类型：{openai_config.model_type}")
        print(f"      - 模型名称：{openai_config.model_name}")
        print(f"      - Base URL: {openai_config.base_url}")
        
        print("\n[3] 创建 Gemini 配置")
        gemini_config = ModelConfig.create_gemini_config(
            api_key="test-key",
            model_name="gemini-1.5-pro"
        )
        print("    配置创建成功")
        print(f"      - 模型类型：{gemini_config.model_type}")
        print(f"      - 模型名称：{gemini_config.model_name}")
        print(f"      - Base URL: {gemini_config.base_url}")
        
        print("\n[提示] 设置真实的 API Key 后可以实际调用模型")
        print("       复制 .env.example 为 .env 并填入你的 API Key\n")
        
    else:
        # 真实 API 调用演示
        print("[1] 创建客户端并发送消息\n")
        
        config = ModelConfig.create_qwen3_config(api_key=api_key)
        
        with FatsiaClient(config) as client:
            response = client.chat("你好，请用一句话介绍你自己")
            print(f"   回复：{response}\n")
    
    print("=" * 60)
    print("[提示] 日志文件位置：../logs/fatsia/fatsia.log")
    print("=" * 60)


if __name__ == "__main__":
    main()
