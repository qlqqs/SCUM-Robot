"""
人物能力系统相关API路由
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from ...modules.sql.services.character_service import CharacterService
from ...modules.sql.services.service_result import ServiceErrorType
from ...modules.auth import jwt_bearer, require_admin
from ...modules.sql.database.manager import DatabaseManager


router = APIRouter(prefix="/api/v1/character", tags=["Character System"])


# Pydantic 模型
class CharacterStatsUpdate(BaseModel):
    """人物能力更新模型"""
    strength: Optional[int] = Field(None, ge=1, le=100, description="力量 (1-100)")
    stamina: Optional[int] = Field(None, ge=1, le=100, description="体力 (1-100)")
    intelligence: Optional[int] = Field(None, ge=1, le=100, description="智力 (1-100)")
    agility: Optional[int] = Field(None, ge=1, le=100, description="敏捷 (1-100)")


class GameStatsSync(BaseModel):
    """游戏数据同步模型"""
    steam_id: str = Field(..., max_length=20, description="Steam ID")
    strength: int = Field(..., ge=1, le=100, description="力量")
    stamina: int = Field(..., ge=1, le=100, description="体力")
    intelligence: int = Field(..., ge=1, le=100, description="智力")
    agility: int = Field(..., ge=1, le=100, description="敏捷")


class BatchStatsUpdate(BaseModel):
    """批量能力更新模型"""
    updates: List[dict] = Field(..., description="更新列表")


# 用户接口
@router.get("/stats", response_model=dict, summary="获取人物能力")
async def get_character_stats(current_user: dict = Depends(jwt_bearer)):
    """
    获取当前用户的人物能力数据

    返回信息包括：
    - 力量、体力、智力、敏捷值
    - 总能力值
    - 最后同步时间
    - 创建和更新时间
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        character_service = CharacterService(db)
        result = character_service.get_character_stats(current_user["user_id"])
        
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


@router.get("/stats/steam/{steam_id}", response_model=dict, summary="通过Steam ID获取人物能力")
async def get_character_stats_by_steam_id(steam_id: int, current_user: dict = Depends(jwt_bearer)):
    """
    通过Steam ID获取人物能力数据
    
    - **steam_id**: Steam ID
    """
    db_manager = DatabaseManager()
    db_manager.init_database()
    
    with db_manager.get_db_session() as db:
        character_service = CharacterService(db)
        result = character_service.get_character_stats_by_steam_id(steam_id)
        
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


@router.get("/leaderboard", response_model=dict, summary="获取能力排行榜")
async def get_character_leaderboard(
    order_by: str = Query("total_stats", description="排序字段"),
    limit: int = Query(50, ge=1, le=100, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: dict = Depends(jwt_bearer)
):
    """
    获取人物能力排行榜
    
    - **order_by**: 排序字段 (total_stats/strength/stamina/intelligence/agility)
    - **limit**: 限制数量 (1-100)
    - **offset**: 偏移量
    """
    db_manager = DatabaseManager()
    db_manager.init_database()
    
    with db_manager.get_db_session() as db:
        character_service = CharacterService(db)
        result = character_service.get_character_stats_list(limit, offset, order_by)
        
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


@router.get("/summary", response_model=dict, summary="获取能力统计摘要")
async def get_character_stats_summary(current_user: dict = Depends(jwt_bearer)):
    """
    获取人物能力统计摘要

    返回信息包括：
    - 总用户数
    - 各能力的平均值、最大值、最小值
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        character_service = CharacterService(db)
        result = character_service.get_character_stats_summary()
        
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


# 管理员接口
@router.put("/stats/{user_id}", response_model=dict, summary="更新用户能力")
async def update_character_stats(
    user_id: int,
    stats_data: CharacterStatsUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    更新指定用户的人物能力 (需要管理员权限)

    - **user_id**: 用户ID
    - **strength**: 力量值 (1-100)
    - **stamina**: 体力值 (1-100)
    - **intelligence**: 智力值 (1-100)
    - **agility**: 敏捷值 (1-100)
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        character_service = CharacterService(db)
        result = character_service.update_character_stats(
            user_id,
            stats_data.strength,
            stats_data.stamina,
            stats_data.intelligence,
            stats_data.agility
        )
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error.message
                )
            elif result.error.error_type == ServiceErrorType.VALIDATION_ERROR:
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


@router.post("/stats/{user_id}/reset", response_model=dict, summary="重置用户能力")
async def reset_character_stats(
    user_id: int,
    current_user: dict = Depends(require_admin)
):
    """
    重置指定用户的人物能力为默认值 (需要管理员权限)
    
    - **user_id**: 用户ID
    """
    db_manager = DatabaseManager()
    db_manager.init_database()
    
    with db_manager.get_db_session() as db:
        character_service = CharacterService(db)
        result = character_service.reset_character_stats(user_id)
        
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


@router.post("/sync", response_model=dict, summary="同步游戏数据")
async def sync_character_stats_from_game(
    sync_data: GameStatsSync,
    current_user: dict = Depends(require_admin)
):
    """
    从游戏同步人物能力数据 (需要管理员权限)
    
    用于从游戏服务器同步最新的人物能力数据
    
    - **steam_id**: Steam ID
    - **strength**: 力量值
    - **stamina**: 体力值
    - **intelligence**: 智力值
    - **agility**: 敏捷值
    """
    db_manager = DatabaseManager()
    db_manager.init_database()
    
    with db_manager.get_db_session() as db:
        character_service = CharacterService(db)
        
        game_stats = {
            'strength': sync_data.strength,
            'stamina': sync_data.stamina,
            'intelligence': sync_data.intelligence,
            'agility': sync_data.agility
        }
        
        result = character_service.sync_character_stats_from_game(sync_data.steam_id, game_stats)
        
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


@router.post("/batch-update", response_model=dict, summary="批量更新能力")
async def batch_update_character_stats(
    batch_data: BatchStatsUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    批量更新多个用户的人物能力 (需要管理员权限)
    
    请求格式：
    ```json
    {
        "updates": [
            {
                "user_id": 1,
                "strength": 20,
                "stamina": 25,
                "intelligence": 15,
                "agility": 30
            },
            {
                "user_id": 2,
                "strength": 35
            }
        ]
    }
    ```
    """
    db_manager = DatabaseManager()
    db_manager.init_database()
    
    with db_manager.get_db_session() as db:
        character_service = CharacterService(db)
        result = character_service.batch_update_character_stats(batch_data.updates)
        
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


@router.get("/admin/stats", response_model=dict, summary="获取所有用户能力")
async def get_all_character_stats(
    limit: int = Query(50, ge=1, le=100, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    order_by: str = Query("total_stats", description="排序字段"),
    current_user: dict = Depends(require_admin)
):
    """
    获取所有用户的人物能力数据 (需要管理员权限)
    
    - **limit**: 限制数量 (1-100)
    - **offset**: 偏移量
    - **order_by**: 排序字段 (total_stats/strength/stamina/intelligence/agility)
    """
    db_manager = DatabaseManager()
    db_manager.init_database()
    
    with db_manager.get_db_session() as db:
        character_service = CharacterService(db)
        result = character_service.get_character_stats_list(limit, offset, order_by)
        
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


@router.get("/admin/stats/{user_id}", response_model=dict, summary="获取指定用户能力")
async def get_user_character_stats(
    user_id: int,
    current_user: dict = Depends(require_admin)
):
    """
    获取指定用户的人物能力数据 (需要管理员权限)

    - **user_id**: 用户ID
    """
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        character_service = CharacterService(db)
        result = character_service.get_character_stats(user_id)
        
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
