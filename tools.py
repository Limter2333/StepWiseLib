import os
import re
import glob as glob_module
import subprocess
import inspect
from typing import List, Optional, Tuple

# 工具装饰器

def tool(func):
    """标记函数为Agent工具"""
    func._is_tool = True
    func._tool_name = func.__name__
    func._tool_description = func.__doc__ or ""
    return func

def discover_tools():
    """自动发现所有标记为tool的函数"""
    tools = []
    current_module = inspect.getmodule(inspect.currentframe())
    
    for name, obj in inspect.getmembers(current_module):
        if inspect.isfunction(obj) and getattr(obj, '_is_tool', False):
            tools.append(obj)
    
    return tools

# 基础文件操作工具

@tool
def read_file(file_path: str, start_line: int = None, end_line: int = None) -> str:
    """
    读取文件内容，支持读取特定行范围
    
    Args:
        file_path: 文件路径
        start_line: 起始行号（从1开始）
        end_line: 结束行号（包含）
    
    Returns:
        文件内容字符串
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if start_line is not None or end_line is not None:
            # 调整为0-based索引
            start = (start_line - 1) if start_line else 0
            end = end_line if end_line else len(lines)
            lines = lines[start:end]
            return ''.join(lines)
        else:
            return ''.join(lines)
    except Exception as e:
        return f"读取文件失败: {str(e)}"

@tool
def write_to_file(file_path: str, content: str, append: bool = False) -> str:
    """
    将内容写入文件
    
    Args:
        file_path: 文件路径
        content: 要写入的内容
        append: 是否追加模式，False为覆盖模式
    
    Returns:
        操作结果消息
    """
    try:
        mode = 'a' if append else 'w'
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content.replace("\\n", "\n"))
        return f"写入成功: {file_path}"
    except Exception as e:
        return f"写入文件失败: {str(e)}"

@tool
def edit_file(file_path: str, old_string: str, new_string: str) -> str:
    """
    使用精确字符串替换修改文件
    
    Args:
        file_path: 文件路径
        old_string: 要替换的原始字符串
        new_string: 替换后的新字符串
    
    Returns:
        操作结果消息
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_string not in content:
            return f"未找到要替换的字符串: {old_string}"
        
        new_content = content.replace(old_string, new_string)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return f"编辑成功: {file_path}"
    except Exception as e:
        return f"编辑文件失败: {str(e)}"

# 搜索工具

@tool
def grep_search(pattern: str, file_path: str = None, directory: str = None, 
                include_pattern: str = None) -> str:
    """
    使用正则表达式搜索文件内容
    
    Args:
        pattern: 正则表达式模式
        file_path: 指定文件路径（与directory二选一）
        directory: 搜索目录（与file_path二选一）
        include_pattern: 文件匹配模式（如 "*.py"）
    
    Returns:
        搜索结果字符串
    """
    try:
        if file_path:
            # 搜索单个文件
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            matches = []
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    matches.append(f"{file_path}:{i}: {line.strip()}")
            
            return '\n'.join(matches) if matches else "未找到匹配内容"
        
        elif directory:
            # 搜索目录
            matches = []
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if include_pattern and not glob_module.fnmatch.fnmatch(file, include_pattern):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        for i, line in enumerate(lines, 1):
                            if re.search(pattern, line):
                                matches.append(f"{file_path}:{i}: {line.strip()}")
                    except:
                        continue
            
            return '\n'.join(matches) if matches else "未找到匹配内容"
        
        else:
            return "请指定file_path或directory参数"
    
    except Exception as e:
        return f"搜索失败: {str(e)}"

@tool
def glob_search(pattern: str, directory: str = ".") -> str:
    """
    通过模式匹配查找文件
    
    Args:
        pattern: glob模式（如 "**/*.py"）
        directory: 搜索目录
    
    Returns:
        匹配的文件路径列表
    """
    try:
        search_pattern = os.path.join(directory, pattern)
        matches = glob_module.glob(search_pattern, recursive=True)
        
        if matches:
            return '\n'.join(matches)
        else:
            return "未找到匹配文件"
    except Exception as e:
        return f"搜索失败: {str(e)}"

# 终端命令工具

@tool
def run_terminal_command(command: str, timeout: int = 30) -> str:
    """
    执行终端命令
    
    Args:
        command: 要执行的命令
        timeout: 超时时间（秒）
    
    Returns:
        命令执行结果
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            return f"执行成功\n{output}" if output else "执行成功"
        else:
            error = result.stderr.strip()
            return f"执行失败\n{error}" if error else "执行失败"
    
    except subprocess.TimeoutExpired:
        return f"命令执行超时（{timeout}秒）"
    except Exception as e:
        return f"命令执行错误: {str(e)}"

# 任务管理工具

class TodoManager:
    """待办事项管理器"""
    
    def __init__(self):
        self.todos = []
    
    def add_todo(self, todo: str, priority: str = "medium") -> str:
        """
        添加待办事项
        
        Args:
            todo: 待办事项内容
            priority: 优先级（high/medium/low）
        
        Returns:
            操作结果消息
        """
        todo_item = {
            "id": len(self.todos) + 1,
            "content": todo,
            "priority": priority,
            "status": "pending"
        }
        self.todos.append(todo_item)
        return f"已添加待办事项 #{todo_item['id']}: {todo}"
    
    def list_todos(self, status: str = None) -> str:
        """
        列出待办事项
        
        Args:
            status: 筛选状态（pending/completed/all）
        
        Returns:
            待办事项列表
        """
        if not self.todos:
            return "暂无待办事项"
        
        filtered_todos = self.todos
        if status and status != "all":
            filtered_todos = [t for t in self.todos if t["status"] == status]
        
        result = []
        for todo in filtered_todos:
            status_icon = "✓" if todo["status"] == "completed" else "○"
            result.append(f"{status_icon} #{todo['id']} [{todo['priority']}] {todo['content']}")
        
        return '\n'.join(result)
    
    def complete_todo(self, todo_id: int) -> str:
        """
        完成待办事项
        
        Args:
            todo_id: 待办事项ID
        
        Returns:
            操作结果消息
        """
        for todo in self.todos:
            if todo["id"] == todo_id:
                todo["status"] = "completed"
                return f"已完成待办事项 #{todo_id}: {todo['content']}"
        
        return f"未找到待办事项 #{todo_id}"

# 创建全局待办事项管理器实例
todo_manager = TodoManager()

@tool
def add_todo(todo: str, priority: str = "medium") -> str:
    """添加待办事项"""
    return todo_manager.add_todo(todo, priority)

@tool
def list_todos(status: str = "all") -> str:
    """列出待办事项"""
    return todo_manager.list_todos(status)

@tool
def complete_todo(todo_id: int) -> str:
    """完成待办事项"""
    return todo_manager.complete_todo(todo_id)

# 用户交互工具

@tool
def ask_question(question: str, options: List[str] = None) -> str:
    """
    向用户提问
    
    Args:
        question: 问题内容
        options: 选项列表（可选）
    
    Returns:
        用户回答
    """
    print(f"\n问题: {question}")
    
    if options:
        print("选项:")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        
        while True:
            try:
                choice = input("请选择 (输入数字): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(options):
                    return options[int(choice) - 1]
                else:
                    print("无效选择，请重新输入")
            except KeyboardInterrupt:
                return "用户取消"
    else:
        try:
            answer = input("请输入答案: ").strip()
            return answer if answer else "用户未提供答案"
        except KeyboardInterrupt:
            return "用户取消"

# 文件系统信息工具

@tool
def list_directory(directory: str = ".") -> str:
    """
    列出目录内容
    
    Args:
        directory: 目录路径
    
    Returns:
        目录内容列表
    """
    try:
        items = []
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isdir(full_path):
                items.append(f"📁 {item}/")
            else:
                size = os.path.getsize(full_path)
                items.append(f"📄 {item} ({size} bytes)")
        
        return '\n'.join(items) if items else "目录为空"
    except Exception as e:
        return f"列出目录失败: {str(e)}"

@tool
def get_file_info(file_path: str) -> str:
    """
    获取文件详细信息
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件信息
    """
    try:
        stat = os.stat(file_path)
        info = {
            "路径": os.path.abspath(file_path),
            "大小": f"{stat.st_size} bytes",
            "创建时间": stat.st_ctime,
            "修改时间": stat.st_mtime,
            "是目录": os.path.isdir(file_path),
            "是文件": os.path.isfile(file_path)
        }
        
        return '\n'.join([f"{k}: {v}" for k, v in info.items()])
    except Exception as e:
        return f"获取文件信息失败: {str(e)}"

# 工具列表（供Agent使用）
def get_tool_list() -> str:
    """获取所有可用工具的描述"""
    tools = [
        "read_file(file_path, start_line=None, end_line=None): 读取文件内容",
        "write_to_file(file_path, content, append=False): 写入文件内容",
        "edit_file(file_path, old_string, new_string): 精确字符串替换编辑",
        "grep_search(pattern, file_path=None, directory=None, include_pattern=None): 正则表达式搜索",
        "glob_search(pattern, directory='.'): 模式匹配查找文件",
        "run_terminal_command(command, timeout=30): 执行终端命令",
        "add_todo(todo, priority='medium'): 添加待办事项",
        "list_todos(status='all'): 列出待办事项",
        "complete_todo(todo_id): 完成待办事项",
        "ask_question(question, options=None): 向用户提问",
        "list_directory(directory='.'): 列出目录内容",
        "get_file_info(file_path): 获取文件详细信息"
    ]
    
    return '\n'.join(tools)