"""
SQLite数据库模块

这是一个功能完整的数据库模块，提供了：
- 数据模型定义 (models)
- 数据库连接管理 (database)
- 业务逻辑服务 (services)

使用方式:
    from bakend.modules.sql import DatabaseManager, ItemService, CategoryService
    
    # 初始化数据库
    db_manager = DatabaseManager()
    db_manager.init_database()
    
    # 使用服务
    item_service = ItemService(db_manager)
    category_service = CategoryService(db_manager)
"""

# 延迟导入避免循环依赖
def _lazy_import():
    """延迟导入模块"""
    try:
        from .database.manager import DatabaseManager
        from .services.item_service import ItemService
        from .services.category_service import CategoryService
        return DatabaseManager, ItemService, CategoryService
    except ImportError as e:
        # 如果依赖未安装，返回None
        return None, None, None

# 导出的类
DatabaseManager, ItemService, CategoryService = _lazy_import()

__all__ = [
    'DatabaseManager',
    'ItemService', 
    'CategoryService'
]

# 模块级别的便捷函数
def create_database_manager(db_url=None):
    """创建数据库管理器的便捷函数"""
    if DatabaseManager is None:
        raise ImportError("数据库模块依赖未安装，请先安装 sqlalchemy 和 python-dotenv")
    return DatabaseManager(db_url)

def get_item_service(db_manager=None):
    """获取物品服务的便捷函数"""
    if ItemService is None:
        raise ImportError("数据库模块依赖未安装，请先安装 sqlalchemy 和 python-dotenv")
    return ItemService(db_manager)

def get_category_service(db_manager=None):
    """获取类目服务的便捷函数"""
    if CategoryService is None:
        raise ImportError("数据库模块依赖未安装，请先安装 sqlalchemy 和 python-dotenv")
    return CategoryService(db_manager)