"""
配置管理API路由

提供配置的增删改查API接口
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from ...modules.sql.services.config_service import ConfigService
from ...modules.sql.services.service_result import ServiceErrorType
from ...modules.auth import jwt_bearer, require_admin, require_super_admin
from ...modules.sql.database.manager import DatabaseManager
from ...modules.sql.models.config_models import SystemConfig, ConfigType, ConfigGroup


router = APIRouter(prefix="/api/v1/configs", tags=["Configuration"])


# ===== Pydantic 模型 =====

class ConfigCreate(BaseModel):
    """创建配置请求模型"""
    key: str = Field(..., description="配置键", example="site.name")
    value: Any = Field(..., description="配置值", example="SCUM Robot")
    type: str = Field(default="string", description="数据类型（string/int/float/bool/json/encrypted）")
    group_name: str = Field(default="custom", description="配置分组")
    description: Optional[str] = Field(None, description="配置描述")
    is_public: bool = Field(default=False, description="是否公开")
    is_encrypted: bool = Field(default=False, description="是否加密")
    sort_order: int = Field(default=0, description="排序顺序")


class ConfigUpdate(BaseModel):
    """更新配置请求模型"""
    value: Any = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    is_public: Optional[bool] = Field(None, description="是否公开")
    is_active: Optional[bool] = Field(None, description="是否启用")
    change_reason: Optional[str] = Field(None, description="修改原因")


# ===== API端点 =====

@router.get("/public", summary="获取公开配置")
async def get_public_configs():
    """
    获取所有公开配置（无需认证）
    
    返回所有标记为公开的配置，供前端使用
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        service = ConfigService(db)
        result = service.get_public()
        
        if result.success:
            return {
                "success": True,
                "data": result.data,
                "message": result.message
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error.message
            )


@router.get("", summary="获取所有配置")
async def get_all_configs(
    include_inactive: bool = Query(False, description="包含禁用的配置"),
    include_encrypted: bool = Query(False, description="包含加密配置的值"),
    current_user: dict = Depends(require_admin)
):
    """
    获取所有配置（需要管理员权限）
    
    返回所有配置的列表，包括配置的元数据
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        service = ConfigService(db)
        result = service.get_all(include_inactive, include_encrypted)
        
        if result.success:
            return {
                "success": True,
                "data": result.data,
                "message": result.message
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error.message
            )


@router.get("/group/{group_name}", summary="获取分组配置")
async def get_group_configs(
    group_name: str,
    current_user: dict = Depends(require_admin)
):
    """
    获取指定分组的配置（需要管理员权限）
    
    返回指定分组的所有配置，以键值对形式返回
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        service = ConfigService(db)
        result = service.get_by_group(group_name)
        
        if result.success:
            return {
                "success": True,
                "data": result.data,
                "message": result.message
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error.message
            )


@router.get("/{key}", summary="获取单个配置")
async def get_config(
    key: str,
    current_user: dict = Depends(require_admin)
):
    """
    获取指定配置（需要管理员权限）
    
    返回指定键的配置值
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        service = ConfigService(db)
        value = service.get(key)
        
        return {
            "success": True,
            "data": {
                "key": key,
                "value": value
            }
        }


@router.post("", summary="创建配置")
async def create_config(
    config_data: ConfigCreate,
    current_user: dict = Depends(require_super_admin)
):
    """
    创建新配置（需要超级管理员权限）
    
    创建一个新的配置项
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        service = ConfigService(db)
        
        # 转换类型
        try:
            config_type = ConfigType(config_data.type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的配置类型: {config_data.type}。有效类型: string, int, float, bool, json, encrypted"
            )
        
        result = service.set(
            key=config_data.key,
            value=config_data.value,
            type=config_type,
            group_name=config_data.group_name,
            description=config_data.description,
            is_public=config_data.is_public,
            is_encrypted=config_data.is_encrypted,
            changed_by=current_user['user_id']
        )
        
        if result.success:
            return {
                "success": True,
                "data": result.data,
                "message": result.message
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error.message
            )


@router.put("/{key}", summary="更新配置")
async def update_config(
    key: str,
    config_data: ConfigUpdate,
    current_user: dict = Depends(require_super_admin)
):
    """
    更新配置（需要超级管理员权限）
    
    更新指定配置的值和元数据
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        service = ConfigService(db)
        
        # 获取现有配置
        existing = db.query(SystemConfig).filter(
            SystemConfig.key == key
        ).first()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 更新配置
        result = service.set(
            key=key,
            value=config_data.value,
            type=existing.type,
            group_name=existing.group_name,
            description=config_data.description or existing.description,
            is_public=config_data.is_public if config_data.is_public is not None else existing.is_public,
            is_encrypted=existing.is_encrypted,
            changed_by=current_user['user_id'],
            change_reason=config_data.change_reason
        )
        
        # 更新 is_active 状态
        if config_data.is_active is not None and existing.is_active != config_data.is_active:
            existing.is_active = config_data.is_active
            db.commit()
        
        if result.success:
            return {
                "success": True,
                "data": result.data,
                "message": result.message
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error.message
            )


@router.delete("/{key}", summary="删除配置")
async def delete_config(
    key: str,
    current_user: dict = Depends(require_super_admin)
):
    """
    删除配置（需要超级管理员权限）
    
    删除指定的配置项
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        service = ConfigService(db)
        result = service.delete(key, changed_by=current_user['user_id'])
        
        if result.success:
            return {
                "success": True,
                "message": result.message
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error.message
            )

