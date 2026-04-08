"""
AI Multi-Agent System - User Client
==================================

简易用户客户端，通过命令行与AI对话
"""

import requests
import json
import sys
import os

# 配置
API_BASE = "http://localhost:8000"
SESSION_ID = f"user_{os.getlogin()}"

class UserClient:
    """用户客户端"""

    def __init__(self, api_base: str = API_BASE):
        self.api_base = api_base
        self.session_id = SESSION_ID
        self.use_knowledge = True

    def chat(self, message: str) -> str:
        """发送消息并获取回复"""
        url = f"{self.api_base}/api/chat/chat"
        data = {
            "message": message,
            "session_id": self.session_id,
            "use_knowledge": self.use_knowledge
        }

        try:
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get("message", "No response")
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to API server. Is it running?"
        except requests.exceptions.Timeout:
            return "Error: Request timeout"
        except Exception as e:
            return f"Error: {str(e)}"

    def toggle_knowledge(self):
        """切换知识库模式"""
        self.use_knowledge = not self.use_knowledge
        status = "enabled" if self.use_knowledge else "disabled"
        print(f"[System] Knowledge base {status}")
        return self.use_knowledge

    def get_history(self) -> list:
        """获取对话历史"""
        url = f"{self.api_base}/api/chat/sessions/{self.session_id}/history"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result.get("messages", [])
        except Exception as e:
            print(f"Error getting history: {e}")
            return []

    def print_history(self):
        """打印对话历史"""
        history = self.get_history()
        if not history:
            print("[System] No conversation history")
            return

        print("\n" + "=" * 60)
        print(f"Conversation History (Session: {self.session_id})")
        print("=" * 60)
        for msg in history[-10:]:  # 最近10条
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            # 截断长消息
            if len(content) > 200:
                content = content[:200] + "..."
            prefix = "You" if role == "user" else "AI"
            print(f"\n[{prefix}]:")
            print(f"  {content}")
        print("\n" + "=" * 60)


def main():
    """主函数"""
    client = UserClient()

    print()
    print("=" * 60)
    print("  AI Multi-Agent System - User Client")
    print("=" * 60)
    print()
    print("Commands:")
    print("  /history  - Show conversation history")
    print("  /knowledge - Toggle knowledge base mode")
    print("  /quit    - Exit")
    print()
    print(f"Knowledge base: {'ON' if client.use_knowledge else 'OFF'}")
    print("=" * 60)
    print()

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "/quit":
                print("Goodbye!")
                break

            if user_input.lower() == "/history":
                client.print_history()
                continue

            if user_input.lower() == "/knowledge":
                client.toggle_knowledge()
                continue

            # 发送消息
            print("\nAI: ", end="", flush=True)
            response = client.chat(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
