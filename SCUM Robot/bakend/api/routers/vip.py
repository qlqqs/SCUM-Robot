"""
VIP系统相关API路由
"""

from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from ...modules.sql.services.vip_service import VIPService
from ...modules.sql.services.service_result import ServiceErrorType
from ...modules.auth import jwt_bearer, require_admin
from ...modules.sql.database.manager import DatabaseManager


router = APIRouter(prefix="/api/v1/vip", tags=["VIP System"])


# Pydantic 模型
class VIPConfigCreate(BaseModel):
    """VIP配置创建模型"""
    level: int = Field(..., ge=0, description="VIP等级")
    name: str = Field(..., min_length=1, max_length=50, description="等级名称")
    daily_gift_id: Optional[int] = Field(None, description="每日礼包ID")
    level_gift_id: Optional[int] = Field(None, description="等级礼包ID（升级时获得）")
    upgrade_required_points: int = Field(0, ge=0, description="升级所需消费积分")
    enable_login_announcement: bool = Field(False, description="是否开启进服公告")


class VIPConfigUpdate(BaseModel):
    """VIP配置更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="等级名称")
    daily_gift_id: Optional[int] = Field(None, description="每日礼包ID")
    level_gift_id: Optional[int] = Field(None, description="等级礼包ID（升级时获得）")
    upgrade_required_points: Optional[int] = Field(None, ge=0, description="升级所需消费积分")
    enable_login_announcement: Optional[bool] = Field(None, description="是否开启进服公告")


class VIPUpgrade(BaseModel):
    """VIP升级模型"""
    user_id: int = Field(..., description="用户ID")
    new_level: int = Field(..., ge=0, description="新VIP等级")
    expire_date: Optional[str] = Field(None, description="过期日期 (YYYY-MM-DD，空表示永不过期)")


class BatchVIPUpdate(BaseModel):
    """批量VIP更新模型"""
    updates: List[VIPUpgrade] = Field(..., description="更新列表")


# 用户接口
@router.get("/status", response_model=dict, summary="获取用户VIP状态")
async def get_user_vip_status(current_user: dict = Depends(jwt_bearer)):
    """
    获取当前用户的VIP状态
    
    返回信息包括：
    - VIP等级和名称
    - VIP过期时间
    - 是否永久VIP
    - VIP权益配置
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        vip_service = VIPService(db)
        result = vip_service.get_user_vip_status(current_user["user_id"])
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.NOT_FOUND:
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


@router.get("/configs", response_model=dict, summary="获取所有VIP配置")
async def get_all_vip_configs(current_user: dict = Depends(jwt_bearer)):
    """
    获取所有VIP等级配置
    
    返回所有可用的VIP等级及其权益配置
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        vip_service = VIPService(db)
        result = vip_service.get_all_vip_configs()
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }


@router.get("/config/{level}", response_model=dict, summary="获取指定VIP配置")
async def get_vip_config(level: int, current_user: dict = Depends(jwt_bearer)):
    """
    获取指定VIP等级的配置
    
    - **level**: VIP等级
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        vip_service = VIPService(db)
        result = vip_service.get_vip_config(level)
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.NOT_FOUND:
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





# 管理员接口
@router.post("/config", response_model=dict, summary="创建VIP配置")
async def create_vip_config(
    config_data: VIPConfigCreate,
    current_user: dict = Depends(require_admin)
):
    """
    创建新的VIP等级配置 (需要管理员权限)
    
    配置包括：
    - VIP等级和名称
    - 签到奖励倍数和自定义奖励
    - 商城权限列表
    - 每日免费礼包数量
    - 特殊功能列表
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        vip_service = VIPService(db)
        result = vip_service.create_vip_config(config_data.dict())
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.ALREADY_EXISTS:
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


@router.put("/config/{level}", response_model=dict, summary="更新VIP配置")
async def update_vip_config(
    level: int,
    config_data: VIPConfigUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    更新指定VIP等级的配置 (需要管理员权限)
    
    - **level**: VIP等级
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        vip_service = VIPService(db)
        result = vip_service.update_vip_config(level, config_data.dict(exclude_unset=True))
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.NOT_FOUND:
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


@router.delete("/config/{level}", response_model=dict, summary="删除VIP配置")
async def delete_vip_config(
    level: int,
    current_user: dict = Depends(require_admin)
):
    """
    删除指定VIP等级的配置 (需要管理员权限)

    注意：
    - VIP0为系统默认配置，不可删除
    - 如果有用户正在使用该VIP等级，则无法删除

    - **level**: VIP等级
    """
    # API层VIP0保护：提前检查并返回明确错误
    if level == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="VIP0为系统默认配置，不可删除"
        )

    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        vip_service = VIPService(db)
        result = vip_service.delete_vip_config(level)
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error.message
                )
            elif result.error.error_type == ServiceErrorType.ALREADY_EXISTS:
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
            "message": result.message
        }


@router.post("/upgrade", response_model=dict, summary="升级用户VIP")
async def upgrade_user_vip(
    upgrade_data: VIPUpgrade,
    current_user: dict = Depends(require_admin)
):
    """
    升级指定用户的VIP等级 (需要管理员权限)
    
    - **user_id**: 用户ID
    - **new_level**: 新VIP等级
    - **expire_date**: 过期日期 (可选，空表示永不过期)
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    # 处理过期日期
    expire_date = None
    if upgrade_data.expire_date:
        try:
            expire_date = datetime.strptime(upgrade_data.expire_date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="日期格式错误，请使用 YYYY-MM-DD 格式"
            )
    
    with db_manager.get_db_session() as db:
        vip_service = VIPService(db)
        result = vip_service.upgrade_user_vip(upgrade_data.user_id, upgrade_data.new_level, expire_date)
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.NOT_FOUND:
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


@router.post("/batch-upgrade", response_model=dict, summary="批量升级VIP")
async def batch_upgrade_vip(
    batch_data: BatchVIPUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    批量升级用户VIP等级 (需要管理员权限)
    
    请求格式：
    ```json
    {
        "updates": [
            {
                "user_id": 1,
                "new_level": 3,
                "expire_date": "2024-12-31"
            },
            {
                "user_id": 2,
                "new_level": 5
            }
        ]
    }
    ```
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        vip_service = VIPService(db)
        
        # 转换数据格式
        updates = []
        for update in batch_data.updates:
            update_dict = {
                'user_id': update.user_id,
                'new_level': update.new_level
            }
            if update.expire_date:
                update_dict['expire_date'] = update.expire_date
            updates.append(update_dict)
        
        result = vip_service.batch_update_vip(updates)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }


@router.get("/statistics", response_model=dict, summary="获取VIP统计")
async def get_vip_statistics(
    min_level: int = Query(2, ge=0, description="最低VIP等级，默认2（只统计付费VIP）"),
    current_user: dict = Depends(require_admin)
):
    """
    获取VIP用户统计数据 (需要管理员权限)

    返回信息包括：
    - 各VIP等级用户数量（默认只统计VIP2及以上）
    - VIP用户比例
    - 总用户数统计

    参数：
    - min_level: 最低统计等级，默认2（只统计付费VIP用户）
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        vip_service = VIPService(db)
        result = vip_service.get_vip_statistics(min_level)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }


# ===== VIP自动升级相关API =====

class VIPAutoUpgradeRequest(BaseModel):
    """VIP自动升级请求模型"""
    user_id: Optional[int] = Field(None, description="用户ID，不提供则检查当前用户")
    upgrade_reason: Optional[str] = Field(None, description="升级原因说明")


class VIPBatchUpgradeRequest(BaseModel):
    """VIP批量升级请求模型"""
    user_ids: Optional[List[int]] = Field(None, description="用户ID列表，不提供则检查所有用户")
    force_check: bool = Field(False, description="是否强制检查")


@router.post("/auto-upgrade/check", response_model=dict, summary="检查VIP自动升级")
async def check_vip_auto_upgrade(
    request_data: VIPAutoUpgradeRequest,
    current_user: dict = Depends(jwt_bearer)
):
    """
    检查并执行VIP自动升级

    - **user_id**: 用户ID（可选，不提供则检查当前用户）
    - **upgrade_reason**: 升级原因说明（可选）

    根据用户当前积分检查是否满足VIP升级条件，如果满足则自动升级。
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    # 确定要检查的用户ID
    target_user_id = request_data.user_id or current_user["user_id"]

    # 检查权限：只能检查自己的或管理员可以检查任何用户
    if target_user_id != current_user["user_id"] and current_user.get("user_type") not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能检查自己的VIP升级状态"
        )

    with db_manager.get_db_session() as db:
        from ...modules.sql.services.vip_auto_upgrade_service import VIPAutoUpgradeService

        upgrade_service = VIPAutoUpgradeService(db)
        result = upgrade_service.check_and_upgrade_user(
            user_id=target_user_id,
            upgrade_type="manual",
            upgrade_reason=request_data.upgrade_reason or "手动检查升级"
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )

        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }


@router.post("/auto-upgrade/batch-check", response_model=dict, summary="批量检查VIP自动升级")
async def batch_check_vip_auto_upgrade(
    request_data: VIPBatchUpgradeRequest,
    current_user: dict = Depends(require_admin)
):
    """
    批量检查VIP自动升级（管理员功能）

    - **user_ids**: 用户ID列表（可选，不提供则检查所有有积分的用户）
    - **force_check**: 是否强制检查

    批量检查多个用户的VIP升级条件并执行升级。
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        from ...modules.sql.services.vip_auto_upgrade_service import VIPAutoUpgradeService

        upgrade_service = VIPAutoUpgradeService(db)
        result = upgrade_service.batch_check_upgrades(
            user_ids=request_data.user_ids,
            force_check=request_data.force_check
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )

        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }


@router.get("/upgrade-history", response_model=dict, summary="获取VIP升级历史")
async def get_vip_upgrade_history(
    user_id: Optional[int] = Query(None, description="用户ID，不提供则查询当前用户"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: dict = Depends(jwt_bearer)
):
    """
    获取VIP升级历史记录

    - **user_id**: 用户ID（可选，不提供则查询当前用户）
    - **limit**: 限制数量 (1-100)
    - **offset**: 偏移量

    返回用户的VIP升级历史记录，包括升级时间、等级变化、奖励发放等信息。
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    # 确定要查询的用户ID
    target_user_id = user_id or current_user["user_id"]

    # 检查权限：只能查询自己的或管理员可以查询任何用户
    if target_user_id != current_user["user_id"] and current_user.get("user_type") not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能查询自己的VIP升级历史"
        )

    with db_manager.get_db_session() as db:
        from ...modules.sql.services.vip_auto_upgrade_service import VIPAutoUpgradeService

        upgrade_service = VIPAutoUpgradeService(db)
        result = upgrade_service.get_upgrade_history(
            user_id=target_user_id,
            limit=limit,
            offset=offset
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )

        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }
