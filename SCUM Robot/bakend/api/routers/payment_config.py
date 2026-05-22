"""
支付配置管理API路由
基于Xboard的API设计，提供支付配置的CRUD操作
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json
import asyncio

from ...modules.sql.database.manager import DatabaseManager
from ...modules.payment.payment_config_service import PaymentConfigService
from ...modules.payment.callback_handler import PaymentCallbackHandler
from ...modules.common.service_result import ServiceResult
from ..dependencies import get_current_admin_user, get_current_user, get_database_manager


router = APIRouter(prefix="/api/v1/payment", tags=["Payment System"])


# Pydantic模型定义
class PaymentConfigCreate(BaseModel):
    """创建支付配置请求模型"""
    provider_code: str = Field(..., description="支付提供商代码")
    provider_name: str = Field(..., description="支付提供商名称")
    environment: str = Field(default="production", description="环境")
    config: Dict[str, Any] = Field(..., description="配置参数")
    is_active: bool = Field(default=True, description="是否启用")
    is_default: bool = Field(default=False, description="是否为默认配置")
    sort_order: int = Field(default=0, description="排序顺序")
    icon: Optional[str] = Field(None, description="图标路径")
    description: Optional[str] = Field(None, description="配置描述")


class PaymentConfigUpdate(BaseModel):
    """更新支付配置请求模型"""
    provider_name: Optional[str] = Field(None, description="支付提供商名称")
    environment: Optional[str] = Field(None, description="环境")
    config: Optional[Dict[str, Any]] = Field(None, description="配置参数")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_default: Optional[bool] = Field(None, description="是否为默认配置")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    icon: Optional[str] = Field(None, description="图标路径")
    description: Optional[str] = Field(None, description="配置描述")


class PaymentConfigResponse(BaseModel):
    """支付配置响应模型"""
    id: int
    uuid: str
    provider_code: str
    provider_name: str
    environment: str
    is_active: bool
    is_default: bool
    sort_order: int
    icon: Optional[str]
    description: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    config: Optional[Dict[str, Any]] = None  # 敏感信息可能被遮蔽


class ApiResponse(BaseModel):
    """统一API响应模型"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


def get_payment_config_service(db_manager: DatabaseManager = Depends(get_database_manager)) -> PaymentConfigService:
    """获取支付配置服务实例"""
    return PaymentConfigService(db_manager)


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    # 优先从X-Forwarded-For获取真实IP
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # 从X-Real-IP获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 最后使用客户端IP
    return request.client.host if request.client else "unknown"


async def parse_request_data(request: Request) -> Dict[str, Any]:
    """解析请求数据"""
    try:
        content_type = request.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            # JSON数据
            body = await request.body()
            if body:
                return json.loads(body.decode('utf-8'))
            else:
                return {}
        elif "application/x-www-form-urlencoded" in content_type:
            # 表单数据
            form_data = await request.form()
            return dict(form_data)
        else:
            # 其他格式，尝试解析为文本
            body = await request.body()
            if body:
                body_str = body.decode('utf-8')
                # 尝试解析为查询字符串格式
                try:
                    from urllib.parse import parse_qs
                    parsed = parse_qs(body_str)
                    # 将列表值转换为单个值
                    return {k: v[0] if isinstance(v, list) and len(v) == 1 else v
                           for k, v in parsed.items()}
                except:
                    return {"raw_body": body_str}
            else:
                return {}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"请求数据解析失败: {str(e)}"
        )


@router.get("/configs", response_model=ApiResponse, summary="获取支付配置列表")
async def get_payment_configs(
    environment: str = "production",
    include_sensitive: bool = False,
    current_user: dict = Depends(get_current_admin_user),
    config_service: PaymentConfigService = Depends(get_payment_config_service)
):
    """
    获取支付配置列表
    
    - **environment**: 环境（production/test）
    - **include_sensitive**: 是否包含敏感信息（需要管理员权限）
    """
    try:
        # 只有超级管理员才能查看敏感信息
        if include_sensitive and current_user.get('user_type') != 'super_admin':
            include_sensitive = False
        
        result = config_service.get_all_configs(environment, include_sensitive)
        
        if result.success:
            return ApiResponse(success=True, data=result.data)
        else:
            return ApiResponse(success=False, error=result.error)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取支付配置失败: {str(e)}"
        )


@router.get("/configs/{config_id}", response_model=ApiResponse, summary="获取单个支付配置")
async def get_payment_config(
    config_id: int,
    include_sensitive: bool = False,
    current_user: dict = Depends(get_current_admin_user),
    config_service: PaymentConfigService = Depends(get_payment_config_service)
):
    """
    获取单个支付配置
    
    - **config_id**: 配置ID
    - **include_sensitive**: 是否包含敏感信息（需要管理员权限）
    """
    try:
        # 只有超级管理员才能查看敏感信息
        if include_sensitive and current_user.get('user_type') != 'super_admin':
            include_sensitive = False
        
        result = config_service.get_config_by_id(config_id, include_sensitive)
        
        if result.success:
            return ApiResponse(success=True, data=result.data)
        else:
            return ApiResponse(success=False, error=result.error)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取支付配置失败: {str(e)}"
        )


@router.post("/configs", response_model=ApiResponse, summary="创建支付配置")
async def create_payment_config(
    config_data: PaymentConfigCreate,
    current_user: dict = Depends(get_current_admin_user),
    config_service: PaymentConfigService = Depends(get_payment_config_service)
):
    """
    创建支付配置
    
    需要管理员权限
    """
    try:
        result = config_service.create_config(
            config_data.dict(),
            operator_id=current_user.get('id')
        )
        
        if result.success:
            return ApiResponse(success=True, data=result.data)
        else:
            return ApiResponse(success=False, error=result.error)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建支付配置失败: {str(e)}"
        )


@router.put("/configs/{config_id}", response_model=ApiResponse, summary="更新支付配置")
async def update_payment_config(
    config_id: int,
    config_data: PaymentConfigUpdate,
    current_user: dict = Depends(get_current_admin_user),
    config_service: PaymentConfigService = Depends(get_payment_config_service)
):
    """
    更新支付配置
    
    需要管理员权限
    """
    try:
        # 只更新提供的字段
        update_data = {k: v for k, v in config_data.dict().items() if v is not None}
        
        result = config_service.update_config(
            config_id,
            update_data,
            operator_id=current_user.get('id')
        )
        
        if result.success:
            return ApiResponse(success=True, data=result.data)
        else:
            return ApiResponse(success=False, error=result.error)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新支付配置失败: {str(e)}"
        )


@router.delete("/configs/{config_id}", response_model=ApiResponse, summary="删除支付配置")
async def delete_payment_config(
    config_id: int,
    current_user: dict = Depends(get_current_admin_user),
    config_service: PaymentConfigService = Depends(get_payment_config_service)
):
    """
    删除支付配置
    
    需要管理员权限
    """
    try:
        result = config_service.delete_config(
            config_id,
            operator_id=current_user.get('id')
        )
        
        if result.success:
            return ApiResponse(success=True, data=result.data)
        else:
            return ApiResponse(success=False, error=result.error)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除支付配置失败: {str(e)}"
        )


@router.post("/configs/{config_id}/test", response_model=ApiResponse, summary="测试支付配置")
async def test_payment_config(
    config_id: int,
    current_user: dict = Depends(get_current_admin_user),
    config_service: PaymentConfigService = Depends(get_payment_config_service)
):
    """
    测试支付配置连通性
    
    需要管理员权限
    """
    try:
        result = config_service.test_config(config_id)
        
        if result.success:
            return ApiResponse(success=True, data=result.data)
        else:
            return ApiResponse(success=False, error=result.error)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试支付配置失败: {str(e)}"
        )


@router.get("/templates", response_model=ApiResponse, summary="获取支付配置模板")
async def get_payment_templates(
    current_user: dict = Depends(get_current_admin_user),
    config_service: PaymentConfigService = Depends(get_payment_config_service)
):
    """
    获取支付提供商配置模板
    
    需要管理员权限
    """
    try:
        result = config_service.get_provider_templates()
        
        if result.success:
            return ApiResponse(success=True, data=result.data)
        else:
            return ApiResponse(success=False, error=result.error)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置模板失败: {str(e)}"
        )


@router.get("/providers/{provider_code}/form", response_model=ApiResponse, summary="获取支付提供商表单配置")
async def get_provider_form(
    provider_code: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取支付提供商的表单配置
    
    需要管理员权限
    """
    try:
        from ...modules.payment.payment_provider_factory import PaymentProviderFactory
        
        # 创建提供商实例获取表单配置
        provider = PaymentProviderFactory.create_provider(provider_code, {})
        
        if not provider:
            return ApiResponse(success=False, error=f"不支持的支付提供商: {provider_code}")
        
        form_config = provider.form()
        return ApiResponse(success=True, data=form_config)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取表单配置失败: {str(e)}"
        )


# 支付集成相关端点
@router.get("/methods", response_model=ApiResponse, summary="获取可用支付方式")
async def get_payment_methods(
    environment: str = "production",
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    获取可用的支付方式（公开端点，无需认证）

    - **environment**: 环境（production/test）
    """
    try:
        from ...modules.payment.payment_integration_service import PaymentIntegrationService

        integration_service = PaymentIntegrationService(db_manager)
        result = integration_service.get_available_payment_methods(environment)

        if result.success:
            return ApiResponse(success=True, data=result.data)
        else:
            return ApiResponse(success=False, error=result.error)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取支付方式失败: {str(e)}"
        )


@router.post("/orders", response_model=ApiResponse, summary="创建支付订单")
async def create_payment_order(
    order_data: dict,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    创建支付订单

    需要用户登录

    请求参数:
    - amount: 支付金额
    - description: 订单描述（可选，默认使用套餐的product_name）
    - payment_method_id: 支付方式ID（可选）
    - package_id: 充值套餐ID（可选，如果提供则使用套餐的product_name）
    """
    try:
        from ...modules.payment.payment_integration_service import PaymentIntegrationService
        from ...modules.sql.models.recharge_package_models import RechargePackage

        integration_service = PaymentIntegrationService(db_manager)

        # JWT token中的用户ID字段是 user_id
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的用户令牌"
            )

        # 获取订单描述
        description = order_data.get('description', '商城币充值')
        package_id = order_data.get('package_id')

        print("[INFO] 创建订单:")
        print(f"   package_id: {package_id}")
        print(f"   description (原始): {description}")

        # 如果提供了package_id，从套餐中获取product_name
        if package_id:
            with db_manager.get_db_session() as session:
                package = session.query(RechargePackage).filter(
                    RechargePackage.id == package_id
                ).first()

                if package:
                    print(f"   package.name: {package.name}")
                    print(f"   package.product_name: {package.product_name}")
                    if package.product_name:
                        description = package.product_name
                        print(f"   description (更新后): {description}")
                else:
                    print("   [WARN] 套餐不存在")

        result = integration_service.create_payment_order(
            user_id=user_id,
            amount=order_data.get('amount'),
            description=description,
            payment_method_id=order_data.get('payment_method_id'),
            package_id=package_id  # 传递套餐ID
        )

        if result.success:
            return ApiResponse(success=True, data=result.data)
        else:
            return ApiResponse(success=False, error=result.error)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建支付订单失败: {str(e)}"
        )


@router.get("/statistics", response_model=ApiResponse, summary="获取支付统计")
async def get_payment_statistics(
    user_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    获取支付统计信息

    - **user_id**: 用户ID（管理员可查看其他用户，普通用户只能查看自己）
    """
    try:
        from ...modules.payment.payment_integration_service import PaymentIntegrationService

        # 获取当前用户ID
        current_user_id = current_user.get('user_id') or current_user.get('id')
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的用户令牌"
            )

        # 权限检查
        if user_id and user_id != current_user_id:
            if current_user.get('user_type') not in ['admin', 'super_admin']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权查看其他用户的统计信息"
                )

        # 如果没有指定user_id，普通用户查看自己的，管理员查看全局的
        if not user_id:
            if current_user.get('user_type') in ['admin', 'super_admin']:
                user_id = None  # 全局统计
            else:
                user_id = current_user_id  # 自己的统计

        integration_service = PaymentIntegrationService(db_manager)
        result = integration_service.get_payment_statistics(user_id)

        if result.success:
            return ApiResponse(success=True, data=result.data)
        else:
            return ApiResponse(success=False, error=result.error)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取支付统计失败: {str(e)}"
        )


# ===== 订单查询端点 =====

@router.get("/orders", response_model=ApiResponse, summary="获取订单列表")
async def get_order_list(
    page: int = 1,
    page_size: int = 10,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    获取订单列表（分页）

    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（默认10，最大100）
    - **status**: 订单状态筛选（pending/success/failed等）
    - **user_id**: 用户ID筛选（仅管理员可用）
    - **start_date**: 开始日期（格式：2025-09-30）
    - **end_date**: 结束日期（格式：2025-09-30）

    普通用户只能查看自己的订单，管理员可以查看所有订单
    """
    try:
        from bakend.modules.sql.models.payment_order_models import PaymentOrder
        from bakend.modules.payment.order_status_service import OrderStatusService
        from datetime import datetime

        # 获取当前用户ID
        current_user_id = current_user.get('user_id') or current_user.get('id')
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的用户令牌"
            )

        # 检查权限
        is_admin = current_user.get('user_type') in ['admin', 'super_admin']

        # 如果指定了user_id，检查权限
        if user_id is not None:
            if not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权查看其他用户的订单"
                )
            query_user_id = user_id
        else:
            # 普通用户只能查看自己的订单
            query_user_id = current_user_id if not is_admin else None

        # 创建订单状态服务
        status_service = OrderStatusService(db_manager)

        # 验证分页参数
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100

        with db_manager.get_db_session() as session:
            # 构建查询
            query = session.query(PaymentOrder)

            # 用户筛选
            if query_user_id is not None:
                query = query.filter(PaymentOrder.user_id == query_user_id)

            # 状态筛选
            if status:
                query = query.filter(PaymentOrder.status == status)

            # 日期筛选
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    query = query.filter(PaymentOrder.created_at >= start_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="开始日期格式错误，应为：YYYY-MM-DD"
                    )

            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    # 包含当天的所有时间
                    from datetime import timedelta
                    end_dt = end_dt + timedelta(days=1)
                    query = query.filter(PaymentOrder.created_at < end_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="结束日期格式错误，应为：YYYY-MM-DD"
                    )

            # 获取总数
            total = query.count()

            # 分页和排序
            orders = query.order_by(PaymentOrder.created_at.desc())\
                         .offset((page - 1) * page_size)\
                         .limit(page_size)\
                         .all()

            # 检查并更新每个订单的状态
            for order in orders:
                status_service.check_and_update_order_status(order, session)

            # 刷新订单对象以获取最新状态
            for order in orders:
                session.refresh(order)

            # 转换为字典列表
            order_list = []
            for order in orders:
                order_dict = {
                    'id': order.id,
                    'order_id': order.order_id,
                    'user_id': order.user_id,
                    'amount': float(order.amount),
                    'currency': order.currency,
                    'description': order.description,
                    'provider_code': order.provider_code,
                    'provider_name': order.provider_name,
                    'status': order.status,
                    'coins_added': order.coins_added,
                    'is_coins_added': order.is_coins_added,
                    'created_at': order.created_at.isoformat() if order.created_at else None,
                    'paid_at': order.paid_at.isoformat() if order.paid_at else None,
                    'expired_at': order.expired_at.isoformat() if order.expired_at else None
                }

                # 管理员可以看到更多信息
                if is_admin:
                    order_dict.update({
                        'platform_order_id': order.platform_order_id,
                        'platform_transaction_id': order.platform_transaction_id,
                        'callback_count': order.callback_count,
                        'last_callback_at': order.last_callback_at.isoformat() if order.last_callback_at else None
                    })

                order_list.append(order_dict)

            # 计算分页信息
            total_pages = (total + page_size - 1) // page_size

            return ApiResponse(success=True, data={
                'orders': order_list,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取订单列表失败: {str(e)}"
        )


@router.get("/orders/{order_id}", summary="查询订单状态")
async def get_order_status(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    查询订单状态

    - **order_id**: 订单号

    返回订单的详细信息，包括支付状态、商城币等
    """
    try:
        from bakend.modules.sql.models.payment_order_models import PaymentOrder
        from bakend.modules.payment.order_status_service import OrderStatusService

        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的用户令牌"
            )

        # 创建订单状态服务
        status_service = OrderStatusService(db_manager)

        with db_manager.get_db_session() as session:
            # 查询订单
            order = session.query(PaymentOrder).filter(
                PaymentOrder.order_id == order_id
            ).first()

            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="订单不存在"
                )

            # 检查订单所有权（管理员可以查看所有订单）
            if current_user.get('user_type') not in ['admin', 'super_admin'] and order.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权查看此订单"
                )

            # 检查并更新订单状态
            status_service.check_and_update_order_status(order, session)
            session.refresh(order)

            # 返回订单信息
            return ApiResponse(success=True, data={
                'order_id': order.order_id,
                'user_id': order.user_id,
                'amount': float(order.amount),
                'currency': order.currency,
                'description': order.description,
                'provider_name': order.provider_name,
                'status': order.status,
                'coins_added': order.coins_added,
                'is_coins_added': order.is_coins_added,
                'paid_at': order.paid_at.isoformat() if order.paid_at else None,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'expired_at': order.expired_at.isoformat() if order.expired_at else None
            })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询订单失败: {str(e)}"
        )


@router.post("/orders/{order_id}/cancel", response_model=ApiResponse, summary="取消订单")
async def cancel_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    取消订单

    - **order_id**: 订单号

    只能取消待支付和处理中的订单
    """
    try:
        from bakend.modules.payment.order_status_service import OrderStatusService

        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的用户令牌"
            )

        # 创建订单状态服务
        status_service = OrderStatusService(db_manager)

        # 检查订单所有权
        with db_manager.get_db_session() as session:
            from bakend.modules.sql.models.payment_order_models import PaymentOrder

            order = session.query(PaymentOrder).filter(
                PaymentOrder.order_id == order_id
            ).first()

            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="订单不存在"
                )

            # 检查权限
            is_admin = current_user.get('user_type') in ['admin', 'super_admin']
            if not is_admin and order.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权取消此订单"
                )

        # 取消订单
        success = status_service.cancel_order(order_id)

        if success:
            return ApiResponse(success=True, data={'message': '订单已取消'})
        else:
            return ApiResponse(success=False, error='订单无法取消（可能已支付或已取消）')

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消订单失败: {str(e)}"
        )


@router.post("/orders/batch-update-status", response_model=ApiResponse, summary="批量更新过期订单状态")
async def batch_update_expired_orders(
    current_user: dict = Depends(get_current_admin_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    批量更新过期订单状态（仅管理员）

    将所有过期的待支付订单标记为已过期
    """
    try:
        from bakend.modules.payment.order_status_service import OrderStatusService

        status_service = OrderStatusService(db_manager)
        updated_count = status_service.batch_update_expired_orders(limit=1000)

        return ApiResponse(success=True, data={
            'message': f'已更新 {updated_count} 个过期订单',
            'updated_count': updated_count
        })

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新失败: {str(e)}"
        )


# ===== 支付回调处理端点 =====

@router.post("/notify/{provider_code}", summary="支付回调通知")
async def payment_notify(
    provider_code: str,
    request: Request,
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    处理支付平台的异步通知回调

    - **provider_code**: 支付提供商代码 (alipay/epay/wechat)

    此端点用于接收支付平台的服务器到服务器通知，
    验证签名后更新订单状态并增加用户商城币。
    """
    try:
        # 打印调试信息
        print(f"[INFO] 收到支付回调: provider_code={provider_code}")
        print(f"   URL: {request.url}")
        print(f"   Method: {request.method}")
        print(f"   Headers: {dict(request.headers)}")

        # 解析请求数据
        request_data = await parse_request_data(request)
        print(f"   Data: {request_data}")

        # 获取客户端IP
        client_ip = get_client_ip(request)

        # 处理回调
        with db_manager.get_db_session() as session:
            handler = PaymentCallbackHandler(session)
            result = await handler.handle_callback(
                provider_code=provider_code,
                callback_type="notify",
                request_data=request_data,
                client_ip=client_ip
            )

        # 打印处理结果
        print("[INFO] 回调处理结果:")
        print(f"   success: {result.success}")
        print(f"   message: {result.message}")
        print(f"   response_status: {result.response_status}")
        print(f"   response_body: {result.response_body}")

        # 根据支付平台返回相应格式的响应
        if provider_code == 'alipay':
            return PlainTextResponse(
                content=result.response_body,
                status_code=result.response_status
            )
        elif provider_code == 'epay':
            return PlainTextResponse(
                content=result.response_body,
                status_code=result.response_status
            )
        else:
            return JSONResponse(
                content={"message": result.response_body},
                status_code=result.response_status
            )

    except Exception as e:
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"支付回调处理异常: {e}", exc_info=True)

        # 返回失败响应
        if provider_code == 'alipay':
            return PlainTextResponse(content="fail", status_code=500)
        elif provider_code == 'epay':
            return PlainTextResponse(content="fail", status_code=500)
        else:
            return JSONResponse(
                content={"error": "系统异常"},
                status_code=500
            )


@router.get("/return/{provider_code}", summary="支付页面跳转回调")
async def payment_return(
    provider_code: str,
    request: Request,
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    处理支付平台的页面跳转回调

    - **provider_code**: 支付提供商代码 (alipay/epay/wechat)

    此端点用于处理用户支付完成后的页面跳转，
    通常用于显示支付结果页面。
    """
    try:
        # 解析请求数据
        request_data = dict(request.query_params)
        request_data.update({
            "_method": request.method,
            "_url": str(request.url),
            "_headers": dict(request.headers),
            "_client_ip": get_client_ip(request)
        })

        # 获取客户端IP
        client_ip = get_client_ip(request)

        # 处理回调
        with db_manager.get_db_session() as session:
            handler = PaymentCallbackHandler(session)
            result = await handler.handle_callback(
                provider_code=provider_code,
                callback_type="return",
                request_data=request_data,
                client_ip=client_ip
            )

        # 返回支付结果页面
        if result.success:
            return JSONResponse(
                content={
                    "success": True,
                    "message": "支付成功",
                    "data": result.data,
                    "redirect_url": "/payment/success"
                }
            )
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "message": result.message,
                    "redirect_url": "/payment/failed"
                }
            )

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"支付跳转回调处理异常: {e}", exc_info=True)

        return JSONResponse(
            content={
                "success": False,
                "message": "系统异常",
                "redirect_url": "/payment/error"
            },
            status_code=500
        )


@router.get("/status/{order_id}", summary="查询订单状态")
async def get_payment_status(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    查询支付订单状态

    - **order_id**: 订单号

    用于前端轮询查询订单支付状态。
    """
    try:
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的用户令牌"
            )

        with db_manager.get_db_session() as session:
            from ...modules.sql.models.payment_order_models import PaymentOrder

            order = session.query(PaymentOrder).filter(
                PaymentOrder.order_id == order_id
            ).first()

            if not order:
                raise HTTPException(
                    status_code=404,
                    detail="订单不存在"
                )

            is_admin = current_user.get('user_type') in ['admin', 'super_admin']
            if not is_admin and order.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权查看此订单"
                )

            return JSONResponse(
                content={
                    "success": True,
                    "data": {
                        "order_id": order.order_id,
                        "status": order.status,
                        "amount": float(order.amount),
                        "provider_name": order.provider_name,
                        "created_at": order.created_at.isoformat() if order.created_at else None,
                        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                        "is_success": order.is_success(),
                        "is_failed": order.is_failed(),
                        "coins_added": order.coins_added if order.is_coins_added else 0
                    }
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"查询订单状态异常: {e}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail="查询订单状态失败"
        )


@router.get("/callback/logs/{order_id}", summary="查询回调日志")
async def get_callback_logs(
    order_id: str,
    current_user: dict = Depends(get_current_admin_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    查询订单的回调处理日志

    - **order_id**: 订单号

    用于调试和监控回调处理情况。
    """
    _ = current_user
    try:
        with db_manager.get_db_session() as session:
            from ...modules.sql.models.payment_order_models import PaymentCallback

            callbacks = session.query(PaymentCallback).filter(
                PaymentCallback.order_id == order_id
            ).order_by(PaymentCallback.created_at.desc()).all()

            callback_logs = []
            for callback in callbacks:
                callback_logs.append({
                    "id": callback.id,
                    "callback_type": callback.callback_type,
                    "provider_code": callback.provider_code,
                    "request_method": callback.request_method,
                    "request_ip": callback.request_ip,
                    "is_valid": callback.is_valid,
                    "processing_status": callback.processing_status,
                    "error_message": callback.error_message,
                    "response_status": callback.response_status,
                    "processing_time": callback.processing_time,
                    "created_at": callback.created_at.isoformat() if callback.created_at else None
                })

            return JSONResponse(
                content={
                    "success": True,
                    "data": {
                        "order_id": order_id,
                        "callback_count": len(callback_logs),
                        "callbacks": callback_logs
                    }
                }
            )

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"查询回调日志异常: {e}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail="查询回调日志失败"
        )
