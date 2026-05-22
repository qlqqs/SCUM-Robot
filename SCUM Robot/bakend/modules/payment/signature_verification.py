"""
支付签名验证服务
实现各支付平台的签名验证机制，确保回调安全性
"""

import hashlib
import hmac
import base64
import json
import time
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode, quote_plus
import xml.etree.ElementTree as ET

# 使用内置的加密库，避免依赖外部包
try:
    from Crypto.PublicKey import RSA
    from Crypto.Signature import pkcs1_15
    from Crypto.Hash import SHA256, SHA1
    CRYPTO_AVAILABLE = True
except ImportError:
    # 如果没有安装pycryptodome，使用简化版本
    CRYPTO_AVAILABLE = False
    print("警告: 未安装pycryptodome，RSA签名验证将被禁用")


class SignatureVerificationError(Exception):
    """签名验证异常"""
    pass


class EpaySignatureVerifier:
    """易支付签名验证器"""

    @staticmethod
    def verify_notify_signature(data: Dict[str, Any], signature: str, key: str) -> bool:
        """
        验证易支付回调签名

        Args:
            data: 回调数据
            signature: 签名
            key: 通信密钥

        Returns:
            bool: 验证是否通过
        """
        try:
            # 构建签名字符串
            sign_string = EpaySignatureVerifier._build_sign_string(data, key)

            # 计算MD5签名
            calculated_signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest()

            return calculated_signature == signature

        except Exception as e:
            raise SignatureVerificationError(f"易支付签名验证失败: {e}")

    @staticmethod
    def _build_sign_string(data: Dict[str, Any], key: str) -> str:
        """构建签名字符串"""
        from urllib.parse import urlencode, unquote

        # 过滤空值和签名相关字段
        filtered_data = {k: v for k, v in data.items()
                        if v is not None and v != '' and k not in ['sign', 'sign_type']}

        # 按key排序
        sorted_items = sorted(filtered_data.items())

        # 构建查询字符串
        query_string = urlencode(sorted_items)

        # URL解码并添加密钥
        sign_string = unquote(query_string) + key

        return sign_string


class AlipaySignatureVerifier:
    """支付宝签名验证器"""
    
    @staticmethod
    def verify_notify_signature(data: Dict[str, Any], signature: str, public_key: str, 
                               sign_type: str = 'RSA2') -> bool:
        """
        验证支付宝回调签名
        
        Args:
            data: 回调数据
            signature: 签名
            public_key: 支付宝公钥
            sign_type: 签名类型 (RSA/RSA2)
            
        Returns:
            bool: 验证是否通过
        """
        try:
            # 构建签名字符串
            sign_string = AlipaySignatureVerifier._build_sign_string(data)
            
            # 验证签名
            if sign_type == 'RSA2':
                return AlipaySignatureVerifier._verify_rsa2_signature(
                    sign_string, signature, public_key
                )
            else:
                return AlipaySignatureVerifier._verify_rsa_signature(
                    sign_string, signature, public_key
                )
                
        except Exception as e:
            raise SignatureVerificationError(f"支付宝签名验证失败: {e}")
    
    @staticmethod
    def _build_sign_string(data: Dict[str, Any]) -> str:
        """构建签名字符串"""
        # 过滤空值和签名相关字段
        filtered_data = {k: v for k, v in data.items() 
                        if v is not None and v != '' and k not in ['sign', 'sign_type']}
        
        # 按key排序
        sorted_items = sorted(filtered_data.items())
        
        # 构建查询字符串
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_items])
        
        return sign_string
    
    @staticmethod
    def _verify_rsa2_signature(data: str, signature: str, public_key: str) -> bool:
        """验证RSA2签名"""
        if not CRYPTO_AVAILABLE:
            print("警告: RSA2签名验证需要pycryptodome库")
            return False

        try:
            # 导入公钥
            key = RSA.import_key(public_key)

            # 计算哈希
            hash_obj = SHA256.new(data.encode('utf-8'))

            # 验证签名
            pkcs1_15.new(key).verify(hash_obj, base64.b64decode(signature))
            return True

        except Exception:
            return False
    
    @staticmethod
    def _verify_rsa_signature(data: str, signature: str, public_key: str) -> bool:
        """验证RSA签名"""
        if not CRYPTO_AVAILABLE:
            print("警告: RSA签名验证需要pycryptodome库")
            return False

        # RSA签名验证实现（简化版）
        # 实际生产环境建议使用专业的支付宝SDK
        try:
            # 导入公钥
            key = RSA.import_key(public_key)

            # 计算哈希
            hash_obj = SHA1.new(data.encode('utf-8'))

            # 验证签名
            pkcs1_15.new(key).verify(hash_obj, base64.b64decode(signature))
            return True

        except Exception:
            return False





class PaymentSignatureVerifier:
    """统一支付签名验证器"""
    
    def __init__(self):
        self.verifiers = {
            'alipay': AlipaySignatureVerifier,
            'epay': EpaySignatureVerifier
        }
    
    def verify_signature(self, provider_code: str, data: Dict[str, Any], 
                        signature: str, config: Dict[str, Any]) -> bool:
        """
        统一签名验证接口
        
        Args:
            provider_code: 支付提供商代码
            data: 回调数据
            signature: 签名
            config: 支付配置
            
        Returns:
            bool: 验证是否通过
        """
        verifier = self.verifiers.get(provider_code)
        if not verifier:
            raise SignatureVerificationError(f"不支持的支付提供商: {provider_code}")
        
        try:
            if provider_code == 'alipay':
                public_key = config.get('public_key')
                sign_type = config.get('sign_type', 'RSA2')
                if not public_key:
                    raise SignatureVerificationError("支付宝公钥未配置")
                return verifier.verify_notify_signature(data, signature, public_key, sign_type)

            elif provider_code == 'epay':
                key = config.get('key')
                if not key:
                    raise SignatureVerificationError("易支付通信密钥未配置")
                return verifier.verify_notify_signature(data, signature, key)

        except Exception as e:
            raise SignatureVerificationError(f"签名验证失败: {e}")
    



class AntiReplayAttackValidator:
    """防重放攻击验证器"""
    
    def __init__(self, cache_ttl: int = 300):
        """
        初始化防重放攻击验证器
        
        Args:
            cache_ttl: 缓存TTL（秒），默认5分钟
        """
        self.cache_ttl = cache_ttl
        self._processed_requests = {}  # 简单内存缓存，生产环境建议使用Redis
    
    def validate_request(self, request_id: str, timestamp: int, 
                        tolerance: int = 300) -> bool:
        """
        验证请求是否为重放攻击
        
        Args:
            request_id: 请求唯一标识
            timestamp: 请求时间戳
            tolerance: 时间容忍度（秒）
            
        Returns:
            bool: 验证是否通过
        """
        current_time = int(time.time())
        
        # 检查时间戳是否在容忍范围内
        if abs(current_time - timestamp) > tolerance:
            return False
        
        # 检查请求是否已处理过
        if request_id in self._processed_requests:
            return False
        
        # 记录请求
        self._processed_requests[request_id] = current_time
        
        # 清理过期记录
        self._cleanup_expired_requests(current_time)
        
        return True
    
    def _cleanup_expired_requests(self, current_time: int):
        """清理过期的请求记录"""
        expired_keys = [
            key for key, timestamp in self._processed_requests.items()
            if current_time - timestamp > self.cache_ttl
        ]
        for key in expired_keys:
            del self._processed_requests[key]


class IPWhitelistValidator:
    """IP白名单验证器"""
    
    def __init__(self, whitelist: Optional[list] = None):
        """
        初始化IP白名单验证器
        
        Args:
            whitelist: IP白名单列表
        """
        self.whitelist = whitelist or self._get_default_whitelist()
    
    def _get_default_whitelist(self) -> list:
        """获取默认IP白名单"""
        return [
            # 微信支付回调IP
            '101.226.103.0/24',
            '101.226.62.0/24',
            # 支付宝回调IP
            '110.75.143.0/24',
            '203.119.24.0/24',
            # 银联回调IP
            '202.101.25.0/24',
            '202.101.25.178',
            # 本地测试
            '192.168.0.0/16',
            '127.0.0.0/8',
            '10.0.0.0/8',
            '127.0.0.1',
            '::1'
        ]
    
    def validate_ip(self, client_ip: str) -> bool:
        """
        验证IP是否在白名单中
        
        Args:
            client_ip: 客户端IP
            
        Returns:
            bool: 验证是否通过
        """
        import ipaddress
        
        try:
            client_addr = ipaddress.ip_address(client_ip)
            
            for allowed in self.whitelist:
                try:
                    if '/' in allowed:
                        # CIDR格式
                        if client_addr in ipaddress.ip_network(allowed, strict=False):
                            return True
                    else:
                        # 单个IP
                        if client_addr == ipaddress.ip_address(allowed):
                            return True
                except ValueError:
                    continue
            
            return False
            
        except ValueError:
            return False
