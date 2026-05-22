"""
数据库连接和会话管理
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import Generator, Optional
import logging
from dotenv import load_dotenv

from ..models import Base

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or self._get_default_db_url()
        self.engine = None
        self.SessionLocal = None
    
    def _get_default_db_url(self) -> str:
        """获取默认数据库URL"""
        # 从环境变量获取，如果没有则使用默认SQLite
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            # 检查是否在exe环境中
            if getattr(sys, 'frozen', False):
                # exe环境：使用exe目录下的data文件夹
                import sys
                from pathlib import Path
                exe_dir = Path(sys.executable).parent
                data_dir = exe_dir / "data"
                data_dir.mkdir(exist_ok=True)
                db_path = data_dir / "scum_robot.db"
                db_url = f'sqlite:///{db_path}'
            else:
                # 开发环境：使用相对路径
                db_url = 'sqlite:///bakend/modules/sql/scum_robot.db'
        return db_url
    
    def create_engine_and_session(self):
        """创建数据库引擎和会话工厂"""
        # 如果引擎已存在，直接返回成功
        if self.engine is not None and self.SessionLocal is not None:
            return True

        try:
            self.engine = create_engine(
                self.db_url,
                echo=False,  # 设置为True可以看到SQL语句
                pool_pre_ping=True,
                connect_args={"check_same_thread": False} if "sqlite" in self.db_url else {}
            )

            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            logger.info(f"数据库引擎创建成功: {self.db_url}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"数据库引擎创建失败: {e}")
            return False
    
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
            return True
        except SQLAlchemyError as e:
            logger.error(f"数据库表创建失败: {e}")
            return False
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        if not self.SessionLocal:
            raise RuntimeError("数据库未初始化，请先调用 create_engine_and_session()")
        return self.SessionLocal()
    
    @contextmanager
    def get_db_session(self) -> Generator[Session, None, None]:
        """上下文管理器形式的数据库会话"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()


# 全局数据库配置实例
db_config = DatabaseConfig()