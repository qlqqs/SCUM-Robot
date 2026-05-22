"""
配置服务层

提供配置的增删改查、加密解密、类型转换等功能
"""

import json
from typing import Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.config_models import SystemConfig, ConfigHistory, ConfigType, ConfigGroup
from .service_result import ServiceResult, ServiceErrorType
from ...payment.encryption import PaymentEncryption


class ConfigService:
    """配置服务类"""
    
    def __init__(self, db_session: Session):
        """
        初始化配置服务

        Args:
            db_session: 数据库会话
        """
        self.db = db_session
        self.encryption = PaymentEncryption()
    
    def get(self, key: str, default: Any = None, decrypt: bool = True) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            decrypt: 是否解密
        
        Returns:
            配置值
        """
        try:
            config = self.db.query(SystemConfig).filter(
                and_(
                    SystemConfig.key == key,
                    SystemConfig.is_active == True
                )
            ).first()
            
            if not config:
                return default
            
            value = config.value
            
            # 解密
            if config.is_encrypted and decrypt:
                try:
                    value = self.encryption.decrypt_data(value)
                except Exception as e:
                    print(f"解密配置失败: {key}, {e}")
                    return default
            
            # 类型转换
            return self._convert_value(value, config.type)
        
        except Exception as e:
            print(f"获取配置失败: {key}, {e}")
            return default
    
    def set(self, key: str, value: Any, type: ConfigType = ConfigType.STRING,
            group_name: str = "custom", description: str = None,
            is_public: bool = False, is_encrypted: bool = False,
            changed_by: int = None, change_reason: str = None) -> ServiceResult:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            type: 数据类型
            group_name: 配置分组
            description: 配置描述
            is_public: 是否公开
            is_encrypted: 是否加密
            changed_by: 修改人ID
            change_reason: 修改原因
        
        Returns:
            ServiceResult
        """
        try:
            # 查找现有配置
            config = self.db.query(SystemConfig).filter(
                SystemConfig.key == key
            ).first()
            
            # 转换值为字符串
            str_value = self._value_to_string(value, type)
            
            # 加密
            if is_encrypted:
                str_value = self.encryption.encrypt_data(str_value)
            
            if config:
                # 更新现有配置
                old_value = config.value
                
                config.value = str_value
                config.type = type
                config.group_name = group_name
                config.is_public = is_public
                config.is_encrypted = is_encrypted
                
                if description:
                    config.description = description
                
                # 记录历史
                if old_value != str_value:
                    history = ConfigHistory(
                        config_id=config.id,
                        old_value=old_value,
                        new_value=str_value,
                        changed_by=changed_by,
                        change_reason=change_reason
                    )
                    self.db.add(history)
            else:
                # 创建新配置
                config = SystemConfig(
                    key=key,
                    value=str_value,
                    type=type,
                    group_name=group_name,
                    description=description,
                    is_public=is_public,
                    is_encrypted=is_encrypted
                )
                self.db.add(config)
            
            self.db.commit()
            
            return ServiceResult.success(
                data=config.to_dict(),
                message="配置设置成功"
            )
        
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"配置设置失败: {str(e)}"
            )
    
    def delete(self, key: str, changed_by: int = None) -> ServiceResult:
        """
        删除配置
        
        Args:
            key: 配置键
            changed_by: 修改人ID
        
        Returns:
            ServiceResult
        """
        try:
            config = self.db.query(SystemConfig).filter(
                SystemConfig.key == key
            ).first()
            
            if not config:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "配置不存在"
                )
            
            # 记录历史
            history = ConfigHistory(
                config_id=config.id,
                old_value=config.value,
                new_value=None,
                changed_by=changed_by,
                change_reason="删除配置"
            )
            self.db.add(history)
            
            self.db.delete(config)
            self.db.commit()
            
            return ServiceResult.success(message="配置删除成功")
        
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"配置删除失败: {str(e)}"
            )
    
    def get_by_group(self, group_name: str, include_inactive: bool = False) -> ServiceResult:
        """
        获取分组配置
        
        Args:
            group_name: 配置分组
            include_inactive: 是否包含禁用的配置
        
        Returns:
            ServiceResult
        """
        try:
            query = self.db.query(SystemConfig).filter(
                SystemConfig.group_name == group_name
            )
            
            if not include_inactive:
                query = query.filter(SystemConfig.is_active == True)
            
            configs = query.order_by(SystemConfig.sort_order).all()
            
            data = {}
            for config in configs:
                value = config.value
                
                # 解密
                if config.is_encrypted:
                    try:
                        value = self.encryption.decrypt_data(value)
                    except:
                        continue
                
                # 类型转换
                data[config.key] = self._convert_value(value, config.type)
            
            return ServiceResult.success(data=data)
        
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"获取分组配置失败: {str(e)}"
            )
    
    def get_all(self, include_inactive: bool = False, include_encrypted: bool = False) -> ServiceResult:
        """
        获取所有配置
        
        Args:
            include_inactive: 是否包含禁用的配置
            include_encrypted: 是否包含加密配置的值
        
        Returns:
            ServiceResult
        """
        try:
            query = self.db.query(SystemConfig)
            
            if not include_inactive:
                query = query.filter(SystemConfig.is_active == True)
            
            configs = query.order_by(
                SystemConfig.group_name,
                SystemConfig.sort_order
            ).all()
            
            data = []
            for config in configs:
                config_dict = config.to_dict()
                
                # 解密
                if config.is_encrypted and include_encrypted:
                    try:
                        config_dict['value'] = self.encryption.decrypt_data(config.value)
                    except:
                        config_dict['value'] = None
                elif config.is_encrypted:
                    # 不显示加密的值
                    config_dict['value'] = '******'
                
                data.append(config_dict)
            
            return ServiceResult.success(data=data)
        
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"获取所有配置失败: {str(e)}"
            )
    
    def get_public(self) -> ServiceResult:
        """
        获取公开配置
        
        Returns:
            ServiceResult
        """
        try:
            configs = self.db.query(SystemConfig).filter(
                and_(
                    SystemConfig.is_public == True,
                    SystemConfig.is_active == True
                )
            ).order_by(
                SystemConfig.group_name,
                SystemConfig.sort_order
            ).all()
            
            data = {}
            for config in configs:
                value = self._convert_value(config.value, config.type)
                data[config.key] = value
            
            return ServiceResult.success(data=data)
        
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"获取公开配置失败: {str(e)}"
            )

    def _convert_value(self, value: str, type: ConfigType) -> Any:
        """
        类型转换

        Args:
            value: 配置值（字符串）
            type: 配置类型

        Returns:
            转换后的值
        """
        if value is None:
            return None

        try:
            if type == ConfigType.INT:
                return int(value)
            elif type == ConfigType.FLOAT:
                return float(value)
            elif type == ConfigType.BOOL:
                return value.lower() in ('true', '1', 'yes')
            elif type == ConfigType.JSON:
                return json.loads(value)
            else:
                return value
        except Exception as e:
            print(f"类型转换失败: {value} -> {type}, {e}")
            return value

    def _value_to_string(self, value: Any, type: ConfigType) -> str:
        """
        值转换为字符串

        Args:
            value: 配置值
            type: 配置类型

        Returns:
            字符串值
        """
        if value is None:
            return ""

        if type == ConfigType.JSON:
            return json.dumps(value, ensure_ascii=False)
        elif type == ConfigType.BOOL:
            return "true" if value else "false"
        else:
            return str(value)

