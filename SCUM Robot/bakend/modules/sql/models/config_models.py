"""
配置系统数据模型

包含系统配置和配置历史记录的数据模型
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from . import Base, TimestampMixin


class ConfigType(PyEnum):
    """配置类型枚举"""
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    JSON = "json"
    ENCRYPTED = "encrypted"


class ConfigGroup(PyEnum):
    """配置分组枚举"""
    SYSTEM = "system"
    PAYMENT = "payment"
    EMAIL = "email"
    SMS = "sms"
    ROBOT = "robot"
    SECURITY = "security"
    CUSTOM = "custom"


class SystemConfig(Base, TimestampMixin):
    """系统配置表"""
    __tablename__ = 'system_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='配置ID')
    key = Column(String(100), nullable=False, unique=True, index=True, comment='配置键')
    value = Column(Text, comment='配置值')
    type = Column(SQLEnum(ConfigType), nullable=False, default=ConfigType.STRING, comment='数据类型')
    group_name = Column(String(50), nullable=False, index=True, comment='配置分组')
    description = Column(Text, comment='配置描述')
    is_public = Column(Boolean, default=False, index=True, comment='是否公开')
    is_encrypted = Column(Boolean, default=False, comment='是否加密')
    sort_order = Column(Integer, default=0, comment='排序顺序')
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    # 关联关系
    history = relationship("ConfigHistory", back_populates="config", cascade="all, delete-orphan")
    
    def to_dict(self, include_value=True):
        """
        转换为字典
        
        Args:
            include_value: 是否包含配置值
        
        Returns:
            dict: 配置字典
        """
        data = {
            'id': self.id,
            'key': self.key,
            'type': self.type.value if isinstance(self.type, PyEnum) else self.type,
            'group_name': self.group_name,
            'description': self.description,
            'is_public': self.is_public,
            'is_encrypted': self.is_encrypted,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_value:
            data['value'] = self.value
        return data


class ConfigHistory(Base):
    """配置历史记录表"""
    __tablename__ = 'config_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='历史记录ID')
    config_id = Column(Integer, ForeignKey('system_configs.id'), nullable=False, index=True, comment='配置ID')
    old_value = Column(Text, comment='旧值')
    new_value = Column(Text, comment='新值')
    changed_by = Column(Integer, ForeignKey('users.id'), comment='修改人ID')
    changed_at = Column(DateTime, default=datetime.utcnow, index=True, comment='修改时间')
    change_reason = Column(Text, comment='修改原因')
    
    # 关联关系
    config = relationship("SystemConfig", back_populates="history")
    user = relationship("User")
    
    def to_dict(self):
        """
        转换为字典
        
        Returns:
            dict: 历史记录字典
        """
        return {
            'id': self.id,
            'config_id': self.config_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'changed_by': self.changed_by,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'change_reason': self.change_reason
        }

