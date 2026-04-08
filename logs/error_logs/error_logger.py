"""
错误日志记录模块 Error Logger
=============================

【学习要点】
1. 为什么要记录错误日志？
   - 快速定位问题
   - 分析错误趋势
   - 优化系统稳定性

2. 错误日志的核心要素
   - timestamp: 发生时间
   - error_type: 错误类型
   - message: 错误信息
   - stack_trace: 调用栈
   - context: 上下文（用户输入、agent状态等）

3. 错误分级
   - CRITICAL: 系统崩溃
   - ERROR: 功能失败
   - WARNING: 异常但可恢复
   - INFO: 一般信息
"""

import logging
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum


class ErrorLevel(Enum):
    """错误级别枚举

    【学习要点】枚举(Enum)的使用
    - 替代魔法字符串: "CRITICAL" vs ErrorLevel.CRITICAL
    - 类型安全: 防止拼写错误
    - 可读性强: 代码更清晰
    """
    CRITICAL = "CRITICAL"  # 系统崩溃，需要立即处理
    ERROR = "ERROR"        # 功能失败，影响业务流程
    WARNING = "WARNING"    # 异常但可自动恢复
    INFO = "INFO"          # 一般信息，仅记录


class ErrorLogger:
    """错误日志记录器

    【设计思路】
    - 单例模式: 全局只有一个实例，避免重复写入
    - 分级记录: 不同级别不同处理
    - 上下文追踪: 记录错误发生的完整上下文
    """

    _instance: Optional['ErrorLogger'] = None

    def __new__(cls) -> 'ErrorLogger':
        """单例模式实现

        【学习要点】__new__ vs __init__
        - __new__: 创建对象（分配内存）
        - __init__: 初始化对象（填充数据）
        - 单例模式需要在__new__中控制实例唯一性
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.log_dir = Path("G:/claude_code_project/logs/error_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 错误日志文件（按日期）
        self.error_log_file = self.log_dir / f"error_{datetime.now().strftime('%Y%m%d')}.json"

        # 结构化日志记录器
        self.logger = logging.getLogger("ErrorLogger")
        self.logger.setLevel(logging.DEBUG)

        # 避免重复添加handler
        if not self.logger.handlers:
            # 控制台输出
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter('[%(levelname)s] %(message)s')
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)

            # 文件输出
            file_handler = logging.FileHandler(self.log_dir / "error.log")
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

        self._initialized = True

    def log(
        self,
        error_type: str,
        message: str,
        level: ErrorLevel = ErrorLevel.ERROR,
        context: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None
    ) -> str:
        """记录错误

        Args:
            error_type: 错误类型（如 "RAGRetrievalError"）
            message: 错误描述
            level: 错误级别
            context: 上下文信息（agent状态、用户输入等）
            exc_info: 异常对象

        Returns:
            error_id: 错误唯一ID，用于追踪
        """
        error_id = f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # 构建错误记录
        error_record = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "level": level.value,
            "message": message,
            "context": context or {},
        }

        # 如果有异常信息，添加堆栈跟踪
        if exc_info:
            error_record["stack_trace"] = traceback.format_exc()
            error_record["exception_type"] = type(exc_info).__name__

        # 写入JSON日志文件（机器可读）
        self._write_json_log(error_record)

        # 写入文本日志（人类可读）
        log_message = f"[{error_id}] {level.value} - {error_type}: {message}"
        if context:
            log_message += f"\n  Context: {json.dumps(context, ensure_ascii=False, indent=2)}"

        if level == ErrorLevel.CRITICAL:
            self.logger.critical(log_message)
        elif level == ErrorLevel.ERROR:
            self.logger.error(log_message)
        elif level == ErrorLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        return error_id

    def _write_json_log(self, record: Dict[str, Any]) -> None:
        """写入JSON格式日志

        【学习要点】JSON日志的优势
        - 结构化数据，便于程序解析
        - 可用于日志分析系统
        - 支持复杂嵌套结构
        """
        logs = []
        if self.error_log_file.exists():
            try:
                with open(self.error_log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

        logs.append(record)

        with open(self.error_log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def get_recent_errors(
        self,
        limit: int = 50,
        level: Optional[ErrorLevel] = None,
        error_type: Optional[str] = None
    ) -> list:
        """获取最近的错误记录

        Args:
            limit: 返回数量限制
            level: 按级别过滤
            error_type: 按类型过滤

        Returns:
            错误记录列表
        """
        if not self.error_log_file.exists():
            return []

        with open(self.error_log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)

        # 过滤
        if level:
            logs = [l for l in logs if l.get('level') == level.value]
        if error_type:
            logs = [l for l in logs if l.get('error_type') == error_type]

        # 返回最近的
        return logs[-limit:]

    def generate_error_report(self) -> str:
        """生成错误报告（用于PM Agent）

        【学习要点】报告生成
        - 统计数据聚合
        - 趋势分析
        - 可读性输出
        """
        if not self.error_log_file.exists():
            return "No errors recorded."

        with open(self.error_log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)

        if not logs:
            return "No errors recorded."

        # 统计
        total = len(logs)
        by_level = {}
        by_type = {}

        for log in logs:
            level = log.get('level', 'UNKNOWN')
            error_type = log.get('error_type', 'UNKNOWN')
            by_level[level] = by_level.get(level, 0) + 1
            by_type[error_type] = by_type.get(error_type, 0) + 1

        # 生成报告
        report = f"""# 错误报告
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 概览
- 总错误数: {total}
- Critical: {by_level.get('CRITICAL', 0)}
- Error: {by_level.get('ERROR', 0)}
- Warning: {by_level.get('WARNING', 0)}

## 错误类型分布
"""
        for et, count in sorted(by_type.items(), key=lambda x: -x[1]):
            report += f"- {et}: {count}\n"

        return report


# 全局单例
error_logger = ErrorLogger()
