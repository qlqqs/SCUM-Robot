"""
支付配置加密服务
基于Xboard的配置管理方式，使用JSON存储配置，敏感信息单独加密
"""

import os
import json
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import base64


class PaymentEncryption:
    """支付配置加密服务（参考Xboard设计）"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        初始化加密服务
        
        Args:
            encryption_key: 加密密钥，如果为None则从环境变量获取
        """
        if encryption_key is None:
            encryption_key = self._get_encryption_key()
        
        # 确保密钥是32字节的base64编码
        if len(encryption_key) != 44:  # base64编码的32字节密钥长度
            # 如果不是标准长度，生成新的密钥
            encryption_key = self._generate_key()
        
        try:
            self.cipher_suite = Fernet(encryption_key.encode())
        except Exception:
            # 如果密钥无效，生成新的密钥
            encryption_key = self._generate_key()
            self.cipher_suite = Fernet(encryption_key.encode())
    
    def _get_encryption_key(self) -> str:
        """从环境变量获取加密密钥"""
        key = os.getenv('PAYMENT_ENCRYPTION_KEY')
        if not key:
            # 如果环境变量不存在，生成新密钥并提示用户
            key = self._generate_key()
            print(f"[WARN] 未找到PAYMENT_ENCRYPTION_KEY环境变量，已生成新密钥：{key}")
            print("请将此密钥添加到.env文件中：PAYMENT_ENCRYPTION_KEY=" + key)
        return key
    
    def _generate_key(self) -> str:
        """生成新的加密密钥"""
        return Fernet.generate_key().decode()
    
    def encrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        加密配置中的敏感字段
        
        Args:
            config: 原始配置字典
            
        Returns:
            加密后的配置字典
        """
        encrypted_config = config.copy()
        sensitive_fields = ['api_key', 'private_key', 'public_key', 'secret', 'app_secret']
        
        for field in sensitive_fields:
            if field in encrypted_config and encrypted_config[field]:
                # 加密敏感字段
                encrypted_value = self.encrypt_data(encrypted_config[field])
                encrypted_config[f"{field}_encrypted"] = encrypted_value
                # 删除明文字段
                del encrypted_config[field]
        
        return encrypted_config
    
    def decrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        解密配置中的敏感字段
        
        Args:
            config: 加密的配置字典
            
        Returns:
            解密后的配置字典
        """
        decrypted_config = config.copy()
        
        for key, value in config.items():
            if key.endswith('_encrypted') and value:
                # 解密敏感字段
                original_key = key.replace('_encrypted', '')
                try:
                    decrypted_value = self.decrypt_data(value)
                    decrypted_config[original_key] = decrypted_value
                    # 删除加密字段
                    del decrypted_config[key]
                except Exception as e:
                    print(f"[WARN] 解密字段 {key} 失败: {e}")
                    # 保留加密字段，但添加错误标记
                    decrypted_config[f"{original_key}_decrypt_error"] = str(e)
        
        return decrypted_config
    
    def encrypt_data(self, data: str) -> str:
        """
        加密单个数据
        
        Args:
            data: 要加密的字符串
            
        Returns:
            加密后的字符串
        """
        if not data:
            return ""
        
        try:
            encrypted_bytes = self.cipher_suite.encrypt(data.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"加密失败: {e}")
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        解密单个数据
        
        Args:
            encrypted_data: 加密的字符串
            
        Returns:
            解密后的字符串
        """
        if not encrypted_data:
            return ""
        
        try:
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"解密失败: {e}")


class PaymentConfigSecurity:
    """支付配置安全处理"""
    
    @staticmethod
    def mask_sensitive_data(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        遮蔽敏感数据用于显示
        
        Args:
            config: 配置字典
            
        Returns:
            遮蔽敏感信息后的配置字典
        """
        masked_config = config.copy()
        sensitive_fields = [
            'api_key', 'private_key', 'public_key', 'secret', 'app_secret',
            'api_key_encrypted', 'private_key_encrypted', 'public_key_encrypted'
        ]
        
        for field in sensitive_fields:
            if field in masked_config and masked_config[field]:
                value = str(masked_config[field])
                if len(value) > 8:
                    masked_config[field] = f"{value[:4]}****{value[-4:]}"
                else:
                    masked_config[field] = "****"
        
        return masked_config
    
    @staticmethod
    def validate_config_integrity(config: Dict[str, Any], provider_code: str) -> bool:
        """
        验证配置完整性
        
        Args:
            config: 配置字典
            provider_code: 支付提供商代码
            
        Returns:
            配置是否完整
        """
        required_fields = {
            'wechat': ['app_id', 'merchant_id', 'api_key'],
            'alipay': ['app_id', 'private_key', 'public_key'],
            'unionpay': ['merchant_id', 'private_key', 'public_key']
        }
        
        if provider_code not in required_fields:
            return False
        
        for field in required_fields[provider_code]:
            # 检查原始字段或加密字段
            if field not in config and f"{field}_encrypted" not in config:
                return False
            if field in config and not config[field]:
                return False
            if f"{field}_encrypted" in config and not config[f"{field}_encrypted"]:
                return False
        
        return True
    
    @staticmethod
    def sanitize_config_for_log(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理配置用于日志记录（完全移除敏感信息）
        
        Args:
            config: 配置字典
            
        Returns:
            清理后的配置字典
        """
        sanitized_config = config.copy()
        sensitive_fields = [
            'api_key', 'private_key', 'public_key', 'secret', 'app_secret',
            'api_key_encrypted', 'private_key_encrypted', 'public_key_encrypted'
        ]
        
        for field in sensitive_fields:
            if field in sanitized_config:
                sanitized_config[field] = "[REDACTED]"
        
        return sanitized_config


def test_encryption():
    """测试加密功能"""
    print("🧪 测试支付配置加密功能...")
    
    # 创建加密服务
    encryption = PaymentEncryption()
    
    # 测试配置
    test_config = {
        'app_id': 'wx1234567890abcdef',
        'merchant_id': '1234567890',
        'api_key': 'test_api_key_12345',
        'private_key': 'test_private_key_67890',
        'api_base_url': 'https://api.mch.weixin.qq.com',
        'min_amount': 0.01,
        'max_amount': 10000.00
    }
    
    print("[INFO] 原始配置:")
    print(json.dumps(test_config, indent=2, ensure_ascii=False))
    
    # 加密配置
    encrypted_config = encryption.encrypt_config(test_config)
    print("\n[INFO] 加密后配置:")
    print(json.dumps(encrypted_config, indent=2, ensure_ascii=False))
    
    # 解密配置
    decrypted_config = encryption.decrypt_config(encrypted_config)
    print("\n[INFO] 解密后配置:")
    print(json.dumps(decrypted_config, indent=2, ensure_ascii=False))
    
    # 验证一致性
    if test_config == decrypted_config:
        print("\n[OK] 加密解密测试通过")
    else:
        print("\n[ERROR] 加密解密测试失败")
    
    # 测试遮蔽功能
    masked_config = PaymentConfigSecurity.mask_sensitive_data(test_config)
    print("\n[INFO] 遮蔽后配置:")
    print(json.dumps(masked_config, indent=2, ensure_ascii=False))
    
    # 测试配置验证
    is_valid = PaymentConfigSecurity.validate_config_integrity(test_config, 'wechat')
    print(f"\n[INFO] 配置完整性验证: {'[OK] 通过' if is_valid else '[ERROR] 失败'}")


if __name__ == "__main__":
    test_encryption()
