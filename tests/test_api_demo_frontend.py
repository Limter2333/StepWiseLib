"""
测试前端API演示页面增强

验证新API端点按钮已添加到前端
"""

import pytest
import re
import os


class TestAPIDemoEnhancement:
    """前端API演示增强测试"""

    @pytest.fixture
    def index_html(self):
        """读取index.html"""
        with open('web/index.html', 'r', encoding='utf-8') as f:
            return f.read()

    def test_multihop_api_button_exists(self, index_html):
        """用户故事: 前端有多跳推理API测试按钮"""
        # 查找multihop按钮
        assert "testApiInCategory('rag', 'multihop')" in index_html
        assert "POST /api/rag/multihop" in index_html

    def test_cache_stats_api_button_exists(self, index_html):
        """用户故事: 前端有缓存统计API测试按钮"""
        assert "testApiInCategory('rag', 'cache-stats')" in index_html
        assert "GET /api/rag/cache/stats" in index_html

    def test_context_set_api_button_exists(self, index_html):
        """用户故事: 前端有Agent上下文设置API测试按钮"""
        assert "testApiInCategory('agent', 'ctx-set')" in index_html
        assert "POST /api/agents/context/set" in index_html

    def test_context_stats_api_button_exists(self, index_html):
        """用户故事: 前端有Agent上下文统计API测试按钮"""
        assert "testApiInCategory('agent', 'ctx-stats')" in index_html
        assert "GET /api/agents/context/stats" in index_html

    def test_collaborate_api_button_exists(self, index_html):
        """用户故事: 前端有Agent协作API测试按钮"""
        assert "testApiInCategory('agent', 'collaborate')" in index_html
        assert "POST /api/agents/collaborate/submit" in index_html

    def test_api_test_config_includes_new_apis(self, index_html):
        """验证testApiInCategory配置包含新API"""
        # 确认tests['rag']包含multihop
        assert "'multihop': { method: 'POST', path: '/api/rag/multihop'" in index_html
        # 确认tests['rag']包含cache-stats
        assert "'cache-stats': { method: 'GET', path: '/api/rag/cache/stats'" in index_html
        # 确认tests['agent']包含ctx-set
        assert "'ctx-set': { method: 'POST', path: '/api/agents/context/set'" in index_html

    def test_test_api_supports_params(self, index_html):
        """用户故事: testApiInCategory支持GET请求的查询参数"""
        # 查找multihop-decompose配置（有params）
        assert "'multihop-decompose': { method: 'POST', path: '/api/rag/multihop/decompose', params:" in index_html
        # 确认函数支持params
        assert "if (test.params)" in index_html
        assert "new URLSearchParams(test.params)" in index_html

    def test_feature_card_elements_added(self, index_html):
        """验证新的feature-card元素已添加"""
        # 查找多跳推理卡
        assert "🔀" in index_html and "多跳推理查询" in index_html
        # 查找缓存统计卡
        assert "📦" in index_html and "缓存统计" in index_html
        # 查找上下文设置卡
        assert "🔗" in index_html and "共享上下文" in index_html

    def test_no_syntax_errors_in_js(self, index_html):
        """验证JavaScript语法正确（无明显错误）"""
        # 提取testApiInCategory函数
        match = re.search(r'async function testApiInCategory\([^)]+\)\s*{(.*?)^\}', index_html, re.MULTILINE | re.DOTALL)
        if match:
            func_body = match.group(1)
            # 检查括号匹配
            open_braces = func_body.count('{')
            close_braces = func_body.count('}')
            assert open_braces == close_braces, f"Brace mismatch: {{ = {open_braces}, }} = {close_braces}"
