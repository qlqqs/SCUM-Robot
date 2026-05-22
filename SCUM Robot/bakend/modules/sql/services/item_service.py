"""
物品管理服务 - Items API系统的物品管理服务
"""

from typing import List, Optional, Dict, Any
import logging
import os
import re
from decimal import Decimal

from ..database import DatabaseManager
from .service_result import (
    ServiceResult, ServiceErrorType, success, error,
    category_not_found_error, subcategory_not_found_error, item_not_found_error,
    name_exists_error, validation_error, database_error
)

logger = logging.getLogger(__name__)


def _is_valid_image_path(image_path: str) -> bool:
    """
    验证图片路径是否有效
    支持：
    1. HTTP/HTTPS URL
    2. 本地文件路径（绝对路径和相对路径）
    3. 网络路径（UNC路径）

    Args:
        image_path: 图片路径字符串

    Returns:
        bool: 路径是否有效
    """
    if not image_path or not image_path.strip():
        return False

    image_path = image_path.strip()

    # 检查HTTP/HTTPS URL
    if image_path.startswith(('http://', 'https://')):
        return True

    # 检查UNC网络路径 (\\server\share\path)
    if image_path.startswith('\\\\'):
        return True

    # 检查绝对路径
    # Windows: C:\path\to\file 或 D:\path\to\file
    if re.match(r'^[A-Za-z]:[\\\/]', image_path):
        return True

    # Unix/Linux绝对路径: /path/to/file
    if image_path.startswith('/'):
        return True

    # 检查相对路径
    # ./path/to/file 或 ../path/to/file 或 path/to/file
    if re.match(r'^\.{0,2}[\\\/]', image_path) or not re.match(r'^[\\\/]', image_path):
        return True

    return False


class ItemManagementService:
    """物品管理服务 - 管理Items API系统中的物品数据"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化物品管理服务

        Args:
            db_manager: 数据库管理器实例，如果不提供则使用全局管理器
        """
        if db_manager is None:
            # 使用全局数据库管理器
            try:
                from ...api.main import get_global_db_manager
                self.db_manager = get_global_db_manager()
            except ImportError:
                # 如果无法导入全局管理器，创建新实例
                self.db_manager = DatabaseManager()
                self.db_manager.init_database()
        else:
            self.db_manager = db_manager
    
    def create_item(self, name: str, item_code: str, category_id: int, subcategory_id: Optional[int] = None,
                   price: float = 0.0, stock: int = 0, image_url: Optional[str] = None,
                   description: Optional[str] = None) -> ServiceResult:
        """创建新的物品"""
        try:
            # 验证输入
            if not name or not name.strip():
                return validation_error("物品名称不能为空")

            name = name.strip()
            if len(name) > 200:
                return validation_error("物品名称长度不能超过200个字符")

            # 验证物品代码
            if not item_code or not item_code.strip():
                return validation_error("物品代码不能为空")

            item_code = item_code.strip()
            if len(item_code) > 2000:
                return validation_error("物品代码长度不能超过2000个字符")

            if category_id <= 0:
                return validation_error("类目ID必须为正整数")
            
            if subcategory_id is not None and subcategory_id <= 0:
                return validation_error("子类目ID必须为正整数")
            
            if price < 0:
                return validation_error("价格不能为负数")
            
            if stock < -1:
                return validation_error("库存不能小于-1（-1表示无限库存）")
            
            # 验证图片路径格式（支持URL和本地路径）
            if image_url and not _is_valid_image_path(image_url):
                return validation_error("图片路径格式不正确，支持HTTP/HTTPS URL或本地文件路径")
            
            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Category, SubCategory, Item
                
                # 检查类目是否存在且活跃
                category = session.query(Category).filter(Category.id == category_id).first()
                if not category:
                    return category_not_found_error(category_id)
                
                if category.is_active is not True:
                    return error(
                        ServiceErrorType.CATEGORY_INACTIVE,
                        f"类目ID {category_id} 已停用，无法创建物品",
                        {"category_id": category_id}
                    )
                
                # 检查子类目（如果提供）
                subcategory = None
                if subcategory_id:
                    subcategory = session.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
                    if not subcategory:
                        return subcategory_not_found_error(subcategory_id)
                    
                    if subcategory.is_active is not True:
                        return error(
                            ServiceErrorType.SUBCATEGORY_INACTIVE,
                            f"子类目ID {subcategory_id} 已停用，无法创建物品",
                            {"subcategory_id": subcategory_id}
                        )
                    
                    # 验证子类目是否属于指定的类目
                    if getattr(subcategory, 'category_id') != category_id:
                        return error(
                            ServiceErrorType.INVALID_CATEGORY_SUBCATEGORY_RELATION,
                            f"子类目ID {subcategory_id} 不属于类目ID {category_id}",
                            {"category_id": category_id, "subcategory_id": subcategory_id}
                        )
                
                # 检查物品名称是否重复
                existing_name = session.query(Item).filter(Item.name == name).first()
                if existing_name:
                    return name_exists_error("物品", name)

                # 检查物品代码是否重复
                existing_code = session.query(Item).filter(Item.item_code == item_code).first()
                if existing_code:
                    return error(
                        ServiceErrorType.ALREADY_EXISTS,
                        f"物品代码 '{item_code}' 已存在，请使用其他代码",
                        {"item_code": item_code}
                    )
                
                # 创建新物品
                item = Item()
                setattr(item, 'name', name)
                setattr(item, 'item_code', item_code)
                setattr(item, 'category_id', category_id)
                setattr(item, 'subcategory_id', subcategory_id)
                setattr(item, 'price', Decimal(str(price)))
                setattr(item, 'stock', stock)
                setattr(item, 'image_url', image_url.strip() if image_url else None)
                setattr(item, 'description', description.strip() if description else None)
                
                session.add(item)
                session.flush()
                session.refresh(item)
                
                # 获取关联信息
                category_name = getattr(category, 'name')
                subcategory_name = None
                if subcategory_id and 'subcategory' in locals():
                    subcategory_name = getattr(subcategory, 'name')
                
                result_data = {
                    'id': getattr(item, 'id'),
                    'name': getattr(item, 'name'),
                    'item_code': getattr(item, 'item_code'),
                    'category_id': getattr(item, 'category_id'),
                    'subcategory_id': getattr(item, 'subcategory_id'),
                    'price': float(getattr(item, 'price', 0)),
                    'stock': getattr(item, 'stock'),
                    'image_url': getattr(item, 'image_url'),
                    'description': getattr(item, 'description'),
                    'is_active': getattr(item, 'is_active'),
                    'created_at': getattr(item, 'created_at'),
                    'category_name': category_name,
                    'subcategory_name': subcategory_name
                }
                
                logger.info(f"创建物品成功: {name} (ID: {item.id})")
                return success(result_data)
                
        except Exception as e:
            logger.error(f"创建物品失败: {e}")
            return database_error(f"创建物品时发生错误: {str(e)}")
    
    def get_item_details(self, item_id: int) -> ServiceResult:
        """获取单个物品的详细信息"""
        try:
            if item_id <= 0:
                return validation_error("物品ID必须为正整数")
            
            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Item
                
                item = session.query(Item).filter(Item.id == item_id).first()
                if not item:
                    return item_not_found_error(item_id)
                
                # 获取关联信息
                category_name = getattr(item.category, 'name') if item.category else None
                subcategory_name = getattr(item.subcategory, 'name') if item.subcategory else None
                
                result_data = {
                    'id': getattr(item, 'id'),
                    'name': getattr(item, 'name'),
                    'item_code': getattr(item, 'item_code'),
                    'category_id': getattr(item, 'category_id'),
                    'subcategory_id': getattr(item, 'subcategory_id'),
                    'price': float(getattr(item, 'price', 0)),
                    'stock': getattr(item, 'stock'),
                    'image_url': getattr(item, 'image_url'),
                    'description': getattr(item, 'description'),
                    'is_active': getattr(item, 'is_active'),
                    'created_at': item.created_at,
                    'updated_at': getattr(item, 'updated_at', None),
                    'category_name': category_name,
                    'subcategory_name': subcategory_name,
                    'in_stock': item.stock == -1 or item.stock > 0
                }
                
                return success(result_data)
                
        except Exception as e:
            logger.error(f"获取物品失败: {e}")
            return database_error(f"获取物品时发生错误: {str(e)}")
    
    def get_items_list(self, category_id: Optional[int] = None, subcategory_id: Optional[int] = None,
                  include_inactive: bool = False, include_out_of_stock: bool = True,
                  page: int = 1, page_size: int = 50, sort_by: str = "id") -> ServiceResult:
        """获取物品列表"""
        try:
            if page <= 0:
                return validation_error("页码必须为正整数")
            if page_size <= 0 or page_size > 100:
                return validation_error("每页大小必须在1-100之间")
            if category_id is not None and category_id <= 0:
                return validation_error("类目ID必须为正整数")
            if subcategory_id is not None and subcategory_id <= 0:
                return validation_error("子类目ID必须为正整数")

            # 验证排序字段
            valid_sort_fields = ["sort_order", "name", "price", "created_at", "id"]
            if sort_by not in valid_sort_fields:
                return validation_error(f"排序字段必须是以下之一: {', '.join(valid_sort_fields)}")
            
            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Item
                
                query = session.query(Item)
                
                # 应用过滤条件
                if category_id:
                    query = query.filter(Item.category_id == category_id)
                if subcategory_id:
                    query = query.filter(Item.subcategory_id == subcategory_id)
                if not include_inactive:
                    query = query.filter(Item.is_active == True)
                if not include_out_of_stock:
                    # 包含有库存的物品（stock > 0）和无限库存的物品（stock = -1）
                    query = query.filter((Item.stock > 0) | (Item.stock == -1))  # type: ignore
                
                # 排序
                if sort_by == "sort_order":
                    query = query.order_by(Item.sort_order.asc(), Item.id.asc())
                elif sort_by == "name":
                    query = query.order_by(Item.name.asc())
                elif sort_by == "price":
                    query = query.order_by(Item.price.asc())
                elif sort_by == "created_at":
                    query = query.order_by(Item.created_at.desc())
                else:  # id
                    query = query.order_by(Item.id.asc())

                # 分页
                offset = (page - 1) * page_size
                total = query.count()
                items = query.offset(offset).limit(page_size).all()
                
                result_data = {
                    'items': [
                        {
                            'id': getattr(item, 'id'),
                            'name': getattr(item, 'name'),
                            'item_code': getattr(item, 'item_code'),
                            'category_id': getattr(item, 'category_id'),
                            'subcategory_id': getattr(item, 'subcategory_id'),
                            'price': float(getattr(item, 'price', 0)),
                            'stock': getattr(item, 'stock'),
                            'image_url': getattr(item, 'image_url'),
                            'description': getattr(item, 'description'),
                            'sort_order': getattr(item, 'sort_order', 0),
                            'is_active': getattr(item, 'is_active'),
                            'created_at': getattr(item, 'created_at'),
                            'updated_at': getattr(item, 'updated_at', None),
                            'category_name': getattr(item.category, 'name') if item.category else None,
                            'subcategory_name': getattr(item.subcategory, 'name') if item.subcategory else None,
                            'in_stock': getattr(item, 'stock', 0) == -1 or getattr(item, 'stock', 0) > 0
                        }
                        for item in items
                    ],
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': total,
                        'total_pages': (total + page_size - 1) // page_size
                    },
                    'filters': {
                        'category_id': category_id,
                        'subcategory_id': subcategory_id,
                        'include_inactive': include_inactive,
                        'include_out_of_stock': include_out_of_stock
                    }
                }
                
                return success(result_data)
                
        except Exception as e:
            logger.error(f"获取物品列表失败: {e}")
            return database_error(f"获取物品列表时发生错误: {str(e)}")

    def update_item_details(self, item_id: int, **kwargs) -> ServiceResult:
        """更新物品详细信息"""
        try:
            if item_id <= 0:
                return validation_error("物品ID必须为正整数")

            # 验证更新字段
            allowed_fields = {'name', 'item_code', 'category_id', 'subcategory_id', 'price', 'stock', 'image_url', 'description', 'is_active'}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}

            if not update_fields:
                return validation_error("至少需要提供一个有效的更新字段")

            # 验证各个字段
            if 'name' in update_fields:
                name = update_fields['name'].strip() if isinstance(update_fields['name'], str) else ""
                if not name:
                    return validation_error("物品名称不能为空")
                if len(name) > 200:
                    return validation_error("物品名称长度不能超过200个字符")
                update_fields['name'] = name

            if 'item_code' in update_fields:
                item_code = update_fields['item_code'].strip() if isinstance(update_fields['item_code'], str) else ""
                if not item_code:
                    return validation_error("物品代码不能为空")
                if len(item_code) > 2000:
                    return validation_error("物品代码长度不能超过2000个字符")
                update_fields['item_code'] = item_code

            if 'category_id' in update_fields and update_fields['category_id'] <= 0:
                return validation_error("类目ID必须为正整数")

            if 'subcategory_id' in update_fields and update_fields['subcategory_id'] is not None and update_fields['subcategory_id'] <= 0:
                return validation_error("子类目ID必须为正整数")

            if 'price' in update_fields and update_fields['price'] < 0:
                return validation_error("价格不能为负数")

            if 'stock' in update_fields and update_fields['stock'] < -1:
                return validation_error("库存不能小于-1（-1表示无限库存）")

            if 'image_url' in update_fields and update_fields['image_url']:
                if not _is_valid_image_path(update_fields['image_url']):
                    return validation_error("图片路径格式不正确，支持HTTP/HTTPS URL或本地文件路径")

            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Item, Category, SubCategory

                # 查找物品
                item = session.query(Item).filter(Item.id == item_id).first()
                if not item:
                    return item_not_found_error(item_id)

                # 验证类目
                if 'category_id' in update_fields:
                    category = session.query(Category).filter(Category.id == update_fields['category_id']).first()
                    if not category:
                        return category_not_found_error(update_fields['category_id'])
                    if category.is_active is not True:
                        return error(
                            ServiceErrorType.CATEGORY_INACTIVE,
                            f"类目ID {update_fields['category_id']} 已停用，无法移动物品",
                            {"category_id": update_fields['category_id']}
                        )

                # 验证子类目
                if 'subcategory_id' in update_fields:
                    subcategory_id = update_fields['subcategory_id']
                    if subcategory_id:
                        subcategory = session.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
                        if not subcategory:
                            return subcategory_not_found_error(subcategory_id)
                        if not getattr(subcategory, 'is_active', False):
                            return error(
                                ServiceErrorType.SUBCATEGORY_INACTIVE,
                                f"子类目ID {subcategory_id} 已停用，无法移动物品",
                                {"subcategory_id": subcategory_id}
                            )

                        # 验证子类目与类目的关系
                        target_category_id = update_fields.get('category_id', item.category_id)
                        if subcategory.category_id != target_category_id:
                            return error(
                                ServiceErrorType.INVALID_CATEGORY_SUBCATEGORY_RELATION,
                                f"子类目ID {subcategory_id} 不属于类目ID {target_category_id}",
                                {"category_id": target_category_id, "subcategory_id": subcategory_id}
                            )

                # 检查名称重复
                if 'name' in update_fields:
                    existing = session.query(Item).filter(
                        Item.name == update_fields['name'],
                        Item.id != item_id
                    ).first()
                    if existing:
                        return name_exists_error("物品", update_fields['name'])

                # 检查物品代码重复
                if 'item_code' in update_fields:
                    existing = session.query(Item).filter(
                        Item.item_code == update_fields['item_code'],
                        Item.id != item_id
                    ).first()
                    if existing:
                        return error(
                            ServiceErrorType.ALREADY_EXISTS,
                            f"物品代码 '{update_fields['item_code']}' 已存在，请使用其他代码",
                            {"item_code": update_fields['item_code']}
                        )

                # 更新字段
                updated = False
                for field, value in update_fields.items():
                    if hasattr(item, field):
                        current_value = getattr(item, field)
                        # 特殊处理价格字段
                        if field == 'price':
                            value = Decimal(str(value))

                        if current_value != value:
                            setattr(item, field, value)
                            updated = True
                            logger.info(f"更新物品字段 {field}: {current_value} -> {value}")

                if updated and hasattr(item, 'update_timestamp'):
                    item.update_timestamp()

                session.flush()
                session.refresh(item)

                # 获取关联信息
                category_name = getattr(item.category, 'name') if item.category else None
                subcategory_name = getattr(item.subcategory, 'name') if item.subcategory else None

                result_data = {
                    'id': getattr(item, 'id'),
                    'name': getattr(item, 'name'),
                    'item_code': getattr(item, 'item_code'),
                    'category_id': getattr(item, 'category_id'),
                    'subcategory_id': getattr(item, 'subcategory_id'),
                    'price': float(getattr(item, 'price', 0)),
                    'stock': getattr(item, 'stock'),
                    'image_url': getattr(item, 'image_url'),
                    'description': getattr(item, 'description'),
                    'is_active': getattr(item, 'is_active'),
                    'created_at': getattr(item, 'created_at'),
                    'updated_at': getattr(item, 'updated_at', None),
                    'category_name': category_name,
                    'subcategory_name': subcategory_name,
                    'in_stock': item.stock == -1 or item.stock > 0
                }

                logger.info(f"更新物品成功: ID {item_id}")
                return success(result_data)

        except Exception as e:
            logger.error(f"更新物品失败: {e}")
            return database_error(f"更新物品时发生错误: {str(e)}")

    def delete_item(self, item_id: int, soft_delete: bool = True) -> ServiceResult:
        """删除物品"""
        try:
            if item_id <= 0:
                return validation_error("物品ID必须为正整数")

            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Item

                item = session.query(Item).filter(Item.id == item_id).first()
                if not item:
                    return item_not_found_error(item_id)

                if soft_delete:
                    # 软删除：设置is_active=False
                    setattr(item, 'is_active', False)
                    if hasattr(item, 'update_timestamp'):
                        item.update_timestamp()
                    logger.info(f"软删除物品 {item_id}")
                else:
                    # 硬删除
                    session.delete(item)
                    logger.info(f"硬删除物品 {item_id}")

                return success({"deleted": True, "soft_delete": soft_delete, "item_id": item_id})

        except Exception as e:
            logger.error(f"删除物品失败: {e}")
            return database_error(f"删除物品时发生错误: {str(e)}")

    def search_items_by_keyword(self, keyword: str, category_id: Optional[int] = None,
                    subcategory_id: Optional[int] = None, include_inactive: bool = False,
                    page: int = 1, page_size: int = 50, sort_by: str = "id") -> ServiceResult:
        """根据关键词搜索物品"""
        try:
            if not keyword or not keyword.strip():
                return validation_error("搜索关键词不能为空")

            keyword = keyword.strip()
            if len(keyword) < 2:
                return validation_error("搜索关键词至少需要2个字符")

            if page <= 0:
                return validation_error("页码必须为正整数")
            if page_size <= 0 or page_size > 100:
                return validation_error("每页大小必须在1-100之间")

            # 验证排序字段
            valid_sort_fields = ["sort_order", "name", "price", "created_at", "id"]
            if sort_by not in valid_sort_fields:
                return validation_error(f"排序字段必须是以下之一: {', '.join(valid_sort_fields)}")

            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Item

                query = session.query(Item).filter(Item.name.contains(keyword))

                # 应用过滤条件
                if category_id:
                    query = query.filter(Item.category_id == category_id)
                if subcategory_id:
                    query = query.filter(Item.subcategory_id == subcategory_id)
                if not include_inactive:
                    query = query.filter(Item.is_active == True)

                # 排序
                if sort_by == "sort_order":
                    query = query.order_by(Item.sort_order.asc(), Item.id.asc())
                elif sort_by == "name":
                    query = query.order_by(Item.name.asc())
                elif sort_by == "price":
                    query = query.order_by(Item.price.asc())
                elif sort_by == "created_at":
                    query = query.order_by(Item.created_at.desc())
                else:  # id
                    query = query.order_by(Item.id.asc())

                # 分页
                offset = (page - 1) * page_size
                total = query.count()
                items = query.offset(offset).limit(page_size).all()

                result_data = {
                    'items': [
                        {
                            'id': getattr(item, 'id'),
                            'name': getattr(item, 'name'),
                            'item_code': getattr(item, 'item_code'),
                            'category_id': getattr(item, 'category_id'),
                            'subcategory_id': getattr(item, 'subcategory_id'),
                            'price': float(getattr(item, 'price', 0)),
                            'stock': getattr(item, 'stock'),
                            'image_url': getattr(item, 'image_url'),
                            'description': getattr(item, 'description'),
                            'sort_order': getattr(item, 'sort_order', 0),
                            'is_active': getattr(item, 'is_active'),
                            'created_at': getattr(item, 'created_at'),
                            'updated_at': getattr(item, 'updated_at', None),
                            'category_name': getattr(item.category, 'name') if item.category else None,
                            'subcategory_name': getattr(item.subcategory, 'name') if item.subcategory else None,
                            'in_stock': getattr(item, 'stock', 0) == -1 or getattr(item, 'stock', 0) > 0
                        }
                        for item in items
                    ],
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': total,
                        'total_pages': (total + page_size - 1) // page_size
                    },
                    'search': {
                        'keyword': keyword,
                        'category_id': category_id,
                        'subcategory_id': subcategory_id,
                        'include_inactive': include_inactive
                    }
                }

                logger.info(f"搜索物品: '{keyword}', 找到 {total} 个结果")
                return success(result_data)

        except Exception as e:
            logger.error(f"搜索物品失败: {e}")
            return database_error(f"搜索物品时发生错误: {str(e)}")

    def update_item_stock(self, item_id: int, stock_change: int, operation: str = "set") -> ServiceResult:
        """更新物品库存数量"""
        try:
            if item_id <= 0:
                return validation_error("物品ID必须为正整数")

            if operation not in ["set", "add", "subtract"]:
                return validation_error("操作类型必须是 'set', 'add', 或 'subtract'")

            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Item

                item = session.query(Item).filter(Item.id == item_id).first()
                if not item:
                    return item_not_found_error(item_id)

                old_stock = getattr(item, 'stock', 0)

                new_stock: int = 0  # 初始化变量
                if operation == "set":
                    if stock_change < -1:
                        return validation_error("库存数量不能小于-1（-1表示无限库存）")
                    new_stock = stock_change
                elif operation == "add":
                    new_stock = old_stock + stock_change
                elif operation == "subtract":
                    # 如果当前是无限库存(-1)，减少后仍保持无限库存
                    if old_stock == -1:
                        new_stock = -1
                    else:
                        new_stock = old_stock - stock_change
                        if new_stock < -1:
                            return validation_error(f"库存不能小于-1，当前库存: {old_stock}, 尝试减少: {stock_change}")

                setattr(item, 'stock', new_stock)
                if hasattr(item, 'update_timestamp'):
                    item.update_timestamp()

                session.flush()
                session.refresh(item)

                result_data = {
                    'id': item.id,
                    'name': item.name,
                    'old_stock': old_stock,
                    'new_stock': new_stock,
                    'stock_change': stock_change,
                    'operation': operation,
                    'in_stock': new_stock == -1 or new_stock > 0
                }

                logger.info(f"更新物品库存: ID {item_id}, {operation} {stock_change}, {old_stock} -> {new_stock}")
                return success(result_data)

        except Exception as e:
            logger.error(f"更新物品库存失败: {e}")
            return database_error(f"更新物品库存时发生错误: {str(e)}")

    def update_item_active_status(self, item_id: int, is_active: bool) -> ServiceResult:
        """
        更新物品的活跃状态

        Args:
            item_id: 物品ID
            is_active: 新的活跃状态

        Returns:
            ServiceResult: 包含更新结果的服务结果
        """
        try:
            if item_id <= 0:
                return validation_error("物品ID必须为正整数")

            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Item

                # 获取物品
                item = session.query(Item).filter(Item.id == item_id).first()
                if not item:
                    return item_not_found_error(item_id)

                # 更新物品状态
                old_status = getattr(item, 'is_active', True)
                setattr(item, 'is_active', is_active)
                if hasattr(item, 'update_timestamp'):
                    item.update_timestamp()

                session.flush()
                session.refresh(item)

                # 获取关联信息
                category_name = getattr(item.category, 'name') if item.category else None
                subcategory_name = getattr(item.subcategory, 'name') if item.subcategory else None

                result_data = {
                    'item_id': item_id,
                    'old_status': old_status,
                    'new_status': is_active,
                    'item': {
                        'id': item.id,
                        'name': item.name,
                        'item_code': item.item_code,
                        'category_id': item.category_id,
                        'subcategory_id': item.subcategory_id,
                        'price': float(getattr(item, 'price', 0)),
                        'stock': item.stock,
                        'image_url': item.image_url,
                        'description': item.description,
                        'is_active': item.is_active,
                        'created_at': item.created_at,
                        'updated_at': getattr(item, 'updated_at', None),
                        'category_name': category_name,
                        'subcategory_name': subcategory_name,
                        'in_stock': item.stock > 0
                    }
                }

                logger.info(f"更新物品 {item_id} 活跃状态: {old_status} -> {is_active}")
                return success(result_data)

        except Exception as e:
            logger.error(f"更新物品活跃状态失败: {e}")
            return database_error(f"更新物品活跃状态时发生错误: {str(e)}")
