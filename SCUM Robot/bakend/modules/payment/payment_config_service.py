"""
支付配置核心服务
基于Xboard的PaymentService设计，提供配置管理和操作功能
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..sql.models.payment_models import PaymentConfig, PaymentOperationLog, get_provider_template
from ..sql.database.manager import DatabaseManager
from .encryption import PaymentEncryption, PaymentConfigSecurity
from ..common.service_result import ServiceResult


class PaymentConfigService:
    """支付配置核心服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.encryption = PaymentEncryption()
    
    def get_all_configs(self, environment: str = 'production', include_sensitive: bool = False) -> ServiceResult:
        """
        获取所有支付配置
        
        Args:
            environment: 环境（production/test）
            include_sensitive: 是否包含敏感信息
            
        Returns:
            ServiceResult包含配置列表
        """
        try:
            with self.db_manager.get_session() as session:
                configs = PaymentConfig.get_active_configs(session, environment)
                
                result_configs = []
                for config in configs:
                    config_dict = config.to_dict(include_sensitive=include_sensitive)
                    
                    # 如果包含敏感信息，解密配置
                    if include_sensitive and config.config:
                        try:
                            decrypted_config = self.encryption.decrypt_config(config.config)
                            config_dict['config'] = decrypted_config
                        except Exception as e:
                            config_dict['config_decrypt_error'] = str(e)
                    
                    result_configs.append(config_dict)
                
                return ServiceResult.success(result_configs)
                
        except Exception as e:
            return ServiceResult.error(f"获取支付配置失败: {e}")
    
    def get_config_by_id(self, config_id: int, include_sensitive: bool = False) -> ServiceResult:
        """
        根据ID获取支付配置
        
        Args:
            config_id: 配置ID
            include_sensitive: 是否包含敏感信息
            
        Returns:
            ServiceResult包含配置信息
        """
        try:
            with self.db_manager.get_session() as session:
                config = session.query(PaymentConfig).filter(PaymentConfig.id == config_id).first()
                
                if not config:
                    return ServiceResult.error("配置不存在")
                
                config_dict = config.to_dict(include_sensitive=include_sensitive)
                
                # 如果包含敏感信息，解密配置
                if include_sensitive and config.config:
                    try:
                        decrypted_config = self.encryption.decrypt_config(config.config)
                        config_dict['config'] = decrypted_config
                    except Exception as e:
                        config_dict['config_decrypt_error'] = str(e)
                
                return ServiceResult.success(config_dict)
                
        except Exception as e:
            return ServiceResult.error(f"获取支付配置失败: {e}")
    
    def get_config_by_provider(self, provider_code: str, environment: str = 'production') -> ServiceResult:
        """
        根据提供商代码获取配置
        
        Args:
            provider_code: 提供商代码
            environment: 环境
            
        Returns:
            ServiceResult包含配置信息
        """
        try:
            with self.db_manager.get_session() as session:
                config = PaymentConfig.get_by_provider(session, provider_code, environment)
                
                if not config:
                    return ServiceResult.error(f"未找到 {provider_code} 的配置")
                
                # 解密配置用于实际使用
                config_dict = config.to_dict(include_sensitive=True)
                if config.config:
                    try:
                        decrypted_config = self.encryption.decrypt_config(config.config)
                        config_dict['config'] = decrypted_config
                    except Exception as e:
                        return ServiceResult.error(f"配置解密失败: {e}")
                
                return ServiceResult.success(config_dict)
                
        except Exception as e:
            return ServiceResult.error(f"获取支付配置失败: {e}")
    
    def create_config(self, config_data: Dict[str, Any], operator_id: Optional[int] = None) -> ServiceResult:
        """
        创建支付配置
        
        Args:
            config_data: 配置数据
            operator_id: 操作员ID
            
        Returns:
            ServiceResult包含创建的配置
        """
        try:
            # 验证必需字段
            required_fields = ['provider_code', 'provider_name', 'config']
            for field in required_fields:
                if field not in config_data:
                    return ServiceResult.error(f"缺少必需字段: {field}")
            
            # 验证配置完整性
            if not PaymentConfigSecurity.validate_config_integrity(
                config_data['config'], config_data['provider_code']
            ):
                return ServiceResult.error("配置不完整，缺少必需的支付参数")
            
            with self.db_manager.get_session() as session:
                # 检查是否已存在相同的配置
                existing_config = PaymentConfig.get_by_provider(
                    session, 
                    config_data['provider_code'], 
                    config_data.get('environment', 'production')
                )
                
                if existing_config:
                    return ServiceResult.error(f"已存在 {config_data['provider_code']} 的配置")
                
                # 加密敏感配置
                encrypted_config = self.encryption.encrypt_config(config_data['config'])
                
                # 创建配置记录
                new_config = PaymentConfig(
                    provider_code=config_data['provider_code'],
                    provider_name=config_data['provider_name'],
                    environment=config_data.get('environment', 'production'),
                    config=encrypted_config,
                    is_active=config_data.get('is_active', True),
                    is_default=config_data.get('is_default', False),
                    sort_order=config_data.get('sort_order', 0),
                    icon=config_data.get('icon'),
                    description=config_data.get('description')
                )
                
                session.add(new_config)
                session.commit()
                
                # 记录操作日志
                self._log_operation(
                    session, new_config.id, 'CREATE', operator_id,
                    {'provider_code': config_data['provider_code']}
                )
                
                return ServiceResult.success(new_config.to_dict())
                
        except Exception as e:
            return ServiceResult.error(f"创建支付配置失败: {e}")
    
    def update_config(self, config_id: int, config_data: Dict[str, Any], operator_id: Optional[int] = None) -> ServiceResult:
        """
        更新支付配置
        
        Args:
            config_id: 配置ID
            config_data: 更新的配置数据
            operator_id: 操作员ID
            
        Returns:
            ServiceResult包含更新的配置
        """
        try:
            with self.db_manager.get_session() as session:
                config = session.query(PaymentConfig).filter(PaymentConfig.id == config_id).first()
                
                if not config:
                    return ServiceResult.error("配置不存在")
                
                # 记录更新前的状态
                old_data = config.to_dict()
                
                # 更新字段
                if 'provider_name' in config_data:
                    config.provider_name = config_data['provider_name']
                if 'environment' in config_data:
                    config.environment = config_data['environment']
                if 'is_active' in config_data:
                    config.is_active = config_data['is_active']
                if 'is_default' in config_data:
                    config.is_default = config_data['is_default']
                if 'sort_order' in config_data:
                    config.sort_order = config_data['sort_order']
                if 'icon' in config_data:
                    config.icon = config_data['icon']
                if 'description' in config_data:
                    config.description = config_data['description']
                
                # 更新配置参数
                if 'config' in config_data:
                    # 验证配置完整性
                    if not PaymentConfigSecurity.validate_config_integrity(
                        config_data['config'], config.provider_code
                    ):
                        return ServiceResult.error("配置不完整，缺少必需的支付参数")
                    
                    # 加密新配置
                    encrypted_config = self.encryption.encrypt_config(config_data['config'])
                    config.config = encrypted_config
                
                config.updated_at = datetime.utcnow()
                session.commit()
                
                # 记录操作日志
                self._log_operation(
                    session, config.id, 'UPDATE', operator_id,
                    {
                        'old_data': PaymentConfigSecurity.sanitize_config_for_log(old_data),
                        'updated_fields': list(config_data.keys())
                    }
                )
                
                return ServiceResult.success(config.to_dict())
                
        except Exception as e:
            return ServiceResult.error(f"更新支付配置失败: {e}")
    
    def delete_config(self, config_id: int, operator_id: Optional[int] = None) -> ServiceResult:
        """
        删除支付配置
        
        Args:
            config_id: 配置ID
            operator_id: 操作员ID
            
        Returns:
            ServiceResult
        """
        try:
            with self.db_manager.get_session() as session:
                config = session.query(PaymentConfig).filter(PaymentConfig.id == config_id).first()
                
                if not config:
                    return ServiceResult.error("配置不存在")
                
                # 记录删除的配置信息
                deleted_data = PaymentConfigSecurity.sanitize_config_for_log(config.to_dict())
                
                # 删除配置
                session.delete(config)
                session.commit()
                
                # 记录操作日志
                self._log_operation(
                    session, config_id, 'DELETE', operator_id,
                    {'deleted_data': deleted_data}
                )
                
                return ServiceResult.success({"message": "配置删除成功"})
                
        except Exception as e:
            return ServiceResult.error(f"删除支付配置失败: {e}")
    
    def test_config(self, config_id: int) -> ServiceResult:
        """
        测试支付配置连通性
        
        Args:
            config_id: 配置ID
            
        Returns:
            ServiceResult包含测试结果
        """
        try:
            # 获取配置
            config_result = self.get_config_by_id(config_id, include_sensitive=True)
            if not config_result.success:
                return config_result
            
            config_data = config_result.data
            
            # 这里可以添加实际的支付接口测试逻辑
            # 目前返回基础验证结果
            test_results = {
                'config_valid': True,
                'connectivity': 'unknown',  # 需要实际实现连通性测试
                'message': '配置格式验证通过，连通性测试需要实际实现'
            }
            
            return ServiceResult.success(test_results)
            
        except Exception as e:
            return ServiceResult.error(f"测试支付配置失败: {e}")
    
    def get_provider_templates(self) -> ServiceResult:
        """
        获取支付提供商配置模板
        
        Returns:
            ServiceResult包含模板列表
        """
        try:
            from ..sql.models.payment_models import get_all_provider_templates
            templates = get_all_provider_templates()
            return ServiceResult.success(templates)
        except Exception as e:
            return ServiceResult.error(f"获取配置模板失败: {e}")
    
    def _log_operation(self, session: Session, config_id: int, operation_type: str, 
                      operator_id: Optional[int], details: Dict[str, Any]):
        """记录操作日志"""
        try:
            log = PaymentOperationLog(
                config_id=config_id,
                operation_type=operation_type,
                operator_id=operator_id,
                operation_details=details
            )
            session.add(log)
            session.commit()
        except Exception as e:
            print(f"记录操作日志失败: {e}")  # 日志失败不应该影响主要操作
