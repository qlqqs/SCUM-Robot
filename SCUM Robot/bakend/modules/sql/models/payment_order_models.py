"""
支付订单相关数据模型
"""

import json
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from . import Base, TimestampMixin


class PaymentOrderStatus(Enum):
    """支付订单状态枚举"""
    PENDING = "pending"          # 待支付
    PROCESSING = "processing"    # 处理中
    SUCCESS = "success"          # 支付成功
    FAILED = "failed"           # 支付失败
    CANCELLED = "cancelled"      # 已取消
    REFUNDED = "refunded"       # 已退款
    EXPIRED = "expired"         # 已过期


class PaymentOrder(Base, TimestampMixin):
    """支付订单表"""
    __tablename__ = 'payment_orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='订单ID')
    order_id = Column(String(64), nullable=False, unique=True, comment='订单号')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    
    # 订单基本信息
    amount = Column(Float(precision=2), nullable=False, comment='支付金额（元）')
    currency = Column(String(3), default='CNY', comment='货币类型')
    description = Column(String(255), nullable=False, comment='订单描述')
    package_id = Column(Integer, ForeignKey('recharge_packages.id'), comment='充值套餐ID')
    
    # 支付相关信息
    payment_config_id = Column(Integer, ForeignKey('payment_configs.id'), nullable=False, comment='支付配置ID')
    provider_code = Column(String(32), nullable=False, comment='支付提供商代码')
    provider_name = Column(String(64), nullable=False, comment='支付提供商名称')
    
    # 订单状态
    status = Column(String(16), default=PaymentOrderStatus.PENDING.value, comment='订单状态')
    
    # 支付平台信息
    platform_order_id = Column(String(128), comment='支付平台订单号')
    platform_transaction_id = Column(String(128), comment='支付平台交易号')
    
    # 支付数据（JSON格式存储支付平台返回的数据）
    payment_data = Column(Text, comment='支付数据（JSON）')
    callback_data = Column(Text, comment='回调数据（JSON）')
    
    # 时间信息
    paid_at = Column(DateTime, comment='支付完成时间')
    expired_at = Column(DateTime, comment='订单过期时间')
    
    # 业务相关
    coins_added = Column(Integer, default=0, comment='已增加的商城币数量')
    is_coins_added = Column(Boolean, default=False, comment='是否已增加商城币')
    
    # 回调处理
    callback_count = Column(Integer, default=0, comment='回调处理次数')
    last_callback_at = Column(DateTime, comment='最后回调时间')
    callback_ip = Column(String(45), comment='回调IP地址')
    
    # 关联关系
    user = relationship("User", back_populates="payment_orders")
    payment_config = relationship("PaymentConfig")
    
    # 索引
    __table_args__ = (
        Index('idx_payment_orders_user_id', 'user_id'),
        Index('idx_payment_orders_status', 'status'),
        Index('idx_payment_orders_provider', 'provider_code'),
        Index('idx_payment_orders_platform_order', 'platform_order_id'),
    )
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """转换为字典格式"""
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'description': self.description,
            'provider_code': self.provider_code,
            'provider_name': self.provider_name,
            'status': self.status,
            'coins_added': self.coins_added,
            'is_coins_added': self.is_coins_added,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'expired_at': self.expired_at.isoformat() if self.expired_at else None
        }
        
        if include_sensitive:
            data.update({
                'platform_order_id': self.platform_order_id,
                'platform_transaction_id': self.platform_transaction_id,
                'payment_data': json.loads(self.payment_data) if self.payment_data else None,
                'callback_data': json.loads(self.callback_data) if self.callback_data else None,
                'callback_count': self.callback_count,
                'last_callback_at': self.last_callback_at.isoformat() if self.last_callback_at else None,
                'callback_ip': self.callback_ip
            })
        
        return data
    
    def set_payment_data(self, data: Dict[str, Any]):
        """设置支付数据"""
        self.payment_data = json.dumps(data, ensure_ascii=False)
    
    def get_payment_data(self) -> Optional[Dict[str, Any]]:
        """获取支付数据"""
        if self.payment_data:
            try:
                return json.loads(self.payment_data)
            except json.JSONDecodeError:
                return None
        return None
    
    def set_callback_data(self, data: Dict[str, Any]):
        """设置回调数据"""
        self.callback_data = json.dumps(data, ensure_ascii=False)
    
    def get_callback_data(self) -> Optional[Dict[str, Any]]:
        """获取回调数据"""
        if self.callback_data:
            try:
                return json.loads(self.callback_data)
            except json.JSONDecodeError:
                return None
        return None
    
    def is_pending(self) -> bool:
        """是否为待支付状态"""
        return self.status == PaymentOrderStatus.PENDING.value
    
    def is_success(self) -> bool:
        """是否为支付成功状态"""
        return self.status == PaymentOrderStatus.SUCCESS.value
    
    def is_failed(self) -> bool:
        """是否为支付失败状态"""
        return self.status == PaymentOrderStatus.FAILED.value
    
    def can_process_callback(self) -> bool:
        """是否可以处理回调"""
        return self.status in [PaymentOrderStatus.PENDING.value, PaymentOrderStatus.PROCESSING.value]
    
    def mark_as_processing(self):
        """标记为处理中"""
        self.status = PaymentOrderStatus.PROCESSING.value
        self.update_timestamp()
    
    def mark_as_success(self, platform_transaction_id: str = None, paid_at: datetime = None):
        """标记为支付成功"""
        self.status = PaymentOrderStatus.SUCCESS.value
        if platform_transaction_id:
            self.platform_transaction_id = platform_transaction_id
        self.paid_at = paid_at or datetime.utcnow()
        self.update_timestamp()
    
    def mark_as_failed(self):
        """标记为支付失败"""
        self.status = PaymentOrderStatus.FAILED.value
        self.update_timestamp()
    
    def increment_callback_count(self, callback_ip: str = None):
        """增加回调次数"""
        self.callback_count += 1
        self.last_callback_at = datetime.utcnow()
        if callback_ip:
            self.callback_ip = callback_ip
        self.update_timestamp()
    
    def __repr__(self):
        return f"<PaymentOrder(id={self.id}, order_id='{self.order_id}', amount={self.amount}, status='{self.status}')>"


class PaymentCallback(Base, TimestampMixin):
    """支付回调记录表"""
    __tablename__ = 'payment_callbacks'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='回调记录ID')
    order_id = Column(String(64), ForeignKey('payment_orders.order_id'), nullable=False, comment='订单号')
    
    # 回调信息
    callback_type = Column(String(32), nullable=False, comment='回调类型（notify/return）')
    provider_code = Column(String(32), nullable=False, comment='支付提供商代码')
    
    # 请求信息
    request_method = Column(String(8), nullable=False, comment='请求方法')
    request_url = Column(String(512), comment='请求URL')
    request_headers = Column(Text, comment='请求头（JSON）')
    request_body = Column(Text, comment='请求体')
    request_ip = Column(String(45), comment='请求IP')
    
    # 处理结果
    is_valid = Column(Boolean, default=False, comment='签名验证是否通过')
    processing_status = Column(String(16), comment='处理状态')
    processing_result = Column(Text, comment='处理结果（JSON）')
    error_message = Column(String(512), comment='错误信息')
    
    # 响应信息
    response_status = Column(Integer, comment='响应状态码')
    response_body = Column(Text, comment='响应内容')
    
    # 处理时间
    processing_time = Column(Float, comment='处理耗时（秒）')
    
    # 关联关系
    payment_order = relationship("PaymentOrder")
    
    # 索引
    __table_args__ = (
        Index('idx_payment_callbacks_order_id', 'order_id'),
        Index('idx_payment_callbacks_provider', 'provider_code'),
        Index('idx_payment_callbacks_is_valid', 'is_valid'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'callback_type': self.callback_type,
            'provider_code': self.provider_code,
            'request_method': self.request_method,
            'request_ip': self.request_ip,
            'is_valid': self.is_valid,
            'processing_status': self.processing_status,
            'error_message': self.error_message,
            'response_status': self.response_status,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def set_request_headers(self, headers: Dict[str, str]):
        """设置请求头"""
        self.request_headers = json.dumps(dict(headers), ensure_ascii=False)
    
    def get_request_headers(self) -> Optional[Dict[str, str]]:
        """获取请求头"""
        if self.request_headers:
            try:
                return json.loads(self.request_headers)
            except json.JSONDecodeError:
                return None
        return None
    
    def set_processing_result(self, result: Dict[str, Any]):
        """设置处理结果"""
        self.processing_result = json.dumps(result, ensure_ascii=False)
    
    def get_processing_result(self) -> Optional[Dict[str, Any]]:
        """获取处理结果"""
        if self.processing_result:
            try:
                return json.loads(self.processing_result)
            except json.JSONDecodeError:
                return None
        return None
    
    def __repr__(self):
        return f"<PaymentCallback(id={self.id}, order_id='{self.order_id}', provider='{self.provider_code}', valid={self.is_valid})>"
