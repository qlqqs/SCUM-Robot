"""
SCUM Robot 模块 - 完整的 SCUM 游戏自动化工具包

这是一个用于 SCUM 游戏的自动化模块，提供了指令集和命令发送功能。
该模块包含两个主要组件：
1. InstructionSet: SCUM 游戏指令集合，包含各种预定义的游戏命令
2. CommandSender: 纯 Windows API 实现的命令发送器，用于自动化键盘输入

作者: GitHub Copilot
日期: 2025年9月17日
版本: 1.0
"""

from .instructionSet import (
    InstructionSet, 
    CurrencyType, 
    ModifierType
)
from .sentCommand import CommandSender

# 模块版本信息
__version__ = "1.0.0"
__author__ = "GitHub Copilot"
__email__ = ""
__description__ = "SCUM 游戏自动化工具包 - 指令集和命令发送器"

# 导出的公共接口
__all__ = [
    # 主要类
    'InstructionSet',
    'CommandSender',
    
    # 枚举类型
    'CurrencyType',
    'ModifierType',
    
    # 便捷函数
    'create_robot',
    'create_instruction_set',
    'create_command_sender',
    
    # 版本信息
    '__version__',
    '__author__',
    '__description__'
]


def create_robot(enable_sender: bool = True) -> InstructionSet:
    """
    创建一个完整的 SCUM Robot 实例
    
    这是一个便捷的工厂函数，用于快速创建包含指令集和命令发送器的完整 robot 实例。
    
    Args:
        enable_sender (bool, optional): 是否启用命令发送器。默认为 True。
        
    Returns:
        InstructionSet: 配置好的指令集实例
        
    Example:
        >>> robot = create_robot()
        >>> robot.give_money("Player1", 1000)  # 直接执行命令
        
        >>> robot = create_robot(enable_sender=False)
        >>> command = robot.give_money("Player1", 1000)  # 只返回命令字符串
    """
    return InstructionSet(enable_sender=enable_sender)


def create_instruction_set(enable_sender: bool = True) -> InstructionSet:
    """
    创建指令集实例
    
    Args:
        enable_sender (bool, optional): 是否启用命令发送器。默认为 True。
        
    Returns:
        InstructionSet: 指令集实例
    """
    return InstructionSet(enable_sender=enable_sender)


def create_command_sender() -> CommandSender:
    """
    创建命令发送器实例
    
    Returns:
        CommandSender: 命令发送器实例
        
    Note:
        CommandSender 的配置（如窗口标题、延迟等）需要在使用时作为参数传递给相应的方法
    """
    return CommandSender()


# 便捷的模块级别函数
def quick_execute(command: str, window_title: str = "SCUM") -> bool:
    """
    快速执行单个命令
    
    Args:
        command (str): 要执行的命令
        window_title (str, optional): 目标窗口标题。默认为 "SCUM"。
        
    Returns:
        bool: 执行是否成功
    """
    sender = create_command_sender()
    return sender.send_command(window_title, command)


# 模块初始化检查
def _check_dependencies():
    """检查模块依赖和兼容性"""
    import sys
    import platform
    
    # 检查操作系统
    if platform.system() != 'Windows':
        raise RuntimeError("此模块仅支持 Windows 操作系统")
        
    # 检查 Python 版本
    if sys.version_info < (3, 7):
        raise RuntimeError("此模块需要 Python 3.7 或更高版本")


# 执行初始化检查
_check_dependencies()