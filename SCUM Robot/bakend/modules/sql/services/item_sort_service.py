"""
物品排序服务模块
"""

import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database.manager import DatabaseManager
from ..models.item_models import Item, Category, SubCategory
from .service_result import (
    ServiceResult, ServiceErrorType, success, error,
    validation_error, database_error, not_found_error
)

logger = logging.getLogger(__name__)


class ItemSortService:
    """物品排序服务类"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化排序服务
        
        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
    
    def batch_update_item_sort(self, sort_updates: List[Dict[str, Any]], 
                              category_id: Optional[int] = None) -> ServiceResult:
        """
        批量更新物品排序
        
        Args:
            sort_updates: 排序更新列表，格式: [{"id": 1, "sort_order": 100}, ...]
            category_id: 可选的分类ID，如果提供则只更新该分类下的物品
            
        Returns:
            ServiceResult: 操作结果
        """
        try:
            if not sort_updates:
                return validation_error("排序更新列表不能为空")
            
            # 验证输入数据
            for update in sort_updates:
                if not isinstance(update, dict):
                    return validation_error("排序更新项必须是字典格式")
                
                if "id" not in update or "sort_order" not in update:
                    return validation_error("排序更新项必须包含id和sort_order字段")
                
                if not isinstance(update["id"], int) or update["id"] <= 0:
                    return validation_error("物品ID必须是正整数")
                
                if not isinstance(update["sort_order"], int):
                    return validation_error("排序值必须是整数")
            
            with self.db_manager.get_db_session() as session:
                # 获取要更新的物品ID列表
                item_ids = [update["id"] for update in sort_updates]
                
                # 构建查询条件
                query = session.query(Item).filter(Item.id.in_(item_ids))
                if category_id is not None:
                    query = query.filter(Item.category_id == category_id)
                
                items = query.all()
                
                # 检查是否所有物品都存在
                found_ids = {item.id for item in items}
                missing_ids = set(item_ids) - found_ids
                if missing_ids:
                    return not_found_error(f"物品ID不存在: {list(missing_ids)}")
                
                # 如果指定了分类，检查所有物品是否都属于该分类
                if category_id is not None:
                    wrong_category_items = [
                        item.id for item in items 
                        if item.category_id != category_id
                    ]
                    if wrong_category_items:
                        return validation_error(
                            f"物品ID {wrong_category_items} 不属于分类 {category_id}"
                        )
                
                # 创建ID到排序值的映射
                sort_map = {update["id"]: update["sort_order"] for update in sort_updates}
                
                # 批量更新排序值
                updated_count = 0
                for item in items:
                    new_sort_order = sort_map[item.id]
                    if item.sort_order != new_sort_order:
                        item.sort_order = new_sort_order
                        if hasattr(item, 'update_timestamp'):
                            item.update_timestamp()
                        updated_count += 1
                
                logger.info(f"批量更新物品排序: 更新了 {updated_count} 个物品")
                
                return success({
                    "updated_count": updated_count,
                    "total_items": len(items),
                    "category_id": category_id,
                    "sort_updates": sort_updates
                })
                
        except Exception as e:
            logger.error(f"批量更新物品排序失败: {e}")
            return database_error(f"批量更新物品排序时发生错误: {str(e)}")
    
    def reset_item_sort_order(self, category_id: Optional[int] = None, 
                             subcategory_id: Optional[int] = None) -> ServiceResult:
        """
        重置物品排序顺序
        
        Args:
            category_id: 可选的分类ID，如果提供则只重置该分类下的物品
            subcategory_id: 可选的子分类ID，如果提供则只重置该子分类下的物品
            
        Returns:
            ServiceResult: 操作结果
        """
        try:
            with self.db_manager.get_db_session() as session:
                # 构建查询条件
                query = session.query(Item).filter(Item.is_active == True)
                
                if category_id is not None:
                    query = query.filter(Item.category_id == category_id)
                
                if subcategory_id is not None:
                    query = query.filter(Item.subcategory_id == subcategory_id)
                
                # 按ID排序获取物品
                items = query.order_by(Item.id.asc()).all()
                
                if not items:
                    return success({
                        "updated_count": 0,
                        "message": "没有找到需要重置排序的物品"
                    })
                
                # 重置排序值，间隔100
                updated_count = 0
                for index, item in enumerate(items):
                    new_sort_order = (index + 1) * 100
                    if item.sort_order != new_sort_order:
                        item.sort_order = new_sort_order
                        if hasattr(item, 'update_timestamp'):
                            item.update_timestamp()
                        updated_count += 1
                
                logger.info(f"重置物品排序: 更新了 {updated_count} 个物品")
                
                return success({
                    "updated_count": updated_count,
                    "total_items": len(items),
                    "category_id": category_id,
                    "subcategory_id": subcategory_id
                })
                
        except Exception as e:
            logger.error(f"重置物品排序失败: {e}")
            return database_error(f"重置物品排序时发生错误: {str(e)}")
    
    def get_sort_order_info(self, category_id: Optional[int] = None) -> ServiceResult:
        """
        获取排序信息统计
        
        Args:
            category_id: 可选的分类ID
            
        Returns:
            ServiceResult: 排序信息统计
        """
        try:
            with self.db_manager.get_db_session() as session:
                query = session.query(Item).filter(Item.is_active == True)
                
                if category_id is not None:
                    query = query.filter(Item.category_id == category_id)
                
                items = query.order_by(Item.sort_order.asc(), Item.id.asc()).all()
                
                # 统计信息
                total_items = len(items)
                max_sort_order = max([item.sort_order for item in items]) if items else 0
                min_sort_order = min([item.sort_order for item in items]) if items else 0
                
                # 检查排序值重复
                sort_orders = [item.sort_order for item in items]
                duplicates = []
                seen = set()
                for sort_order in sort_orders:
                    if sort_order in seen and sort_order not in duplicates:
                        duplicates.append(sort_order)
                    seen.add(sort_order)
                
                return success({
                    "total_items": total_items,
                    "max_sort_order": max_sort_order,
                    "min_sort_order": min_sort_order,
                    "duplicate_sort_orders": duplicates,
                    "category_id": category_id,
                    "items": [
                        {
                            "id": item.id,
                            "name": item.name,
                            "sort_order": item.sort_order,
                            "category_id": item.category_id,
                            "subcategory_id": item.subcategory_id
                        }
                        for item in items
                    ]
                })
                
        except Exception as e:
            logger.error(f"获取排序信息失败: {e}")
            return database_error(f"获取排序信息时发生错误: {str(e)}")
    
    def auto_assign_sort_order(self, category_id: Optional[int] = None, 
                              start_value: int = 100, interval: int = 100) -> ServiceResult:
        """
        自动分配排序值
        
        Args:
            category_id: 可选的分类ID
            start_value: 起始排序值
            interval: 排序值间隔
            
        Returns:
            ServiceResult: 操作结果
        """
        try:
            if start_value < 0:
                return validation_error("起始排序值不能为负数")
            
            if interval <= 0:
                return validation_error("排序值间隔必须为正数")
            
            with self.db_manager.get_db_session() as session:
                query = session.query(Item).filter(Item.is_active == True)
                
                if category_id is not None:
                    query = query.filter(Item.category_id == category_id)
                
                # 按当前排序值和ID排序
                items = query.order_by(Item.sort_order.asc(), Item.id.asc()).all()
                
                if not items:
                    return success({
                        "updated_count": 0,
                        "message": "没有找到需要分配排序的物品"
                    })
                
                # 自动分配排序值
                updated_count = 0
                for index, item in enumerate(items):
                    new_sort_order = start_value + (index * interval)
                    if item.sort_order != new_sort_order:
                        item.sort_order = new_sort_order
                        if hasattr(item, 'update_timestamp'):
                            item.update_timestamp()
                        updated_count += 1
                
                logger.info(f"自动分配排序值: 更新了 {updated_count} 个物品")
                
                return success({
                    "updated_count": updated_count,
                    "total_items": len(items),
                    "start_value": start_value,
                    "interval": interval,
                    "category_id": category_id
                })
                
        except Exception as e:
            logger.error(f"自动分配排序值失败: {e}")
            return database_error(f"自动分配排序值时发生错误: {str(e)}")
