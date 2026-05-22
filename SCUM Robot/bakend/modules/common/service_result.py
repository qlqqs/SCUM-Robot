"""
服务结果类
统一的服务层返回结果格式
"""

from typing import Any, Optional, Dict


class ServiceResult:
    """服务结果类"""
    
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None, 
                 error_code: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error
        self.error_code = error_code
    
    @classmethod
    def success(cls, data: Any = None) -> 'ServiceResult':
        """创建成功结果"""
        return cls(success=True, data=data)
    
    @classmethod
    def error(cls, error: str, error_code: Optional[str] = None, data: Any = None) -> 'ServiceResult':
        """创建错误结果"""
        return cls(success=False, error=error, error_code=error_code, data=data)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'success': self.success
        }
        
        if self.success:
            result['data'] = self.data
        else:
            result['error'] = self.error
            if self.error_code:
                result['error_code'] = self.error_code
            if self.data is not None:
                result['data'] = self.data
        
        return result
    
    def __str__(self) -> str:
        if self.success:
            return f"ServiceResult(success=True, data={self.data})"
        else:
            return f"ServiceResult(success=False, error='{self.error}', error_code='{self.error_code}')"
    
    def __repr__(self) -> str:
        return self.__str__()
