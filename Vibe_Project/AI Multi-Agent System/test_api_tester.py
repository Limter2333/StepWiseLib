from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

    def _load_templates(self) -> Dict:
        """加载测试模板"""
        return {
            "pytest": """import pytest
import requests

BASE_URL = "{base_url}"

class Test{endpoint_name}:
    """Test cases for {endpoint_path}"""

    def test_{method_lower}_{endpoint_safe}(self):
        """Test {method} {path}"""
        response = requests.{method_lower}(
            f"{{BASE_URL}}{path}",
            {headers_str}{data_str}
        )
        assert response.status_code == {expected_status}

    def test_{method_lower}_{endpoint_safe}_response_format(self):
        """Test {method} {path} response format"""
        response = requests.{method_lower}(
            f"{{BASE_URL}}{path}",
            {headers_str}{data_str}
        )
        assert response.status_code == {expected_status}
        assert "application/json" in response.headers.get("Content-Type", "")
""",
            "javascript": """const axios = require('axios');

describe('{endpoint_name}', () => {{
    const BASE_URL = '{base_url}';

    test('{method} {path}', async () => {{
        const response = await axios.{method_lower}(
            `{{BASE_URL}}{path}`,
            {{ {headers_str}{data_str} }}
        );
        expect(response.status).toBe({expected_status});
    }});
}});"""
        }

# Test it
obj = TestClass()
print('Templates loaded:', type(obj.test_templates))
