"""
示例代码 - 展示 Fatsia 库的各种使用方式

本文件包含多个示例，演示如何使用 Fatsia 与不同的 AI 模型进行交互。
运行前请确保已设置相应的 API Key。
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def example_basic_chat():
    """示例 1: 基础聊天功能"""
    print("\n" + "=" * 60)
    print("示例 1: 基础聊天功能")
    print("=" * 60)
    
    from src.fatsia import FatsiaClient, ModelConfig
    
    # 创建千问 3 配置
    config = ModelConfig.create_qwen3_config(
        api_key=os.getenv("QWEN_API_KEY", "your-qwen-api-key"),
        model_name="qwen3-max-2026-01-23"
    )
    
    # 创建客户端
    with FatsiaClient(config) as client:
        # 发送消息
        response = client.chat("你好，请简单介绍一下自己")
        print(f"\n回复：{response}")


def example_with_system_prompt():
    """示例 2: 带系统提示词的聊天"""
    print("\n" + "=" * 60)
    print("示例 2: 带系统提示词的聊天")
    print("=" * 60)
    
    from src.fatsia import FatsiaClient, ModelConfig
    
    config = ModelConfig.create_qwen3_config(
        api_key=os.getenv("QWEN_API_KEY", "your-qwen-api-key"),
    )
    
    with FatsiaClient(config) as client:
        response = client.chat(
            message="深圳有哪些著名景点？",
            system_prompt="你是一个专业的旅游顾问，擅长提供详细的旅游攻略。请用简洁的语言，可爱的语气回答。"
        )
        print(f"\n回复：{response}")


def example_stream_chat():
    """示例 3: 流式聊天"""
    print("\n" + "=" * 60)
    print("示例 3: 流式聊天")
    print("=" * 60)
    
    from src.fatsia import FatsiaClient, ModelConfig
    
    config = ModelConfig.create_qwen3_config(
        api_key=os.getenv("QWEN_API_KEY", "your-qwen-api-key"),
    )
    
    with FatsiaClient(config) as client:
        print("\n正在生成回复（流式）：\n")
        for chunk in client.stream_chat(
            message="我即将去深圳旅行，周五到深圳高铁站，行程为6天，请给我整理一份旅游攻略",
            system_prompt="你是一个专业的旅游顾问，擅长提供详细的旅游攻略。请用简洁的语言，可爱的语气回答。"
        ):
            print(chunk, end="", flush=True)
        print()


def example_multi_turn_chat():
    """示例 4: 多轮对话"""
    print("\n" + "=" * 60)
    print("示例 4: 多轮对话")
    print("=" * 60)
    
    from src.fatsia import FatsiaClient, ModelConfig
    
    config = ModelConfig.create_qwen3_config(
        api_key=os.getenv("QWEN_API_KEY", "your-qwen-api-key"),
    )
    
    with FatsiaClient(config) as client:
        # 构建多轮对话历史
        messages = [
            {"role": "system", "content": "你是一个乐于助人的 AI 助手"},
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
            {"role": "user", "content": "我想学习 Python，应该从哪里开始？"}
        ]
        
        response = client.chat_with_messages(messages)
        print(f"\n回复：{response}")


def example_model_switch():
    """示例 5: 动态切换模型"""
    print("\n" + "=" * 60)
    print("示例 5: 动态切换模型")
    print("=" * 60)
    
    from src.fatsia import FatsiaClient, ModelConfig, ModelType
    
    # 初始使用千问 3
    config = ModelConfig.create_qwen3_config(
        api_key=os.getenv("QWEN_API_KEY", "your-qwen-api-key"),
    )
    
    client = FatsiaClient(config)
    
    print("\n使用千问 3:")
    response = client.chat("你好")
    print(f"回复：{response[:100]}...")
    
    # 切换到 OpenAI（如果有 API Key）
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        new_config = ModelConfig.create_openai_config(
            api_key=openai_key,
            model_name="gpt-4o"
        )
        client.switch_model(new_config)
        print("\n切换到 OpenAI GPT-4o:")
        response = client.chat("你好")
        print(f"回复：{response[:100]}...")
    
    client.close()


def example_langchain_integration():
    """示例 6: LangChain 集成"""
    print("\n" + "=" * 60)
    print("示例 6: LangChain 集成")
    print("=" * 60)
    
    from src.fatsia import FatsiaChatModel, ModelConfig
    from langchain_core.messages import HumanMessage, SystemMessage
    
    config = ModelConfig.create_qwen3_config(
        api_key=os.getenv("QWEN_API_KEY", "your-qwen-api-key"),
    )
    
    # 创建 LangChain 聊天模型
    llm = FatsiaChatModel(config=config)
    
    # 简单调用
    messages = [
        SystemMessage(content="你是一个数学老师，擅长用简单的语言解释复杂的概念"),
        HumanMessage(content="什么是微积分？")
    ]
    
    response = llm.invoke(messages)
    print(f"\n回复：{response.content}")
    
    llm.close()


def example_openai_compatible():
    """示例 7: OpenAI 兼容接口"""
    print("\n" + "=" * 60)
    print("示例 7: OpenAI 兼容接口")
    print("=" * 60)
    
    from src.fatsia import FatsiaOpenAIClient, ModelConfig
    
    # 创建兼容客户端（使用千问 3）
    config = ModelConfig.create_qwen3_config(
        api_key=os.getenv("QWEN_API_KEY", "your-qwen-api-key"),
    )
    
    client = FatsiaOpenAIClient(config)
    
    # 使用方式与 OpenAI SDK 完全相同
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "你是一个程序员助手"},
            {"role": "user", "content": "如何用 Python 实现快速排序？"}
        ],
        temperature=0.7,
    )
    
    print(f"\n回复：{response.choices[0].message.content}")
    
    # 流式调用
    print("\n流式输出：\n")
    stream_response = client.chat.completions.create(
        model="qwen-plus",
        messages=[{"role": "user", "content": "写一首关于秋天的短诗"}],
        stream=True,
    )
    
    for chunk in stream_response:
        content = chunk.choices[0].delta.get("content")
        if content:
            print(content, end="", flush=True)
    print()


def example_gemini():
    """示例 8: 使用 Google Gemini"""
    print("\n" + "=" * 60)
    print("示例 8: 使用 Google Gemini")
    print("=" * 60)
    
    from src.fatsia import FatsiaClient, ModelConfig
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("未设置 GEMINI_API_KEY，跳过此示例")
        return
    
    config = ModelConfig.create_gemini_config(
        api_key=gemini_key,
        model_name="gemini-1.5-pro",
    )
    
    with FatsiaClient(config) as client:
        response = client.chat("你好，Gemini！")
        print(f"\n回复：{response}")


def main():
    """主函数 - 运行所有示例"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║              Fatsia 示例程序                              ║
    ║                                                          ║
    ║         支持：千问 3 | OpenAI | Gemini                    ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # 运行示例
    # try:
    #     example_basic_chat()
    # except Exception as e:
    #     print(f"示例 1 执行失败：{e}")
    
    # try:
    #     example_with_system_prompt()
    # except Exception as e:
    #     print(f"示例 2 执行失败：{e}")

    # try:
    #     example_stream_chat()
    # except Exception as e:
    #     print(f"示例 3 执行失败：{e}")

    # try:
    #     example_multi_turn_chat()
    # except Exception as e:
    #     print(f"示例 4 执行失败：{e}")

    # try:
    #     example_model_switch()
    # except Exception as e:
    #     print(f"示例 5 执行失败：{e}")

    try:
        example_langchain_integration()
    except Exception as e:
        print(f"示例 6 执行失败：{e}")

    # try:
    #     example_openai_compatible()
    # except Exception as e:
    #     print(f"示例 7 执行失败：{e}")

    # try:
    #     example_gemini()
    # except Exception as e:
    #     print(f"示例 8 执行失败：{e}")
    
    print("\n" + "=" * 60)
    print("所有示例执行完毕")
    print("=" * 60)
    print("\n日志文件位置：../logs/fatsia/fatsia.log")
    print("可以在日志文件中查看完整的请求和响应报文\n")


if __name__ == "__main__":
    main()
