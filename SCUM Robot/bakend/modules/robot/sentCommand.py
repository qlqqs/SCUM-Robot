"""
命令发送模块 - 纯 Windows API 实现

使用纯 Windows API 实现窗口聚焦、键盘输入和剪贴板操作
完全摆脱第三方依赖，提供更高的性能和稳定性

作者: GitHub Copilot  
日期: 2025年9月16日
版本: 2.0 (纯 Win32 API)
"""

import ctypes
from ctypes import wintypes, Structure, Union, POINTER, byref, c_void_p, c_char_p
import time
from typing import Optional, List, Callable
import threading


# Windows API 结构定义
class POINT(Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class RECT(Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

class WINDOWINFO(Structure):
    _fields_ = [("cbSize", wintypes.DWORD),
                ("rcWindow", RECT),
                ("rcClient", RECT),
                ("dwStyle", wintypes.DWORD),
                ("dwExStyle", wintypes.DWORD),
                ("dwWindowStatus", wintypes.DWORD),
                ("cxWindowBorders", wintypes.UINT),
                ("cyWindowBorders", wintypes.UINT),
                ("atomWindowType", wintypes.ATOM),
                ("wCreatorVersion", wintypes.WORD)]

class KEYBDINPUT(Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", POINTER(wintypes.ULONG))]

class HARDWAREINPUT(Structure):
    _fields_ = [("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]

class MOUSEINPUT(Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", POINTER(wintypes.ULONG))]

class INPUT_UNION(Union):
    _fields_ = [("ki", KEYBDINPUT),
                ("mi", MOUSEINPUT), 
                ("hi", HARDWAREINPUT)]

class INPUT(Structure):
    _fields_ = [("type", wintypes.DWORD),
                ("union", INPUT_UNION)]

class WindowInfo:
    """窗口信息类"""
    def __init__(self, hwnd: int, title: str, class_name: str):
        self.hwnd = hwnd
        self.title = title
        self.class_name = class_name
        self.is_visible = False
        self.is_minimized = False
        self.rect = None

class CommandSender:
    """命令发送器类 - 纯 Windows API 实现"""
    
    # Windows API 常量
    HWND_TOP = 0
    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOZORDER = 0x0004
    SWP_NOREDRAW = 0x0008
    SWP_NOACTIVATE = 0x0010
    SWP_SHOWWINDOW = 0x0040
    
    SW_HIDE = 0
    SW_SHOWNORMAL = 1
    SW_SHOWMINIMIZED = 2
    SW_SHOWMAXIMIZED = 3
    SW_SHOWNOACTIVATE = 4
    SW_SHOW = 5
    SW_MINIMIZE = 6
    SW_SHOWMINNOACTIVE = 7
    SW_SHOWNA = 8
    SW_RESTORE = 9
    
    INPUT_KEYBOARD = 1
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    KEYEVENTF_SCANCODE = 0x0008
    
    CF_TEXT = 1
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    GHND = 0x0042
    
    # 虚拟键码
    VK_RETURN = 0x0D
    VK_CONTROL = 0x11
    VK_V = 0x56
    VK_T = 0x54
    
    def __init__(self):
        """初始化命令发送器"""
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.gdi32 = ctypes.windll.gdi32
        
        # 窗口枚举回调函数类型（必须在_init_api_prototypes之前定义）
        self.enum_windows_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        
        # 初始化API函数原型
        self._init_api_prototypes()
    
    def _init_api_prototypes(self):
        """初始化 Windows API 函数原型"""
        # 窗口管理API
        self.user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
        self.user32.FindWindowW.restype = wintypes.HWND
        
        self.user32.EnumWindows.argtypes = [self.enum_windows_proc, wintypes.LPARAM]
        self.user32.EnumWindows.restype = wintypes.BOOL
        
        self.user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self.user32.GetWindowTextW.restype = ctypes.c_int
        
        self.user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        self.user32.GetWindowTextLengthW.restype = ctypes.c_int
        
        self.user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self.user32.GetClassNameW.restype = ctypes.c_int
        
        self.user32.IsWindowVisible.argtypes = [wintypes.HWND]
        self.user32.IsWindowVisible.restype = wintypes.BOOL
        
        self.user32.IsIconic.argtypes = [wintypes.HWND]
        self.user32.IsIconic.restype = wintypes.BOOL
        
        self.user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        self.user32.SetForegroundWindow.restype = wintypes.BOOL
        
        self.user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user32.ShowWindow.restype = wintypes.BOOL
        
        self.user32.BringWindowToTop.argtypes = [wintypes.HWND]
        self.user32.BringWindowToTop.restype = wintypes.BOOL
        
        self.user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, 
                                            ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        self.user32.SetWindowPos.restype = wintypes.BOOL
        
        self.user32.GetForegroundWindow.restype = wintypes.HWND
        
        self.user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
        self.user32.AttachThreadInput.restype = wintypes.BOOL
        
        self.user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, POINTER(wintypes.DWORD)]
        self.user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        
        # 输入API
        self.user32.SendInput.argtypes = [wintypes.UINT, POINTER(INPUT), ctypes.c_int]
        self.user32.SendInput.restype = wintypes.UINT
        
        # 剪贴板API  
        self.user32.OpenClipboard.argtypes = [wintypes.HWND]
        self.user32.OpenClipboard.restype = wintypes.BOOL
        
        self.user32.EmptyClipboard.restype = wintypes.BOOL
        self.user32.CloseClipboard.restype = wintypes.BOOL
        
        self.user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        self.user32.SetClipboardData.restype = wintypes.HANDLE
        
        self.user32.GetClipboardData.argtypes = [wintypes.UINT]
        self.user32.GetClipboardData.restype = wintypes.HANDLE
        
        # 内存管理API
        self.kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        self.kernel32.GlobalAlloc.restype = wintypes.HANDLE
        
        self.kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
        self.kernel32.GlobalLock.restype = c_void_p
        
        self.kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
        self.kernel32.GlobalUnlock.restype = wintypes.BOOL
        
        self.kernel32.GetCurrentThreadId.restype = wintypes.DWORD
        
        # 修复函数原型定义
        self.enum_windows_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    
    def _enum_windows_callback(self, hwnd: int, lparam: int) -> bool:
        """EnumWindows 回调函数"""
        try:
            # 检查窗口是否可见
            if not self.user32.IsWindowVisible(hwnd):
                return True  # 继续枚举
            
            # 获取窗口标题长度
            title_length = self.user32.GetWindowTextLengthW(hwnd)
            if title_length == 0:
                return True  # 继续枚举
            
            # 获取窗口标题
            title_buffer = ctypes.create_unicode_buffer(title_length + 1)
            actual_length = self.user32.GetWindowTextW(hwnd, title_buffer, title_length + 1)
            
            if actual_length > 0:
                title = title_buffer.value
                
                # 获取窗口类名
                class_buffer = ctypes.create_unicode_buffer(256)
                self.user32.GetClassNameW(hwnd, class_buffer, 256)
                class_name = class_buffer.value
                
                # 检查窗口是否最小化
                is_minimized = self.user32.IsIconic(hwnd)
                
                # 创建窗口信息对象
                window_info = WindowInfo(hwnd, title, class_name)
                window_info.is_visible = True
                window_info.is_minimized = bool(is_minimized)
                
                # 将窗口信息添加到结果列表
                self._enum_result.append(window_info)
            
            return True  # 继续枚举
            
        except Exception as e:
            print(f"枚举窗口回调函数错误: {e}")
            return True  # 继续枚举
    
    def get_all_windows(self) -> List[WindowInfo]:
        """
        获取所有可见窗口的信息
        
        Returns:
            窗口信息列表
        """
        self._enum_result = []
        try:
            # 创建回调函数
            callback = self.enum_windows_proc(self._enum_windows_callback)
            
            # 枚举所有顶层窗口
            self.user32.EnumWindows(callback, 0)
            
            return self._enum_result
            
        except Exception as e:
            print(f"获取窗口列表时发生错误: {e}")
            return []
    
    def find_window_by_title(self, window_title: str) -> Optional[WindowInfo]:
        """
        根据窗口标题精确查找窗口
        
        Args:
            window_title: 窗口标题
            
        Returns:
            找到的窗口信息，如果未找到则返回None
        """
        try:
            # 先尝试直接通过FindWindow查找
            hwnd = self.user32.FindWindowW(None, window_title)
            if hwnd:
                # 获取窗口类名
                class_buffer = ctypes.create_unicode_buffer(256)
                self.user32.GetClassNameW(hwnd, class_buffer, 256)
                class_name = class_buffer.value
                
                window_info = WindowInfo(hwnd, window_title, class_name)
                window_info.is_visible = bool(self.user32.IsWindowVisible(hwnd))
                window_info.is_minimized = bool(self.user32.IsIconic(hwnd))
                return window_info
            
            # 如果直接查找失败，枚举所有窗口进行模糊匹配
            all_windows = self.get_all_windows()
            
            for window in all_windows:
                if window.title:
                    # 精确匹配和模糊匹配
                    if (window.title.strip().lower() == window_title.strip().lower() or
                        window_title.strip().lower() in window.title.strip().lower()):
                        return window
            
            return None
            
        except Exception as e:
            print(f"查找窗口时发生错误: {e}")
            return None
    
    def focus_window_by_hwnd(self, hwnd: int) -> bool:
        """
        使用Windows API聚焦窗口
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            是否成功聚焦
        """
        try:
            # 获取当前前台窗口和线程ID
            current_hwnd = self.user32.GetForegroundWindow()
            current_thread_id = self.user32.GetWindowThreadProcessId(current_hwnd, None)
            target_thread_id = self.user32.GetWindowThreadProcessId(hwnd, None)
            
            # 如果窗口已经是前台窗口，直接返回成功
            if current_hwnd == hwnd:
                return True
            
            # 方法1: 尝试直接SetForegroundWindow
            if self.user32.SetForegroundWindow(hwnd):
                return True
            
            # 方法2: 使用线程输入附加的方法
            if current_thread_id != target_thread_id:
                # 附加到目标窗口的线程输入
                self.user32.AttachThreadInput(current_thread_id, target_thread_id, True)
                
                try:
                    # 确保窗口可见
                    self.user32.ShowWindow(hwnd, self.SW_RESTORE)
                    time.sleep(0.05)
                    
                    # 将窗口置顶
                    self.user32.BringWindowToTop(hwnd)
                    time.sleep(0.05)
                    
                    # 设置为前台窗口
                    success = self.user32.SetForegroundWindow(hwnd)
                    
                finally:
                    # 分离线程输入
                    self.user32.AttachThreadInput(current_thread_id, target_thread_id, False)
                
                if success:
                    return True
            
            # 方法3: 最后尝试ShowWindow + BringWindowToTop组合
            self.user32.ShowWindow(hwnd, self.SW_SHOW)
            time.sleep(0.05)
            self.user32.BringWindowToTop(hwnd)
            time.sleep(0.05)
            
            return self.user32.SetForegroundWindow(hwnd) != 0
            
        except Exception as e:
            print(f"Windows API聚焦失败: {e}")
            return False
    
    def set_clipboard_text(self, text: str) -> bool:
        """
        使用Windows API设置剪贴板文本
        
        Args:
            text: 要复制到剪贴板的文本
            
        Returns:
            是否成功设置
        """
        try:
            # 打开剪贴板
            if not self.user32.OpenClipboard(0):
                return False
            
            try:
                # 清空剪贴板
                self.user32.EmptyClipboard()
                
                # 转换文本为Unicode并计算大小
                unicode_text = text.encode('utf-16le') + b'\x00\x00'
                text_size = len(unicode_text)
                
                # 分配全局内存
                h_mem = self.kernel32.GlobalAlloc(self.GMEM_MOVEABLE, text_size)
                if not h_mem:
                    return False
                
                # 锁定内存并复制文本
                p_mem = self.kernel32.GlobalLock(h_mem)
                if p_mem:
                    ctypes.memmove(p_mem, unicode_text, text_size)
                    self.kernel32.GlobalUnlock(h_mem)
                    
                    # 设置剪贴板数据
                    if self.user32.SetClipboardData(self.CF_UNICODETEXT, h_mem):
                        return True
                    
            finally:
                # 关闭剪贴板
                self.user32.CloseClipboard()
            
            return False
            
        except Exception as e:
            print(f"Windows API剪贴板操作失败: {e}")
            return False
    
    def send_unicode_input(self, text: str) -> bool:
        """
        使用Windows API SendInput发送Unicode文本输入
        
        Args:
            text: 要输入的文本
            
        Returns:
            是否成功发送
        """
        try:
            inputs = []
            
            for char in text:
                # 对于Unicode输入，只需要一个事件，不需要按下/释放对
                input_obj = INPUT()
                input_obj.type = self.INPUT_KEYBOARD
                input_obj.union.ki = KEYBDINPUT()
                input_obj.union.ki.wVk = 0  # Unicode输入时虚拟键码为0
                input_obj.union.ki.wScan = ord(char)  # Unicode字符码
                input_obj.union.ki.dwFlags = self.KEYEVENTF_UNICODE
                input_obj.union.ki.time = 0
                input_obj.union.ki.dwExtraInfo = None
                
                inputs.append(input_obj)
            
            # 发送所有输入事件
            if inputs:
                input_array = (INPUT * len(inputs))(*inputs)
                sent_count = self.user32.SendInput(
                    len(inputs),
                    input_array,
                    ctypes.sizeof(INPUT)
                )
                
                return sent_count == len(inputs)
            
            return True
            
        except Exception as e:
            print(f"Windows API文本输入失败: {e}")
            return False
    
    def send_virtual_key_input(self, char: str) -> bool:
        """
        使用虚拟键码发送字符输入（适用于ASCII字符）
        
        Args:
            char: 要输入的字符
            
        Returns:
            是否成功发送
        """
        try:
            if len(char) != 1:
                return False
            
            # 获取字符的虚拟键码
            vk_code = ctypes.windll.user32.VkKeyScanW(ord(char)) & 0xFF
            
            if vk_code == -1:
                # 如果无法获取虚拟键码，回退到Unicode输入
                return self.send_unicode_input(char)
            
            # 按下键
            success1 = self.send_key_input(vk_code, False)
            if not success1:
                return False
            
            # 释放键
            success2 = self.send_key_input(vk_code, True)
            return success2
            
        except Exception as e:
            print(f"虚拟键码输入失败: {e}")
            return False
    
    def send_key_input(self, vk_code: int, key_up: bool = False) -> bool:
        """
        发送虚拟键输入
        
        Args:
            vk_code: 虚拟键码
            key_up: 是否为键弹起事件
            
        Returns:
            是否成功发送
        """
        try:
            input_obj = INPUT()
            input_obj.type = self.INPUT_KEYBOARD
            input_obj.union.ki = KEYBDINPUT()
            input_obj.union.ki.wVk = vk_code
            input_obj.union.ki.wScan = 0
            input_obj.union.ki.dwFlags = self.KEYEVENTF_KEYUP if key_up else 0
            input_obj.union.ki.time = 0
            input_obj.union.ki.dwExtraInfo = None
            
            return self.user32.SendInput(1, byref(input_obj), ctypes.sizeof(INPUT)) == 1
            
        except Exception as e:
            print(f"发送按键输入失败: {e}")
            return False
    
    def press_key(self, vk_code: int) -> bool:
        """
        按下并释放一个键
        
        Args:
            vk_code: 虚拟键码
            
        Returns:
            是否成功
        """
        return (self.send_key_input(vk_code, False) and 
                self.send_key_input(vk_code, True))
    
    def press_enter(self) -> bool:
        """按下回车键"""
        return self.press_key(self.VK_RETURN)
    
    def press_ctrl_v(self) -> bool:
        """按下Ctrl+V组合键"""
        # 按下Ctrl
        if not self.send_key_input(self.VK_CONTROL, False):
            return False
        time.sleep(0.01)
        
        # 按下V
        if not self.send_key_input(self.VK_V, False):
            return False
        time.sleep(0.01)
        
        # 释放V
        if not self.send_key_input(self.VK_V, True):
            return False
        time.sleep(0.01)
        
        # 释放Ctrl
        return self.send_key_input(self.VK_CONTROL, True)
    
    def focus_window(self, window_title: str, retry_count: int = 3) -> bool:
        """
        精确聚焦窗口
        
        Args:
            window_title: 窗口标题
            retry_count: 重试次数
            
        Returns:
            是否成功聚焦窗口
        """
        for attempt in range(retry_count):
            try:
                # 查找窗口
                target_window = self.find_window_by_title(window_title)
                
                if target_window is None:
                    print(f"未找到标题为 '{window_title}' 的窗口")
                    if attempt < retry_count - 1:
                        print(f"等待1秒后重试... (尝试 {attempt + 1}/{retry_count})")
                        time.sleep(1)
                        continue
                    return False
                
                hwnd = target_window.hwnd
                
                # 检查窗口是否最小化，如果是则恢复
                if target_window.is_minimized:
                    self.user32.ShowWindow(hwnd, self.SW_RESTORE)
                    time.sleep(0.1)
                
                # 使用Windows API聚焦窗口
                if self.focus_window_by_hwnd(hwnd):
                    # 验证聚焦是否成功
                    time.sleep(0.1)
                    current_hwnd = self.user32.GetForegroundWindow()
                    if current_hwnd == hwnd:
                        print(f"成功聚焦窗口: {target_window.title}")
                        return True
                
            except Exception as e:
                print(f"聚焦窗口时发生错误 (尝试 {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
        
        return False
    
    def send_text(self, text: str) -> bool:
        """
        发送文本输入
        
        Args:
            text: 要输入的文本
            
        Returns:
            是否成功发送文本
        """
        try:
            if not text:
                print("警告: 输入文本为空")
                return True
            
            # 对于单个ASCII字符，优先使用虚拟键码方法
            if len(text) == 1 and ord(text) < 128:
                if self.send_virtual_key_input(text):
                    print(f"成功通过虚拟键码发送文本: {text}")
                    return True
                print("虚拟键码失败，尝试Unicode输入")
            
            # 使用Unicode输入作为备用方法
            if self.send_unicode_input(text):
                print(f"成功通过Unicode发送文本: {text}")
                return True
            else:
                print("Unicode输入失败")
                return False
            
        except Exception as e:
            print(f"发送文本时发生错误: {e}")
            return False
    
    def paste_text(self, text: str) -> bool:
        """
        通过剪贴板粘贴文本
        
        Args:
            text: 要粘贴的文本
            
        Returns:
            是否成功粘贴文本
        """
        try:
            # 设置剪贴板内容
            if not self.set_clipboard_text(text):
                print("设置剪贴板失败，回退到直接输入")
                return self.send_text(text)
            
            time.sleep(0.05)  # 等待剪贴板操作完成
            
            # 发送Ctrl+V
            if self.press_ctrl_v():
                print(f"成功粘贴文本: {text}")
                return True
            else:
                print("Ctrl+V失败，回退到直接输入")
                return self.send_text(text)
            
        except Exception as e:
            print(f"粘贴文本失败: {e}")
            return self.send_text(text)
    
    def send_command(self, window_title: str, command: str, press_enter: bool = True) -> bool:
        """
        组合操作：聚焦窗口并发送命令
        
        Args:
            window_title: 目标窗口标题
            command: 要发送的命令
            press_enter: 是否在命令后按回车键
            
        Returns:
            是否成功完成操作
        """
        try:
            # 1. 聚焦窗口
            if not self.focus_window(window_title):
                return False
            
            # 2. 等待窗口完全激活
            time.sleep(0.2)
            
            # 3. 第一步：输入"t"（开启聊天模式）
            if not self.send_text("t"):
                return False
            
            time.sleep(0.05)
            
            # 4. 第二步：粘贴命令
            if not self.paste_text(command):
                return False
            
            # 5. 第三步：按两下回车键
            if press_enter:
                time.sleep(0.05)
                self.press_enter()
                time.sleep(0.05)
                self.press_enter()
                print("已按下两次回车键")
            
            return True
            
        except Exception as e:
            print(f"发送命令时发生错误: {e}")
            return False
    
    def send_scum_command(self, command: str) -> bool:
        """
        专门用于SCUM游戏的命令发送方法
        
        Args:
            command: 要发送的游戏命令
            
        Returns:
            是否成功完成操作
        """
        return self.send_command(
            window_title="SCUM  ",
            command=command,
            press_enter=True
        )
    
    def get_all_window_titles(self) -> List[str]:
        """
        获取所有可用窗口的标题列表
        
        Returns:
            窗口标题列表
        """
        try:
            windows = self.get_all_windows()
            return [window.title for window in windows if window.title.strip()]
        except Exception as e:
            print(f"获取窗口列表时发生错误: {e}")
            return []
    
    def print_available_windows(self):
        """打印所有可用窗口"""
        windows = self.get_all_window_titles()
        print("可用窗口列表:")
        for i, title in enumerate(windows, 1):
            print(f"{i}. {title}")


def main():
    """主函数 - 示例用法"""
    # 创建命令发送器实例
    sender = CommandSender()
    
    print("=== 纯 Windows API 命令发送模块测试 ===")
    
    # 显示所有可用窗口
    sender.print_available_windows()
    
    # 示例：聚焦记事本并发送文本
    print("\n测试聚焦窗口和发送文本...")
    
    # 你可以修改这里的窗口标题和命令
    test_window = "记事本"  # 或者 "Notepad"
    test_command = "Hello World! 这是一个测试命令。"
    
    success = sender.send_command(
        window_title=test_window,
        command=test_command,
        press_enter=True
    )
    
    if success:
        print("测试完成！")
    else:
        print("测试失败，请检查窗口标题是否正确。")


if __name__ == "__main__":
    main()
