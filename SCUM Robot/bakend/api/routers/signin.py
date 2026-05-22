"""
签到系统相关API路由
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from ...modules.sql.services.signin_service import SigninService
from ...modules.sql.services.service_result import ServiceErrorType
from ...modules.auth import jwt_bearer, require_admin
from ...modules.sql.database.manager import DatabaseManager


router = APIRouter(prefix="/api/v1/signin", tags=["Signin System"])


# Pydantic 模型
class SigninResponse(BaseModel):
    """签到响应模型"""
    success: bool
    message: str
    data: dict


# API 路由
@router.get("/status", response_model=dict, summary="获取签到状态")
async def get_signin_status(current_user: dict = Depends(jwt_bearer)):
    """
    获取当前用户的签到状态
    
    返回信息包括：
    - 今日是否已签到
    - 连续签到天数
    - 累计签到天数
    - 通行证等级和经验
    - VIP等级
    - 是否可以签到
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        signin_service = SigninService(db)
        result = signin_service.check_signin_status(current_user["user_id"])
        
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


@router.post("/checkin", response_model=dict, summary="每日签到")
async def daily_checkin(current_user: dict = Depends(jwt_bearer)):
    """
    执行每日签到
    
    功能：
    - 检查今日是否已签到
    - 计算连续签到天数
    - 发放签到奖励（根据VIP等级）
    - 增加通行证经验
    - 检查通行证升级
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        signin_service = SigninService(db)
        result = signin_service.daily_signin(current_user["user_id"])
        
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
            "message": result.message,
            "data": result.data
        }


@router.get("/history", response_model=dict, summary="获取签到历史")
async def get_signin_history(
    limit: int = Query(30, ge=1, le=100, description="限制数量"),
    current_user: dict = Depends(jwt_bearer)
):
    """
    获取用户签到历史记录
    
    - **limit**: 限制数量 (1-100)
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        signin_service = SigninService(db)
        result = signin_service.get_signin_history(current_user["user_id"], limit)
        
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


@router.get("/rewards", response_model=dict, summary="获取签到奖励配置")
async def get_signin_rewards(current_user: dict = Depends(jwt_bearer)):
    """
    获取签到奖励配置信息
    
    返回信息包括：
    - 基础奖励
    - 连续签到奖励
    - 里程碑奖励
    - VIP等级奖励配置
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        signin_service = SigninService(db)
        result = signin_service.get_signin_rewards_config()
        
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


@router.get("/leaderboard", response_model=dict, summary="获取签到排行榜")
async def get_signin_leaderboard(
    type: str = Query("total", description="排行榜类型 (total/consecutive)"),
    limit: int = Query(50, ge=1, le=100, description="限制数量"),
    current_user: dict = Depends(jwt_bearer)
):
    """
    获取签到排行榜
    
    - **type**: 排行榜类型
      - total: 累计签到排行榜
      - consecutive: 连续签到排行榜
    - **limit**: 限制数量 (1-100)
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        signin_service = SigninService(db)
        result = signin_service.get_signin_leaderboard(type, limit)
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.VALIDATION_ERROR:
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


# 管理员接口
@router.post("/admin/reset-flags", response_model=dict, summary="重置今日签到标志")
async def reset_daily_signin_flags(current_user: dict = Depends(require_admin)):
    """
    重置所有用户的今日签到标志 (管理员功能)
    
    用于定时任务或手动重置
    """
    # 检查管理员权限
    if current_user.get("user_type") not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    from ..main import get_global_db_manager

    
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        signin_service = SigninService(db)
        result = signin_service.reset_daily_signin_flags()
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data if hasattr(result, 'data') else None
        }


@router.get("/admin/statistics", response_model=dict, summary="获取签到统计")
async def get_signin_statistics(current_user: dict = Depends(require_admin)):
    """
    获取签到系统统计数据 (管理员功能)
    
    返回信息包括：
    - 今日签到用户数
    - 总签到用户数
    - 平均签到天数
    - 最高连续签到记录
    """
    # 检查管理员权限
    if current_user.get("user_type") not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    from ..main import get_global_db_manager

    
    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        from ...modules.sql.models.user_models import User
        from sqlalchemy import func
        from datetime import date
        
        try:
            # 今日签到用户数
            today = date.today()
            today_signin_count = db.query(User).filter(
                User.today_signed_in == True,
                User.last_signin_date == today
            ).count()
            
            # 总签到用户数
            total_signin_users = db.query(User).filter(User.total_signin_days > 0).count()
            
            # 平均签到天数
            avg_signin_days = db.query(func.avg(User.total_signin_days)).filter(
                User.total_signin_days > 0
            ).scalar() or 0
            
            # 最高连续签到记录
            max_consecutive_days = db.query(func.max(User.consecutive_signin_days)).scalar() or 0
            
            # 最高累计签到记录
            max_total_days = db.query(func.max(User.total_signin_days)).scalar() or 0
            
            statistics = {
                'today_signin_count': today_signin_count,
                'total_signin_users': total_signin_users,
                'avg_signin_days': round(avg_signin_days, 2),
                'max_consecutive_days': max_consecutive_days,
                'max_total_days': max_total_days,
                'beijing_date': today.isoformat()
            }
            
            return {
                "success": True,
                "message": "获取签到统计成功",
                "data": statistics
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"获取签到统计失败: {str(e)}"
            )
