"""
Items API - 物品管理API系统
"""

from typing import Optional, List, Any
from fastapi import APIRouter, HTTPException, status, Query, File, UploadFile, Depends
from pydantic import BaseModel, Field, field_validator
import os
import uuid
import json
import hashlib
import base64
import time
from pathlib import Path
from PIL import Image

from ...modules.sql.services.category_service import ItemCategoryService
from ...modules.sql.services.item_service import ItemManagementService
from ...modules.sql.services.service_result import ServiceErrorType

# 导入JWT认证依赖
from ...modules.auth.jwt_handler import jwt_bearer, require_admin, require_super_admin
from typing import Dict, Any

# 定义API响应模型
class ApiResponse(BaseModel):
    """通用API响应模型"""
    success: bool
    message: str
    data: Optional[Any] = None

router = APIRouter(prefix="/api/v1/items", tags=["Items"])

# ===== Pydantic 模型 =====

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="类目名称")
    description: Optional[str] = Field(None, max_length=500, description="类目描述")

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="类目名称")
    description: Optional[str] = Field(None, max_length=500, description="类目描述")
    is_active: Optional[bool] = Field(None, description="是否激活")

class SubCategoryCreate(BaseModel):
    category_id: int = Field(..., gt=0, description="父类目ID")
    name: str = Field(..., min_length=1, max_length=100, description="子类目名称")
    description: Optional[str] = Field(None, max_length=500, description="子类目描述")

class SubCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="子类目名称")
    description: Optional[str] = Field(None, max_length=500, description="子类目描述")
    is_active: Optional[bool] = Field(None, description="是否激活")

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="物品名称")
    item_code: str = Field(..., min_length=1, max_length=2000, description="物品代码，支持JSON格式")
    category_id: int = Field(..., gt=0, description="类目ID")
    subcategory_id: Optional[int] = Field(None, gt=0, description="子类目ID")
    price: float = Field(0.0, ge=0, description="价格")
    stock: int = Field(0, ge=-1, description="库存（-1表示无限库存）")
    image_url: Optional[str] = Field(None, max_length=500, description="图片URL")
    description: Optional[str] = Field(None, max_length=1000, description="物品描述")

    @field_validator('item_code')
    @classmethod
    def validate_item_code(cls, v):
        """验证物品代码，允许JSON数组或JSON对象格式"""
        if v and v.strip().startswith('[') and v.strip().endswith(']'):
            # JSON数组格式
            try:
                parsed = json.loads(v)
                if not isinstance(parsed, list):
                    raise ValueError('JSON数组格式错误')

                # 验证数组中的每个元素都是有效的命令对象
                for i, item in enumerate(parsed):
                    if not isinstance(item, dict):
                        raise ValueError(f'数组第{i+1}个元素必须是JSON对象')
                    if 'command' not in item or 'item' not in item:
                        raise ValueError(f'数组第{i+1}个元素必须包含command和item字段')

            except json.JSONDecodeError:
                raise ValueError('物品代码包含无效的JSON格式')
        elif v and v.strip().startswith('{') and v.strip().endswith('}'):
            # JSON对象格式
            try:
                parsed = json.loads(v)
                if not isinstance(parsed, dict):
                    raise ValueError('JSON对象格式错误')

                # 验证对象包含必需字段
                if 'command' not in parsed or 'item' not in parsed:
                    raise ValueError('JSON对象必须包含command和item字段')

            except json.JSONDecodeError:
                raise ValueError('物品代码包含无效的JSON格式')
        return v

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="物品名称")
    item_code: Optional[str] = Field(None, min_length=1, max_length=2000, description="物品代码，支持JSON格式")
    category_id: Optional[int] = Field(None, gt=0, description="类目ID")
    subcategory_id: Optional[int] = Field(None, gt=0, description="子类目ID")
    price: Optional[float] = Field(None, ge=0, description="价格")
    stock: Optional[int] = Field(None, ge=-1, description="库存（-1表示无限库存）")
    image_url: Optional[str] = Field(None, max_length=500, description="图片URL")
    description: Optional[str] = Field(None, max_length=1000, description="物品描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class ItemSortUpdate(BaseModel):
    """物品排序更新模型"""
    id: int = Field(..., gt=0, description="物品ID")
    sort_order: int = Field(..., description="排序值")


class ItemsSortRequest(BaseModel):
    """批量物品排序请求模型"""
    items: List[ItemSortUpdate] = Field(..., min_items=1, description="物品排序更新列表")
    category_id: Optional[int] = Field(None, gt=0, description="可选的分类ID，如果提供则只更新该分类下的物品")


class ItemSortResetRequest(BaseModel):
    """物品排序重置请求模型"""
    category_id: Optional[int] = Field(None, gt=0, description="可选的分类ID")
    subcategory_id: Optional[int] = Field(None, gt=0, description="可选的子分类ID")
    start_value: int = Field(100, ge=0, description="起始排序值")
    interval: int = Field(100, gt=0, description="排序值间隔")



class StockUpdate(BaseModel):
    stock_change: int = Field(..., description="库存变化量")
    operation: str = Field("set", pattern="^(set|add|subtract)$", description="操作类型: set(设置), add(增加), subtract(减少)")

# ===== 错误处理函数 =====

def handle_service_error(service_result):
    """处理服务层错误并转换为HTTP异常"""
    # 获取错误类型和消息
    error_type = service_result.get_error_type() if hasattr(service_result, 'get_error_type') else None
    message = service_result.message if hasattr(service_result, 'message') else "未知错误"

    # 如果没有错误类型，尝试从error对象获取
    if not error_type and hasattr(service_result, 'error') and service_result.error:
        error_type = service_result.error.error_type
        message = service_result.error.message

    if error_type == ServiceErrorType.VALIDATION_ERROR:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    elif error_type == ServiceErrorType.NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    elif error_type == ServiceErrorType.DUPLICATE_ENTRY:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)
    elif error_type == ServiceErrorType.ALREADY_EXISTS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)
    elif error_type == ServiceErrorType.DATABASE_ERROR:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
    elif error_type == ServiceErrorType.CATEGORY_INACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    elif error_type == ServiceErrorType.SUBCATEGORY_INACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message or "未知错误")

# ===== 类目管理API =====

@router.post("/categories", response_model=ApiResponse, summary="创建类目")
async def create_category(category: CategoryCreate, current_user: Dict[str, Any] = Depends(require_admin)):
    """创建新的物品类目"""
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    service = ItemCategoryService(db_manager)
    result = service.create_item_category(
        name=category.name,
        description=category.description
    )
    
    if not result.success:
        handle_service_error(result)
    
    return ApiResponse(
        success=True,
        message="类目创建成功",
        data=result.data
    )

@router.get("/categories/{category_id}", response_model=ApiResponse, summary="获取类目详情")
async def get_category(category_id: int, current_user: Dict[str, Any] = Depends(jwt_bearer)):
    """获取单个类目的详细信息"""
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    service = ItemCategoryService(db_manager)
    result = service.get_item_category(category_id)

    if not result.success:
        handle_service_error(result)

    return ApiResponse(
        success=True,
        message="获取类目成功",
        data=result.data
    )

@router.get("/categories", response_model=ApiResponse, summary="获取类目列表")
async def list_categories(
    include_inactive: bool = Query(False, description="是否包含非活跃类目"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    current_user: Dict[str, Any] = Depends(jwt_bearer)
):
    """获取类目列表"""
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    service = ItemCategoryService(db_manager)
    result = service.list_item_categories(
        include_inactive=include_inactive,
        page=page,
        page_size=page_size
    )

    if not result.success:
        handle_service_error(result)

    return ApiResponse(
        success=True,
        message="获取类目列表成功",
        data=result.data
    )

@router.put("/categories/{category_id}", response_model=ApiResponse, summary="更新类目")
async def update_category(category_id: int, category: CategoryUpdate, current_user: Dict[str, Any] = Depends(require_admin)):
    """更新类目信息"""
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    service = ItemCategoryService(db_manager)

    # 构建更新数据
    update_data = {}
    if category.name is not None:
        update_data['name'] = category.name
    if category.description is not None:
        update_data['description'] = category.description
    if category.is_active is not None:
        update_data['is_active'] = category.is_active
    
    result = service.update_item_category(category_id, **update_data)
    
    if not result.success:
        handle_service_error(result)
    
    return ApiResponse(
        success=True,
        message="类目更新成功",
        data=result.data
    )

@router.delete("/categories/{category_id}", response_model=ApiResponse, summary="删除类目")
async def delete_category(
    category_id: int,
    soft_delete: bool = Query(True, description="是否软删除"),
    force: bool = Query(False, description="是否强制删除"),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """删除类目"""
    from ..main import get_global_db_manager
    db_manager = get_global_db_manager()
    service = ItemCategoryService(db_manager)
    result = service.delete_item_category(category_id, soft_delete=soft_delete, force=force)
    
    if not result.success:
        handle_service_error(result)
    
    return ApiResponse(
        success=True,
        message="类目删除成功",
        data=result.data
    )

# ===== 子类目管理API =====

@router.post("/subcategories", response_model=ApiResponse, summary="创建子类目")
async def create_subcategory(subcategory: SubCategoryCreate, current_user: Dict[str, Any] = Depends(require_admin)):
    """创建新的子类目"""
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    service = ItemCategoryService(db_manager)
    result = service.create_item_subcategory(
        category_id=subcategory.category_id,
        name=subcategory.name,
        description=subcategory.description
    )
    
    if not result.success:
        handle_service_error(result)
    
    return ApiResponse(
        success=True,
        message="子类目创建成功",
        data=result.data
    )

@router.get("/subcategories/{subcategory_id}", response_model=ApiResponse, summary="获取子类目详情")
async def get_subcategory(subcategory_id: int, current_user: Dict[str, Any] = Depends(jwt_bearer)):
    """获取单个子类目的详细信息"""
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    service = ItemCategoryService(db_manager)
    result = service.get_item_subcategory(subcategory_id)
    
    if not result.success:
        handle_service_error(result)
    
    return ApiResponse(
        success=True,
        message="获取子类目成功",
        data=result.data
    )

@router.get("/subcategories", response_model=ApiResponse, summary="获取子类目列表")
async def list_subcategories(
    category_id: Optional[int] = Query(None, description="父类目ID"),
    include_inactive: bool = Query(False, description="是否包含非活跃子类目"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    current_user: Dict[str, Any] = Depends(jwt_bearer)
):
    """获取子类目列表"""
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    service = ItemCategoryService(db_manager)
    result = service.list_item_subcategories(
        category_id=category_id,
        include_inactive=include_inactive,
        page=page,
        page_size=page_size
    )
    
    if not result.success:
        handle_service_error(result)
    
    return ApiResponse(
        success=True,
        message="获取子类目列表成功",
        data=result.data
    )

@router.put("/subcategories/{subcategory_id}", response_model=ApiResponse, summary="更新子类目")
async def update_subcategory(subcategory_id: int, subcategory: SubCategoryUpdate, current_user: Dict[str, Any] = Depends(require_admin)):
    """更新子类目信息"""
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    service = ItemCategoryService(db_manager)
    
    # 构建更新数据
    update_data = {}
    if subcategory.name is not None:
        update_data['name'] = subcategory.name
    if subcategory.description is not None:
        update_data['description'] = subcategory.description
    if subcategory.is_active is not None:
        update_data['is_active'] = subcategory.is_active
    
    result = service.update_item_subcategory(subcategory_id, **update_data)
    
    if not result.success:
        handle_service_error(result)
    
    return ApiResponse(
        success=True,
        message="子类目更新成功",
        data=result.data
    )

@router.delete("/subcategories/{subcategory_id}", response_model=ApiResponse, summary="删除子类目")
async def delete_subcategory(
    subcategory_id: int,
    soft_delete: bool = Query(True, description="是否软删除"),
    force: bool = Query(False, description="是否强制删除"),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """删除子类目"""
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    service = ItemCategoryService(db_manager)
    result = service.delete_item_subcategory(subcategory_id, soft_delete=soft_delete, force=force)
    
    if not result.success:
        handle_service_error(result)
    
    return ApiResponse(
        success=True,
        message="子类目删除成功",
        data=result.data
    )

# ===== 物品管理API =====

@router.post("/items", response_model=ApiResponse, summary="创建物品")
async def create_item(item: ItemCreate, current_user: Dict[str, Any] = Depends(require_admin)):
    """创建新的物品"""
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    service = ItemManagementService(db_manager)
    result = service.create_item(
        name=item.name,
        item_code=item.item_code,
        category_id=item.category_id,
        subcategory_id=item.subcategory_id,
        price=item.price,
        stock=item.stock,
        image_url=item.image_url,
        description=item.description
    )

    if not result.success:
        handle_service_error(result)

    return ApiResponse(
        success=True,
        message="物品创建成功",
        data=result.data
    )

@router.get("/items/search", response_model=ApiResponse, summary="搜索物品")
async def search_items(
    keyword: str = Query(..., description="搜索关键词"),
    category_id: Optional[int] = Query(None, description="类目ID"),
    subcategory_id: Optional[int] = Query(None, description="子类目ID"),
    include_inactive: bool = Query(False, description="是否包含非活跃物品"),
    sort_by: str = Query("id", description="排序字段 (sort_order/name/price/created_at/id)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    current_user: Dict[str, Any] = Depends(jwt_bearer)
):
    """根据关键词搜索物品"""
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    service = ItemManagementService(db_manager)
    result = service.search_items_by_keyword(
        keyword=keyword,
        category_id=category_id,
        subcategory_id=subcategory_id,
        include_inactive=include_inactive,
        sort_by=sort_by,
        page=page,
        page_size=page_size
    )

    if not result.success:
        handle_service_error(result)

    return ApiResponse(
        success=True,
        message="搜索物品成功",
        data=result.data
    )

@router.get("/items/{item_id}", response_model=ApiResponse, summary="获取物品详情")
async def get_item(item_id: int, current_user: Dict[str, Any] = Depends(jwt_bearer)):
    """获取单个物品的详细信息"""
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    service = ItemManagementService(db_manager)
    result = service.get_item_details(item_id)

    if not result.success:
        handle_service_error(result)

    return ApiResponse(
        success=True,
        message="获取物品成功",
        data=result.data
    )

@router.get("/items", response_model=ApiResponse, summary="获取物品列表")
async def list_items(
    category_id: Optional[int] = Query(None, description="类目ID"),
    subcategory_id: Optional[int] = Query(None, description="子类目ID"),
    include_inactive: bool = Query(False, description="是否包含非活跃物品"),
    include_out_of_stock: bool = Query(True, description="是否包含缺货物品"),
    sort_by: str = Query("id", description="排序字段 (sort_order/name/price/created_at/id)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    current_user: Dict[str, Any] = Depends(jwt_bearer)
):
    """获取物品列表"""
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    service = ItemManagementService(db_manager)
    result = service.get_items_list(
        category_id=category_id,
        subcategory_id=subcategory_id,
        include_inactive=include_inactive,
        include_out_of_stock=include_out_of_stock,
        sort_by=sort_by,
        page=page,
        page_size=page_size
    )

    if not result.success:
        handle_service_error(result)

    return ApiResponse(
        success=True,
        message="获取物品列表成功",
        data=result.data
    )

# ===== 物品排序管理API =====

@router.put("/items/batch-sort", response_model=ApiResponse, summary="批量更新物品排序")
async def update_items_sort(
    request: ItemsSortRequest,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """批量更新物品排序（仅管理员）"""
    from ..main import get_global_db_manager
    from bakend.modules.sql.services.item_sort_service import ItemSortService

    db_manager = get_global_db_manager()
    sort_service = ItemSortService(db_manager)

    # 转换请求数据
    sort_updates = [
        {"id": item.id, "sort_order": item.sort_order}
        for item in request.items
    ]

    result = sort_service.batch_update_item_sort(
        sort_updates=sort_updates,
        category_id=request.category_id
    )

    if not result.success:
        handle_service_error(result)

    return ApiResponse(
        success=True,
        message="物品排序更新成功",
        data=result.data
    )


@router.post("/items/sort/reset", response_model=ApiResponse, summary="重置物品排序")
async def reset_items_sort(
    request: ItemSortResetRequest,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """重置物品排序（仅管理员）"""
    from ..main import get_global_db_manager
    from bakend.modules.sql.services.item_sort_service import ItemSortService

    db_manager = get_global_db_manager()
    sort_service = ItemSortService(db_manager)

    result = sort_service.auto_assign_sort_order(
        category_id=request.category_id,
        start_value=request.start_value,
        interval=request.interval
    )

    if not result.success:
        handle_service_error(result)

    return ApiResponse(
        success=True,
        message="物品排序重置成功",
        data=result.data
    )


@router.get("/items/sort/info", response_model=ApiResponse, summary="获取排序信息")
async def get_sort_info(
    category_id: Optional[int] = Query(None, description="分类ID"),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """获取物品排序信息（仅管理员）"""
    from ..main import get_global_db_manager
    from bakend.modules.sql.services.item_sort_service import ItemSortService

    db_manager = get_global_db_manager()
    sort_service = ItemSortService(db_manager)

    result = sort_service.get_sort_order_info(category_id=category_id)

    if not result.success:
        handle_service_error(result)

    return ApiResponse(
        success=True,
        message="获取排序信息成功",
        data=result.data
    )

@router.put("/items/{item_id}", response_model=ApiResponse, summary="更新物品")
async def update_item(item_id: int, item: ItemUpdate, current_user: Dict[str, Any] = Depends(require_admin)):
    """更新物品信息"""
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    service = ItemManagementService(db_manager)

    # 检查是否需要处理物品代码更改
    item_code_changed = item.item_code is not None
    old_item_code = None
    current_image_url = None

    if item_code_changed:
        # 获取当前物品信息
        current_item_result = service.get_item_details(item_id)
        if current_item_result.success and current_item_result.data:
            old_item_code = current_item_result.data.get('item_code')
            current_image_url = current_item_result.data.get('image_url')

    # 构建更新数据
    update_data = {}
    if item.name is not None:
        update_data['name'] = item.name
    if item.item_code is not None:
        update_data['item_code'] = item.item_code
    if item.category_id is not None:
        update_data['category_id'] = item.category_id
    if item.subcategory_id is not None:
        update_data['subcategory_id'] = item.subcategory_id
    if item.price is not None:
        update_data['price'] = item.price
    if item.stock is not None:
        update_data['stock'] = item.stock
    if item.image_url is not None:
        update_data['image_url'] = item.image_url
    if item.description is not None:
        update_data['description'] = item.description
    if item.is_active is not None:
        update_data['is_active'] = item.is_active

    # 如果物品代码被修改且有图片，处理图片重命名
    # 确保新的物品代码有效（不为None且不为空字符串）
    if (item_code_changed and old_item_code and current_image_url and
        item.item_code is not None and str(item.item_code).strip() and
        old_item_code != item.item_code):
        try:
            new_image_url = rename_item_image_files(old_item_code, item.item_code, current_image_url)
            if new_image_url and new_image_url != current_image_url:
                # 更新图片URL
                update_data['image_url'] = new_image_url
                print(f"物品代码更改，图片URL已更新: {current_image_url} -> {new_image_url}")
        except Exception as e:
            print(f"处理图片重命名时出错: {e}")
            # 继续执行更新，不因图片重命名失败而中断

    result = service.update_item_details(item_id, **update_data)

    if not result.success:
        handle_service_error(result)

    return ApiResponse(
        success=True,
        message="物品更新成功",
        data=result.data
    )

@router.delete("/items/{item_id}", response_model=ApiResponse, summary="删除物品")
async def delete_item(
    item_id: int,
    soft_delete: bool = Query(True, description="是否软删除"),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """删除物品"""
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    service = ItemManagementService(db_manager)

    # 如果是硬删除，先获取物品信息以便删除图片
    image_url = None
    if not soft_delete:
        item_result = service.get_item_details(item_id)
        if item_result.success and item_result.data:
            image_url = item_result.data.get('image_url')

    # 执行物品删除
    result = service.delete_item(item_id, soft_delete=soft_delete)

    if not result.success:
        handle_service_error(result)

    # 如果是硬删除且有图片，删除相关图片文件
    if not soft_delete and image_url:
        try:
            delete_success = delete_item_image_files(image_url)
            if delete_success:
                print(f"物品 {item_id} 的图片文件已删除")
            else:
                print(f"物品 {item_id} 的图片文件删除失败，但物品删除成功")
        except Exception as e:
            print(f"删除物品 {item_id} 的图片文件时出错: {e}")
            # 不因图片删除失败而影响物品删除的成功状态

    return ApiResponse(
        success=True,
        message="物品删除成功",
        data=result.data
    )



# ===== 数据库管理API =====

@router.post("/database/init", response_model=ApiResponse, summary="初始化数据库")
async def init_database(current_user: Dict[str, Any] = Depends(require_super_admin)):
    """初始化数据库"""
    try:
        from ..main import get_global_db_manager
        db_manager = get_global_db_manager()
        success = db_manager.init_database()

        if success:
            return ApiResponse(success=True, message="数据库初始化成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="数据库初始化失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库初始化时发生错误: {str(e)}"
        )

@router.get("/database/status", response_model=ApiResponse, summary="获取数据库状态")
async def get_database_status(current_user: Dict[str, Any] = Depends(require_admin)):
    """获取数据库状态"""
    try:
        from ..main import get_global_db_manager
        db_manager = get_global_db_manager()

        status_info = db_manager.get_database_info()

        return ApiResponse(success=True, message="获取数据库状态成功", data=status_info)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据库状态时发生错误: {str(e)}"
        )

# ===== 图片上传相关辅助函数 =====

def is_json_item_code(item_code: str) -> bool:
    """检查物品代码是否为JSON格式（数组或对象）"""
    if not item_code:
        return False

    item_code = item_code.strip()
    return (item_code.startswith('[') and item_code.endswith(']')) or \
           (item_code.startswith('{') and item_code.endswith('}'))

def generate_item_code_hash(item_code: str, add_timestamp: bool = False) -> str:
    """为JSON格式的物品代码生成唯一哈希编码（支持数组和对象格式）"""
    if not is_json_item_code(item_code):
        return item_code

    # 构建哈希输入，包含物品代码
    hash_input = item_code

    # 如果需要，添加时间戳以增加唯一性
    if add_timestamp:
        timestamp = str(int(time.time() * 1000))  # 毫秒级时间戳
        hash_input = f"{item_code}_{timestamp}"

    # 使用SHA256生成哈希
    hash_object = hashlib.sha256(hash_input.encode('utf-8'))
    hash_hex = hash_object.hexdigest()

    # 取前16位作为短哈希（增加长度以减少冲突），并添加前缀
    short_hash = hash_hex[:16]
    return f"item_{short_hash}"

def is_valid_image_file(filename: str) -> bool:
    """验证文件是否为有效的图片格式"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    return Path(filename).suffix.lower() in valid_extensions

def validate_filename(filename: str) -> bool:
    """验证文件名是否安全（防止路径遍历攻击）"""
    if not filename:
        return False

    # 检查是否包含危险字符
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        if char in filename:
            return False

    # 检查文件名长度
    if len(filename) > 255:
        return False

    return True

async def validate_file_content(file: UploadFile) -> bool:
    """验证文件内容是否为真实的图片文件"""
    try:
        # 读取文件头部字节来验证文件类型
        content = await file.read(32)  # 读取前32字节
        await file.seek(0)  # 重置文件指针

        # 检查常见图片格式的文件头
        if content.startswith(b'\xff\xd8\xff'):  # JPEG
            return True
        elif content.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
            return True
        elif content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):  # GIF
            return True
        elif content.startswith(b'RIFF') and b'WEBP' in content[:12]:  # WebP
            return True
        elif content.startswith(b'BM'):  # BMP
            return True

        return False
    except Exception:
        return False

def generate_unique_filename(item_code: str, original_filename: str, check_conflicts: bool = True) -> str:
    """根据物品代码生成文件名，确保唯一性"""
    # 获取文件扩展名
    file_extension = Path(original_filename).suffix.lower()

    # 如果是JSON格式的物品代码，生成唯一哈希编码
    if is_json_item_code(item_code):
        safe_code = generate_item_code_hash(item_code)
    else:
        # 普通字符串代码，清理特殊字符
        safe_code = "".join(c for c in item_code if c.isalnum() or c in '-_')
        # 如果清理后为空，使用哈希
        if not safe_code:
            safe_code = hashlib.md5(item_code.encode('utf-8')).hexdigest()[:12]

    # 生成基础文件名
    base_filename = f"{safe_code}{file_extension}"

    # 如果不需要检查冲突，直接返回
    if not check_conflicts:
        return base_filename

    # 检查文件是否已存在，如果存在则添加时间戳
    imgs_dir, thumbs_dir = get_upload_directory()
    file_path = imgs_dir / base_filename

    if file_path.exists():
        # 添加时间戳以避免冲突
        timestamp = str(int(time.time() * 1000))
        if is_json_item_code(item_code):
            safe_code = generate_item_code_hash(item_code, add_timestamp=True)
        else:
            safe_code = f"{safe_code}_{timestamp}"
        base_filename = f"{safe_code}{file_extension}"

    return base_filename

def generate_thumbnail_filename(item_code: str, original_filename: str, check_conflicts: bool = True) -> str:
    """根据物品代码生成缩略图文件名，确保唯一性"""
    # 获取文件扩展名
    file_extension = Path(original_filename).suffix.lower()

    # 如果是JSON格式的物品代码，生成唯一哈希编码
    if is_json_item_code(item_code):
        safe_code = generate_item_code_hash(item_code)
    else:
        # 普通字符串代码，清理特殊字符
        safe_code = "".join(c for c in item_code if c.isalnum() or c in '-_')
        # 如果清理后为空，使用哈希
        if not safe_code:
            safe_code = hashlib.md5(item_code.encode('utf-8')).hexdigest()[:12]

    # 生成基础缩略图文件名
    base_filename = f"{safe_code}-thumb{file_extension}"

    # 如果不需要检查冲突，直接返回
    if not check_conflicts:
        return base_filename

    # 检查文件是否已存在，如果存在则添加时间戳
    imgs_dir, thumbs_dir = get_upload_directory()
    file_path = thumbs_dir / base_filename

    if file_path.exists():
        # 添加时间戳以避免冲突
        timestamp = str(int(time.time() * 1000))
        if is_json_item_code(item_code):
            safe_code = generate_item_code_hash(item_code, add_timestamp=True)
        else:
            safe_code = f"{safe_code}_{timestamp}"
        base_filename = f"{safe_code}-thumb{file_extension}"

    return base_filename

def get_thumbnail_filename_from_original(original_filename: str) -> str:
    """从原始文件名推断对应的缩略图文件名"""
    file_path = Path(original_filename)
    name_without_ext = file_path.stem
    extension = file_path.suffix
    return f"{name_without_ext}-thumb{extension}"

def get_upload_directory() -> tuple[Path, Path]:
    """获取上传目录路径，返回(原图目录, 缩略图目录)"""
    # 获取项目根目录
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    imgs_dir = project_root / "public" / "images" / "items" / "imgs"
    thumbs_dir = project_root / "public" / "images" / "items" / "thumbs"

    # 确保目录存在
    imgs_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    return imgs_dir, thumbs_dir

async def save_uploaded_file(file: UploadFile, filename: str) -> str:
    """保存上传的文件并返回相对路径"""
    try:
        imgs_dir, thumbs_dir = get_upload_directory()
        file_path = imgs_dir / filename

        # 检查文件是否已存在
        if file_path.exists():
            raise ValueError(f"文件 {filename} 已存在")

        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            if not content:
                raise ValueError("文件内容为空")
            buffer.write(content)

        # 验证文件是否成功保存
        if not file_path.exists() or file_path.stat().st_size == 0:
            raise ValueError("文件保存失败")

        # 返回用于HTTP访问的相对路径
        return f"/static/images/items/imgs/{filename}"

    except Exception as e:
        # 如果保存失败，尝试清理可能创建的文件
        try:
            imgs_dir, thumbs_dir = get_upload_directory()
            file_path = imgs_dir / filename
            if file_path.exists():
                file_path.unlink()
        except:
            pass
        raise ValueError(f"保存文件失败: {str(e)}")

def create_thumbnail(original_path: Path, thumbnail_path: Path, size: tuple = (200, 200)) -> bool:
    """创建缩略图"""
    try:
        with Image.open(original_path) as img:
            # 转换为RGB模式（处理RGBA等格式）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 创建缩略图（保持宽高比）
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # 保存缩略图
            img.save(thumbnail_path, optimize=True, quality=85)

            return True
    except Exception as e:
        print(f"创建缩略图失败: {e}")
        return False

async def save_uploaded_file_with_thumbnail(file: UploadFile, filename: str, thumbnail_filename: str) -> tuple[str, Optional[str]]:
    """保存上传的文件和缩略图，返回原图和缩略图的相对路径"""
    try:
        imgs_dir, thumbs_dir = get_upload_directory()
        file_path = imgs_dir / filename
        thumbnail_path = thumbs_dir / thumbnail_filename

        # 如果文件已存在，将会被覆盖（允许更新物品图片）
        if file_path.exists():
            print(f"文件 {filename} 已存在，将被覆盖")
        if thumbnail_path.exists():
            print(f"缩略图文件 {thumbnail_filename} 已存在，将被覆盖")

        # 保存原图
        with open(file_path, "wb") as buffer:
            content = await file.read()
            if not content:
                raise ValueError("文件内容为空")
            buffer.write(content)

        # 验证原图是否成功保存
        if not file_path.exists() or file_path.stat().st_size == 0:
            raise ValueError("原图保存失败")

        # 生成缩略图
        if not create_thumbnail(file_path, thumbnail_path):
            # 缩略图生成失败，但不影响原图上传
            print(f"警告: 缩略图生成失败，但原图上传成功")
            thumbnail_url = None
        else:
            thumbnail_url = f"/static/images/items/thumbs/{thumbnail_filename}"

        # 返回用于HTTP访问的相对路径
        image_url = f"/static/images/items/imgs/{filename}"
        return image_url, thumbnail_url

    except Exception as e:
        # 如果保存失败，尝试清理可能创建的文件
        try:
            imgs_dir, thumbs_dir = get_upload_directory()
            file_path = imgs_dir / filename
            thumbnail_path = thumbs_dir / thumbnail_filename
            if file_path.exists():
                file_path.unlink()
            if thumbnail_path.exists():
                thumbnail_path.unlink()
        except:
            pass
        raise ValueError(f"保存文件失败: {str(e)}")

def rename_item_image_files(old_item_code: str, new_item_code: str, current_image_url: Optional[str]) -> Optional[str]:
    """
    当物品代码更改时，重命名相关的图片文件

    Args:
        old_item_code: 旧的物品代码
        new_item_code: 新的物品代码
        current_image_url: 当前的图片URL

    Returns:
        新的图片URL，如果没有图片则返回None
    """
    if not current_image_url:
        return None

    try:
        imgs_dir, thumbs_dir = get_upload_directory()

        # 从当前URL提取文件名（处理URL路径）
        url_path = current_image_url.replace('/static/images/items/imgs/', '').replace('/static/images/', '')
        current_filename = Path(url_path).name
        if not current_filename:
            return current_image_url

        # 获取文件扩展名
        file_extension = Path(current_filename).suffix.lower()
        if not file_extension:
            print(f"警告: 无法确定文件扩展名: {current_filename}")
            return current_image_url

        # 使用与上传时相同的逻辑生成新文件名
        # 创建一个临时文件名来保持扩展名一致性
        temp_original_filename = f"image{file_extension}"
        new_filename = generate_unique_filename(new_item_code, temp_original_filename, check_conflicts=False)
        new_thumbnail_filename = generate_thumbnail_filename(new_item_code, temp_original_filename, check_conflicts=False)

        # 构建文件路径
        old_file_path = imgs_dir / current_filename
        new_file_path = imgs_dir / new_filename

        # 使用更可靠的方法确定缩略图文件名
        old_thumbnail_filename = get_thumbnail_filename_from_original(current_filename)
        old_thumbnail_path = thumbs_dir / old_thumbnail_filename
        new_thumbnail_path = thumbs_dir / new_thumbnail_filename

        # 检查新文件名是否与当前文件名相同
        if current_filename == new_filename:
            print(f"文件名未改变，无需重命名: {current_filename}")
            return current_image_url

        # 重命名原图文件
        renamed_original = False
        if old_file_path.exists():
            if new_file_path.exists():
                # 如果新文件名已存在，添加时间戳避免冲突
                timestamp = str(int(time.time() * 1000))
                new_filename = generate_unique_filename(f"{new_item_code}_{timestamp}", temp_original_filename, check_conflicts=False)
                new_file_path = imgs_dir / new_filename
                new_thumbnail_filename = generate_thumbnail_filename(f"{new_item_code}_{timestamp}", temp_original_filename, check_conflicts=False)
                new_thumbnail_path = thumbs_dir / new_thumbnail_filename

            # 执行重命名
            old_file_path.rename(new_file_path)
            renamed_original = True
            print(f"重命名图片文件: {current_filename} -> {new_filename}")
        else:
            print(f"警告: 原图文件不存在: {old_file_path}")

        # 重命名缩略图文件
        if old_thumbnail_path.exists():
            if new_thumbnail_path.exists():
                # 如果新缩略图已存在，删除旧缩略图
                old_thumbnail_path.unlink()
                print(f"删除旧缩略图文件: {old_thumbnail_filename}")
            else:
                # 重命名缩略图
                old_thumbnail_path.rename(new_thumbnail_path)
                print(f"重命名缩略图文件: {old_thumbnail_filename} -> {new_thumbnail_filename}")

        # 只有在原图成功重命名时才返回新URL
        if renamed_original:
            return f"/static/images/items/imgs/{new_filename}"
        else:
            print(f"警告: 原图文件不存在: {current_filename}")
            return current_image_url

    except Exception as e:
        print(f"重命名图片文件失败: {e}")
        # 如果重命名失败，返回原URL
        return current_image_url

def delete_item_image_files(image_url: Optional[str]) -> bool:
    """
    删除物品的图片文件和缩略图文件

    Args:
        image_url: 图片URL

    Returns:
        是否成功删除
    """
    if not image_url:
        return True

    try:
        imgs_dir, thumbs_dir = get_upload_directory()

        # 从URL提取文件名
        url_path = image_url.replace('/static/images/items/imgs/', '').replace('/static/images/', '')
        filename = Path(url_path).name
        if not filename:
            return True

        # 构建文件路径
        file_path = imgs_dir / filename
        thumbnail_filename = get_thumbnail_filename_from_original(filename)
        thumbnail_path = thumbs_dir / thumbnail_filename

        deleted_files = []

        # 删除原图文件
        if file_path.exists():
            file_path.unlink()
            deleted_files.append(filename)
            print(f"删除图片文件: {filename}")

        # 删除缩略图文件
        if thumbnail_path.exists():
            thumbnail_path.unlink()
            deleted_files.append(thumbnail_filename)
            print(f"删除缩略图文件: {thumbnail_filename}")

        if deleted_files:
            print(f"成功删除 {len(deleted_files)} 个文件: {', '.join(deleted_files)}")

        return True

    except Exception as e:
        print(f"删除图片文件失败: {e}")
        return False

# ===== 图片上传API =====

@router.post("/{item_code}/upload-image", response_model=ApiResponse, summary="上传物品图片")
async def upload_item_image(
    item_code: str,
    file: UploadFile = File(..., description="要上传的图片文件"),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """为指定物品代码上传图片"""
    try:
        # 验证文件名
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未提供文件名"
            )

        if not validate_filename(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件名包含非法字符或过长"
            )

        if not is_valid_image_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件格式，请上传 JPG、PNG、GIF、WebP 或 BMP 格式的图片"
            )

        # 验证文件内容
        if not await validate_file_content(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件内容不是有效的图片格式"
            )

        # 验证文件大小（5MB限制）
        if file.size and file.size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小不能超过5MB"
            )

        # 验证物品代码是否存在
        from ..main import get_global_db_manager
        service = ItemManagementService(get_global_db_manager())

        # 直接查询数据库检查item_code是否存在
        with service.db_manager.get_db_session() as session:
            from ...modules.sql.models.item_models import Item

            item = session.query(Item).filter(Item.item_code == item_code).first()
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"物品代码 '{item_code}' 不存在"
                )

            item_id = getattr(item, 'id')

        # 生成唯一文件名并保存文件（包括缩略图）
        filename = generate_unique_filename(item_code, file.filename, check_conflicts=True)
        thumbnail_filename = generate_thumbnail_filename(item_code, file.filename, check_conflicts=True)

        try:
            image_url, thumbnail_url = await save_uploaded_file_with_thumbnail(file, filename, thumbnail_filename)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

        # 更新数据库中的图片路径
        try:
            update_result = service.update_item_details(item_id, image_url=image_url)
            if not update_result.success:
                handle_service_error(update_result)
        except Exception as e:
            # 如果数据库更新失败，删除已上传的文件
            try:
                imgs_dir, thumbs_dir = get_upload_directory()
                file_path = imgs_dir / filename
                if file_path.exists():
                    file_path.unlink()
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"数据库更新失败: {str(e)}"
            )

        return ApiResponse(
            success=True,
            message="图片上传成功",
            data={
                "item_code": item_code,
                "filename": filename,
                "thumbnail_filename": thumbnail_filename,
                "image_url": image_url,
                "thumbnail_url": thumbnail_url,
                "file_size": file.size
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图片上传失败: {str(e)}"
        )
