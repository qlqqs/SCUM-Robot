"""
用户服务层
"""

import hashlib
import secrets
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import User, UserAssets, UserType
from .service_result import ServiceResult, ServiceErrorType


class UserService:
    """用户服务类"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_user(self, steam_id: str, username: str, password: str,
                   email: Optional[str] = None, phone: Optional[str] = None,
                   user_type: UserType = UserType.USER) -> ServiceResult:
        """
        创建新用户
        
        Args:
            steam_id: Steam ID
            username: 用户名
            password: 密码
            email: 邮箱
            phone: 手机号
            user_type: 用户类型
            
        Returns:
            ServiceResult: 创建结果
        """
        try:
            # 检查Steam ID是否已存在
            existing_user = self.db.query(User).filter(User.steam_id == steam_id).first()
            if existing_user:
                return ServiceResult.error(
                    ServiceErrorType.DUPLICATE_ENTRY,
                    f"Steam ID {steam_id} 已存在"
                )
            
            # 检查邮箱是否已存在
            if email:
                existing_email = self.db.query(User).filter(User.email == email).first()
                if existing_email:
                    return ServiceResult.error(
                        ServiceErrorType.DUPLICATE_ENTRY,
                        f"邮箱 {email} 已存在"
                    )
            
            # 创建用户
            password_hash = self._hash_password(password)
            user = User(
                steam_id=steam_id,
                username=username,
                email=email,
                phone=phone,
                password_hash=password_hash,
                user_type=user_type
            )
            
            self.db.add(user)
            self.db.flush()  # 获取用户ID
            
            # 创建用户资产记录
            assets = UserAssets(user_id=user.id)
            self.db.add(assets)
            
            self.db.commit()
            
            return ServiceResult.success(
                data={
                    "user_id": user.id,
                    "steam_id": user.steam_id,
                    "username": user.username,
                    "user_type": user.user_type.value
                },
                message="用户创建成功"
            )
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"创建用户失败: {str(e)}"
            )
    
    def authenticate_user(self, steam_id: str, password: str) -> ServiceResult:
        """
        用户认证 (通过Steam ID)

        Args:
            steam_id: Steam ID
            password: 密码

        Returns:
            ServiceResult: 认证结果
        """
        try:
            user = self.db.query(User).filter(
                and_(User.steam_id == steam_id, User.is_active == True)
            ).first()
            
            if not user:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "用户不存在或已被禁用"
                )
            
            if not self._verify_password(password, user.password_hash):
                return ServiceResult.error(
                    ServiceErrorType.AUTHENTICATION_FAILED,
                    "密码错误"
                )
            
            # 更新登录信息
            user.last_login_at = datetime.utcnow()
            user.login_count += 1
            self.db.commit()
            
            return ServiceResult.success(
                data={
                    "user_id": user.id,
                    "steam_id": user.steam_id,
                    "username": user.username,
                    "user_type": user.user_type.value,
                    "is_admin": user.is_admin(),
                    "is_super_admin": user.is_super_admin()
                },
                message="认证成功"
            )
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"认证失败: {str(e)}"
            )

    def authenticate_user_by_username(self, username: str, password: str) -> ServiceResult:
        """
        用户认证 (通过用户名)

        Args:
            username: 用户名
            password: 密码

        Returns:
            ServiceResult: 认证结果
        """
        try:
            user = self.db.query(User).filter(
                and_(User.username == username, User.is_active == True)
            ).first()

            if not user:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "用户不存在或已被禁用"
                )

            if not self._verify_password(password, user.password_hash):
                return ServiceResult.error(
                    ServiceErrorType.AUTHENTICATION_FAILED,
                    "密码错误"
                )

            # 更新登录信息
            user.last_login_at = datetime.utcnow()
            user.login_count += 1
            self.db.commit()

            return ServiceResult.success(
                data={
                    "user_id": user.id,
                    "steam_id": user.steam_id,
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "user_type": user.user_type.value,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin(),
                    "is_super_admin": user.is_super_admin(),
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                    "login_count": user.login_count,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat()
                }
            )

        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"认证失败: {str(e)}"
            )

    def get_user_by_id(self, user_id: int) -> ServiceResult:
        """根据ID获取用户信息"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "用户不存在"
                )
            
            return ServiceResult.success(
                data={
                    "id": user.id,
                    "steam_id": user.steam_id,
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "user_type": user.user_type.value,
                    "is_active": user.is_active,
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                    "login_count": user.login_count,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                }
            )
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"获取用户信息失败: {str(e)}"
            )
    
    def get_user_by_steam_id(self, steam_id: int) -> ServiceResult:
        """根据Steam ID获取用户信息"""
        try:
            user = self.db.query(User).filter(User.steam_id == steam_id).first()
            if not user:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "用户不存在"
                )
            
            return ServiceResult.success(
                data={
                    "id": user.id,
                    "steam_id": user.steam_id,
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "user_type": user.user_type.value,
                    "is_active": user.is_active,
                    "has_pass": user.has_pass,
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                    "login_count": user.login_count,
                    "created_at": user.created_at.isoformat()
                }
            )
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"获取用户信息失败: {str(e)}"
            )
    
    def update_user(self, user_id: int, **kwargs) -> ServiceResult:
        """更新用户信息"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "用户不存在"
                )
            
            # 允许更新的字段
            allowed_fields = ['steam_id', 'username', 'email', 'phone', 'is_active']
            
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            user.update_timestamp()
            self.db.commit()
            
            return ServiceResult.success(
                data={"user_id": user.id},
                message="用户信息更新成功"
            )
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"更新用户信息失败: {str(e)}"
            )
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> ServiceResult:
        """修改密码"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "用户不存在"
                )
            
            # 验证旧密码
            if not self._verify_password(old_password, user.password_hash):
                return ServiceResult.error(
                    ServiceErrorType.AUTHENTICATION_FAILED,
                    "原密码错误"
                )
            
            # 更新密码
            user.password_hash = self._hash_password(new_password)
            user.update_timestamp()
            self.db.commit()
            
            return ServiceResult.success(message="密码修改成功")
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"修改密码失败: {str(e)}"
            )
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt, stored_hash = password_hash.split(':')
            password_hash_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash_check.hex() == stored_hash
        except:
            return False
