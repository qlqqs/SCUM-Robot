"""
管理员功能相关API路由
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime

from ...modules.sql.services.user_service import UserService
from ...modules.sql.services.service_result import ServiceErrorType
from ...modules.auth import jwt_bearer, require_admin, require_super_admin
from ...modules.sql.database.manager import DatabaseManager
from ...modules.sql.models import User, UserType, UserAssets, UserGiftRecord, GiftPackage


router = APIRouter(prefix="/api/v1/admin", tags=["Admin Management"])


# Pydantic 模型
class UserCreate(BaseModel):
    """管理员创建用户模型"""
    steam_id: str = Field(..., max_length=20, description="Steam ID")
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    user_type: str = Field("user", description="用户类型 (user/admin)")


class UserUpdate(BaseModel):
    """管理员更新用户模型"""
    steam_id: Optional[str] = Field(None, max_length=20, description="Steam ID")
    username: Optional[str] = Field(None, min_length=2, max_length=50, description="用户名")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    is_active: Optional[bool] = Field(None, description="账户状态")
    has_pass: Optional[bool] = Field(None, description="是否有通行证")
    user_type: Optional[str] = Field(None, description="用户类型")


# API 路由
@router.get("/users", response_model=dict, summary="获取用户列表")
async def get_users_list(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    user_type: Optional[str] = Query(None, description="用户类型筛选"),
    current_user: dict = Depends(require_admin)
):
    """
    获取用户列表 (需要管理员权限)
    
    - **page**: 页码
    - **limit**: 每页数量
    - **search**: 搜索关键词 (用户名或邮箱)
    - **user_type**: 用户类型筛选
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        try:
            query = db.query(User)
            
            # 搜索过滤
            if search:
                from sqlalchemy import or_
                query = query.filter(
                    or_(
                        User.username.contains(search),
                        User.email.contains(search) if search else False
                    )
                )
            
            # 用户类型过滤
            if user_type:
                try:
                    user_type_enum = UserType(user_type)
                    query = query.filter(User.user_type == user_type_enum)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="无效的用户类型"
                    )
            
            # 分页
            total = query.count()
            offset = (page - 1) * limit
            users = query.offset(offset).limit(limit).all()
            
            user_list = []
            for user in users:
                user_data = {
                    "id": user.id,
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
                    "created_at": user.created_at.isoformat()
                }
                user_list.append(user_data)
            
            response_data = {
                "success": True,
                "message": "获取用户列表成功",
                "data": {
                    "users": user_list,
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total,
                        "pages": (total + limit - 1) // limit
                    }
                }
            }

            return JSONResponse(
                content=response_data,
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取用户列表失败: {str(e)}"
            )


@router.post("/users", response_model=dict, summary="创建用户")
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_admin)
):
    """
    创建新用户 (需要管理员权限)
    
    - **steam_id**: Steam ID
    - **username**: 用户名
    - **password**: 密码
    - **email**: 邮箱 (可选)
    - **phone**: 手机号 (可选)
    - **user_type**: 用户类型
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    # 验证用户类型
    try:
        user_type_enum = UserType(user_data.user_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户类型"
        )
    
    # 只有超级管理员可以创建管理员
    if user_type_enum in [UserType.ADMIN, UserType.SUPER_ADMIN]:
        if not current_user.get("is_super_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有超级管理员可以创建管理员账户"
            )
    
    with db_manager.get_db_session() as db:
        user_service = UserService(db)
        result = user_service.create_user(
            steam_id=user_data.steam_id,
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            phone=user_data.phone,
            user_type=user_type_enum
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


@router.put("/users/{user_id}", response_model=dict, summary="更新用户信息")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    更新用户信息 (需要管理员权限)
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        # 检查目标用户是否存在
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 权限检查：只有超级管理员可以修改管理员
        if target_user.user_type in [UserType.ADMIN, UserType.SUPER_ADMIN]:
            if not current_user.get("is_super_admin", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有超级管理员可以修改管理员账户"
                )
        
        # 验证用户类型
        if user_data.user_type:
            try:
                user_type_enum = UserType(user_data.user_type)
                # 只有超级管理员可以设置管理员权限
                if user_type_enum in [UserType.ADMIN, UserType.SUPER_ADMIN]:
                    if not current_user.get("is_super_admin", False):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="只有超级管理员可以设置管理员权限"
                        )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的用户类型"
                )
        
        user_service = UserService(db)
        
        # 准备更新数据
        update_data = {}
        if user_data.steam_id is not None:
            update_data['steam_id'] = user_data.steam_id
        if user_data.username is not None:
            update_data['username'] = user_data.username
        if user_data.email is not None:
            update_data['email'] = user_data.email
        if user_data.phone is not None:
            update_data['phone'] = user_data.phone
        if user_data.is_active is not None:
            update_data['is_active'] = user_data.is_active
        if user_data.has_pass is not None:
            update_data['has_pass'] = user_data.has_pass
        
        # 特殊处理用户类型
        if user_data.user_type:
            target_user.user_type = user_type_enum
            target_user.update_timestamp()
        
        if update_data:
            result = user_service.update_user(user_id, **update_data)
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error.message
                )
        
        db.commit()
        
        return {
            "success": True,
            "message": "用户信息更新成功",
            "data": {"user_id": user_id}
        }


@router.get("/statistics", response_model=dict, summary="获取系统统计")
async def get_system_statistics(current_user: dict = Depends(require_admin)):
    """
    获取系统统计数据 (需要管理员权限)
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        try:
            # 用户统计
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            admin_users = db.query(User).filter(
                User.user_type.in_([UserType.ADMIN, UserType.SUPER_ADMIN])
            ).count()
            
            # 今日新增用户
            from datetime import date
            today = date.today()
            today_users = db.query(User).filter(
                User.created_at >= today
            ).count()
            
            # 礼包统计
            total_gifts = db.query(GiftPackage).count()
            active_gifts = db.query(GiftPackage).filter(GiftPackage.is_active == True).count()
            
            # 礼包领取统计
            total_claims = db.query(UserGiftRecord).count()
            today_claims = db.query(UserGiftRecord).filter(
                UserGiftRecord.claimed_at >= today
            ).count()
            
            # 资产统计
            from sqlalchemy import func
            total_game_coins = db.query(func.sum(UserAssets.game_coins)).scalar() or 0
            total_shop_coins = db.query(func.sum(UserAssets.shop_coins)).scalar() or 0
            total_points = db.query(func.sum(UserAssets.points)).scalar() or 0
            total_recharge = db.query(func.sum(UserAssets.total_recharge)).scalar() or 0
            
            return {
                "success": True,
                "message": "获取系统统计成功",
                "data": {
                    "users": {
                        "total": total_users,
                        "active": active_users,
                        "admins": admin_users,
                        "today_new": today_users
                    },
                    "gifts": {
                        "total": total_gifts,
                        "active": active_gifts,
                        "total_claims": total_claims,
                        "today_claims": today_claims
                    },
                    "assets": {
                        "total_game_coins": int(total_game_coins),
                        "total_shop_coins": int(total_shop_coins),
                        "total_points": int(total_points),
                        "total_recharge": float(total_recharge)
                    }
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取系统统计失败: {str(e)}"
            )


@router.delete("/users/{user_id}", response_model=dict, summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(require_super_admin)
):
    """
    删除用户 (需要超级管理员权限)
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # 不能删除自己
            if user_id == current_user["user_id"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete your own account"
                )

            # 不能删除其他超级管理员
            if user.user_type == UserType.SUPER_ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete super admin account"
                )
            
            username = user.username
            db.delete(user)
            db.commit()
            
            return {
                "success": True,
                "message": f"用户 {username} 删除成功",
                "data": {"user_id": user_id}
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete user: {str(e)}"
            )
