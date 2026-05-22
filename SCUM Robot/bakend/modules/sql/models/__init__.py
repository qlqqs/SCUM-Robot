"""
数据库模型模块
"""

try:
    from sqlalchemy import create_engine, Column, DateTime
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from datetime import datetime
    from typing import Optional

    # 创建基础模型类
    Base = declarative_base()

    # 基础时间戳混入类
    class TimestampMixin:
        """为模型添加创建和更新时间戳"""
        created_at = Column(DateTime, default=datetime.now, nullable=False, comment='创建时间')
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment='更新时间')

        def update_timestamp(self):
            """更新时间戳"""
            self.updated_at = datetime.now()

    # 导入具体模型
    from .item_models import Category, SubCategory, Item
    from .user_models import (
        User, UserAssets, GiftPackage, UserGiftRecord,
        AdminPermission, UserOperationLog, UserType, GiftType, UserCharacterStats, VIPConfig, PassConfig, VIPUpgradeHistory
    )
    from .payment_models import PaymentConfig, PaymentOperationLog
    from .payment_order_models import PaymentOrder, PaymentCallback, PaymentOrderStatus
    from .recharge_package_models import RechargePackage, RechargeRecord
    from .config_models import SystemConfig, ConfigHistory, ConfigType, ConfigGroup

    __all__ = [
        'Base',
        'TimestampMixin',
        'Category',
        'SubCategory',
        'Item',
        'User',
        'UserAssets',
        'GiftPackage',
        'UserGiftRecord',
        'AdminPermission',
        'UserOperationLog',
        'UserType',
        'GiftType',
        'UserCharacterStats',
        'VIPConfig',
        'PassConfig',
        'VIPUpgradeHistory',
        'PaymentConfig',
        'PaymentOperationLog',
        'PaymentOrder',
        'PaymentCallback',
        'PaymentOrderStatus',
        'RechargePackage',
        'RechargeRecord',
        'SystemConfig',
        'ConfigHistory',
        'ConfigType',
        'ConfigGroup'
    ]

except ImportError:
    # 如果SQLAlchemy未安装，定义占位符
    Base = None
    Category = None
    SubCategory = None
    Item = None
    User = None
    UserAssets = None
    GiftPackage = None
    UserGiftRecord = None
    AdminPermission = None
    UserOperationLog = None
    UserType = None
    GiftType = None
    UserCharacterStats = None
    VIPConfig = None
    PassConfig = None

    __all__ = []