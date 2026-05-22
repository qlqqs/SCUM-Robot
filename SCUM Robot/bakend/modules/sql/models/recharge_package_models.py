"""
充值套餐相关数据模型
"""

from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, Index
from sqlalchemy.orm import Session

from . import Base, TimestampMixin


class RechargePackage(Base, TimestampMixin):
    """充值套餐表"""
    __tablename__ = 'recharge_packages'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='套餐ID')
    
    # 套餐基本信息
    name = Column(String(64), nullable=False, comment='套餐名称')
    description = Column(String(255), comment='套餐描述')
    tag = Column(String(32), comment='标签（如：性价比之选、热门推荐）')
    product_name = Column(String(64), default='商城币充值', comment='支付项目名称（显示在支付宝账单中）')
    
    # 价格信息
    price = Column(Float(precision=2), nullable=False, comment='充值金额（元）')
    currency = Column(String(3), default='CNY', comment='货币类型')
    
    # 商城币信息
    coins = Column(Integer, nullable=False, comment='获得商城币数量')
    bonus_coins = Column(Integer, default=0, comment='额外赠送商城币')
    total_coins = Column(Integer, nullable=False, comment='总共获得商城币（coins + bonus_coins）')
    
    # 显示信息
    icon = Column(String(255), comment='套餐图标URL')
    badge = Column(String(32), comment='徽章（如：HOT、NEW、推荐）')
    sort_order = Column(Integer, default=0, comment='排序顺序（数字越小越靠前）')
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_hot = Column(Boolean, default=False, comment='是否热门')
    is_recommended = Column(Boolean, default=False, comment='是否推荐')
    
    # 限制信息
    daily_limit = Column(Integer, comment='每日购买限制（NULL表示不限制）')
    total_limit = Column(Integer, comment='总购买限制（NULL表示不限制）')
    user_daily_limit = Column(Integer, comment='用户每日购买限制（NULL表示不限制）')
    user_total_limit = Column(Integer, comment='用户总购买限制（NULL表示不限制）')
    
    # 时间限制
    start_time = Column(String(20), comment='开始时间（格式：YYYY-MM-DD HH:MM:SS）')
    end_time = Column(String(20), comment='结束时间（格式：YYYY-MM-DD HH:MM:SS）')
    
    # 额外信息
    extra_info = Column(Text, comment='额外信息（JSON格式）')
    
    # 索引
    __table_args__ = (
        Index('idx_recharge_packages_active', 'is_active'),
        Index('idx_recharge_packages_sort', 'sort_order'),
        Index('idx_recharge_packages_price', 'price'),
    )
    
    def to_dict(self, include_stats: bool = False) -> Dict[str, Any]:
        """转换为字典格式"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'tag': self.tag,
            'product_name': self.product_name,
            'price': float(self.price),
            'currency': self.currency,
            'coins': self.coins,
            'bonus_coins': self.bonus_coins,
            'total_coins': self.total_coins,
            'icon': self.icon,
            'badge': self.badge,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'is_hot': self.is_hot,
            'is_recommended': self.is_recommended,
            'daily_limit': self.daily_limit,
            'total_limit': self.total_limit,
            'user_daily_limit': self.user_daily_limit,
            'user_total_limit': self.user_total_limit,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_stats:
            # 可以添加统计信息，如购买次数等
            pass
        
        return data
    
    def is_available(self) -> bool:
        """检查套餐是否可用"""
        if not self.is_active:
            return False
        
        # 检查时间限制
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if self.start_time and now < self.start_time:
            return False
        
        if self.end_time and now > self.end_time:
            return False
        
        return True
    
    def calculate_total_coins(self):
        """计算总商城币"""
        self.total_coins = self.coins + (self.bonus_coins or 0)
    
    @classmethod
    def get_active_packages(cls, session: Session, order_by_sort: bool = True):
        """获取所有启用的套餐"""
        query = session.query(cls).filter(cls.is_active == True)
        
        if order_by_sort:
            query = query.order_by(cls.sort_order.asc(), cls.price.asc())
        
        return query.all()
    
    @classmethod
    def get_hot_packages(cls, session: Session, limit: int = 3):
        """获取热门套餐"""
        return session.query(cls).filter(
            cls.is_active == True,
            cls.is_hot == True
        ).order_by(cls.sort_order.asc()).limit(limit).all()
    
    @classmethod
    def get_recommended_packages(cls, session: Session, limit: int = 3):
        """获取推荐套餐"""
        return session.query(cls).filter(
            cls.is_active == True,
            cls.is_recommended == True
        ).order_by(cls.sort_order.asc()).limit(limit).all()
    
    def __repr__(self):
        return f"<RechargePackage(id={self.id}, name='{self.name}', price={self.price}, coins={self.total_coins})>"


class RechargeRecord(Base, TimestampMixin):
    """充值记录表"""
    __tablename__ = 'recharge_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='记录ID')
    
    # 关联信息
    user_id = Column(Integer, nullable=False, comment='用户ID')
    package_id = Column(Integer, nullable=False, comment='套餐ID')
    order_id = Column(String(64), nullable=False, unique=True, comment='订单号')
    
    # 套餐快照（记录购买时的套餐信息）
    package_name = Column(String(64), nullable=False, comment='套餐名称')
    price = Column(Float(precision=2), nullable=False, comment='充值金额')
    coins = Column(Integer, nullable=False, comment='基础商城币')
    bonus_coins = Column(Integer, default=0, comment='赠送商城币')
    total_coins = Column(Integer, nullable=False, comment='总商城币')
    
    # 状态信息
    status = Column(String(16), default='pending', comment='状态（pending/success/failed）')
    
    # 索引
    __table_args__ = (
        Index('idx_recharge_records_user', 'user_id'),
        Index('idx_recharge_records_package', 'package_id'),
        Index('idx_recharge_records_order', 'order_id'),
        Index('idx_recharge_records_status', 'status'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'package_id': self.package_id,
            'order_id': self.order_id,
            'package_name': self.package_name,
            'price': float(self.price),
            'coins': self.coins,
            'bonus_coins': self.bonus_coins,
            'total_coins': self.total_coins,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<RechargeRecord(id={self.id}, user_id={self.user_id}, package='{self.package_name}', total_coins={self.total_coins})>"

