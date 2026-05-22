"""
API依赖项
提供通用的依赖注入功能
"""

from fastapi import Depends, HTTPException, status
from typing import Optional

from ..modules.auth import jwt_bearer
from ..modules.sql.database.manager import DatabaseManager


def get_database_manager() -> DatabaseManager:
    """
    获取数据库管理器实例

    使用全局数据库管理器，确保整个应用使用同一个数据库实例
    """
    from .main import get_global_db_manager
    return get_global_db_manager()


def get_current_user(current_user: dict = Depends(jwt_bearer)) -> dict:
    """获取当前登录用户"""
    return current_user


def get_current_admin_user(current_user: dict = Depends(jwt_bearer)) -> dict:
    """获取当前管理员用户"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录"
        )
    
    user_type = current_user.get('user_type', '')
    if user_type not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return current_user


def get_current_super_admin_user(current_user: dict = Depends(jwt_bearer)) -> dict:
    """获取当前超级管理员用户"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录"
        )
    
    user_type = current_user.get('user_type', '')
    if user_type != 'super_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    
    return current_user
