"""
用户认证相关API路由
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, validator
import re

from ...modules.sql.services.user_service import UserService
from ...modules.sql.services.service_result import ServiceErrorType
from ...modules.auth import jwt_handler, jwt_bearer, require_admin
from ...modules.sql.database.manager import DatabaseManager


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# Pydantic 模型
class UserRegister(BaseModel):
    """用户注册模型"""
    steam_id: str = Field(..., max_length=20, description="Steam ID")
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    
    @validator('email')
    def validate_email(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('邮箱格式不正确')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式不正确')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        if not re.search(r'[A-Za-z]', v) or not re.search(r'\d', v):
            raise ValueError('密码必须包含字母和数字')
        return v


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我（勾选后token有效期168小时，否则12小时）")


class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: dict


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


# API 路由
@router.post("/register", response_model=dict, summary="用户注册")
async def register_user(user_data: UserRegister):
    """
    用户注册

    - **steam_id**: Steam ID (必填)
    - **username**: 用户名 (2-50字符)
    - **password**: 密码 (至少6位，包含字母和数字)
    - **email**: 邮箱 (可选)
    - **phone**: 手机号 (可选)
    """
    # 使用全局数据库管理器
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        user_service = UserService(db)
        
        result = user_service.create_user(
            steam_id=user_data.steam_id,
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            phone=user_data.phone
        )
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.DUPLICATE_ENTRY:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=result.error.message
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error.message
                )
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login_user(login_data: UserLogin):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码
    - **remember_me**: 记住我（可选，默认false）
      - false: token有效期12小时
      - true: token有效期168小时（7天）

    返回访问令牌和刷新令牌
    """
    # 使用全局数据库管理器
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        user_service = UserService(db)
        
        result = user_service.authenticate_user_by_username(
            username=login_data.username,
            password=login_data.password
        )
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.AUTHENTICATION_FAILED:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=result.error.message,
                    headers={"WWW-Authenticate": "Bearer"},
                )
            elif result.error.error_type == ServiceErrorType.NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error.message
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error.message
                )
        
        # 生成令牌
        user_info = result.data

        # 根据remember_me参数设置token有效期
        if login_data.remember_me:
            # 记住我：168小时（7天）
            expire_minutes = 168 * 60
        else:
            # 不记住：12小时
            expire_minutes = 12 * 60

        access_token = jwt_handler.create_access_token(user_info, expire_minutes)
        refresh_token = jwt_handler.create_refresh_token(user_info["user_id"])

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expire_minutes * 60,  # 返回秒数
            user_info=user_info
        )


@router.post("/refresh", response_model=dict, summary="刷新访问令牌")
async def refresh_access_token(refresh_data: RefreshTokenRequest):
    """
    使用刷新令牌获取新的访问令牌
    
    - **refresh_token**: 刷新令牌
    """
    # 验证刷新令牌
    payload = jwt_handler.verify_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户信息
    # 使用全局数据库管理器
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        user_service = UserService(db)
        result = user_service.get_user_by_id(user_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user_data = result.data
        user_info = {
            "user_id": user_data["id"],
            "steam_id": user_data["steam_id"],
            "username": user_data["username"],
            "user_type": user_data["user_type"],
            "is_admin": user_data["user_type"] in ["admin", "super_admin"],
            "is_super_admin": user_data["user_type"] == "super_admin"
        }
        
        # 生成新的访问令牌
        new_access_token = jwt_handler.create_access_token(user_info)
        
        return {
            "success": True,
            "message": "令牌刷新成功",
            "data": {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": jwt_handler.access_token_expire_minutes * 60
            }
        }


@router.get("/me", response_model=dict, summary="获取当前用户信息")
async def get_current_user(current_user: dict = Depends(jwt_bearer)):
    """
    获取当前登录用户的信息

    需要提供有效的访问令牌
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        user_service = UserService(db)
        result = user_service.get_user_by_id(current_user["user_id"])

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return {
            "success": True,
            "message": "获取用户信息成功",
            "data": result.data
        }


@router.get("/debug", response_model=dict, summary="调试用户信息")
async def debug_user_info(current_user: dict = Depends(require_admin)):
    """
    调试端点：返回详细的用户信息和系统状态
    """
    import os
    import sqlite3
    from datetime import datetime

    # 获取JWT信息
    jwt_info = {
        "user_id": current_user.get("user_id"),
        "steam_id": current_user.get("steam_id"),
        "username": current_user.get("username"),
        "user_type": current_user.get("user_type"),
        "is_admin": current_user.get("is_admin"),
        "is_super_admin": current_user.get("is_super_admin")
    }

    # 获取数据库信息
    db_path = os.path.abspath("bakend/modules/sql/scum_robot.db")
    db_info = {
        "path": db_path,
        "exists": os.path.exists(db_path),
        "size": os.path.getsize(db_path) if os.path.exists(db_path) else 0
    }

    # 直接查询数据库
    db_user_info = None
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, steam_id, username, updated_at FROM users WHERE id = ?', (current_user["user_id"],))
            result = cursor.fetchone()
            if result:
                db_user_info = {
                    "id": result[0],
                    "steam_id": result[1],
                    "username": result[2],
                    "updated_at": result[3]
                }
            conn.close()
        except Exception as e:
            db_user_info = {"error": str(e)}

    # 通过API服务获取用户信息
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    api_user_info = None
    try:
        with db_manager.get_db_session() as db:
            user_service = UserService(db)
            result = user_service.get_user_by_id(current_user["user_id"])
            if result.success:
                api_user_info = result.data
            else:
                api_user_info = {"error": result.error.message}
    except Exception as e:
        api_user_info = {"error": str(e)}

    return {
        "success": True,
        "message": "调试信息",
        "data": {
            "timestamp": datetime.now().isoformat(),
            "jwt_payload": jwt_info,
            "database_info": db_info,
            "direct_db_query": db_user_info,
            "api_service_query": api_user_info,
            "process_id": os.getpid()
        }
    }


@router.get("/swagger-test", response_model=dict, summary="Swagger UI专用测试")
async def swagger_test(current_user: dict = Depends(require_admin)):
    """
    专门为Swagger UI测试设计的端点
    返回详细的请求和响应信息
    """
    import time
    from datetime import datetime

    # 获取当前时间戳
    timestamp = datetime.now().isoformat()

    # 获取JWT信息
    jwt_info = {
        "user_id": current_user.get("user_id"),
        "steam_id": current_user.get("steam_id"),
        "username": current_user.get("username")
    }

    # 获取用户信息 (使用与/auth/me相同的逻辑)
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        user_service = UserService(db)
        result = user_service.get_user_by_id(current_user["user_id"])

        if result.success:
            user_data = result.data
        else:
            user_data = {"error": result.error.message}

    # 直接数据库查询验证
    import sqlite3
    db_path = "bakend/modules/sql/scum_robot.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, steam_id, username FROM users WHERE id = ?', (current_user["user_id"],))
        db_result = cursor.fetchone()
        conn.close()

        if db_result:
            direct_db = {
                "id": db_result[0],
                "steam_id": db_result[1],
                "username": db_result[2]
            }
        else:
            direct_db = {"error": "用户不存在"}
    except Exception as e:
        direct_db = {"error": str(e)}

    return {
        "success": True,
        "message": "Swagger UI测试成功",
        "data": {
            "timestamp": timestamp,
            "test_type": "swagger_ui_specific",
            "jwt_token_info": jwt_info,
            "api_service_result": user_data,
            "direct_database_query": direct_db,
            "consistency_check": {
                "jwt_vs_api": jwt_info.get("steam_id") == user_data.get("steam_id"),
                "jwt_vs_db": jwt_info.get("steam_id") == direct_db.get("steam_id"),
                "api_vs_db": user_data.get("steam_id") == direct_db.get("steam_id")
            }
        }
    }


@router.post("/logout", response_model=dict, summary="用户登出")
async def logout_user(current_user: dict = Depends(jwt_bearer)):
    """
    用户登出
    
    注意：由于JWT是无状态的，实际的令牌失效需要在客户端处理
    """
    return {
        "success": True,
        "message": "登出成功",
        "data": {
            "user_id": current_user["user_id"],
            "username": current_user["username"]
        }
    }
