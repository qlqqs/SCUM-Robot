"""
数据库管理器 - 提供统一的数据库管理接口
"""

import os
import logging
from typing import Optional

from .config import db_config, DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_url: 数据库连接URL，如果不提供则使用默认配置
        """
        self.config = db_config if not db_url else DatabaseConfig(db_url)
        self._initialized = False
    
    def init_database(self, create_tables: bool = True) -> bool:
        """
        初始化数据库

        Args:
            create_tables: 是否自动创建表

        Returns:
            bool: 初始化是否成功
        """
        # 如果已经初始化，直接返回成功
        if self._initialized:
            return True

        try:
            # 创建引擎和会话
            if not self.config.create_engine_and_session():
                return False

            # 创建表
            if create_tables:
                if not self.config.create_tables():
                    return False

            self._initialized = True
            logger.info("数据库初始化成功")
            return True

        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """检查数据库是否已初始化"""
        return self._initialized
    
    def get_session(self):
        """获取数据库会话"""
        if not self._initialized:
            raise RuntimeError("数据库未初始化，请先调用 init_database()")
        return self.config.get_session()
    
    def get_db_session(self):
        """获取数据库会话上下文管理器"""
        if not self._initialized:
            raise RuntimeError("数据库未初始化，请先调用 init_database()")
        return self.config.get_db_session()
    
    def is_data_initialized(self) -> bool:
        """
        检查数据库数据是否已初始化

        Returns:
            bool: 数据是否已初始化
        """
        if not self._initialized:
            return False

        try:
            with self.get_db_session() as session:
                from ..models.user_models import User, VIPConfig, UserType

                # 检查是否存在超级管理员
                super_admin = session.query(User).filter(
                    User.user_type == UserType.SUPER_ADMIN
                ).first()

                # 检查是否存在VIP0配置
                vip0_config = session.query(VIPConfig).filter(
                    VIPConfig.level == 0
                ).first()

                # 如果关键数据都存在，则认为已初始化
                return super_admin is not None and vip0_config is not None

        except Exception as e:
            logger.error(f"检查数据初始化状态失败: {e}")
            return False

    def check_required_data(self) -> dict:
        """
        检查必需数据的详细状态
        只检查核心必需项：超级管理员和VIP0配置

        Returns:
            dict: 各项数据的检查结果
        """
        result = {
            'super_admin': False,
            'vip0_config': False,
        }

        if not self._initialized:
            return result

        try:
            with self.get_db_session() as session:
                from ..models.user_models import User, VIPConfig, UserType

                # 检查超级管理员
                super_admin = session.query(User).filter(
                    User.user_type == UserType.SUPER_ADMIN
                ).first()
                result['super_admin'] = super_admin is not None

                # 检查VIP0配置
                vip0_config = session.query(VIPConfig).filter(
                    VIPConfig.level == 0
                ).first()
                result['vip0_config'] = vip0_config is not None

        except Exception as e:
            logger.error(f"检查必需数据状态失败: {e}")

        return result

    def auto_initialize_data(self) -> bool:
        """
        自动初始化缺失的数据

        Returns:
            bool: 初始化是否成功
        """
        if not self._initialized:
            logger.error("数据库未初始化，无法创建数据")
            return False

        try:
            with self.get_db_session() as session:
                from .init_data import get_bootstrap_admin_settings, initialize_database

                bootstrap_settings = get_bootstrap_admin_settings()

                # 调用现有的初始化函数
                success = initialize_database(
                    session,
                    admin_username=bootstrap_settings["username"],
                    admin_password=bootstrap_settings["password"]
                )

                if success:
                    logger.info("数据库数据初始化成功")
                else:
                    logger.error("数据库数据初始化失败")

                return success

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"自动初始化数据失败: {e}")
            return False

    def get_initialization_status(self) -> dict:
        """
        获取详细的初始化状态报告

        Returns:
            dict: 初始化状态报告
        """
        status = {
            'database_initialized': self._initialized,
            'data_initialized': False,
            'required_data': {},
            'missing_data': [],
            'recommendations': []
        }

        if self._initialized:
            status['data_initialized'] = self.is_data_initialized()
            status['required_data'] = self.check_required_data()

            # 找出缺失的数据
            for key, exists in status['required_data'].items():
                if not exists:
                    status['missing_data'].append(key)

            # 生成建议
            if status['missing_data']:
                status['recommendations'].append("建议运行 auto_initialize_data() 创建缺失数据")
            else:
                status['recommendations'].append("数据库数据完整，无需额外操作")
        else:
            status['recommendations'].append("请先运行 init_database() 初始化数据库")

        return status

    def close(self):
        """关闭数据库连接"""
        if self.config.engine:
            self.config.engine.dispose()
            logger.info("数据库连接已关闭")
    
    def reset_database(self) -> bool:
        """重置数据库（删除所有表并重新创建）"""
        try:
            if not self._initialized:
                logger.error("数据库未初始化")
                return False
            
            from ..models import Base
            
            # 删除所有表
            Base.metadata.drop_all(bind=self.config.engine)
            logger.info("所有数据库表已删除")
            
            # 重新创建表
            if self.config.create_tables():
                logger.info("数据库重置成功")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"数据库重置失败: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """获取数据库信息"""
        # 检查数据库是否真正初始化（不仅仅是当前实例状态）
        actual_initialized = self._check_database_actually_initialized()

        return {
            'database_url': self.config.db_url,
            'initialized': actual_initialized,
            'engine': str(self.config.engine) if self.config.engine else None
        }

    def _check_database_actually_initialized(self) -> bool:
        """检查数据库是否真正已初始化"""
        try:
            # 首先确保引擎存在
            if not self.config.engine:
                # 尝试创建引擎
                if not self.config.create_engine_and_session():
                    return False

            # 检查数据库文件是否存在（对于SQLite）
            if 'sqlite' in self.config.db_url:
                import re
                # 从URL中提取文件路径
                match = re.search(r'sqlite:///(.+)', self.config.db_url)
                if match:
                    db_file_path = match.group(1)
                    if not os.path.exists(db_file_path):
                        return False

            # 检查关键表是否存在
            from sqlalchemy import inspect
            inspector = inspect(self.config.engine)
            existing_tables = inspector.get_table_names()

            # 检查是否存在我们的核心表
            required_tables = ['categories', 'subcategories', 'items']
            for table in required_tables:
                if table not in existing_tables:
                    return False

            return True

        except Exception as e:
            logger.error(f"检查数据库初始化状态时出错: {e}")
            return False
