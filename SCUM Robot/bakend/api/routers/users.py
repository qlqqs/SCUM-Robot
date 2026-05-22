"""
用户管理相关API路由
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from ...modules.sql.services.user_service import UserService
from ...modules.sql.services.user_assets_service import UserAssetsService
from ...modules.sql.services.service_result import ServiceErrorType
from ...modules.auth import jwt_bearer, require_admin, check_user_or_admin
from ...modules.sql.database.manager import DatabaseManager


router = APIRouter(prefix="/api/v1/users", tags=["User Management"])


# Pydantic 模型
class UserProfileUpdate(BaseModel):
    """用户资料更新模型"""
    username: Optional[str] = Field(None, min_length=2, max_length=50, description="用户名")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")


class PasswordChange(BaseModel):
    """密码修改模型"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")


class AssetUpdate(BaseModel):
    """资产更新模型"""
    asset_type: str = Field(..., description="资产类型 (game_coins/shop_coins/points)")
    amount: int = Field(..., description="变更数量")
    operation: str = Field("add", description="操作类型 (add/subtract/set)")


class AssetTransfer(BaseModel):
    """资产转账模型"""
    to_user_id: int = Field(..., description="转入用户ID")
    asset_type: str = Field(..., description="资产类型 (game_coins/shop_coins/points)")
    amount: int = Field(..., gt=0, description="转账数量")


# API 路由
@router.get("/profile", response_model=dict, summary="获取用户资料")
async def get_user_profile(current_user: dict = Depends(jwt_bearer)):
    """
    获取当前用户的详细资料信息
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        user_service = UserService(db)
        result = user_service.get_user_by_id(current_user["user_id"])

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error.message
            )

        return {
            "success": True,
            "message": "获取用户资料成功",
            "data": result.data
        }


@router.put("/profile", response_model=dict, summary="更新用户资料")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(jwt_bearer)
):
    """
    更新当前用户的资料信息
    
    - **username**: 用户名 (可选)
    - **email**: 邮箱 (可选)
    - **phone**: 手机号 (可选)
    """
    db_manager = DatabaseManager()
    db_manager.init_database()
    
    with db_manager.get_db_session() as db:
        user_service = UserService(db)
        
        # 只更新提供的字段
        update_data = {}
        if profile_data.username is not None:
            update_data['username'] = profile_data.username
        if profile_data.email is not None:
            update_data['email'] = profile_data.email
        if profile_data.phone is not None:
            update_data['phone'] = profile_data.phone
        
        result = user_service.update_user(current_user["user_id"], **update_data)
        
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


@router.post("/change-password", response_model=dict, summary="修改密码")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(jwt_bearer)
):
    """
    修改当前用户的密码
    
    - **old_password**: 原密码
    - **new_password**: 新密码 (至少6位)
    """
    db_manager = DatabaseManager()
    db_manager.init_database()
    
    with db_manager.get_db_session() as db:
        user_service = UserService(db)
        result = user_service.change_password(
            current_user["user_id"],
            password_data.old_password,
            password_data.new_password
        )
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.AUTHENTICATION_FAILED:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=result.error.message
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error.message
                )
        
        return {
            "success": True,
            "message": result.message
        }


@router.get("/assets", response_model=dict, summary="获取用户资产")
async def get_user_assets(current_user: dict = Depends(jwt_bearer)):
    """
    获取当前用户的资产信息
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        assets_service = UserAssetsService(db)
        result = assets_service.get_user_assets(current_user["user_id"])

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error.message
            )

        return {
            "success": True,
            "message": "获取用户资产成功",
            "data": result.data
        }


@router.get("/{user_id}/stats", response_model=dict, summary="获取用户统计信息")
async def get_user_stats(
    user_id: int,
    current_user: dict = Depends(jwt_bearer)
):
    """
    获取指定用户的统计信息 (需要管理员权限或查看自己的信息)
    """
    # 检查权限：只能查看自己的信息或需要管理员权限
    check_user_or_admin(current_user, user_id)

    db_manager = DatabaseManager()
    db_manager.init_database()

    with db_manager.get_db_session() as db:
        from ...modules.sql.services.character_service import CharacterService
        character_service = CharacterService(db)
        result = character_service.get_character_stats_by_user_id(user_id)

        if not result.success:
            # 如果没有人物能力数据，返回默认值
            return {
                "success": True,
                "message": "获取用户统计信息成功",
                "data": {
                    "user_id": user_id,
                    "strength": 10,
                    "stamina": 10,
                    "intelligence": 10,
                    "agility": 10,
                    "total_stats": 40,
                    "last_sync_time": None,
                    "created_at": None,
                    "updated_at": None
                }
            }

        return {
            "success": True,
            "message": "获取用户统计信息成功",
            "data": result.data
        }


@router.get("/{user_id}/assets", response_model=dict, summary="获取用户资产信息")
async def get_user_assets_by_id(
    user_id: int,
    current_user: dict = Depends(jwt_bearer)
):
    """
    获取指定用户的资产信息 (需要管理员权限或查看自己的信息)
    """
    # 检查权限：只能查看自己的信息或需要管理员权限
    check_user_or_admin(current_user, user_id)

    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        assets_service = UserAssetsService(db)
        result = assets_service.get_user_assets(user_id)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error.message
            )

        return {
            "success": True,
            "message": "获取用户资产信息成功",
            "data": result.data
        }


@router.get("/{user_id}", response_model=dict, summary="获取指定用户信息")
async def get_user_by_id(
    user_id: int,
    current_user: dict = Depends(jwt_bearer)
):
    """
    获取指定用户的信息 (需要管理员权限或查看自己的信息)
    """
    # 检查权限：只能查看自己的信息或需要管理员权限
    check_user_or_admin(current_user, user_id)

    # 使用与 /auth/me 相同的全局数据库管理器
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        user_service = UserService(db)
        result = user_service.get_user_by_id(user_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error.message
            )
        
        return {
            "success": True,
            "message": "获取用户信息成功",
            "data": result.data
        }


@router.put("/{user_id}/assets", response_model=dict, summary="更新用户资产")
async def update_user_assets(
    user_id: int,
    asset_data: AssetUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    更新指定用户的资产 (需要管理员权限)

    - **asset_type**: 资产类型 (game_coins/shop_coins/points)
    - **amount**: 变更数量
    - **operation**: 操作类型 (add/subtract/set)
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        assets_service = UserAssetsService(db)
        
        if asset_data.asset_type == "game_coins":
            result = assets_service.update_game_coins(
                user_id, asset_data.amount, asset_data.operation
            )
        elif asset_data.asset_type == "shop_coins":
            result = assets_service.update_shop_coins(
                user_id, asset_data.amount, asset_data.operation
            )
        elif asset_data.asset_type == "points":
            result = assets_service.update_points(
                user_id, asset_data.amount, asset_data.operation
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的资产类型"
            )
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.INSUFFICIENT_BALANCE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
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


@router.post("/transfer", response_model=dict, summary="资产转账")
async def transfer_assets(
    transfer_data: AssetTransfer,
    current_user: dict = Depends(jwt_bearer)
):
    """
    向其他用户转账资产
    
    - **to_user_id**: 转入用户ID
    - **asset_type**: 资产类型 (game_coins/shop_coins/points)
    - **amount**: 转账数量
    """
    db_manager = DatabaseManager()
    db_manager.init_database()
    
    with db_manager.get_db_session() as db:
        assets_service = UserAssetsService(db)
        result = assets_service.transfer_assets(
            current_user["user_id"],
            transfer_data.to_user_id,
            transfer_data.asset_type,
            transfer_data.amount
        )
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.INSUFFICIENT_BALANCE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error.message
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
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }
