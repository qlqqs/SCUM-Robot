"""
支付提供商工厂类
基于Xboard的插件化设计，支持多种支付方式的统一管理
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum


class PaymentStatus(Enum):
    """支付状态枚举"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentResult:
    """支付结果类"""
    
    def __init__(self, success: bool, status: PaymentStatus, data: Optional[Dict[str, Any]] = None, 
                 error: Optional[str] = None):
        self.success = success
        self.status = status
        self.data = data or {}
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'status': self.status.value,
            'data': self.data,
            'error': self.error
        }


class PaymentInterface(ABC):
    """支付接口抽象类（参考Xboard的PaymentInterface）"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def form(self) -> Dict[str, Any]:
        """
        获取支付表单配置
        
        Returns:
            表单配置字典
        """
        pass
    
    @abstractmethod
    def pay(self, order_data: Dict[str, Any]) -> PaymentResult:
        """
        发起支付
        
        Args:
            order_data: 订单数据
            
        Returns:
            PaymentResult支付结果
        """
        pass
    
    @abstractmethod
    def notify(self, notify_data: Dict[str, Any]) -> PaymentResult:
        """
        处理支付回调通知
        
        Args:
            notify_data: 回调数据
            
        Returns:
            PaymentResult处理结果
        """
        pass
    
    def validate_config(self) -> bool:
        """
        验证配置有效性
        
        Returns:
            配置是否有效
        """
        return True


class EpayProvider(PaymentInterface):
    """易支付提供商（参考Xboard Epay插件）"""

    def form(self) -> Dict[str, Any]:
        """获取易支付表单配置"""
        return {
            'name': '易支付',
            'icon': self.config.get('icon', '/payment/icons/epay.png'),
            'description': '第三方易支付接口',
            'fields': [
                {
                    'name': 'url',
                    'label': '支付网关地址',
                    'type': 'text',
                    'required': True,
                    'placeholder': '请填写完整的支付网关地址，包括协议（http或https）'
                },
                {
                    'name': 'pid',
                    'label': '商户ID',
                    'type': 'text',
                    'required': True,
                    'placeholder': '请填写商户ID'
                },
                {
                    'name': 'key',
                    'label': '通信密钥',
                    'type': 'password',
                    'required': True,
                    'placeholder': '请填写通信密钥'
                },
                {
                    'name': 'type',
                    'label': '支付类型',
                    'type': 'text',
                    'required': False,
                    'default': 'alipay',
                    'placeholder': '支付类型，如: alipay, wxpay, qqpay 等'
                }
            ]
        }

    def pay(self, order_data: Dict[str, Any]) -> PaymentResult:
        """发起易支付"""
        try:
            import urllib.parse
            import hashlib

            # 构建支付参数
            params = {
                'money': order_data['amount'],
                'name': order_data.get('description', order_data['order_id']),
                'notify_url': order_data.get('notify_url', ''),
                'return_url': order_data.get('return_url', ''),
                'out_trade_no': order_data['order_id'],
                'pid': self.config.get('pid', '')
            }

            # 添加支付类型
            if payment_type := self.config.get('type'):
                params['type'] = payment_type

            # 参数排序
            sorted_params = dict(sorted(params.items()))

            # 构建签名字符串
            query_string = urllib.parse.urlencode(sorted_params)
            sign_string = urllib.parse.unquote(query_string) + self.config.get('key', '')

            # 生成签名
            params['sign'] = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
            params['sign_type'] = 'MD5'

            # 构建支付URL
            payment_url = f"{self.config.get('url', '')}/submit.php?" + urllib.parse.urlencode(params)

            return PaymentResult(
                success=True,
                status=PaymentStatus.PENDING,
                data={
                    'type': 1,  # 跳转类型
                    'payment_url': payment_url,
                    'order_id': order_data['order_id'],
                    'amount': order_data['amount']
                }
            )

        except Exception as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                error=f"易支付失败: {e}"
            )

    def notify(self, notify_data: Dict[str, Any]) -> PaymentResult:
        """处理易支付回调"""
        try:
            import urllib.parse
            import hashlib

            # 验证签名
            sign = notify_data.get('sign', '')
            verify_data = notify_data.copy()
            verify_data.pop('sign', None)
            verify_data.pop('sign_type', None)

            # 参数排序
            sorted_params = dict(sorted(verify_data.items()))

            # 构建签名字符串
            query_string = urllib.parse.urlencode(sorted_params)
            sign_string = urllib.parse.unquote(query_string) + self.config.get('key', '')

            # 验证签名
            expected_sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()

            if sign != expected_sign:
                return PaymentResult(
                    success=False,
                    status=PaymentStatus.FAILED,
                    error='签名验证失败'
                )

            # 检查支付状态
            if notify_data.get('trade_status') == 'TRADE_SUCCESS':
                return PaymentResult(
                    success=True,
                    status=PaymentStatus.SUCCESS,
                    data={
                        'transaction_id': notify_data.get('trade_no'),
                        'order_id': notify_data.get('out_trade_no'),
                        'amount': float(notify_data.get('money', 0))
                    }
                )
            else:
                return PaymentResult(
                    success=False,
                    status=PaymentStatus.FAILED,
                    error='支付未成功'
                )

        except Exception as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                error=f"处理易支付回调失败: {e}"
            )


class AlipayProvider(PaymentInterface):
    """支付宝提供商（使用AlipayF2F实现）"""

    def form(self) -> Dict[str, Any]:
        """获取支付宝表单配置"""
        return {
            'name': '支付宝当面付',
            'icon': self.config.get('icon', '/payment/icons/alipay.png'),
            'description': '支付宝当面付（扫码支付）',
            'fields': [
                {
                    'name': 'app_id',
                    'label': '应用ID',
                    'type': 'text',
                    'required': True,
                    'placeholder': '请输入支付宝应用ID'
                },
                {
                    'name': 'private_key',
                    'label': '应用私钥',
                    'type': 'textarea',
                    'required': True,
                    'placeholder': '请输入RSA私钥（PKCS1或PKCS8格式）'
                },
                {
                    'name': 'public_key',
                    'label': '支付宝公钥',
                    'type': 'textarea',
                    'required': True,
                    'placeholder': '请输入支付宝公钥'
                },
                {
                    'name': 'product_name',
                    'label': '商品名称',
                    'type': 'text',
                    'required': False,
                    'default': '商城币充值',
                    'placeholder': '将显示在支付宝账单中'
                }
            ]
        }

    def pay(self, order_data: Dict[str, Any]) -> PaymentResult:
        """发起支付宝当面付"""
        try:
            from .alipay_f2f import AlipayF2F, AlipayF2FException

            # 创建AlipayF2F实例
            gateway = AlipayF2F(sandbox=False)
            gateway.set_app_id(self.config.get('app_id'))
            gateway.set_private_key(self.config.get('private_key'))
            gateway.set_alipay_public_key(self.config.get('public_key'))
            gateway.set_method('alipay.trade.precreate')
            gateway.set_notify_url(order_data.get('notify_url', ''))

            # 设置业务参数
            gateway.set_biz_content({
                'subject': order_data.get('description', '商城币充值'),  # 使用订单描述
                'out_trade_no': order_data['order_id'],
                'total_amount': str(order_data['amount'])  # 金额必须是字符串
            })

            # 发送请求
            response = gateway.send()
            qr_code = gateway.get_qr_code_url()

            return PaymentResult(
                success=True,
                status=PaymentStatus.PENDING,
                data={
                    'type': 0,  # 二维码类型
                    'qr_code': qr_code,
                    'order_id': order_data['order_id'],
                    'amount': order_data['amount'],
                    'out_trade_no': response.get('out_trade_no')
                }
            )

        except AlipayF2FException as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                error=f"支付宝当面付失败: {e}"
            )
        except Exception as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                error=f"支付宝支付失败: {e}"
            )

    def notify(self, notify_data: Dict[str, Any]) -> PaymentResult:
        """处理支付宝回调"""
        try:
            from .alipay_f2f import AlipayF2F, AlipayF2FException

            # 创建AlipayF2F实例用于验签
            gateway = AlipayF2F(sandbox=False)
            gateway.set_app_id(self.config.get('app_id'))
            gateway.set_alipay_public_key(self.config.get('public_key'))

            # 验证签名
            if not gateway.verify(notify_data):
                return PaymentResult(
                    success=False,
                    status=PaymentStatus.FAILED,
                    error='签名验证失败'
                )

            # 检查交易状态
            trade_status = notify_data.get('trade_status')
            if trade_status == 'TRADE_SUCCESS':
                return PaymentResult(
                    success=True,
                    status=PaymentStatus.SUCCESS,
                    data={
                        'transaction_id': notify_data.get('trade_no'),
                        'order_id': notify_data.get('out_trade_no'),
                        'amount': float(notify_data.get('total_amount', 0))
                    }
                )
            elif trade_status == 'TRADE_FINISHED':
                # 交易完成（不可退款）
                return PaymentResult(
                    success=True,
                    status=PaymentStatus.SUCCESS,
                    data={
                        'transaction_id': notify_data.get('trade_no'),
                        'order_id': notify_data.get('out_trade_no'),
                        'amount': float(notify_data.get('total_amount', 0))
                    }
                )
            else:
                return PaymentResult(
                    success=False,
                    status=PaymentStatus.FAILED,
                    error=f'支付未成功，状态: {trade_status}'
                )

        except AlipayF2FException as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                error=f"处理支付宝回调失败: {e}"
            )
        except Exception as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                error=f"处理回调失败: {e}"
            )





class PaymentProviderFactory:
    """支付提供商工厂类（参考Xboard设计）"""
    
    _providers = {
        'alipay': AlipayProvider,
        'epay': EpayProvider
    }
    
    @classmethod
    def create_provider(cls, provider_code: str, config: Dict[str, Any]) -> Optional[PaymentInterface]:
        """
        创建支付提供商实例
        
        Args:
            provider_code: 提供商代码
            config: 配置参数
            
        Returns:
            支付提供商实例
        """
        provider_class = cls._providers.get(provider_code)
        if not provider_class:
            return None
        
        return provider_class(config)
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """获取支持的支付提供商列表"""
        return list(cls._providers.keys())
    
    @classmethod
    def register_provider(cls, provider_code: str, provider_class: type):
        """
        注册新的支付提供商
        
        Args:
            provider_code: 提供商代码
            provider_class: 提供商类
        """
        cls._providers[provider_code] = provider_class
