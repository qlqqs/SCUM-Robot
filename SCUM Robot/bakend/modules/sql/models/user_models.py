"""
用户系统相关数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean, Enum, BigInteger, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
from enum import Enum as PyEnum
from . import Base, TimestampMixin


class UserType(PyEnum):
    """用户类型枚举"""
    SUPER_ADMIN = "super_admin"  # 超级管理员
    ADMIN = "admin"              # 普通管理员
    USER = "user"                # 普通用户


class GiftType(PyEnum):
    """礼包类型枚举"""
    ONE_TIME = "one_time"       # 一次性礼包
    DAILY = "daily"             # 每日礼包
    LIMITED_QUANTITY = "limited_quantity"  # 限量礼包
    LIMITED_TIME = "limited_time"          # 限时礼包
    LIMITED_TIME_QUANTITY = "limited_time_quantity"  # 限时限量礼包


class User(Base, TimestampMixin):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='用户ID')
    steam_id = Column(String(20), nullable=False, unique=True, comment='Steam ID')
    username = Column(String(50), nullable=False, unique=True, comment='用户名/昵称')
    email = Column(String(100), unique=True, comment='邮箱')
    phone = Column(String(20), comment='手机号')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    user_type = Column(Enum(UserType), default=UserType.USER, comment='用户类型')
    is_active = Column(Boolean, default=True, comment='账户是否激活')
    last_login_at = Column(DateTime, comment='最后登录时间')
    login_count = Column(Integer, default=0, comment='登录次数')

    # 签到相关字段
    today_signed_in = Column(Boolean, default=False, comment='今日是否已签到')
    consecutive_signin_days = Column(Integer, default=0, comment='连续签到天数')
    total_signin_days = Column(Integer, default=0, comment='累计签到天数')
    last_signin_date = Column(Date, comment='最后签到日期')

    # 等级系统字段
    pass_level = Column(Integer, default=0, comment='通行证等级')
    pass_exp = Column(Integer, default=0, comment='通行证经验值')
    vip_level = Column(Integer, default=0, comment='VIP等级 (0=普通用户)')
    vip_expire_date = Column(Date, default=date(9999, 12, 31), comment='VIP到期日期 (9999-12-31表示永不到期)')

    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    assets = relationship("UserAssets", back_populates="user", uselist=False, cascade="all, delete-orphan")
    gift_records = relationship("UserGiftRecord", back_populates="user", cascade="all, delete-orphan")
    admin_permissions = relationship("AdminPermission", back_populates="user", foreign_keys="AdminPermission.user_id", cascade="all, delete-orphan")
    operation_logs = relationship("UserOperationLog", back_populates="user", cascade="all, delete-orphan")
    character_stats = relationship("UserCharacterStats", back_populates="user", uselist=False, cascade="all, delete-orphan")
    payment_orders = relationship("PaymentOrder", back_populates="user", cascade="all, delete-orphan")
    vip_upgrade_history = relationship("VIPUpgradeHistory", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, steam_id={self.steam_id}, username='{self.username}', type={self.user_type.value})>"
    
    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.user_type in [UserType.ADMIN, UserType.SUPER_ADMIN]
    
    def is_super_admin(self) -> bool:
        """检查是否为超级管理员"""
        return self.user_type == UserType.SUPER_ADMIN


class UserAssets(Base, TimestampMixin):
    """用户资产表"""
    __tablename__ = 'user_assets'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='资产ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True, comment='用户ID')
    game_coins = Column(Integer, default=0, comment='游戏币数量')
    shop_coins = Column(Integer, default=0, comment='商城币数量')
    points = Column(Integer, default=0, comment='积分数量')
    total_recharge = Column(Float(precision=2), default=0.0, comment='累计充值金额')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    user = relationship("User", back_populates="assets")
    
    def __repr__(self):
        return f"<UserAssets(user_id={self.user_id}, game_coins={self.game_coins}, shop_coins={self.shop_coins}, points={self.points})>"


class GiftPackage(Base, TimestampMixin):
    """礼包定义表"""
    __tablename__ = 'gift_packages'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='礼包ID')
    name = Column(String(100), nullable=False, comment='礼包名称')
    description = Column(Text, comment='礼包描述')
    gift_type = Column(Enum(GiftType), nullable=False, comment='礼包类型')
    items_config = Column(Text, nullable=False, comment='物品配置JSON')
    image_url = Column(String(500), nullable=True, comment='礼包图片URL')
    is_active = Column(Boolean, default=True, comment='是否启用')
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    max_claims = Column(Integer, default=1, comment='最大领取次数(-1为无限制)')
    cooldown_hours = Column(Integer, default=24, comment='冷却时间(小时)')
    required_level = Column(Integer, default=0, comment='所需等级')
    total_quantity = Column(Integer, nullable=True, comment='全服总数量，null表示无限制')
    claimed_quantity = Column(Integer, default=0, comment='已领取数量')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    user_records = relationship("UserGiftRecord", back_populates="gift_package")
    
    def __repr__(self):
        return f"<GiftPackage(id={self.id}, name='{self.name}', type={self.gift_type.value})>"


class UserGiftRecord(Base, TimestampMixin):
    """用户礼包领取记录表"""
    __tablename__ = 'user_gift_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='记录ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    gift_package_id = Column(Integer, ForeignKey('gift_packages.id'), nullable=False, comment='礼包ID')
    claimed_at = Column(DateTime, default=datetime.utcnow, comment='领取时间')
    items_received = Column(Text, comment='实际获得的物品JSON')
    status = Column(String(20), default='success', comment='领取状态')
    
    # 关联关系
    user = relationship("User", back_populates="gift_records")
    gift_package = relationship("GiftPackage", back_populates="user_records")
    
    def __repr__(self):
        return f"<UserGiftRecord(user_id={self.user_id}, gift_id={self.gift_package_id}, claimed_at={self.claimed_at})>"


class AdminPermission(Base, TimestampMixin):
    """管理员权限表"""
    __tablename__ = 'admin_permissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='权限ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    permission_key = Column(String(50), nullable=False, comment='权限键')
    permission_name = Column(String(100), nullable=False, comment='权限名称')
    granted_by = Column(Integer, ForeignKey('users.id'), comment='授权人ID')
    granted_at = Column(DateTime, default=datetime.utcnow, comment='授权时间')
    
    # 关联关系
    user = relationship("User", back_populates="admin_permissions", foreign_keys=[user_id])
    granter = relationship("User", foreign_keys=[granted_by], post_update=True)
    
    def __repr__(self):
        return f"<AdminPermission(user_id={self.user_id}, permission='{self.permission_key}')>"


class UserOperationLog(Base, TimestampMixin):
    """用户操作日志表"""
    __tablename__ = 'user_operation_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='日志ID')
    user_id = Column(Integer, ForeignKey('users.id'), comment='操作用户ID')
    operation_type = Column(String(50), nullable=False, comment='操作类型')
    operation_desc = Column(String(200), comment='操作描述')
    target_user_id = Column(Integer, comment='目标用户ID')
    ip_address = Column(String(45), comment='IP地址')
    user_agent = Column(String(500), comment='用户代理')
    extra_data = Column(Text, comment='额外数据JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关联关系
    user = relationship("User", back_populates="operation_logs")
    
    def __repr__(self):
        return f"<UserOperationLog(user_id={self.user_id}, type='{self.operation_type}', time={self.created_at})>"


class UserCharacterStats(Base, TimestampMixin):
    """游戏人物能力表"""
    __tablename__ = 'user_character_stats'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True, comment='用户ID')
    steam_id = Column(String(20), nullable=False, unique=True, comment='Steam ID')
    strength = Column(Integer, default=10, comment='力量 (1-100)')
    stamina = Column(Integer, default=10, comment='体力 (1-100)')
    intelligence = Column(Integer, default=10, comment='智力 (1-100)')
    agility = Column(Integer, default=10, comment='敏捷 (1-100)')
    last_sync_time = Column(DateTime, comment='最后同步时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关联关系
    user = relationship("User", back_populates="character_stats")

    def get_total_stats(self):
        """获取总能力值"""
        return self.strength + self.stamina + self.intelligence + self.agility

    def validate_stats(self):
        """验证能力值范围"""
        for stat in [self.strength, self.stamina, self.intelligence, self.agility]:
            if stat < 1 or stat > 100:
                return False
        return True

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'steam_id': self.steam_id,
            'strength': self.strength,
            'stamina': self.stamina,
            'intelligence': self.intelligence,
            'agility': self.agility,
            'total_stats': self.get_total_stats(),
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<UserCharacterStats(id={self.id}, user_id={self.user_id}, total_stats={self.get_total_stats()})>"


class VIPConfig(Base, TimestampMixin):
    """VIP配置表"""
    __tablename__ = 'vip_configs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    level = Column(Integer, nullable=False, unique=True, comment='VIP等级')
    name = Column(String(50), nullable=False, comment='等级名称')
    daily_gift_id = Column(Integer, ForeignKey('gift_packages.id'), comment='每日礼包ID')
    level_gift_id = Column(Integer, ForeignKey('gift_packages.id'), comment='等级礼包ID（升级时获得）')
    upgrade_required_points = Column(Integer, default=0, comment='升级所需消费积分')
    enable_login_announcement = Column(Boolean, default=False, comment='是否开启进服公告')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关联关系
    daily_gift = relationship("GiftPackage", foreign_keys=[daily_gift_id])
    level_gift = relationship("GiftPackage", foreign_keys=[level_gift_id])

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'level': self.level,
            'name': self.name,
            'daily_gift_id': self.daily_gift_id,
            'level_gift_id': self.level_gift_id,
            'upgrade_required_points': self.upgrade_required_points,
            'enable_login_announcement': self.enable_login_announcement,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<VIPConfig(id={self.id}, level={self.level}, name='{self.name}')>"


class PassConfig(Base, TimestampMixin):
    """通行证配置表"""
    __tablename__ = 'pass_configs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    level = Column(Integer, nullable=False, unique=True, comment='通行证等级')
    required_exp = Column(Integer, nullable=False, comment='所需经验值')
    rewards = Column(Text, comment='等级奖励 (JSON格式)')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    def to_dict(self):
        """转换为字典"""
        import json
        return {
            'id': self.id,
            'level': self.level,
            'required_exp': self.required_exp,
            'rewards': json.loads(self.rewards) if self.rewards else {},
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<PassConfig(id={self.id}, level={self.level}, required_exp={self.required_exp})>"


class VIPUpgradeHistory(Base, TimestampMixin):
    """VIP升级历史表"""
    __tablename__ = 'vip_upgrade_history'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    old_level = Column(Integer, nullable=False, comment='原VIP等级')
    new_level = Column(Integer, nullable=False, comment='新VIP等级')
    upgrade_type = Column(String(20), nullable=False, default='auto', comment='升级类型 (auto/manual)')
    trigger_points = Column(Integer, nullable=False, comment='触发升级时的积分数量')
    required_points = Column(Integer, nullable=False, comment='升级所需积分')
    upgrade_reason = Column(Text, comment='升级原因说明')
    created_at = Column(DateTime, default=datetime.utcnow, comment='升级时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关联关系
    user = relationship("User", back_populates="vip_upgrade_history")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'old_level': self.old_level,
            'new_level': self.new_level,
            'upgrade_type': self.upgrade_type,
            'trigger_points': self.trigger_points,
            'required_points': self.required_points,
            'upgrade_reason': self.upgrade_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<VIPUpgradeHistory(id={self.id}, user_id={self.user_id}, {self.old_level}->{self.new_level})>"
