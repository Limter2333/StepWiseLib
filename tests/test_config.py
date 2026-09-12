"""配置模块单元测试。"""
import os
import pytest
import tempfile
import yaml
from harness.config import LLMConfig, AgentConfig, HarnessConfig


class TestLLMConfig:
    """LLMConfig 测试。"""
    
    def test_default_values(self):
        """测试默认值。"""
        config = LLMConfig()
        assert config.base_url == "https://opencode.ai/zen/v1"
        assert config.model == "deepseek-v4-flash-free"
        assert config.max_retries == 5
        assert config.timeout == 60.0


class TestAgentConfig:
    """AgentConfig 测试。"""
    
    def test_default_values(self):
        """测试默认值。"""
        config = AgentConfig()
        assert config.max_steps == 15
        assert config.observe_max_chars == 4000
        assert config.working_dir == "."


class TestHarnessConfig:
    """HarnessConfig 测试。"""
    
    def test_from_yaml(self, tmp_path):
        """测试从 YAML 加载配置。"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "llm": {
                "model": "test-model",
                "base_url": "https://test.example.com",
            },
            "agent": {
                "max_steps": 10,
                "working_dir": "/tmp",
            },
            "permissions": {
                "run_terminal_command": "confirm"
            }
        }
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")
        
        config = HarnessConfig.from_yaml(str(config_file))
        
        assert config.llm.model == "test-model"
        assert config.llm.base_url == "https://test.example.com"
        assert config.agent.max_steps == 10
        assert config.agent.working_dir == "/tmp"
        assert config.permissions.get("run_terminal_command") == "confirm"
    
    def test_from_empty_yaml(self, tmp_path):
        """测试从空 YAML 加载配置。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("", encoding="utf-8")
        
        config = HarnessConfig.from_yaml(str(config_file))
        assert config.llm.model == "deepseek-v4-flash-free"  # 默认值
    
    def test_resolve_working_dir(self):
        """测试工作目录解析。"""
        config = HarnessConfig()
        resolved = config.resolve_working_dir()
        assert os.path.isabs(resolved)
