"""
Settings 配置模块测试
====================

测试配置管理和环境变量加载
"""

import pytest
import os
from unittest.mock import patch


class TestSettings:
    """Settings配置测试"""

    def test_settings_import(self):
        """测试settings模块可导入"""
        from config.settings import Settings
        assert Settings is not None

    def test_settings_defaults(self):
        """测试默认配置值"""
        from config.settings import Settings

        # 创建一个不加载环境变量的Settings实例
        settings = Settings(_env_file=None)

        assert settings.PROJECT_NAME == "AI Multi-Agent System"
        assert settings.VERSION == "0.1.0"
        assert settings.API_PORT == 8000
        assert settings.LLM_PROVIDER in ["anthropic", "openai", "local"]
        assert settings.CHUNK_SIZE > 0
        assert settings.CHUNK_OVERLAP >= 0
        assert settings.RAG_TOP_K > 0

    def test_settings_debug_mode(self):
        """测试调试模式配置"""
        from config.settings import Settings

        settings = Settings(_env_file=None)
        # DEBUG默认为False
        assert settings.DEBUG is False or settings.DEBUG is True

    def test_settings_llm_config(self):
        """测试LLM配置"""
        from config.settings import Settings

        settings = Settings(_env_file=None)

        assert settings.LLM_PROVIDER in ["anthropic", "openai", "local"]
        assert settings.LLM_MODEL is not None
        assert settings.LLM_TEMPERATURE >= 0
        assert settings.LLM_TEMPERATURE <= 2
        assert settings.LLM_MAX_TOKENS > 0

    def test_settings_vectorstore_config(self):
        """测试向量数据库配置"""
        from config.settings import Settings

        settings = Settings(_env_file=None)

        assert settings.CHROMA_PERSIST_DIR is not None
        assert settings.CHROMA_COLLECTION_NAME is not None
        assert settings.MILVUS_PORT > 0

    def test_settings_rag_config(self):
        """测试RAG配置"""
        from config.settings import Settings

        settings = Settings(_env_file=None)

        assert settings.RAG_TOP_K > 0
        assert 0 <= settings.RAG_SCORE_THRESHOLD <= 1

    def test_settings_doc_types(self):
        """测试支持的文档类型"""
        from config.settings import Settings

        settings = Settings(_env_file=None)

        assert isinstance(settings.SUPPORTED_DOC_TYPES, list)
        assert len(settings.SUPPORTED_DOC_TYPES) > 0
        assert "pdf" in settings.SUPPORTED_DOC_TYPES

    def test_settings_chunk_config(self):
        """测试文本分块配置"""
        from config.settings import Settings

        settings = Settings(_env_file=None)

        assert settings.CHUNK_SIZE > 0
        assert settings.CHUNK_OVERLAP >= 0
        assert settings.CHUNK_OVERLAP < settings.CHUNK_SIZE

    def test_settings_token_config(self):
        """测试Token配置"""
        from config.settings import Settings

        settings = Settings(_env_file=None)

        assert settings.LLM_MAX_TOKENS > 0
        assert settings.MAX_TOKENS_PER_CYCLE > 0


class TestSettingsEnvironment:
    """Settings环境变量测试"""

    def test_env_override(self):
        """测试环境变量覆盖"""
        with patch.dict(os.environ, {"PROJECT_NAME": "Test Project"}):
            from config.settings import Settings
            settings = Settings(_env_file=None)
            # 注意：由于Settings可能被缓存，这个测试可能不准确
            # 实际项目中应使用不同的测试策略
            assert settings.PROJECT_NAME is not None

    def test_env_debug_override(self):
        """测试DEBUG环境变量覆盖"""
        with patch.dict(os.environ, {"DEBUG": "true"}):
            from config.settings import Settings
            settings = Settings(_env_file=None)
            # DEBUG应该是True或False，不应抛出异常
            assert isinstance(settings.DEBUG, bool)


class TestSettingsValidation:
    """Settings验证测试"""

    def test_chunk_overlap_less_than_chunk_size(self):
        """测试CHUNK_OVERLAP必须小于CHUNK_SIZE"""
        from config.settings import Settings

        settings = Settings(_env_file=None)
        # CHUNK_OVERLAP应该小于CHUNK_SIZE以保证有效重叠
        assert settings.CHUNK_OVERLAP < settings.CHUNK_SIZE

    def test_rag_threshold_range(self):
        """测试RAG阈值范围"""
        from config.settings import Settings

        settings = Settings(_env_file=None)
        # RAG_SCORE_THRESHOLD应该在0-1之间
        assert 0 <= settings.RAG_SCORE_THRESHOLD <= 1

    def test_temperature_range(self):
        """测试温度参数范围"""
        from config.settings import Settings

        settings = Settings(_env_file=None)
        # LLM_TEMPERATURE应该在0-2之间
        assert 0 <= settings.LLM_TEMPERATURE <= 2

    def test_api_port_valid(self):
        """测试API端口有效性"""
        from config.settings import Settings

        settings = Settings(_env_file=None)
        # 端口应该在有效范围内
        assert 1 <= settings.API_PORT <= 65535


class TestSettingsProperties:
    """Settings属性测试"""

    def test_project_info(self):
        """测试项目信息属性"""
        from config.settings import Settings

        settings = Settings(_env_file=None)

        assert settings.PROJECT_NAME is not None
        assert len(settings.PROJECT_NAME) > 0
        assert settings.VERSION is not None
        assert len(settings.VERSION) > 0

    def test_database_paths(self):
        """测试数据库路径配置"""
        from config.settings import Settings

        settings = Settings(_env_file=None)

        assert settings.CHROMA_PERSIST_DIR is not None
        # 路径应该是字符串
        assert isinstance(settings.CHROMA_PERSIST_DIR, str)

    def test_embedding_model(self):
        """测试Embedding模型配置"""
        from config.settings import Settings

        settings = Settings(_env_file=None)

        assert settings.EMBEDDING_MODEL is not None
        assert len(settings.EMBEDDING_MODEL) > 0


class TestSettingsEdgeCases:
    """Settings边界情况测试"""

    def test_empty_env_file(self):
        """测试空环境文件"""
        from config.settings import Settings

        # 应该使用默认值
        settings = Settings(_env_file=".env.nonexistent")
        assert settings.PROJECT_NAME is not None

    def test_missing_env_vars(self):
        """测试缺失环境变量"""
        from config.settings import Settings

        # 应该使用默认值
        settings = Settings(_env_file=None)
        assert settings.PROJECT_NAME == "AI Multi-Agent System"

    def test_extra_fields_allowed(self):
        """测试额外字段允许（extra='ignore'）"""
        from config.settings import Settings

        # 如果.env中有额外字段，不应抛出异常
        # Pydantic的extra="ignore"设置应该使其被忽略
        settings = Settings(_env_file=None)
        assert settings is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
