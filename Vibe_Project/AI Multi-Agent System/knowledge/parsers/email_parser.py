"""
邮件文件解析器
==============

【支持格式】
- .eml: RFC 822格式（Unix mail格式，Outlook Express等）
- .msg: Microsoft Outlook格式

【功能】
- 解析邮件头（发件人、收件人、主题、时间）
- 提取正文内容（纯文本+HTML）
- 提取附件列表
- 处理编码问题

【使用场景】
- 邮件归档检索
- 企业知识库构建
- 邮件历史搜索
"""

import email
import email.policy
from email import policy
from email.parser import BytesParser, Parser
from email.policy import default
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import re

# 可选导入msg格式支持
try:
    from extract_msg import Message as MsgReader
    HAS_EXTRACT_MSG = True
except ImportError:
    HAS_EXTRACT_MSG = False


@dataclass
class EmailContent:
    """邮件内容"""
    subject: str
    sender: str
    recipients: List[str]
    date: str
    body_text: str          # 纯文本正文
    body_html: str           # HTML正文
    body_plain: str          # 简化后的纯文本
    attachments: List[Dict]  # 附件列表
    headers: Dict[str, str]  # 邮件头
    metadata: Dict[str, Any]


class EmailParser:
    """邮件解析器

    支持 .eml (RFC 822) 和 .msg (Outlook) 格式
    """

    def __init__(self):
        self.supported_extensions = {'.eml', '.msg'}

    def parse(self, file_path: str) -> Dict:
        """解析邮件文件

        Args:
            file_path: 邮件文件路径

        Returns:
            包含邮件内容的字典
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == '.eml':
            return self._parse_eml(file_path)
        elif ext == '.msg':
            return self._parse_msg(file_path)
        else:
            raise ValueError(f"Unsupported email format: {ext}")

    def _parse_eml(self, file_path: str) -> Dict:
        """解析RFC 822格式邮件(.eml)"""
        with open(file_path, 'rb') as f:
            raw_email = f.read()

        # 使用BytesParser解析
        msg = BytesParser(policy=default).parsebytes(raw_email)

        # 提取邮件信息
        subject = self._decode_header(msg.get('Subject', ''))
        sender = self._decode_header(msg.get('From', ''))
        recipients = self._parse_recipients(msg.get('To', ''))
        date = msg.get('Date', '')

        # 提取正文
        body_text, body_html = self._extract_body(msg)
        body_plain = self._simplify_text(body_text)

        # 提取附件
        attachments = self._extract_attachments(msg)

        # 提取头信息
        headers = dict(msg.items())

        # 提取元数据
        metadata = {
            "file_name": Path(file_path).name,
            "file_size": Path(file_path).stat().st_size,
            "content_type": msg.get('Content-Type', ''),
            "message_id": msg.get('Message-ID', ''),
            "in_reply_to": msg.get('In-Reply-To', ''),
            "references": msg.get('References', ''),
        }

        content = EmailContent(
            subject=subject,
            sender=sender,
            recipients=recipients,
            date=date,
            body_text=body_text,
            body_html=body_html,
            body_plain=body_plain,
            attachments=attachments,
            headers=headers,
            metadata=metadata
        )

        return self._content_to_dict(content)

    def _parse_msg(self, file_path: str) -> Dict:
        """解析Outlook邮件(.msg)"""
        if not HAS_EXTRACT_MSG:
            raise ImportError(
                "extract_msg library not installed. "
                "Install with: pip install extract_msg"
            )

        try:
            msg_obj = MsgReader(file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to parse .msg file: {e}")

        # 提取基本信息
        subject = msg_obj.subject or ""
        sender = msg_obj.sender or ""
        recipients = msg_obj.to or []
        date = msg_obj.date or ""

        # 提取正文
        body_html = msg_obj.htmlBody or ""
        body_text = msg_obj.body or ""
        body_plain = self._simplify_text(body_text)

        # 提取附件
        attachments = []
        try:
            for att in msg_obj.attachments:
                attachments.append({
                    "name": att.get("name", "unknown"),
                    "size": att.get("size", 0),
                    "type": att.get("type", "application/octet-stream")
                })
        except Exception:
            pass  # 附件提取失败不影响主内容

        # 头信息
        headers = {
            "From": sender,
            "To": ", ".join(recipients),
            "Subject": subject,
            "Date": date,
        }

        # 元数据
        metadata = {
            "file_name": Path(file_path).name,
            "file_size": Path(file_path).stat().st_size,
            "message_class": getattr(msg_obj, "message_class", ""),
        }

        content = EmailContent(
            subject=subject,
            sender=sender,
            recipients=recipients,
            date=date,
            body_text=body_text,
            body_html=body_html,
            body_plain=body_plain,
            attachments=attachments,
            headers=headers,
            metadata=metadata
        )

        return self._content_to_dict(content)

    def _decode_header(self, header_value: str) -> str:
        """解码邮件头（处理编码）"""
        if not header_value:
            return ""

        try:
            decoded_parts = email.header.decode_header(header_value)
            result = []
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    try:
                        result.append(part.decode(encoding or 'utf-8', errors='replace'))
                    except (LookupError, UnicodeDecodeError):
                        result.append(part.decode('utf-8', errors='replace'))
                else:
                    result.append(part)
            return ' '.join(result)
        except Exception:
            return header_value

    def _parse_recipients(self, to_header: str) -> List[str]:
        """解析收件人列表"""
        if not to_header:
            return []

        # 使用邮件解析器解析地址
        try:
            addresses = email.utils.getaddresses([to_header])
            return [self._decode_header(addr[1]) or addr[0] for addr in addresses]
        except Exception:
            # 回退：逗号分隔
            return [r.strip() for r in to_header.split(',') if r.strip()]

    def _extract_body(self, msg) -> tuple:
        """提取邮件正文（纯文本和HTML）"""
        body_text = ""
        body_html = ""

        if msg.is_multipart():
            # 多部分邮件，遍历所有部分
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = part.get_content_disposition()

                # 跳过附件
                if content_disposition == 'attachment':
                    continue

                if content_type == 'text/plain' and not body_text:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body_text = part.get_payload(decode=True).decode(charset, errors='replace')
                    except Exception:
                        body_text = str(part.get_payload())
                elif content_type == 'text/html' and not body_html:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body_html = part.get_payload(decode=True).decode(charset, errors='replace')
                    except Exception:
                        body_html = str(part.get_payload())
        else:
            # 单部分邮件
            content_type = msg.get_content_type()
            try:
                charset = msg.get_content_charset() or 'utf-8'
                payload = msg.get_payload(decode=True)
                if payload:
                    decoded = payload.decode(charset, errors='replace')
                else:
                    decoded = str(msg.get_payload())
            except Exception:
                decoded = str(msg.get_payload())

            if content_type == 'text/html':
                body_html = decoded
                body_text = self._html_to_text(decoded)
            else:
                body_text = decoded

        return body_text, body_html

    def _extract_attachments(self, msg) -> List[Dict]:
        """提取附件列表"""
        attachments = []

        for part in msg.walk():
            content_disposition = part.get_content_disposition()
            if content_disposition and 'attachment' in content_disposition:
                filename = part.get_filename()
                if filename:
                    # 解码文件名
                    filename = self._decode_header(filename)
                    attachments.append({
                        "name": filename,
                        "size": len(part.get_payload(decode=True) or b''),
                        "type": part.get_content_type()
                    })

        return attachments

    def _simplify_text(self, text: str) -> str:
        """简化文本（去除多余空白）"""
        if not text:
            return ""

        # 去除多余空白
        lines = text.split('\n')
        simplified_lines = []

        for line in lines:
            # 去除首尾空白
            line = line.strip()
            # 跳过引用标记行（>开头）
            if line.startswith('>'):
                continue
            # 跳过空行（但保留最多一个）
            if line == '':
                if simplified_lines and simplified_lines[-1] != '':
                    simplified_lines.append('')
                continue
            simplified_lines.append(line)

        result = '\n'.join(simplified_lines)
        # 去除首尾空白
        return result.strip()

    def _html_to_text(self, html: str) -> str:
        """HTML转纯文本"""
        if not html:
            return ""

        # 简单的HTML标签去除
        text = re.sub(r'<br\s*/?>', '\n', html)
        text = re.sub(r'</p>', '\n\n', text)
        text = re.sub(r'</div>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)

        # 解码HTML实体
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')

        return text.strip()

    def _content_to_dict(self, content: EmailContent) -> Dict:
        """将EmailContent转换为字典"""
        return {
            "subject": content.subject,
            "sender": content.sender,
            "recipients": content.recipients,
            "date": content.date,
            "body_text": content.body_text,
            "body_html": content.body_html,
            "body_plain": content.body_plain,
            "attachments": content.attachments,
            "headers": content.headers,
            "metadata": content.metadata,
            "num_attachments": len(content.attachments)
        }

    def can_parse(self, file_path: str) -> bool:
        """检查是否支持此文件"""
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_extensions


# ========== 使用示例 ==========
"""
from knowledge.parsers.email_parser import EmailParser

parser = EmailParser()

# 解析.eml文件
result = parser.parse("email.eml")
print(f"Subject: {result['subject']}")
print(f"From: {result['sender']}")
print(f"Body: {result['body_plain'][:200]}...")

# 检查是否支持
if parser.can_parse("document.pdf"):
    print("Cannot parse PDF")
if parser.can_parse("email.eml"):
    print("Can parse EML")
"""


if __name__ == "__main__":
    # 快速测试
    parser = EmailParser()
    print(f"EmailParser initialized. Supported: {parser.supported_extensions}")
    print(f"MSG support available: {HAS_EXTRACT_MSG}")
