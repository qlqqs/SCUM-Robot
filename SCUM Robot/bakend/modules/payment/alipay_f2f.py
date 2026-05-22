"""
支付宝当面付封装类
参考Xboard的AlipayF2F实现，使用Python重写
支持alipay.trade.precreate接口（生成支付二维码）
"""

import json
import base64
import hashlib
import time
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlencode, quote_plus
import httpx

try:
    from Crypto.PublicKey import RSA
    from Crypto.Signature import pkcs1_15
    from Crypto.Hash import SHA256
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    raise ImportError("需要安装pycryptodome库: pip install pycryptodome")


class AlipayF2FException(Exception):
    """支付宝当面付异常"""
    pass


class AlipayF2F:
    """
    支付宝当面付封装类
    
    参考Xboard实现，提供以下功能：
    1. 生成支付二维码（alipay.trade.precreate）
    2. RSA2签名生成
    3. 回调签名验证
    """
    
    def __init__(self, sandbox: bool = False):
        """
        初始化支付宝当面付
        
        Args:
            sandbox: 是否使用沙箱环境
        """
        self.app_id = None
        self.private_key = None
        self.alipay_public_key = None
        self.method = None
        self.notify_url = None
        self.biz_content = {}
        
        # 网关地址
        if sandbox:
            self.gateway = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
        else:
            self.gateway = "https://openapi.alipay.com/gateway.do"
        
        # 固定参数
        self.charset = "UTF-8"
        self.sign_type = "RSA2"
        self.version = "1.0"
        self.format = "JSON"
        
        # 响应数据
        self.response_data = None
    
    def set_app_id(self, app_id: str):
        """设置应用ID"""
        self.app_id = app_id
    
    def set_private_key(self, private_key: str):
        """
        设置应用私钥
        
        Args:
            private_key: RSA私钥字符串（可以是PKCS1或PKCS8格式）
        """
        # 处理私钥格式
        private_key = private_key.strip()
        
        # 如果没有BEGIN标记，添加PKCS1格式的标记
        if not private_key.startswith('-----BEGIN'):
            private_key = f"-----BEGIN RSA PRIVATE KEY-----\n{private_key}\n-----END RSA PRIVATE KEY-----"
        
        self.private_key = private_key
    
    def set_alipay_public_key(self, public_key: str):
        """
        设置支付宝公钥
        
        Args:
            public_key: 支付宝公钥字符串
        """
        # 处理公钥格式
        public_key = public_key.strip()
        
        # 如果没有BEGIN标记，添加标记
        if not public_key.startswith('-----BEGIN'):
            public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
        
        self.alipay_public_key = public_key
    
    def set_method(self, method: str):
        """设置API方法"""
        self.method = method
    
    def set_notify_url(self, notify_url: str):
        """设置异步通知地址"""
        self.notify_url = notify_url
    
    def set_biz_content(self, biz_content: Dict[str, Any]):
        """设置业务参数"""
        self.biz_content = biz_content
    
    def _build_request_params(self) -> Dict[str, Any]:
        """
        构建请求参数

        Returns:
            请求参数字典
        """
        params = {
            'app_id': self.app_id,
            'method': self.method,
            'charset': self.charset,
            'sign_type': self.sign_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': self.version,
            'biz_content': json.dumps(self.biz_content, ensure_ascii=False)
        }

        # 添加可选参数
        if self.notify_url:
            params['notify_url'] = self.notify_url
            print(f"[INFO] 支付宝API - notify_url: {self.notify_url}")
        else:
            print("[WARN] 支付宝API - notify_url 未设置！")

        return params
    
    def _build_sign_string(self, params: Dict[str, Any]) -> str:
        """
        构建待签名字符串
        
        Args:
            params: 参数字典
            
        Returns:
            待签名字符串
        """
        # 过滤空值和sign字段
        filtered_params = {k: v for k, v in params.items() 
                          if v is not None and v != '' and k != 'sign'}
        
        # 按key排序
        sorted_items = sorted(filtered_params.items())
        
        # 构建字符串：key1=value1&key2=value2
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_items])
        
        return sign_string
    
    def _sign(self, sign_string: str) -> str:
        """
        生成RSA2签名
        
        Args:
            sign_string: 待签名字符串
            
        Returns:
            Base64编码的签名
        """
        if not CRYPTO_AVAILABLE:
            raise AlipayF2FException("需要安装pycryptodome库")
        
        if not self.private_key:
            raise AlipayF2FException("未设置应用私钥")
        
        try:
            # 导入私钥
            key = RSA.import_key(self.private_key)
            
            # 计算SHA256哈希
            hash_obj = SHA256.new(sign_string.encode('utf-8'))
            
            # 生成签名
            signature = pkcs1_15.new(key).sign(hash_obj)
            
            # Base64编码
            return base64.b64encode(signature).decode('utf-8')
            
        except Exception as e:
            raise AlipayF2FException(f"签名生成失败: {e}")
    
    def send(self) -> Dict[str, Any]:
        """
        发送请求到支付宝网关

        Returns:
            响应数据
        """
        # 构建请求参数
        params = self._build_request_params()

        # 生成签名
        sign_string = self._build_sign_string(params)
        params['sign'] = self._sign(sign_string)

        try:
            # 发送POST请求（使用form-urlencoded格式）
            # 注意：所有参数都需要进行URL编码
            from urllib.parse import urlencode

            # 对参数进行URL编码
            encoded_params = urlencode(params, encoding='utf-8')

            response = httpx.post(
                self.gateway,
                content=encoded_params,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
                },
                timeout=30.0
            )
            response.raise_for_status()

            # 解析响应（支付宝可能返回GBK编码）
            try:
                # 先尝试UTF-8
                response_data = json.loads(response.content.decode('utf-8'))
            except UnicodeDecodeError:
                # 如果失败，尝试GBK
                response_data = json.loads(response.content.decode('gbk'))

            self.response_data = response_data
            
            # 检查响应
            response_key = f"{self.method.replace('.', '_')}_response"
            if response_key not in response_data:
                raise AlipayF2FException(f"响应格式错误: {response_data}")
            
            result = response_data[response_key]
            
            # 检查业务结果
            if result.get('code') != '10000':
                error_msg = result.get('sub_msg') or result.get('msg', '未知错误')
                raise AlipayF2FException(f"支付宝API错误: {error_msg}")
            
            return result
            
        except httpx.HTTPError as e:
            raise AlipayF2FException(f"HTTP请求失败: {e}")
        except json.JSONDecodeError as e:
            raise AlipayF2FException(f"响应解析失败: {e}")
    
    def get_qr_code_url(self) -> str:
        """
        获取二维码URL
        
        Returns:
            二维码URL字符串
        """
        if not self.response_data:
            raise AlipayF2FException("请先调用send()方法")
        
        response_key = f"{self.method.replace('.', '_')}_response"
        result = self.response_data.get(response_key, {})
        
        qr_code = result.get('qr_code')
        if not qr_code:
            raise AlipayF2FException("响应中没有qr_code字段")
        
        return qr_code
    
    def verify(self, params: Dict[str, Any]) -> bool:
        """
        验证支付宝回调签名
        
        Args:
            params: 回调参数
            
        Returns:
            验证是否通过
        """
        if not CRYPTO_AVAILABLE:
            raise AlipayF2FException("需要安装pycryptodome库")
        
        if not self.alipay_public_key:
            raise AlipayF2FException("未设置支付宝公钥")
        
        # 提取签名
        sign = params.get('sign')
        if not sign:
            return False
        
        try:
            # 构建待验签字符串
            sign_string = self._build_sign_string(params)
            
            # 导入公钥
            key = RSA.import_key(self.alipay_public_key)
            
            # 计算哈希
            hash_obj = SHA256.new(sign_string.encode('utf-8'))
            
            # 验证签名
            pkcs1_15.new(key).verify(hash_obj, base64.b64decode(sign))
            return True
            
        except Exception:
            return False
