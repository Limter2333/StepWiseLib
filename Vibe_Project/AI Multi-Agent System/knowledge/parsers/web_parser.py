"""
网页解析器
==========

【学习要点】
1. 网页抓取 vs 解析
   - 抓取: 获取HTML内容
   - 解析: 提取目标信息

2. 常用库
   - requests: HTTP请求
   - BeautifulSoup: HTML解析
   - crawl4ai: 专为AI设计的抓取工具
"""

from typing import List, Dict
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin


class WebParser:
    """网页解析器

    【使用流程】
    1. 发送HTTP请求获取HTML
    2. 用BeautifulSoup解析
    3. 提取文本和链接
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.supported_extensions = [".html", ".htm"]

    def parse(self, url: str) -> Dict:
        """解析网页

        Args:
            url: 网页URL

        Returns:
            解析结果字典
        """
        result = {
            "url": url,
            "title": "",
            "text": "",
            "links": [],
            "metadata": {}
        }

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # 提取标题
            if soup.title:
                result["title"] = soup.title.string

            # 提取正文（尝试多种选择器）
            main_content = (
                soup.find("main") or
                soup.find("article") or
                soup.find("div", class_="content") or
                soup.find("body")
            )

            if main_content:
                # 移除script和style
                for tag in main_content.find_all(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

                # 提取文本
                text = main_content.get_text(separator="\n", strip=True)
                # 清理多余空行
                lines = [line for line in text.split("\n") if line.strip()]
                result["text"] = "\n".join(lines)

            # 提取链接
            for link in soup.find_all("a", href=True):
                href = link["href"]
                # 处理相对URL
                full_url = urljoin(url, href)
                result["links"].append({
                    "text": link.get_text(strip=True),
                    "url": full_url
                })

            # 提取元数据
            meta_tags = soup.find_all("meta")
            for tag in meta_tags:
                name = tag.get("name") or tag.get("property", "")
                content = tag.get("content", "")
                if name and content:
                    result["metadata"][name] = content

        except requests.RequestException as e:
            result["error"] = str(e)

        return result

    def extract_structured_data(self, url: str) -> Dict:
        """提取结构化数据（如JSON-LD）

        【学习要点】JSON-LD
        - 结构化数据格式
        - 被搜索引擎支持
        - 通常包含文章作者、日期等信息
        """
        result = self.parse(url)

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            # 查找JSON-LD脚本
            json_ld = soup.find("script", type="application/ld+json")
            if json_ld:
                import json
                result["structured_data"] = json.loads(json_ld.string)

        except Exception as e:
            result["structured_error"] = str(e)

        return result
