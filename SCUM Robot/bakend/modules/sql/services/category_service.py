"""
物品类目服务 - Items API系统的类目管理服务
"""

from typing import List, Optional, Dict, Any
import logging

from ..database import DatabaseManager
from .service_result import (
    ServiceResult, ServiceErrorType, success, error,
    category_not_found_error, subcategory_not_found_error,
    name_exists_error, validation_error, database_error
)

logger = logging.getLogger(__name__)


class ItemCategoryService:
    """物品类目服务 - 管理Items API系统中的类目和子类目"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化物品类目服务

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
    
    # ===== 物品类目管理 =====

    def create_item_category(self, name: str, description: Optional[str] = None) -> ServiceResult:
        """创建新的物品类目"""
        try:
            # 验证输入
            if not name or not name.strip():
                return validation_error("类目名称不能为空")
            
            name = name.strip()
            if len(name) > 100:
                return validation_error("类目名称长度不能超过100个字符")
            
            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Category
                
                # 检查是否已存在同名类目
                existing = session.query(Category).filter(Category.name == name).first()
                if existing:
                    return name_exists_error("类目", name)
                
                # 创建新类目
                category = Category()
                setattr(category, 'name', name)
                if description:
                    setattr(category, 'description', description.strip())
                
                session.add(category)
                session.flush()
                session.refresh(category)
                
                # 提取数据
                result_data = {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'is_active': category.is_active,
                    'created_at': category.created_at
                }
                
                logger.info(f"创建物品类目成功: {name} (ID: {category.id})")
                return success(result_data)

        except Exception as e:
            logger.error(f"创建物品类目失败: {e}")
            return database_error(f"创建物品类目时发生错误: {str(e)}")

    def get_item_category(self, category_id: int) -> ServiceResult:
        """获取单个物品类目详情"""
        try:
            if category_id <= 0:
                return validation_error("类目ID必须为正整数")
            
            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Category
                
                category = session.query(Category).filter(Category.id == category_id).first()
                if not category:
                    return category_not_found_error(category_id)
                
                result_data = {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'is_active': category.is_active,
                    'created_at': category.created_at,
                    'updated_at': getattr(category, 'updated_at', None)
                }
                
                return success(result_data)
                
        except Exception as e:
            logger.error(f"获取类目失败: {e}")
            return database_error(f"获取类目时发生错误: {str(e)}")
    
    def list_item_categories(self, include_inactive: bool = False, page: int = 1, page_size: int = 50) -> ServiceResult:
        """获取物品类目列表"""
        try:
            if page <= 0:
                return validation_error("页码必须为正整数")
            if page_size <= 0 or page_size > 100:
                return validation_error("每页大小必须在1-100之间")
            
            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Category
                
                query = session.query(Category)
                if not include_inactive:
                    query = query.filter(Category.is_active == True)
                
                # 分页
                offset = (page - 1) * page_size
                total = query.count()
                categories = query.offset(offset).limit(page_size).all()
                
                result_data = {
                    'categories': [
                        {
                            'id': cat.id,
                            'name': cat.name,
                            'description': cat.description,
                            'is_active': cat.is_active,
                            'created_at': cat.created_at,
                            'updated_at': getattr(cat, 'updated_at', None)
                        }
                        for cat in categories
                    ],
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': total,
                        'total_pages': (total + page_size - 1) // page_size
                    }
                }
                
                return success(result_data)
                
        except Exception as e:
            logger.error(f"获取类目列表失败: {e}")
            return database_error(f"获取类目列表时发生错误: {str(e)}")
    
    def update_item_category(self, category_id: int, **kwargs) -> ServiceResult:
        """更新物品类目信息"""
        try:
            if category_id <= 0:
                return validation_error("类目ID必须为正整数")
            
            # 验证更新字段
            allowed_fields = {'name', 'description', 'is_active'}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
            
            if not update_fields:
                return validation_error("至少需要提供一个有效的更新字段")
            
            # 验证名称
            if 'name' in update_fields:
                name = update_fields['name'].strip() if isinstance(update_fields['name'], str) else ""
                if not name:
                    return validation_error("类目名称不能为空")
                if len(name) > 100:
                    return validation_error("类目名称长度不能超过100个字符")
                update_fields['name'] = name
            
            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Category
                
                category = session.query(Category).filter(Category.id == category_id).first()
                if not category:
                    return category_not_found_error(category_id)
                
                # 检查名称重复
                if 'name' in update_fields:
                    existing = session.query(Category).filter(
                        Category.name == update_fields['name'],
                        Category.id != category_id
                    ).first()
                    if existing:
                        return name_exists_error("类目", update_fields['name'])
                
                # 检查是否需要级联更新活跃状态
                if 'is_active' in update_fields:
                    # 使用级联更新方法
                    cascade_result = self.update_category_active_status(category_id, update_fields['is_active'])
                    if not cascade_result.success:
                        return cascade_result

                    # 移除is_active字段，因为已经通过级联更新处理了
                    update_fields = {k: v for k, v in update_fields.items() if k != 'is_active'}

                # 更新其他字段
                updated = False
                for field, value in update_fields.items():
                    if hasattr(category, field):
                        current_value = getattr(category, field)
                        if current_value != value:
                            setattr(category, field, value)
                            updated = True
                            logger.info(f"更新类目字段 {field}: {current_value} -> {value}")

                if updated and hasattr(category, 'update_timestamp'):
                    category.update_timestamp()

                session.flush()
                session.refresh(category)

                result_data = {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'is_active': category.is_active,
                    'created_at': category.created_at,
                    'updated_at': getattr(category, 'updated_at', None)
                }

                logger.info(f"更新类目成功: ID {category_id}")
                return success(result_data)
                
        except Exception as e:
            logger.error(f"更新类目失败: {e}")
            return database_error(f"更新类目时发生错误: {str(e)}")
    
    def delete_item_category(self, category_id: int, soft_delete: bool = True, force: bool = False) -> ServiceResult:
        """删除物品类目"""
        try:
            if category_id <= 0:
                return validation_error("类目ID必须为正整数")
            
            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Category, SubCategory, Item
                
                category = session.query(Category).filter(Category.id == category_id).first()
                if not category:
                    return category_not_found_error(category_id)
                
                # 检查是否有子类目
                subcategories_count = session.query(SubCategory).filter(SubCategory.category_id == category_id).count()
                if subcategories_count > 0 and not force:
                    return error(
                        ServiceErrorType.CATEGORY_HAS_SUBCATEGORIES,
                        f"类目下有 {subcategories_count} 个子类目，无法删除。请先删除子类目或使用强制删除",
                        {"category_id": category_id, "subcategories_count": subcategories_count}
                    )
                
                # 检查是否有物品
                items_count = session.query(Item).filter(Item.category_id == category_id).count()
                if items_count > 0 and not force:
                    return error(
                        ServiceErrorType.CATEGORY_HAS_ITEMS,
                        f"类目下有 {items_count} 个物品，无法删除。请先删除物品或使用强制删除",
                        {"category_id": category_id, "items_count": items_count}
                    )
                
                if soft_delete:
                    # 软删除：设置is_active=False
                    setattr(category, 'is_active', False)
                    if hasattr(category, 'update_timestamp'):
                        category.update_timestamp()
                    logger.info(f"软删除类目 {category_id}")
                else:
                    # 硬删除
                    if force:
                        # 强制删除：先删除关联的子类目和物品
                        session.query(Item).filter(Item.category_id == category_id).delete()
                        session.query(SubCategory).filter(SubCategory.category_id == category_id).delete()
                    
                    session.delete(category)
                    logger.info(f"硬删除类目 {category_id}")
                
                return success({"deleted": True, "soft_delete": soft_delete, "category_id": category_id})
                
        except Exception as e:
            logger.error(f"删除类目失败: {e}")
            return database_error(f"删除类目时发生错误: {str(e)}")

    # ===== 物品子类目管理 =====

    def create_item_subcategory(self, category_id: int, name: str, description: Optional[str] = None) -> ServiceResult:
        """创建物品子类目"""
        try:
            # 验证输入
            if category_id <= 0:
                return validation_error("父类目ID必须为正整数")
            if not name or not name.strip():
                return validation_error("子类目名称不能为空")

            name = name.strip()
            if len(name) > 100:
                return validation_error("子类目名称长度不能超过100个字符")

            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Category, SubCategory

                # 检查父类目是否存在且活跃
                parent_category = session.query(Category).filter(Category.id == category_id).first()
                if not parent_category:
                    return error(
                        ServiceErrorType.PARENT_CATEGORY_NOT_FOUND,
                        f"父类目ID {category_id} 不存在",
                        {"category_id": category_id}
                    )

                if not getattr(parent_category, 'is_active', False):
                    return error(
                        ServiceErrorType.PARENT_CATEGORY_INACTIVE,
                        f"父类目ID {category_id} 已停用，无法创建子类目",
                        {"category_id": category_id}
                    )

                # 检查同名子类目
                existing = session.query(SubCategory).filter(
                    SubCategory.name == name,
                    SubCategory.category_id == category_id
                ).first()
                if existing:
                    return name_exists_error("子类目", name, f"父类目'{parent_category.name}'")

                # 创建新子类目
                subcategory = SubCategory()
                setattr(subcategory, 'category_id', category_id)
                setattr(subcategory, 'name', name)
                if description:
                    setattr(subcategory, 'description', description.strip())

                session.add(subcategory)
                session.flush()
                session.refresh(subcategory)

                result_data = {
                    'id': subcategory.id,
                    'category_id': subcategory.category_id,
                    'name': subcategory.name,
                    'description': subcategory.description,
                    'is_active': subcategory.is_active,
                    'created_at': subcategory.created_at,
                    'category_name': parent_category.name
                }

                logger.info(f"创建子类目成功: {name} (ID: {subcategory.id}, 父类目: {parent_category.name})")
                return success(result_data)

        except Exception as e:
            logger.error(f"创建子类目失败: {e}")
            return database_error(f"创建子类目时发生错误: {str(e)}")

    def get_item_subcategory(self, subcategory_id: int) -> ServiceResult:
        """获取单个物品子类目详情"""
        try:
            if subcategory_id <= 0:
                return validation_error("子类目ID必须为正整数")

            with self.db_manager.get_db_session() as session:
                from ..models.item_models import SubCategory

                subcategory = session.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
                if not subcategory:
                    return subcategory_not_found_error(subcategory_id)

                # 获取父类目名称
                category_name = subcategory.category.name if subcategory.category else None

                result_data = {
                    'id': subcategory.id,
                    'category_id': subcategory.category_id,
                    'name': subcategory.name,
                    'description': subcategory.description,
                    'is_active': subcategory.is_active,
                    'created_at': subcategory.created_at,
                    'updated_at': getattr(subcategory, 'updated_at', None),
                    'category_name': category_name
                }

                return success(result_data)

        except Exception as e:
            logger.error(f"获取子类目失败: {e}")
            return database_error(f"获取子类目时发生错误: {str(e)}")

    def list_item_subcategories(self, category_id: Optional[int] = None, include_inactive: bool = False,
                          page: int = 1, page_size: int = 50) -> ServiceResult:
        """获取物品子类目列表"""
        try:
            if page <= 0:
                return validation_error("页码必须为正整数")
            if page_size <= 0 or page_size > 100:
                return validation_error("每页大小必须在1-100之间")
            if category_id is not None and category_id <= 0:
                return validation_error("类目ID必须为正整数")

            with self.db_manager.get_db_session() as session:
                from ..models.item_models import SubCategory, Category

                query = session.query(SubCategory)
                if category_id:
                    query = query.filter(SubCategory.category_id == category_id)
                if not include_inactive:
                    query = query.filter(SubCategory.is_active == True)

                # 分页
                offset = (page - 1) * page_size
                total = query.count()
                subcategories = query.offset(offset).limit(page_size).all()

                result_data = {
                    'subcategories': [
                        {
                            'id': sub.id,
                            'category_id': sub.category_id,
                            'name': sub.name,
                            'description': sub.description,
                            'is_active': sub.is_active,
                            'created_at': sub.created_at,
                            'updated_at': getattr(sub, 'updated_at', None),
                            'category_name': sub.category.name if sub.category else None
                        }
                        for sub in subcategories
                    ],
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': total,
                        'total_pages': (total + page_size - 1) // page_size
                    },
                    'filter': {
                        'category_id': category_id,
                        'include_inactive': include_inactive
                    }
                }

                return success(result_data)

        except Exception as e:
            logger.error(f"获取子类目列表失败: {e}")
            return database_error(f"获取子类目列表时发生错误: {str(e)}")

    def update_item_subcategory(self, subcategory_id: int, **kwargs) -> ServiceResult:
        """更新物品子类目"""
        try:
            if subcategory_id <= 0:
                return validation_error("子类目ID必须为正整数")

            # 验证更新字段
            allowed_fields = {'name', 'description', 'is_active', 'category_id'}
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}

            if not update_fields:
                return validation_error("至少需要提供一个有效的更新字段")

            # 验证名称
            if 'name' in update_fields:
                name = update_fields['name'].strip() if isinstance(update_fields['name'], str) else ""
                if not name:
                    return validation_error("子类目名称不能为空")
                if len(name) > 100:
                    return validation_error("子类目名称长度不能超过100个字符")
                update_fields['name'] = name

            # 验证父类目ID
            if 'category_id' in update_fields and update_fields['category_id'] <= 0:
                return validation_error("父类目ID必须为正整数")

            with self.db_manager.get_db_session() as session:
                from ..models.item_models import SubCategory, Category

                # 查找子类目
                subcategory = session.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
                if not subcategory:
                    return subcategory_not_found_error(subcategory_id)

                # 验证新的父类目（如果要更改）
                if 'category_id' in update_fields:
                    new_category_id = update_fields['category_id']
                    if new_category_id != subcategory.category_id:
                        new_category = session.query(Category).filter(Category.id == new_category_id).first()
                        if not new_category:
                            return error(
                                ServiceErrorType.PARENT_CATEGORY_NOT_FOUND,
                                f"父类目ID {new_category_id} 不存在",
                                {"category_id": new_category_id}
                            )
                        if not getattr(new_category, 'is_active', False):
                            return error(
                                ServiceErrorType.PARENT_CATEGORY_INACTIVE,
                                f"父类目ID {new_category_id} 已停用，无法移动子类目",
                                {"category_id": new_category_id}
                            )

                # 检查名称重复
                if 'name' in update_fields:
                    new_name = update_fields['name']
                    target_category_id = update_fields.get('category_id', subcategory.category_id)

                    existing = session.query(SubCategory).filter(
                        SubCategory.name == new_name,
                        SubCategory.category_id == target_category_id,
                        SubCategory.id != subcategory_id
                    ).first()
                    if existing:
                        target_category = session.query(Category).filter(Category.id == target_category_id).first()
                        category_name = getattr(target_category, 'name') if target_category else None
                        return name_exists_error("子类目", new_name, f"父类目'{category_name}'")

                # 检查是否需要级联更新活跃状态
                if 'is_active' in update_fields:
                    # 使用级联更新方法
                    cascade_result = self.update_subcategory_active_status(subcategory_id, update_fields['is_active'])
                    if not cascade_result.success:
                        return cascade_result

                    # 移除is_active字段，因为已经通过级联更新处理了
                    update_fields = {k: v for k, v in update_fields.items() if k != 'is_active'}

                # 更新其他字段
                updated = False
                for field, value in update_fields.items():
                    if hasattr(subcategory, field):
                        current_value = getattr(subcategory, field)
                        if current_value != value:
                            setattr(subcategory, field, value)
                            updated = True
                            logger.info(f"更新子类目字段 {field}: {current_value} -> {value}")

                if updated and hasattr(subcategory, 'update_timestamp'):
                    subcategory.update_timestamp()

                session.flush()
                session.refresh(subcategory)

                # 获取父类目名称
                category_name = subcategory.category.name if subcategory.category else None

                result_data = {
                    'id': subcategory.id,
                    'category_id': subcategory.category_id,
                    'name': subcategory.name,
                    'description': subcategory.description,
                    'is_active': subcategory.is_active,
                    'created_at': subcategory.created_at,
                    'updated_at': getattr(subcategory, 'updated_at', None),
                    'category_name': category_name
                }

                logger.info(f"更新子类目成功: ID {subcategory_id}")
                return success(result_data)

        except Exception as e:
            logger.error(f"更新子类目失败: {e}")
            return database_error(f"更新子类目时发生错误: {str(e)}")

    def delete_item_subcategory(self, subcategory_id: int, soft_delete: bool = True, force: bool = False) -> ServiceResult:
        """删除物品子类目"""
        try:
            if subcategory_id <= 0:
                return validation_error("子类目ID必须为正整数")

            with self.db_manager.get_db_session() as session:
                from ..models.item_models import SubCategory, Item

                subcategory = session.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
                if not subcategory:
                    return subcategory_not_found_error(subcategory_id)

                # 检查是否有关联的物品
                items_count = session.query(Item).filter(Item.subcategory_id == subcategory_id).count()
                if items_count > 0 and not force:
                    return error(
                        ServiceErrorType.SUBCATEGORY_HAS_ITEMS,
                        f"子类目下有 {items_count} 个物品，无法删除。请先删除物品或使用强制删除",
                        {"subcategory_id": subcategory_id, "items_count": items_count}
                    )

                if soft_delete:
                    # 软删除：设置is_active=False
                    setattr(subcategory, 'is_active', False)
                    if hasattr(subcategory, 'update_timestamp'):
                        subcategory.update_timestamp()
                    logger.info(f"软删除子类目 {subcategory_id}")
                else:
                    # 硬删除
                    if force and items_count > 0:
                        # 强制删除：先删除关联的物品
                        session.query(Item).filter(Item.subcategory_id == subcategory_id).delete()

                    session.delete(subcategory)
                    logger.info(f"硬删除子类目 {subcategory_id}")

                return success({"deleted": True, "soft_delete": soft_delete, "subcategory_id": subcategory_id})

        except Exception as e:
            logger.error(f"删除子类目失败: {e}")
            return database_error(f"删除子类目时发生错误: {str(e)}")

    # ===== 状态管理方法 =====

    def update_category_active_status(self, category_id: int, is_active: bool) -> ServiceResult:
        """
        更新类目的活跃状态，并级联更新其下所有子类目和物品的状态

        Args:
            category_id: 类目ID
            is_active: 新的活跃状态

        Returns:
            ServiceResult: 包含更新结果的服务结果
        """
        try:
            if category_id <= 0:
                return validation_error("类目ID必须为正整数")

            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Category, SubCategory, Item

                # 获取类目
                category = session.query(Category).filter(Category.id == category_id).first()
                if not category:
                    return category_not_found_error(category_id)

                # 更新类目状态
                old_status = getattr(category, 'is_active', True)
                setattr(category, 'is_active', is_active)
                if hasattr(category, 'update_timestamp'):
                    category.update_timestamp()

                # 级联更新子类目状态
                subcategories = session.query(SubCategory).filter(SubCategory.category_id == category_id).all()
                updated_subcategories = 0
                for subcategory in subcategories:
                    setattr(subcategory, 'is_active', is_active)
                    if hasattr(subcategory, 'update_timestamp'):
                        subcategory.update_timestamp()
                    updated_subcategories += 1

                # 级联更新物品状态
                items = session.query(Item).filter(Item.category_id == category_id).all()
                updated_items = 0
                for item in items:
                    setattr(item, 'is_active', is_active)
                    if hasattr(item, 'update_timestamp'):
                        item.update_timestamp()
                    updated_items += 1

                session.flush()
                session.refresh(category)

                result_data = {
                    'category_id': category_id,
                    'old_status': old_status,
                    'new_status': is_active,
                    'updated_subcategories': updated_subcategories,
                    'updated_items': updated_items,
                    'category': {
                        'id': category.id,
                        'name': category.name,
                        'description': category.description,
                        'is_active': category.is_active,
                        'created_at': category.created_at,
                        'updated_at': getattr(category, 'updated_at', None)
                    }
                }

                logger.info(f"更新类目 {category_id} 活跃状态: {old_status} -> {is_active}, "
                           f"级联更新 {updated_subcategories} 个子类目, {updated_items} 个物品")
                return success(result_data)

        except Exception as e:
            logger.error(f"更新类目活跃状态失败: {e}")
            return database_error(f"更新类目活跃状态时发生错误: {str(e)}")

    def update_subcategory_active_status(self, subcategory_id: int, is_active: bool) -> ServiceResult:
        """
        更新子类目的活跃状态，并级联更新其下所有物品的状态

        Args:
            subcategory_id: 子类目ID
            is_active: 新的活跃状态

        Returns:
            ServiceResult: 包含更新结果的服务结果
        """
        try:
            if subcategory_id <= 0:
                return validation_error("子类目ID必须为正整数")

            with self.db_manager.get_db_session() as session:
                from ..models.item_models import SubCategory, Item

                # 获取子类目
                subcategory = session.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
                if not subcategory:
                    return subcategory_not_found_error(subcategory_id)

                # 更新子类目状态
                old_status = getattr(subcategory, 'is_active', True)
                setattr(subcategory, 'is_active', is_active)
                if hasattr(subcategory, 'update_timestamp'):
                    subcategory.update_timestamp()

                # 级联更新物品状态
                items = session.query(Item).filter(Item.subcategory_id == subcategory_id).all()
                updated_items = 0
                for item in items:
                    setattr(item, 'is_active', is_active)
                    if hasattr(item, 'update_timestamp'):
                        item.update_timestamp()
                    updated_items += 1

                session.flush()
                session.refresh(subcategory)

                # 获取父类目名称
                category_name = subcategory.category.name if subcategory.category else None

                result_data = {
                    'subcategory_id': subcategory_id,
                    'old_status': old_status,
                    'new_status': is_active,
                    'updated_items': updated_items,
                    'subcategory': {
                        'id': subcategory.id,
                        'category_id': subcategory.category_id,
                        'name': subcategory.name,
                        'description': subcategory.description,
                        'is_active': subcategory.is_active,
                        'created_at': subcategory.created_at,
                        'updated_at': getattr(subcategory, 'updated_at', None),
                        'category_name': category_name
                    }
                }

                logger.info(f"更新子类目 {subcategory_id} 活跃状态: {old_status} -> {is_active}, "
                           f"级联更新 {updated_items} 个物品")
                return success(result_data)

        except Exception as e:
            logger.error(f"更新子类目活跃状态失败: {e}")
            return database_error(f"更新子类目活跃状态时发生错误: {str(e)}")

    # ===== 组合查询方法 =====

    def get_categories_with_subcategories(self, include_inactive: bool = False) -> ServiceResult:
        """获取类目及其子类目的完整列表"""
        try:
            with self.db_manager.get_db_session() as session:
                from ..models.item_models import Category, SubCategory

                query = session.query(Category)
                if not include_inactive:
                    query = query.filter(Category.is_active == True)

                categories = query.all()

                result_data = []
                for category in categories:
                    subcategories_query = session.query(SubCategory).filter(SubCategory.category_id == category.id)
                    if not include_inactive:
                        subcategories_query = subcategories_query.filter(SubCategory.is_active == True)

                    subcategories = subcategories_query.all()

                    category_data = {
                        'id': category.id,
                        'name': category.name,
                        'description': category.description,
                        'is_active': category.is_active,
                        'created_at': category.created_at,
                        'updated_at': getattr(category, 'updated_at', None),
                        'subcategories': [
                            {
                                'id': sub.id,
                                'category_id': sub.category_id,
                                'name': sub.name,
                                'description': sub.description,
                                'is_active': sub.is_active,
                                'created_at': sub.created_at,
                                'updated_at': getattr(sub, 'updated_at', None)
                            }
                            for sub in subcategories
                        ]
                    }
                    result_data.append(category_data)

                return success(result_data)

        except Exception as e:
            logger.error(f"获取类目和子类目列表失败: {e}")
            return database_error(f"获取类目和子类目列表时发生错误: {str(e)}")
