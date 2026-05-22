"""
全局配置管理器

提供简单的配置访问接口，封装配置服务的复杂性
"""

from typing import Any, Optional, Dict
from ..sql.database.manager import DatabaseManager
from ..sql.services.config_service import ConfigService
from ..sql.models.config_models import ConfigType


class ConfigManager:
    """全局配置管理器（单例模式）"""
    
    _instance = None
    _db_manager = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def init(self, db_manager: DatabaseManager):
        """
        初始化配置管理器
        
        Args:
            db_manager: 数据库管理器
        """
        self._db_manager = db_manager
        print("[OK] 配置管理器初始化成功")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            配置值
        
        Example:
            >>> config_manager.get('site.name', 'SCUM Robot')
            'SCUM Robot'
        """
        if not self._db_manager:
            print("[WARN] 配置管理器未初始化，返回默认值")
            return default
        
        try:
            with self._db_manager.get_db_session() as db:
                service = ConfigService(db)
                return service.get(key, default)
        except Exception as e:
            print(f"[ERROR] 获取配置失败: {key}, {e}")
            return default
    
    def set(self, key: str, value: Any, **kwargs) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            **kwargs: 其他参数（type, group_name, description等）
        
        Returns:
            是否成功
        
        Example:
            >>> config_manager.set('site.name', 'My SCUM Server')
            True
        """
        if not self._db_manager:
            print("[WARN] 配置管理器未初始化")
            return False
        
        try:
            with self._db_manager.get_db_session() as db:
                service = ConfigService(db)
                result = service.set(key, value, **kwargs)
                return result.success
        except Exception as e:
            print(f"[ERROR] 设置配置失败: {key}, {e}")
            return False
    
    def get_group(self, group_name: str) -> Dict[str, Any]:
        """
        获取分组配置
        
        Args:
            group_name: 配置分组
        
        Returns:
            配置字典
        
        Example:
            >>> config_manager.get_group('system')
            {'site.name': 'SCUM Robot', 'site.description': '...'}
        """
        if not self._db_manager:
            print("[WARN] 配置管理器未初始化")
            return {}
        
        try:
            with self._db_manager.get_db_session() as db:
                service = ConfigService(db)
                result = service.get_by_group(group_name)
                return result.data if result.success else {}
        except Exception as e:
            print(f"[ERROR] 获取分组配置失败: {group_name}, {e}")
            return {}
    
    def get_public(self) -> Dict[str, Any]:
        """
        获取所有公开配置
        
        Returns:
            配置字典
        
        Example:
            >>> config_manager.get_public()
            {'site.name': 'SCUM Robot', 'site.description': '...'}
        """
        if not self._db_manager:
            print("[WARN] 配置管理器未初始化")
            return {}
        
        try:
            with self._db_manager.get_db_session() as db:
                service = ConfigService(db)
                result = service.get_public()
                return result.data if result.success else {}
        except Exception as e:
            print(f"[ERROR] 获取公开配置失败: {e}")
            return {}
    
    def is_initialized(self) -> bool:
        """
        检查配置管理器是否已初始化
        
        Returns:
            是否已初始化
        """
        return self._db_manager is not None


# 全局单例实例
config_manager = ConfigManager()
