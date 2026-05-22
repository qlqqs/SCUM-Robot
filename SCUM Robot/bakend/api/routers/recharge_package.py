"""
充值套餐相关API路由
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from bakend.modules.sql.database.manager import DatabaseManager
from bakend.modules.sql.models.recharge_package_models import RechargePackage, RechargeRecord
from ..dependencies import get_database_manager, get_current_user, get_current_admin_user


router = APIRouter(prefix="/api/v1/recharge", tags=["充值套餐"])


# ==================== Pydantic 模型 ====================

class RechargePackageResponse(BaseModel):
    """充值套餐响应模型"""
    id: int
    name: str
    description: Optional[str]
    tag: Optional[str]
    product_name: Optional[str] = Field(default='商城币充值', description="支付项目名称")
    price: float
    currency: str
    coins: int
    bonus_coins: int
    total_coins: int
    icon: Optional[str]
    badge: Optional[str]
    sort_order: int
    is_active: bool
    is_hot: bool
    is_recommended: bool

    class Config:
        from_attributes = True


class RechargePackageCreate(BaseModel):
    """创建充值套餐请求模型"""
    name: str = Field(..., min_length=1, max_length=64, description="套餐名称")
    description: Optional[str] = Field(None, max_length=255, description="套餐描述")
    tag: Optional[str] = Field(None, max_length=32, description="标签")
    product_name: Optional[str] = Field('商城币充值', max_length=64, description="支付项目名称")
    price: float = Field(..., gt=0, description="充值金额")
    currency: str = Field("CNY", max_length=3, description="货币类型")
    coins: int = Field(..., ge=0, description="基础商城币")
    bonus_coins: int = Field(0, ge=0, description="赠送商城币")
    icon: Optional[str] = Field(None, max_length=255, description="图标URL")
    badge: Optional[str] = Field(None, max_length=32, description="徽章")
    sort_order: int = Field(0, description="排序")
    is_active: bool = Field(True, description="是否启用")
    is_hot: bool = Field(False, description="是否热门")
    is_recommended: bool = Field(False, description="是否推荐")
    daily_limit: Optional[int] = Field(None, description="每日限制")
    total_limit: Optional[int] = Field(None, description="总限制")
    user_daily_limit: Optional[int] = Field(None, description="用户每日限制")
    user_total_limit: Optional[int] = Field(None, description="用户总限制")
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")


class RechargePackageUpdate(BaseModel):
    """更新充值套餐请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=255)
    tag: Optional[str] = Field(None, max_length=32)
    product_name: Optional[str] = Field(None, max_length=64, description="支付项目名称")
    price: Optional[float] = Field(None, gt=0)
    coins: Optional[int] = Field(None, ge=0)
    bonus_coins: Optional[int] = Field(None, ge=0)
    icon: Optional[str] = Field(None, max_length=255)
    badge: Optional[str] = Field(None, max_length=32)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_hot: Optional[bool] = None
    is_recommended: Optional[bool] = None


# ==================== API 端点 ====================

@router.get("/packages", response_model=List[RechargePackageResponse])
async def get_recharge_packages(
    active_only: bool = Query(True, description="只返回启用的套餐"),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    获取充值套餐列表
    
    - **active_only**: 是否只返回启用的套餐（默认：True）
    """
    try:
        with db_manager.get_db_session() as session:
            if active_only:
                packages = RechargePackage.get_active_packages(session)
            else:
                packages = session.query(RechargePackage).order_by(
                    RechargePackage.sort_order.asc(),
                    RechargePackage.price.asc()
                ).all()
            
            return [pkg.to_dict() for pkg in packages]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取充值套餐失败: {str(e)}"
        )


@router.get("/packages/hot", response_model=List[RechargePackageResponse])
async def get_hot_packages(
    limit: int = Query(3, ge=1, le=10, description="返回数量"),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    获取热门充值套餐
    
    - **limit**: 返回数量（默认：3，最大：10）
    """
    try:
        with db_manager.get_db_session() as session:
            packages = RechargePackage.get_hot_packages(session, limit=limit)
            return [pkg.to_dict() for pkg in packages]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取热门套餐失败: {str(e)}"
        )


@router.get("/packages/recommended", response_model=List[RechargePackageResponse])
async def get_recommended_packages(
    limit: int = Query(3, ge=1, le=10, description="返回数量"),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    获取推荐充值套餐
    
    - **limit**: 返回数量（默认：3，最大：10）
    """
    try:
        with db_manager.get_db_session() as session:
            packages = RechargePackage.get_recommended_packages(session, limit=limit)
            return [pkg.to_dict() for pkg in packages]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取推荐套餐失败: {str(e)}"
        )


@router.get("/packages/{package_id}", response_model=RechargePackageResponse)
async def get_package_detail(
    package_id: int,
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    获取充值套餐详情
    
    - **package_id**: 套餐ID
    """
    try:
        with db_manager.get_db_session() as session:
            package = session.query(RechargePackage).filter(
                RechargePackage.id == package_id
            ).first()
            
            if not package:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="套餐不存在"
                )
            
            return package.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取套餐详情失败: {str(e)}"
        )


@router.post("/packages", response_model=RechargePackageResponse)
async def create_package(
    package_data: RechargePackageCreate,
    current_user: dict = Depends(get_current_admin_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    创建充值套餐（需要管理员权限）

    - **package_data**: 套餐数据
    """
    
    try:
        with db_manager.get_db_session() as session:
            # 创建套餐
            package = RechargePackage(**package_data.dict())
            package.calculate_total_coins()
            
            session.add(package)
            session.commit()
            session.refresh(package)
            
            return package.to_dict()
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建套餐失败: {str(e)}"
        )


@router.put("/packages/{package_id}", response_model=RechargePackageResponse)
async def update_package(
    package_id: int,
    package_data: RechargePackageUpdate,
    current_user: dict = Depends(get_current_admin_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    更新充值套餐（需要管理员权限）

    - **package_id**: 套餐ID
    - **package_data**: 更新数据
    """
    
    try:
        with db_manager.get_db_session() as session:
            package = session.query(RechargePackage).filter(
                RechargePackage.id == package_id
            ).first()
            
            if not package:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="套餐不存在"
                )
            
            # 更新字段
            update_data = package_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(package, key, value)
            
            # 重新计算总商城币
            if 'coins' in update_data or 'bonus_coins' in update_data:
                package.calculate_total_coins()
            
            package.update_timestamp()
            session.commit()
            session.refresh(package)
            
            return package.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新套餐失败: {str(e)}"
        )


@router.delete("/packages/{package_id}")
async def delete_package(
    package_id: int,
    current_user: dict = Depends(get_current_admin_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    删除充值套餐（需要管理员权限）

    - **package_id**: 套餐ID
    """
    
    try:
        with db_manager.get_db_session() as session:
            package = session.query(RechargePackage).filter(
                RechargePackage.id == package_id
            ).first()
            
            if not package:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="套餐不存在"
                )
            
            session.delete(package)
            session.commit()
            
            return {"success": True, "message": "套餐删除成功"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除套餐失败: {str(e)}"
        )

