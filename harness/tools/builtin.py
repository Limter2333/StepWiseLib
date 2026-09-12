import os
import subprocess
from .base import tool


@tool(description="读取指定路径的文件内容", permission="safe")
def read_file(file_path: str) -> str:
    """读取指定路径的文件内容。
    
    Args:
        file_path: 文件的绝对路径
        
    Returns:
        文件内容字符串，或错误信息
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"文件不存在：{file_path}"
    except PermissionError:
        return f"无权限读取文件：{file_path}"
    except Exception as e:
        return f"读取文件失败：{str(e)}"


@tool(description="将内容写入指定路径的文件", permission="confirm", requires_confirm=True)
def write_to_file(file_path: str, content: str) -> str:
    """将内容写入指定路径的文件。
    
    如果文件不存在会自动创建，存在则覆盖。
    
    Args:
        file_path: 文件的绝对路径
        content: 要写入的内容
        
    Returns:
        成功或失败消息
    """
    try:
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"文件已成功写入：{file_path}"
    except PermissionError:
        return f"无权限写入文件：{file_path}"
    except Exception as e:
        return f"写入文件失败：{str(e)}"


@tool(description="执行终端命令，返回命令输出", permission="admin", requires_confirm=True)
def run_terminal_command(command: str) -> str:
    """执行终端命令并返回输出。
    
    注意：执行前会请求用户确认（由 requires_confirm=True 控制）。
    仅允许安全的命令（白名单机制待实现）。
    
    Args:
        command: 要执行的终端命令
        
    Returns:
        命令的标准输出和错误输出
    """
    try:
        # 安全检查：禁止危险命令
        dangerous_commands = ["rm -rf", "format", "del /f", "shutdown", "reboot"]
        cmd_lower = command.lower().strip()
        for dangerous in dangerous_commands:
            if dangerous in cmd_lower:
                return f"安全限制：禁止执行危险命令 '{dangerous}'"
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,  # 30秒超时
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n错误输出：{result.stderr}"
        
        if not output.strip():
            output = "命令执行完成，无输出"
        
        return output
    except subprocess.TimeoutExpired:
        return "命令执行超时（30秒）"
    except Exception as e:
        return f"命令执行失败：{str(e)}"


def builtin_tools() -> list:
    """返回所有内置工具的 ToolSpec 列表。"""
    return [read_file, write_to_file, run_terminal_command]
