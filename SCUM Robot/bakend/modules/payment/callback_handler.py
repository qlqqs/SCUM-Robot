"""
支付回调处理服务
处理各支付平台的回调通知，确保支付流程完整性和安全性
"""

import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from .signature_verification import (
    PaymentSignatureVerifier, 
    AntiReplayAttackValidator, 
    IPWhitelistValidator,
    SignatureVerificationError
)
from ..sql.models.payment_order_models import PaymentOrder, PaymentCallback, PaymentOrderStatus
from ..sql.models.payment_models import PaymentConfig
from ..sql.services.user_assets_service import UserAssetsService
from ..common.service_result import ServiceResult


class PaymentCallbackResult:
    """支付回调处理结果"""
    
    def __init__(self, success: bool, message: str = "", data: Dict[str, Any] = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.response_body = ""
        self.response_status = 200 if success else 400
    
    def set_response(self, body: str, status: int = None):
        """设置响应内容"""
        self.response_body = body
        if status:
            self.response_status = status


class PaymentCallbackHandler:
    """支付回调处理器"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.signature_verifier = PaymentSignatureVerifier()
        self.anti_replay_validator = AntiReplayAttackValidator()
        self.ip_validator = IPWhitelistValidator()
    
    async def handle_callback(self, provider_code: str, callback_type: str,
                            request_data: Dict[str, Any], client_ip: str = None) -> PaymentCallbackResult:
        """
        处理支付回调
        
        Args:
            provider_code: 支付提供商代码
            callback_type: 回调类型 (notify/return)
            request_data: 请求数据
            client_ip: 客户端IP
            
        Returns:
            PaymentCallbackResult: 处理结果
        """
        start_time = time.time()
        callback_record = None
        
        try:
            # 1. 创建回调记录
            callback_record = self._create_callback_record(
                provider_code, callback_type, request_data, client_ip
            )
            
            # 2. 基础安全验证
            security_result = await self._validate_security(
                provider_code, request_data, client_ip
            )
            if not security_result.success:
                callback_record.is_valid = False
                callback_record.error_message = security_result.message
                self.db.commit()
                return security_result
            
            # 3. 解析订单信息
            order_info = self._parse_order_info(provider_code, request_data)
            if not order_info:
                result = PaymentCallbackResult(False, "无法解析订单信息")
                callback_record.is_valid = False
                callback_record.error_message = result.message
                self.db.commit()
                return result
            
            # 4. 查找订单
            order = self._find_order(order_info['order_id'])
            if not order:
                result = PaymentCallbackResult(False, f"订单不存在: {order_info['order_id']}")
                callback_record.is_valid = False
                callback_record.error_message = result.message
                self.db.commit()
                return result
            
            # 5. 验证订单状态
            if not order.can_process_callback():
                result = PaymentCallbackResult(False, f"订单状态不允许处理回调: {order.status}")
                callback_record.is_valid = False
                callback_record.error_message = result.message
                self.db.commit()
                return result
            
            # 6. 签名验证
            signature_result = await self._verify_signature(
                provider_code, request_data, order.payment_config_id
            )
            if not signature_result.success:
                callback_record.is_valid = False
                callback_record.error_message = signature_result.message
                self.db.commit()
                return signature_result
            
            # 7. 处理支付结果
            callback_record.is_valid = True
            processing_result = await self._process_payment_result(
                order, order_info, request_data
            )
            
            # 8. 更新回调记录
            callback_record.processing_status = "success" if processing_result.success else "failed"
            callback_record.set_processing_result(processing_result.data)
            callback_record.processing_time = time.time() - start_time
            
            # 9. 生成响应
            response = self._generate_response(provider_code, processing_result.success)
            processing_result.set_response(response['body'], response['status'])
            
            callback_record.response_status = processing_result.response_status
            callback_record.response_body = processing_result.response_body
            
            self.db.commit()
            return processing_result
            
        except Exception as e:
            # 记录异常
            if callback_record:
                callback_record.is_valid = False
                callback_record.error_message = str(e)
                callback_record.processing_time = time.time() - start_time
                self.db.commit()
            
            result = PaymentCallbackResult(False, f"回调处理异常: {e}")
            response = self._generate_response(provider_code, False)
            result.set_response(response['body'], response['status'])
            return result
    
    def _create_callback_record(self, provider_code: str, callback_type: str,
                              request_data: Dict[str, Any], client_ip: str) -> PaymentCallback:
        """创建回调记录"""
        callback_record = PaymentCallback(
            order_id=self._extract_order_id(provider_code, request_data),
            callback_type=callback_type,
            provider_code=provider_code,
            request_method=request_data.get('_method', 'POST'),
            request_url=request_data.get('_url', ''),
            request_body=json.dumps(request_data, ensure_ascii=False),
            request_ip=client_ip
        )
        
        # 设置请求头
        headers = request_data.get('_headers', {})
        if headers:
            callback_record.set_request_headers(headers)
        
        self.db.add(callback_record)
        self.db.flush()  # 获取ID
        return callback_record
    
    async def _validate_security(self, provider_code: str, request_data: Dict[str, Any],
                                client_ip: str) -> PaymentCallbackResult:
        """安全验证"""
        # IP白名单验证（测试环境暂时禁用）
        # TODO: 生产环境需要启用IP白名单验证
        if client_ip and not self.ip_validator.validate_ip(client_ip):
            return PaymentCallbackResult(False, f"IP地址不在白名单中: {client_ip}")
        
        # 防重放攻击验证
        request_id = self._generate_request_id(provider_code, request_data)
        timestamp = self._extract_timestamp(provider_code, request_data)
        
        if request_id and timestamp:
            if not self.anti_replay_validator.validate_request(request_id, timestamp):
                return PaymentCallbackResult(False, "检测到重放攻击")
        
        return PaymentCallbackResult(True, "安全验证通过")
    
    def _parse_order_info(self, provider_code: str, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析订单信息"""
        try:
            if provider_code == 'alipay':
                return {
                    'order_id': request_data.get('out_trade_no'),
                    'transaction_id': request_data.get('trade_no'),
                    'total_fee': float(request_data.get('total_amount', 0)),
                    'trade_status': request_data.get('trade_status')
                }
            elif provider_code == 'epay':
                return {
                    'order_id': request_data.get('out_trade_no'),
                    'transaction_id': request_data.get('trade_no'),
                    'total_fee': float(request_data.get('money', 0)),
                    'trade_status': request_data.get('trade_status')
                }
            
            return None
            
        except (ValueError, TypeError):
            return None
    
    def _find_order(self, order_id: str) -> Optional[PaymentOrder]:
        """查找订单"""
        return self.db.query(PaymentOrder).filter(
            PaymentOrder.order_id == order_id
        ).first()
    
    async def _verify_signature(self, provider_code: str, request_data: Dict[str, Any],
                               payment_config_id: int) -> PaymentCallbackResult:
        """验证签名"""
        try:
            # 获取支付配置
            config = self.db.query(PaymentConfig).filter(
                PaymentConfig.id == payment_config_id
            ).first()
            
            if not config:
                return PaymentCallbackResult(False, "支付配置不存在")
            
            # 解密配置
            config_data = config.get_decrypted_config()
            
            # 提取签名
            signature = self._extract_signature(provider_code, request_data)
            if not signature:
                return PaymentCallbackResult(False, "签名不存在")
            
            # 验证签名
            is_valid = self.signature_verifier.verify_signature(
                provider_code, request_data, signature, config_data
            )
            
            if is_valid:
                return PaymentCallbackResult(True, "签名验证通过")
            else:
                return PaymentCallbackResult(False, "签名验证失败")
                
        except SignatureVerificationError as e:
            return PaymentCallbackResult(False, str(e))
        except Exception as e:
            return PaymentCallbackResult(False, f"签名验证异常: {e}")
    
    async def _process_payment_result(self, order: PaymentOrder, order_info: Dict[str, Any],
                                    request_data: Dict[str, Any]) -> PaymentCallbackResult:
        """处理支付结果"""
        try:
            # 判断支付是否成功
            is_payment_success = self._is_payment_success(order.provider_code, order_info)
            
            if is_payment_success:
                # 支付成功处理
                return await self._handle_payment_success(order, order_info, request_data)
            else:
                # 支付失败处理
                return await self._handle_payment_failure(order, order_info, request_data)
                
        except Exception as e:
            return PaymentCallbackResult(False, f"支付结果处理异常: {e}")
    
    async def _handle_payment_success(self, order: PaymentOrder, order_info: Dict[str, Any],
                                    request_data: Dict[str, Any]) -> PaymentCallbackResult:
        """处理支付成功"""
        try:
            # 防止重复处理
            if order.is_success():
                return PaymentCallbackResult(True, "订单已处理", {
                    'order_id': order.order_id,
                    'already_processed': True
                })
            
            # 更新订单状态
            order.mark_as_success(
                platform_transaction_id=order_info.get('transaction_id'),
                paid_at=datetime.utcnow()
            )
            order.set_callback_data(request_data)
            order.increment_callback_count(request_data.get('_client_ip'))
            
            # 增加商城币
            coins_result = await self._add_shop_coins(order)
            if not coins_result.success:
                # 回滚订单状态
                order.mark_as_failed()
                return PaymentCallbackResult(False, f"增加商城币失败: {coins_result.message}")
            
            # 标记商城币已增加
            order.is_coins_added = True
            order.coins_added = coins_result.data.get('coins_added', 0)
            
            self.db.commit()
            
            return PaymentCallbackResult(True, "支付成功处理完成", {
                'order_id': order.order_id,
                'transaction_id': order_info.get('transaction_id'),
                'amount': float(order.amount),
                'coins_added': order.coins_added,
                'user_id': order.user_id
            })
            
        except Exception as e:
            self.db.rollback()
            return PaymentCallbackResult(False, f"支付成功处理异常: {e}")
    
    async def _handle_payment_failure(self, order: PaymentOrder, order_info: Dict[str, Any],
                                    request_data: Dict[str, Any]) -> PaymentCallbackResult:
        """处理支付失败"""
        try:
            # 更新订单状态
            order.mark_as_failed()
            order.set_callback_data(request_data)
            order.increment_callback_count(request_data.get('_client_ip'))
            
            self.db.commit()
            
            return PaymentCallbackResult(True, "支付失败处理完成", {
                'order_id': order.order_id,
                'status': 'failed',
                'reason': order_info.get('error_message', '支付失败')
            })
            
        except Exception as e:
            self.db.rollback()
            return PaymentCallbackResult(False, f"支付失败处理异常: {e}")
    
    async def _add_shop_coins(self, order: PaymentOrder) -> ServiceResult:
        """增加商城币"""
        try:
            # 如果订单关联了套餐，从套餐中获取商城币数量
            coins_to_add = 0
            if order.package_id:
                from ..sql.models.recharge_package_models import RechargePackage
                package = self.db.query(RechargePackage).filter(
                    RechargePackage.id == order.package_id
                ).first()
                if package:
                    coins_to_add = package.total_coins
                    print("[INFO] 从套餐获取商城币:")
                    print(f"   package_id: {order.package_id}")
                    print(f"   package_name: {package.name}")
                    print(f"   coins: {package.coins}")
                    print(f"   bonus_coins: {package.bonus_coins}")
                    print(f"   total_coins: {package.total_coins}")
                else:
                    print(f"[WARN] 套餐不存在: package_id={order.package_id}")
                    # 如果套餐不存在，使用默认计算方式
                    coins_to_add = int(order.amount * 10)
            else:
                # 如果没有关联套餐，使用默认计算方式（1元 = 10商城币）
                coins_to_add = int(order.amount * 10)
                print("[INFO] 使用默认计算方式（1元 = 10商城币）")

            print("[INFO] 开始增加商城币:")
            print(f"   user_id: {order.user_id}")
            print(f"   order_id: {order.order_id}")
            print(f"   amount: {order.amount}")
            print(f"   coins_to_add: {coins_to_add}")

            # 获取用户资产服务
            assets_service = UserAssetsService(self.db)

            # 增加商城币
            result = assets_service.update_shop_coins(
                user_id=order.user_id,
                amount=coins_to_add,
                operation="add"
            )

            print("[INFO] 商城币更新结果:")
            print(f"   success: {result.success}")
            print(f"   message: {result.message}")
            print(f"   data: {result.data}")

            if result.success:
                # 更新用户累计充值金额
                assets_result = assets_service.get_user_assets(order.user_id)
                if assets_result.success:
                    from ..sql.models.user_models import UserAssets
                    assets = self.db.query(UserAssets).filter(
                        UserAssets.user_id == order.user_id
                    ).first()
                    if assets:
                        assets.total_recharge += order.amount
                        assets.update_timestamp()
                        print(f"[INFO] 更新累计充值金额: {assets.total_recharge}")

                result.data['coins_added'] = coins_to_add

            return result

        except Exception as e:
            print(f"[ERROR] 增加商城币异常: {e}")
            import traceback
            traceback.print_exc()
            return ServiceResult.error(f"增加商城币异常: {e}")
    
    def _is_payment_success(self, provider_code: str, order_info: Dict[str, Any]) -> bool:
        """判断支付是否成功"""
        if provider_code == 'alipay':
            return order_info.get('trade_status') in ['TRADE_SUCCESS', 'TRADE_FINISHED']
        elif provider_code == 'epay':
            return order_info.get('trade_status') == 'TRADE_SUCCESS'

        return False
    
    def _generate_response(self, provider_code: str, success: bool) -> Dict[str, Any]:
        """生成响应"""
        if provider_code == 'alipay':
            return {
                'body': 'success' if success else 'fail',
                'status': 200
            }
        elif provider_code == 'epay':
            return {
                'body': 'success' if success else 'fail',
                'status': 200
            }
        
        return {
            'body': 'OK' if success else 'FAIL',
            'status': 200 if success else 400
        }
    
    def _extract_order_id(self, provider_code: str, request_data: Dict[str, Any]) -> str:
        """提取订单ID"""
        if provider_code == 'alipay':
            return request_data.get('out_trade_no', '')
        elif provider_code == 'epay':
            return request_data.get('out_trade_no', '')
        return ''
    
    def _extract_signature(self, provider_code: str, request_data: Dict[str, Any]) -> str:
        """提取签名"""
        if provider_code == 'alipay':
            return request_data.get('sign', '')
        elif provider_code == 'epay':
            return request_data.get('sign', '')
        return ''
    
    def _generate_request_id(self, provider_code: str, request_data: Dict[str, Any]) -> str:
        """生成请求ID（用于防重放攻击）"""
        order_id = self._extract_order_id(provider_code, request_data)
        timestamp = self._extract_timestamp(provider_code, request_data)
        return f"{provider_code}_{order_id}_{timestamp}"
    
    def _extract_timestamp(self, provider_code: str, request_data: Dict[str, Any]) -> int:
        """提取时间戳"""
        # 大多数支付平台不提供时间戳，使用当前时间
        return int(time.time())
