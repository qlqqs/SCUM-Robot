"""
支付配置数据模型
基于Xboard的v2_payment表设计，采用单表+JSON配置的简洁架构
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import json
from typing import Optional, Dict, Any

from . import Base, TimestampMixin


class PaymentConfig(Base, TimestampMixin):
    """支付配置模型（借鉴Xboard的v2_payment设计）"""
    __tablename__ = 'payment_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(32), nullable=False, unique=True, default=lambda: uuid.uuid4().hex)
    provider_code = Column(String(50), nullable=False, comment='支付提供商代码')
    provider_name = Column(String(100), nullable=False, comment='支付提供商名称')
    environment = Column(String(20), default='production', comment='环境')
    
    # 核心配置（JSON格式，类似Xboard的config字段）
    config = Column(JSON, nullable=False, comment='支付配置参数')
    
    # 状态控制
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_default = Column(Boolean, default=False, comment='是否为默认配置')
    sort_order = Column(Integer, default=0, comment='排序顺序')
    
    # 扩展字段
    icon = Column(String(255), comment='支付方式图标')
    description = Column(Text, comment='配置描述')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, include_sensitive=False) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'id': self.id,
            'uuid': self.uuid,
            'provider_code': self.provider_code,
            'provider_name': self.provider_name,
            'environment': self.environment,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'sort_order': self.sort_order,
            'icon': self.icon,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            result['config'] = self.config
        else:
            # 遮蔽敏感信息
            result['config'] = self._mask_sensitive_data(self.config or {})
        
        return result
    
    def _mask_sensitive_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """遮蔽敏感数据用于显示"""
        masked_config = config.copy()
        sensitive_fields = ['api_key', 'private_key', 'public_key', 'secret', 'api_key_encrypted', 'private_key_encrypted', 'public_key_encrypted']
        
        for field in sensitive_fields:
            if field in masked_config and masked_config[field]:
                value = str(masked_config[field])
                if len(value) > 8:
                    masked_config[field] = f"{value[:4]}****{value[-4:]}"
                else:
                    masked_config[field] = "****"
        
        return masked_config
    
    @classmethod
    def get_by_provider(cls, session, provider_code: str, environment: str = 'production'):
        """根据提供商代码获取配置"""
        return session.query(cls).filter(
            cls.provider_code == provider_code,
            cls.environment == environment,
            cls.is_active == True
        ).first()
    
    @classmethod
    def get_default_config(cls, session, environment: str = 'production'):
        """获取默认配置"""
        return session.query(cls).filter(
            cls.environment == environment,
            cls.is_default == True,
            cls.is_active == True
        ).first()
    
    @classmethod
    def get_active_configs(cls, session, environment: str = 'production'):
        """获取所有激活的配置"""
        return session.query(cls).filter(
            cls.environment == environment,
            cls.is_active == True
        ).order_by(cls.sort_order, cls.id).all()
    
    def validate_config(self) -> bool:
        """验证配置完整性"""
        if not self.config:
            return False
        
        required_fields = {
            'alipay': ['app_id', 'private_key', 'public_key'],
            'epay': ['url', 'pid', 'key']
        }
        
        if self.provider_code not in required_fields:
            return False
        
        for field in required_fields[self.provider_code]:
            # 检查原始字段或加密字段
            if field not in self.config and f"{field}_encrypted" not in self.config:
                return False
            if field in self.config and not self.config[field]:
                return False
            if f"{field}_encrypted" in self.config and not self.config[f"{field}_encrypted"]:
                return False
        
        return True

    def set_encrypted_config(self, config_data: Dict[str, Any]):
        """设置加密配置"""
        try:
            from ...payment.encryption import PaymentEncryption
            encryption = PaymentEncryption()

            # 加密敏感字段
            encrypted_config = config_data.copy()
            sensitive_fields = ['api_key', 'private_key', 'public_key', 'secret']

            for field in sensitive_fields:
                if field in encrypted_config and encrypted_config[field]:
                    encrypted_config[field] = encryption.encrypt(encrypted_config[field])

            self.config = encrypted_config

        except Exception as e:
            # 如果加密失败，直接存储（开发环境）
            self.config = config_data

    def get_decrypted_config(self) -> Dict[str, Any]:
        """获取解密后的配置"""
        if not self.config:
            return {}

        try:
            from ...payment.encryption import PaymentEncryption
            encryption = PaymentEncryption()

            # 解密敏感字段
            decrypted_config = self.config.copy()
            sensitive_fields = ['api_key', 'private_key', 'public_key', 'secret']

            for field in sensitive_fields:
                # 检查加密字段（field_encrypted）
                encrypted_field = f"{field}_encrypted"
                if encrypted_field in decrypted_config and decrypted_config[encrypted_field]:
                    try:
                        decrypted_value = encryption.decrypt_data(decrypted_config[encrypted_field])
                        decrypted_config[field] = decrypted_value
                        # 删除加密字段
                        del decrypted_config[encrypted_field]
                    except Exception as e:
                        # 如果解密失败，可能是未加密的数据
                        print(f"[WARN] 解密 {encrypted_field} 失败: {e}")
                        pass
                # 检查未加密字段
                elif field in decrypted_config and decrypted_config[field]:
                    try:
                        decrypted_config[field] = encryption.decrypt_data(decrypted_config[field])
                    except:
                        # 如果解密失败，可能是未加密的数据
                        pass

            return decrypted_config

        except Exception:
            # 如果解密失败，返回原始配置
            return self.config


class PaymentOperationLog(Base, TimestampMixin):
    """支付配置操作日志"""
    __tablename__ = 'payment_operation_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, nullable=False, comment='配置ID')
    operation_type = Column(String(50), nullable=False, comment='操作类型')
    operator_id = Column(Integer, comment='操作员ID')
    operation_details = Column(JSON, comment='操作详情')
    ip_address = Column(String(45), comment='操作IP地址')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'config_id': self.config_id,
            'operation_type': self.operation_type,
            'operator_id': self.operator_id,
            'operation_details': self.operation_details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# 支付提供商配置模板
PAYMENT_PROVIDER_TEMPLATES = {
    'alipay': {
        'provider_name': '支付宝',
        'icon': '/payment/icons/alipay.png',
        'description': '支付宝官方接口',
        'config_template': {
            'app_id': '',
            'private_key': '',
            'public_key': '',
            'product_name': '商城币充值',
            'api_base_url': 'https://openapi.alipay.com/gateway.do',
            'notify_url': '/api/v1/payment/notify/alipay',
            'return_url': '/api/v1/payment/return/alipay',
            'min_amount': 0.01,
            'max_amount': 50000.00,
            'fee_rate': 0.006,
            'extra_config': {
                'product_code': 'FAST_INSTANT_TRADE_PAY',
                'charset': 'UTF-8',
                'sign_type': 'RSA2'
            }
        }
    },
    'epay': {
        'provider_name': '易支付',
        'icon': '/payment/icons/epay.png',
        'description': '易支付第三方接口',
        'config_template': {
            'url': '',
            'pid': '',
            'key': '',
            'type': 'alipay',
            'notify_url': '/api/v1/payment/notify/epay',
            'return_url': '/api/v1/payment/return/epay',
            'min_amount': 0.01,
            'max_amount': 10000.00,
            'fee_rate': 0.01,
            'extra_config': {
                'sign_type': 'MD5'
            }
        }
    }
}


def get_provider_template(provider_code: str) -> Optional[Dict[str, Any]]:
    """获取支付提供商配置模板"""
    return PAYMENT_PROVIDER_TEMPLATES.get(provider_code)


def get_all_provider_templates() -> Dict[str, Dict[str, Any]]:
    """获取所有支付提供商配置模板"""
    return PAYMENT_PROVIDER_TEMPLATES
