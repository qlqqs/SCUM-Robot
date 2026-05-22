"""
支付集成服务
与现有商城币系统和礼包系统集成
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..sql.database.manager import DatabaseManager
from ..sql.services.user_assets_service import UserAssetsService
from ..sql.services.service_result import ServiceResult, ServiceErrorType
from .payment_config_service import PaymentConfigService
from .payment_provider_factory import PaymentProviderFactory, PaymentStatus
from ..common.service_result import ServiceResult as CommonServiceResult


class PaymentIntegrationService:
    """支付集成服务（与现有系统集成）"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.config_service = PaymentConfigService(db_manager)

    def _get_full_callback_url(self, config_data: dict, url_key: str) -> str:
        """
        获取完整的回调URL

        Args:
            config_data: 支付配置数据
            url_key: URL键名（notify_url 或 return_url）

        Returns:
            str: 完整的回调URL
        """
        import os

        # 从配置中获取URL
        url = config_data.get(url_key, '')

        print("[DEBUG] _get_full_callback_url:")
        print(f"   url_key: {url_key}")
        print(f"   config_data[{url_key}]: {url}")

        # 如果已经是完整URL，直接返回
        if url.startswith('http://') or url.startswith('https://'):
            print(f"   [OK] 已是完整URL，直接返回: {url}")
            return url

        # 否则拼接完整URL
        # 优先从环境变量获取域名
        base_url = os.getenv('PAYMENT_CALLBACK_DOMAIN', '')
        print(f"   环境变量 PAYMENT_CALLBACK_DOMAIN: {base_url}")

        # 如果环境变量未设置，尝试从配置中获取
        if not base_url:
            base_url = config_data.get('callback_domain', '')
            print(f"   从配置获取 callback_domain: {base_url}")

        # 如果还是没有，则拒绝继续创建支付回调地址
        if not base_url:
            raise ValueError("未配置 PAYMENT_CALLBACK_DOMAIN 或 callback_domain，无法生成支付回调地址")

        # 移除base_url末尾的斜杠
        base_url = base_url.rstrip('/')
        print(f"   base_url (去除末尾斜杠): {base_url}")

        # 确保url以斜杠开头
        if not url.startswith('/'):
            url = '/' + url

        final_url = base_url + url
        print(f"   [OK] 最终URL: {final_url}")

        return final_url
    
    def check_payment_availability(self, environment: str = 'production') -> bool:
        """
        检查支付服务可用性
        
        Args:
            environment: 环境
            
        Returns:
            支付服务是否可用
        """
        try:
            # 获取激活的支付配置
            result = self.config_service.get_all_configs(environment, include_sensitive=False)
            if not result.success:
                return False
            
            # 检查是否有激活的配置
            active_configs = [config for config in result.data if config['is_active']]
            return len(active_configs) > 0
            
        except Exception as e:
            print(f"检查支付可用性失败: {e}")
            return False
    
    def get_available_payment_methods(self, environment: str = 'production') -> CommonServiceResult:
        """
        获取可用的支付方式
        
        Args:
            environment: 环境
            
        Returns:
            ServiceResult包含可用支付方式列表
        """
        try:
            result = self.config_service.get_all_configs(environment, include_sensitive=False)
            if not result.success:
                return CommonServiceResult.error(result.error)
            
            # 过滤激活的配置并格式化
            payment_methods = []
            for config in result.data:
                if config['is_active']:
                    payment_methods.append({
                        'id': config['id'],
                        'provider_code': config['provider_code'],
                        'provider_name': config['provider_name'],
                        'icon': config['icon'],
                        'description': config['description'],
                        'is_default': config['is_default']
                    })
            
            # 按排序顺序和默认状态排序
            payment_methods.sort(key=lambda x: (not x['is_default'], x.get('sort_order', 0)))
            
            return CommonServiceResult.success(payment_methods)
            
        except Exception as e:
            return CommonServiceResult.error(f"获取支付方式失败: {e}")
    
    def create_payment_order(self, user_id: int, amount: float, description: str,
                           payment_method_id: Optional[int] = None, package_id: Optional[int] = None) -> CommonServiceResult:
        """
        创建支付订单

        Args:
            user_id: 用户ID
            amount: 支付金额（元）
            description: 订单描述
            payment_method_id: 支付方式ID（可选，不提供则使用默认）
            package_id: 充值套餐ID（可选）

        Returns:
            ServiceResult包含订单信息
        """
        try:
            # 获取支付配置
            if payment_method_id:
                config_result = self.config_service.get_config_by_id(payment_method_id, include_sensitive=True)
            else:
                # 获取默认配置
                with self.db_manager.get_session() as session:
                    from ..sql.models.payment_models import PaymentConfig
                    default_config = PaymentConfig.get_default_config(session)
                    if not default_config:
                        return CommonServiceResult.error("未找到默认支付配置")
                    config_result = self.config_service.get_config_by_id(default_config.id, include_sensitive=True)
            
            if not config_result.success:
                return CommonServiceResult.error(config_result.error)
            
            config_data = config_result.data
            
            # 创建支付提供商实例
            provider = PaymentProviderFactory.create_provider(
                config_data['provider_code'], 
                config_data['config']
            )
            
            if not provider:
                return CommonServiceResult.error(f"不支持的支付提供商: {config_data['provider_code']}")
            
            # 生成订单ID
            import uuid
            order_id = f"SCUM_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

            # 获取完整的回调URL（从config_data['config']中获取）
            notify_url = self._get_full_callback_url(config_data['config'], 'notify_url')
            return_url = self._get_full_callback_url(config_data['config'], 'return_url')

            # 打印调试信息
            print(f"[INFO] 创建订单 {order_id}")
            print(f"   notify_url: {notify_url}")
            print(f"   return_url: {return_url}")

            # 准备订单数据
            order_data = {
                'order_id': order_id,
                'amount': amount,
                'description': description,
                'user_id': user_id,
                'notify_url': notify_url,
                'return_url': return_url
            }
            
            # 调用支付提供商创建支付
            payment_result = provider.pay(order_data)

            if payment_result.success:
                # 保存订单到数据库
                order_info = self._save_payment_order(
                    order_id, user_id, amount, description,
                    config_data, payment_result, package_id
                )

                return CommonServiceResult.success(order_info)
            else:
                return CommonServiceResult.error(payment_result.error)
                
        except Exception as e:
            return CommonServiceResult.error(f"创建支付订单失败: {e}")
    
    def process_payment_success(self, order_id: str, transaction_id: str, amount: float) -> CommonServiceResult:
        """
        处理支付成功回调
        
        Args:
            order_id: 订单ID
            transaction_id: 交易ID
            amount: 支付金额
            
        Returns:
            ServiceResult处理结果
        """
        try:
            # 从订单ID中提取用户ID
            order_parts = order_id.split('_')
            if len(order_parts) < 2 or order_parts[0] != 'SCUM':
                return CommonServiceResult.error("无效的订单ID格式")
            
            user_id = int(order_parts[1])
            
            # 计算要增加的商城币（1元 = 10商城币）
            coins_to_add = int(amount * 10)
            
            with self.db_manager.get_session() as session:
                # 获取用户资产服务
                assets_service = UserAssetsService(session)
                
                # 增加商城币
                result = assets_service.update_shop_coins(
                    user_id=user_id,
                    amount=coins_to_add,
                    operation="add"
                )
                
                if result.success:
                    # 更新用户累计充值金额
                    assets_result = assets_service.get_user_assets(user_id)
                    if assets_result.success:
                        from ..sql.models.user_models import UserAssets
                        assets = session.query(UserAssets).filter(UserAssets.user_id == user_id).first()
                        if assets:
                            assets.total_recharge += amount
                            assets.update_timestamp()
                            session.commit()

                    # 支付成功后检查VIP自动升级
                    try:
                        from ..sql.services.vip_auto_upgrade_service import VIPAutoUpgradeService
                        upgrade_service = VIPAutoUpgradeService(session)
                        upgrade_service.check_and_upgrade_user(
                            user_id=user_id,
                            upgrade_type="auto",
                            upgrade_reason=f"充值{amount}元成功，触发VIP升级检查"
                        )
                    except Exception as e:
                        # VIP升级失败不影响支付成功
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"支付成功后VIP升级检查失败: {e}")

                    return CommonServiceResult.success({
                        'user_id': user_id,
                        'order_id': order_id,
                        'transaction_id': transaction_id,
                        'amount_paid': amount,
                        'coins_added': coins_to_add,
                        'new_balance': result.data['new_amount']
                    })
                else:
                    return CommonServiceResult.error(f"增加商城币失败: {result.error.message}")
                    
        except Exception as e:
            return CommonServiceResult.error(f"处理支付成功回调失败: {e}")
    
    def validate_gift_payment_requirement(self, gift_name: str, user_id: int) -> CommonServiceResult:
        """
        验证礼包支付要求（与现有礼包系统集成）
        
        Args:
            gift_name: 礼包名称
            user_id: 用户ID
            
        Returns:
            ServiceResult验证结果
        """
        try:
            # 使用现有的价格解析逻辑
            from ..sql.services.gift_service import GiftService
            
            with self.db_manager.get_session() as session:
                gift_service = GiftService(session)
                price_yuan = gift_service._parse_gift_price(gift_name)
                
                if price_yuan is None:
                    # 免费礼包，无需支付验证
                    return CommonServiceResult.success({
                        'is_paid_gift': False,
                        'price_yuan': 0,
                        'required_coins': 0
                    })
                
                # 付费礼包，检查支付服务可用性
                if not self.check_payment_availability():
                    return CommonServiceResult.error("支付服务当前不可用，无法购买付费礼包")
                
                # 检查用户商城币余额
                assets_service = UserAssetsService(session)
                assets_result = assets_service.get_user_assets(user_id)
                
                if not assets_result.success:
                    return CommonServiceResult.error("获取用户资产信息失败")
                
                required_coins = price_yuan * 10
                current_coins = assets_result.data['shop_coins']
                
                return CommonServiceResult.success({
                    'is_paid_gift': True,
                    'price_yuan': price_yuan,
                    'required_coins': required_coins,
                    'current_coins': current_coins,
                    'balance_sufficient': current_coins >= required_coins,
                    'payment_methods_available': True
                })
                
        except Exception as e:
            return CommonServiceResult.error(f"验证礼包支付要求失败: {e}")
    
    def get_payment_statistics(self, user_id: Optional[int] = None) -> CommonServiceResult:
        """
        获取支付统计信息
        
        Args:
            user_id: 用户ID（可选，不提供则获取全局统计）
            
        Returns:
            ServiceResult包含统计信息
        """
        try:
            with self.db_manager.get_session() as session:
                from ..sql.models.user_models import UserAssets
                
                if user_id:
                    # 获取单个用户的统计
                    assets = session.query(UserAssets).filter(UserAssets.user_id == user_id).first()
                    if not assets:
                        return CommonServiceResult.error("用户资产信息不存在")
                    
                    stats = {
                        'user_id': user_id,
                        'total_recharge': float(assets.total_recharge),
                        'current_shop_coins': assets.shop_coins,
                        'current_game_coins': assets.game_coins,
                        'current_points': assets.points
                    }
                else:
                    # 获取全局统计
                    from sqlalchemy import func
                    
                    total_recharge = session.query(func.sum(UserAssets.total_recharge)).scalar() or 0
                    total_shop_coins = session.query(func.sum(UserAssets.shop_coins)).scalar() or 0
                    total_users = session.query(func.count(UserAssets.user_id)).scalar() or 0
                    
                    stats = {
                        'total_recharge': float(total_recharge),
                        'total_shop_coins': total_shop_coins,
                        'total_users': total_users,
                        'average_recharge': float(total_recharge / total_users) if total_users > 0 else 0
                    }
                
                return CommonServiceResult.success(stats)
                
        except Exception as e:
            return CommonServiceResult.error(f"获取支付统计失败: {e}")

    def _save_payment_order(self, order_id: str, user_id: int, amount: float,
                           description: str, config_data: dict, payment_result, package_id: Optional[int] = None) -> dict:
        """保存支付订单到数据库"""
        try:
            from datetime import datetime, timedelta
            from ..sql.models.payment_order_models import PaymentOrder

            with self.db_manager.get_db_session() as session:
                # 创建订单记录
                order = PaymentOrder(
                    order_id=order_id,
                    user_id=user_id,
                    amount=amount,
                    description=description,
                    payment_config_id=config_data['id'],
                    provider_code=config_data['provider_code'],
                    provider_name=config_data['provider_name'],
                    status=payment_result.status.value,
                    package_id=package_id,  # 设置套餐ID
                    expired_at=datetime.now() + timedelta(minutes=15)  # 15分钟过期
                )

                # 设置支付数据
                if payment_result.data:
                    order.set_payment_data(payment_result.data)

                session.add(order)
                session.commit()

                # 提取二维码和计算商城币
                qr_code = None
                coins = int(amount * 10)  # 1元 = 10商城币
                if payment_result.data:
                    qr_code = payment_result.data.get('qr_code')

                return {
                    'id': order.id,
                    'order_id': order.order_id,
                    'user_id': user_id,
                    'amount': amount,
                    'coins': coins,
                    'qr_code': qr_code,
                    'description': description,
                    'provider_code': config_data['provider_code'],
                    'provider_name': config_data['provider_name'],
                    'status': payment_result.status.value,
                    'payment_data': payment_result.data,
                    'expired_at': order.expired_at.isoformat() if order.expired_at else None,
                    'expires_at': order.expired_at.isoformat() if order.expired_at else None,  # 前端兼容
                    'created_at': order.created_at.isoformat() if order.created_at else None
                }

        except Exception as e:
            raise Exception(f"保存支付订单失败: {e}")
