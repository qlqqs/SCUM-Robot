"""
礼包服务层
"""

import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import GiftPackage, UserGiftRecord, User, GiftType, UserAssets
from ..models.user_models import VIPConfig
from .service_result import ServiceResult, ServiceErrorType
from .user_assets_service import UserAssetsService


class GiftService:
    """礼包服务类"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_gift_package(self, name: str, description: str, gift_type: GiftType,
                           items_config: Dict[str, Any], **kwargs) -> ServiceResult:
        """
        创建礼包
        
        Args:
            name: 礼包名称
            description: 礼包描述
            gift_type: 礼包类型
            items_config: 物品配置
            **kwargs: 其他配置参数
            
        Returns:
            ServiceResult: 创建结果
        """
        try:
            # 检查礼包名称是否已存在
            existing_gift = self.db.query(GiftPackage).filter(GiftPackage.name == name).first()
            if existing_gift:
                return ServiceResult.error(
                    ServiceErrorType.DUPLICATE_ENTRY,
                    f"礼包名称 '{name}' 已存在"
                )
            
            # 验证礼包配置
            validation_result = self._validate_gift_config(gift_type, kwargs)
            if not validation_result[0]:
                return ServiceResult.error(
                    ServiceErrorType.INVALID_PARAMETER,
                    validation_result[1]
                )

            # 创建礼包
            gift_package = GiftPackage(
                name=name,
                description=description,
                gift_type=gift_type,
                items_config=json.dumps(items_config, ensure_ascii=False),
                image_url=kwargs.get('image_url'),
                is_active=kwargs.get('is_active', True),
                start_time=kwargs.get('start_time'),
                end_time=kwargs.get('end_time'),
                max_claims=kwargs.get('max_claims', 1),
                cooldown_hours=kwargs.get('cooldown_hours', 24),
                required_level=kwargs.get('required_level', 0),
                total_quantity=kwargs.get('total_quantity'),
                claimed_quantity=kwargs.get('claimed_quantity', 0)
            )
            
            self.db.add(gift_package)
            self.db.commit()
            
            return ServiceResult.success(
                data={
                    "gift_id": gift_package.id,
                    "name": gift_package.name,
                    "gift_type": gift_package.gift_type.value
                },
                message="礼包创建成功"
            )
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"创建礼包失败: {str(e)}"
            )
    
    def get_available_gifts(self, user_id: int) -> ServiceResult:
        """
        获取用户可领取的礼包列表 - 增强版

        Args:
            user_id: 用户ID

        Returns:
            ServiceResult: 可领取礼包列表
        """
        try:
            user_vip_status = self._get_user_vip_status(user_id)
            current_time = datetime.utcnow()

            # 获取所有活跃的礼包
            active_gifts = self.db.query(GiftPackage).filter(
                and_(
                    GiftPackage.is_active == True,
                    or_(GiftPackage.start_time.is_(None), GiftPackage.start_time <= current_time),
                    or_(GiftPackage.end_time.is_(None), GiftPackage.end_time >= current_time)
                )
            ).all()

            available_gifts = []

            for gift in active_gifts:
                # 获取礼包分类和VIP要求
                category, gift_vip_level = self.get_gift_category_and_vip_level(gift.id)

                # 预过滤：只显示用户有权限查看的礼包
                if not self._should_show_gift_to_user(user_vip_status, category, gift_vip_level):
                    continue

                # 检查是否可以领取
                can_claim, reason = self._can_user_claim_gift(user_id, gift.id)

                # 获取用户领取历史
                claim_history = self._get_user_claim_history(user_id, gift.id)

                gift_data = {
                    "id": gift.id,
                    "name": gift.name,
                    "description": gift.description,
                    "gift_type": gift.gift_type.value,
                    "category": category,
                    "vip_level_required": gift_vip_level if category.startswith('vip') else None,
                    "items_config": json.loads(gift.items_config),
                    "max_claims": gift.max_claims,
                    "cooldown_hours": gift.cooldown_hours,
                    "required_level": gift.required_level,
                    "total_quantity": gift.total_quantity,
                    "claimed_quantity": gift.claimed_quantity,
                    "remaining_quantity": gift.total_quantity - gift.claimed_quantity if gift.total_quantity is not None else None,
                    "can_claim": can_claim,
                    "reason": reason if not can_claim else None,
                    "claim_history": claim_history,
                    "is_claimed": len(claim_history) > 0
                }

                available_gifts.append(gift_data)

            return ServiceResult.success(
                data={"gifts": available_gifts},
                message="获取礼包列表成功"
            )

        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"获取礼包列表失败: {str(e)}"
            )
    
    def claim_gift(self, user_id: int, gift_id: int) -> ServiceResult:
        """
        领取礼包
        
        Args:
            user_id: 用户ID
            gift_id: 礼包ID
            
        Returns:
            ServiceResult: 领取结果
        """
        # 初始化变量
        price_yuan = None
        deduct_result = None

        try:
            # 使用行锁获取礼包信息，防止并发问题
            from sqlalchemy import select
            gift_package = self.db.query(GiftPackage).filter(GiftPackage.id == gift_id).with_for_update().first()
            if not gift_package:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "礼包不存在"
                )

            # 检查用户是否可以领取（在锁定状态下再次检查）
            can_claim, reason = self._can_user_claim_gift(user_id, gift_id)
            if not can_claim:
                return ServiceResult.error(
                    ServiceErrorType.INVALID_PARAMETER,
                    reason
                )
            
            # 获取用户的steam_id
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "用户不存在"
                )

            # 检查是否为付费礼包并处理商城币扣除
            price_yuan = self._parse_gift_price(gift_package.name)

            if price_yuan is not None:
                # 这是付费礼包，检查并预扣除商城币
                deduct_result = self._check_and_deduct_shop_coins(user_id, price_yuan)
                if not deduct_result.success:
                    return deduct_result

            # 解析物品配置
            items_config = json.loads(gift_package.items_config)

            # 调用robot的生成物品功能
            items_received = self._generate_items_from_config(items_config, user.steam_id)
            
            # 更新已领取数量（如果是限量礼包）
            if gift_package.total_quantity is not None:
                gift_package.claimed_quantity += 1

            # 创建领取记录
            gift_record = UserGiftRecord(
                user_id=user_id,
                gift_package_id=gift_id,
                items_received=json.dumps(items_received, ensure_ascii=False),
                status='success'
            )

            self.db.add(gift_record)
            self.db.commit()

            # 准备返回数据
            result_data = {
                "gift_name": gift_package.name,
                "items_received": items_received,
                "claimed_at": gift_record.claimed_at.isoformat()
            }

            # 如果是付费礼包，添加扣费信息
            if price_yuan is not None and deduct_result:
                result_data["payment_info"] = {
                    "price_yuan": price_yuan,
                    "shop_coins_deducted": price_yuan * 10,
                    "remaining_coins": deduct_result.data["new_amount"]
                }

            # 调用反馈工具
            try:
                self._send_feedback_enhanced(user, gift_package, price_yuan, items_received)
            except Exception as e:
                print(f"调用反馈工具失败: {e}")

            return ServiceResult.success(
                data=result_data,
                message="礼包领取成功"
            )
            
        except Exception as e:
            self.db.rollback()

            # 如果是付费礼包且已经扣除了商城币，需要回滚
            if price_yuan is not None and deduct_result and deduct_result.success:
                try:
                    assets_service = UserAssetsService(self.db)
                    # 回滚商城币扣除
                    rollback_result = assets_service.update_shop_coins(
                        user_id=user_id,
                        amount=price_yuan * 10,
                        operation="add"
                    )
                    if rollback_result.success:
                        print(f"已回滚用户{user_id}的商城币扣除: {price_yuan * 10}")
                    else:
                        print(f"回滚商城币失败: {rollback_result.error.message}")
                except Exception as rollback_error:
                    print(f"回滚商城币时发生异常: {rollback_error}")

            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"领取礼包失败: {str(e)}"
            )
    
    def get_user_gift_history(self, user_id: int, limit: int = 50, offset: int = 0) -> ServiceResult:
        """
        获取用户礼包领取历史
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            ServiceResult: 领取历史
        """
        try:
            records = self.db.query(UserGiftRecord).filter(
                UserGiftRecord.user_id == user_id
            ).order_by(UserGiftRecord.claimed_at.desc()).offset(offset).limit(limit).all()
            
            history = []
            for record in records:
                gift_package = self.db.query(GiftPackage).filter(
                    GiftPackage.id == record.gift_package_id
                ).first()
                
                history_item = {
                    "id": record.id,
                    "gift_name": gift_package.name if gift_package else "未知礼包",
                    "gift_type": gift_package.gift_type.value if gift_package else "unknown",
                    "items_received": json.loads(record.items_received) if record.items_received else [],
                    "claimed_at": record.claimed_at.isoformat(),
                    "status": record.status
                }
                
                history.append(history_item)
            
            return ServiceResult.success(
                data={"history": history},
                message="获取领取历史成功"
            )
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"获取领取历史失败: {str(e)}"
            )
    
    def _can_user_claim_gift(self, user_id: int, gift_id: int) -> tuple[bool, str]:
        """
        检查用户是否可以领取指定礼包 - 增强版

        Args:
            user_id: 用户ID
            gift_id: 礼包ID

        Returns:
            tuple: (是否可以领取, 原因)
        """
        try:
            # 基础验证
            basic_check = self._basic_gift_validation(user_id, gift_id)
            if not basic_check[0]:
                return basic_check

            # 获取礼包分类和VIP等级
            category, gift_vip_level = self.get_gift_category_and_vip_level(gift_id)

            # 根据分类进行相应验证
            if category == 'vip_daily':
                vip_check = self._validate_vip_daily_gift(user_id, gift_vip_level)
                if not vip_check[0]:
                    return vip_check
            elif category == 'vip_level':
                vip_check = self._validate_vip_level_gift(user_id, gift_vip_level)
                if not vip_check[0]:
                    return vip_check
            elif category == 'paid_daily':
                paid_check = self._validate_paid_daily_gift(user_id, gift_id)
                if not paid_check[0]:
                    return paid_check
            # general 类型无需额外验证

            return True, ""

        except Exception as e:
            return False, f"权限验证失败: {str(e)}"

    def _basic_gift_validation(self, user_id: int, gift_id: int) -> tuple[bool, str]:
        """
        基础礼包验证 (原有逻辑)

        Args:
            user_id: 用户ID
            gift_id: 礼包ID

        Returns:
            tuple: (是否可以领取, 原因)
        """
        try:
            gift_package = self.db.query(GiftPackage).filter(GiftPackage.id == gift_id).first()
            if not gift_package:
                return False, "礼包不存在"

            if not gift_package.is_active:
                return False, "礼包已停用"

            current_time = datetime.utcnow()

            # 检查时间限制
            if gift_package.start_time and gift_package.start_time > current_time:
                return False, "礼包尚未开始"

            if gift_package.end_time and gift_package.end_time < current_time:
                return False, "礼包已过期"

            # 检查领取次数限制
            if gift_package.max_claims > 0:
                claim_count = self.db.query(UserGiftRecord).filter(
                    and_(
                        UserGiftRecord.user_id == user_id,
                        UserGiftRecord.gift_package_id == gift_id,
                        UserGiftRecord.status == 'success'
                    )
                ).count()

                if claim_count >= gift_package.max_claims:
                    return False, "已达到最大领取次数"

            # 检查冷却时间 (优化版)
            if gift_package.cooldown_hours > 0:
                if gift_package.cooldown_hours == 24:
                    # 每日礼包：按自然日检查
                    cooldown_check = self._check_daily_cooldown(user_id, gift_id, gift_package)
                    if not cooldown_check[0]:
                        return cooldown_check
                else:
                    # 其他礼包：按小时检查
                    cooldown_check = self._check_hour_cooldown(user_id, gift_id, gift_package)
                    if not cooldown_check[0]:
                        return cooldown_check

            # 检查全服限量
            if gift_package.total_quantity is not None:
                if gift_package.claimed_quantity >= gift_package.total_quantity:
                    return False, "礼包已被领完"

            return True, ""

        except Exception as e:
            return False, f"基础验证失败: {str(e)}"
    
    def get_gift_category_and_vip_level(self, gift_id: int) -> tuple:
        """
        获取礼包分类和所属VIP等级

        Args:
            gift_id: 礼包ID

        Returns:
            tuple: (category, vip_level)
            - category: 'general', 'vip_daily', 'vip_level', 'paid_daily'
            - vip_level: VIP等级 (仅VIP礼包有效)
        """
        try:
            # 检查是否为VIP每日礼包
            vip_daily = self.db.query(VIPConfig).filter(VIPConfig.daily_gift_id == gift_id).first()
            if vip_daily:
                return 'vip_daily', vip_daily.level

            # 检查是否为VIP等级礼包
            vip_level = self.db.query(VIPConfig).filter(VIPConfig.level_gift_id == gift_id).first()
            if vip_level:
                return 'vip_level', vip_level.level

            # 检查是否为付费每日礼包
            gift = self.db.query(GiftPackage).filter(GiftPackage.id == gift_id).first()
            if gift and self._is_paid_daily_gift(gift):
                return 'paid_daily', 0

            # 默认为普通礼包
            return 'general', 0

        except Exception as e:
            # 出错时默认为普通礼包
            return 'general', 0

    def _is_paid_daily_gift(self, gift: GiftPackage) -> bool:
        """
        判断是否为付费每日礼包

        Args:
            gift: 礼包对象

        Returns:
            bool: 是否为付费每日礼包
        """
        # 通过命名规则识别付费礼包
        if not gift.name:
            return False

        paid_keywords = ['付费', '购买', '商店', '充值']
        return any(keyword in gift.name for keyword in paid_keywords)

    def _get_user_vip_status(self, user_id: int) -> dict:
        """
        获取用户VIP状态

        Args:
            user_id: 用户ID

        Returns:
            dict: VIP状态信息
        """
        try:
            from ..models.user_models import User
            from datetime import date

            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'vip_level': 0, 'is_expired': False, 'expire_date': None}

            # 检查VIP是否过期
            today = date.today()
            is_expired = user.vip_expire_date < today if user.vip_expire_date else False

            return {
                'vip_level': user.vip_level if not is_expired else 0,
                'is_expired': is_expired,
                'expire_date': user.vip_expire_date
            }

        except Exception as e:
            return {'vip_level': 0, 'is_expired': False, 'expire_date': None}

    def _validate_vip_daily_gift(self, user_id: int, required_vip_level: int) -> tuple:
        """
        验证VIP每日礼包权限 - 精确匹配

        Args:
            user_id: 用户ID
            required_vip_level: 所需VIP等级

        Returns:
            tuple: (是否可以领取, 原因)
        """
        user_vip_status = self._get_user_vip_status(user_id)
        user_vip_level = user_vip_status['vip_level']
        is_vip_expired = user_vip_status['is_expired']

        # VIP过期检查
        if required_vip_level > 0 and is_vip_expired:
            return False, "VIP已过期，无法领取VIP礼包"

        # 精确等级匹配
        if user_vip_level != required_vip_level:
            if required_vip_level == 0:
                return False, "此礼包仅限普通用户领取"
            else:
                return False, f"此礼包仅限VIP{required_vip_level}等级领取"

        return True, ""

    def _validate_vip_level_gift(self, user_id: int, required_vip_level: int) -> tuple:
        """
        验证VIP等级礼包权限 - 向下兼容

        Args:
            user_id: 用户ID
            required_vip_level: 所需VIP等级

        Returns:
            tuple: (是否可以领取, 原因)
        """
        user_vip_status = self._get_user_vip_status(user_id)
        user_vip_level = user_vip_status['vip_level']
        is_vip_expired = user_vip_status['is_expired']

        # VIP过期检查
        if required_vip_level > 0 and is_vip_expired:
            return False, "VIP已过期，无法领取VIP等级礼包"

        # 等级达到要求检查
        if user_vip_level < required_vip_level:
            return False, f"需要达到VIP{required_vip_level}等级才能领取此礼包"

        return True, ""

    def _validate_paid_daily_gift(self, user_id: int, gift_id: int) -> tuple:
        """
        验证付费每日礼包权限 - 每人每天限购一次

        Args:
            user_id: 用户ID
            gift_id: 礼包ID

        Returns:
            tuple: (是否可以领取, 原因)
        """
        try:
            from datetime import date
            from sqlalchemy import func

            today = date.today()

            # 检查今日是否已购买
            today_purchase = self.db.query(UserGiftRecord).filter(
                and_(
                    UserGiftRecord.user_id == user_id,
                    UserGiftRecord.gift_package_id == gift_id,
                    UserGiftRecord.status == 'success',
                    func.date(UserGiftRecord.claimed_at) == today
                )
            ).first()

            if today_purchase:
                return False, "今日已购买此礼包，明天可再次购买"

            return True, ""

        except Exception as e:
            return False, f"验证付费礼包权限失败: {str(e)}"

    def _check_daily_cooldown(self, user_id: int, gift_id: int, gift_package: GiftPackage) -> tuple:
        """
        检查每日礼包冷却 - 按自然日重置

        Args:
            user_id: 用户ID
            gift_id: 礼包ID
            gift_package: 礼包对象

        Returns:
            tuple: (是否可以领取, 原因)
        """
        try:
            from datetime import date
            from sqlalchemy import func

            today = date.today()

            # 检查今日是否已领取
            today_claim = self.db.query(UserGiftRecord).filter(
                and_(
                    UserGiftRecord.user_id == user_id,
                    UserGiftRecord.gift_package_id == gift_id,
                    UserGiftRecord.status == 'success',
                    func.date(UserGiftRecord.claimed_at) == today
                )
            ).first()

            if today_claim:
                return False, "今日已领取，明天00:00后可再次领取"

            return True, ""

        except Exception as e:
            return False, f"检查每日冷却失败: {str(e)}"

    def _check_hour_cooldown(self, user_id: int, gift_id: int, gift_package: GiftPackage) -> tuple:
        """
        检查小时冷却 - 原有逻辑

        Args:
            user_id: 用户ID
            gift_id: 礼包ID
            gift_package: 礼包对象

        Returns:
            tuple: (是否可以领取, 原因)
        """
        try:
            last_claim = self.db.query(UserGiftRecord).filter(
                and_(
                    UserGiftRecord.user_id == user_id,
                    UserGiftRecord.gift_package_id == gift_id,
                    UserGiftRecord.status == 'success'
                )
            ).order_by(UserGiftRecord.claimed_at.desc()).first()

            if last_claim:
                cooldown_end = last_claim.claimed_at + timedelta(hours=gift_package.cooldown_hours)
                current_time = datetime.utcnow()
                if current_time < cooldown_end:
                    remaining_hours = (cooldown_end - current_time).total_seconds() / 3600
                    return False, f"冷却中，还需等待 {remaining_hours:.1f} 小时"

            return True, ""

        except Exception as e:
            return False, f"检查小时冷却失败: {str(e)}"

    def _should_show_gift_to_user(self, user_vip_status: dict, category: str, gift_vip_level: int) -> bool:
        """
        判断是否应该向用户显示此礼包

        Args:
            user_vip_status: 用户VIP状态
            category: 礼包分类
            gift_vip_level: 礼包所需VIP等级

        Returns:
            bool: 是否应该显示
        """
        user_vip_level = user_vip_status['vip_level']
        is_vip_expired = user_vip_status['is_expired']

        if category == 'general' or category == 'paid_daily':
            return True  # 普通礼包和付费礼包对所有人可见

        if category == 'vip_daily':
            # VIP每日礼包：只显示当前VIP等级的礼包
            if is_vip_expired and gift_vip_level > 0:
                return False
            return user_vip_level == gift_vip_level

        if category == 'vip_level':
            # VIP等级礼包：显示当前等级及以下的礼包
            if is_vip_expired and gift_vip_level > 0:
                return False
            return user_vip_level >= gift_vip_level

        return True

    def _get_user_claim_history(self, user_id: int, gift_id: int) -> list:
        """
        获取用户对特定礼包的领取历史

        Args:
            user_id: 用户ID
            gift_id: 礼包ID

        Returns:
            list: 领取历史记录
        """
        try:
            records = self.db.query(UserGiftRecord).filter(
                and_(
                    UserGiftRecord.user_id == user_id,
                    UserGiftRecord.gift_package_id == gift_id,
                    UserGiftRecord.status == 'success'
                )
            ).order_by(UserGiftRecord.claimed_at.desc()).all()

            history = []
            for record in records:
                history.append({
                    'claimed_at': record.claimed_at.isoformat(),
                    'items_received': json.loads(record.items_received) if record.items_received else []
                })

            return history

        except Exception as e:
            return []

    def _generate_items_from_config(self, items_config: Dict[str, Any], steam_id: str) -> List[Dict[str, Any]]:
        """
        根据配置生成物品并发送SCUM命令

        Args:
            items_config: 物品配置
            steam_id: 用户的Steam ID

        Returns:
            List: 生成的物品列表
        """
        from ...robot.instructionSet import InstructionSet

        # 创建robot指令集实例，启用命令发送器
        robot = InstructionSet(enable_sender=True)

        items_received = []
        failed_items = []

        # 处理包装格式：{"items": [...]}
        if isinstance(items_config, dict) and "items" in items_config:
            # 提取items数组
            items_list = items_config["items"]
            if isinstance(items_list, list):
                items_config = items_list
            else:
                print(f"警告: items字段不是数组格式: {type(items_list)}")
                return items_received

        # 处理不同格式的物品配置
        if isinstance(items_config, dict):
            # 字典格式：{物品代码: 数量}
            for item_code, quantity in items_config.items():
                try:
                    # 默认使用spawnitem命令
                    success = robot.spawn_item(
                        item_name=item_code,
                        quantity=quantity,
                        location=steam_id,
                        execute=True
                    )

                    if success:
                        items_received.append({
                            "command": "#spawnitem",
                            "item": item_code,
                            "amount": quantity,
                            "status": "success",
                            "generated_at": datetime.utcnow().isoformat()
                        })
                    else:
                        failed_items.append({
                            "command": "#spawnitem",
                            "item": item_code,
                            "amount": quantity,
                            "status": "failed",
                            "error": "命令执行失败"
                        })

                except Exception as e:
                    failed_items.append({
                        "command": "#spawnitem",
                        "item": item_code,
                        "amount": quantity,
                        "status": "failed",
                        "error": str(e)
                    })

        elif isinstance(items_config, list):
            # 数组格式：[{command, item, amount}]
            for item_config in items_config:
                try:
                    command = item_config.get("command", "#spawnitem")
                    item = item_config.get("item", "")
                    amount = item_config.get("amount", 1)

                    success = False

                    if command == "#spawnitem":
                        # 生成物品命令
                        success = robot.spawn_item(
                            item_name=item,
                            quantity=amount,
                            location=steam_id,
                            execute=True
                        )
                    elif command == "#ChangeCurrencyBalance":
                        # 改变货币余额命令
                        success = robot.change_currency_balance(
                            amount=amount,
                            player_identifier=steam_id,
                            execute=True
                        )
                    elif command == "#ChangeFamePoints":
                        # 改变声望点数命令 - 只需要命令、数量和steamid，不需要物品字段
                        success = robot.change_fame_points(
                            points=amount,
                            player_identifier=steam_id,
                            execute=True
                        )
                    else:
                        # 其他命令，直接发送
                        from ...robot.sentCommand import CommandSender
                        sender = CommandSender()

                        # 对于#ChangeFamePoints命令，不包含物品字段
                        if command == "#ChangeFamePoints":
                            full_command = f"{command} {amount} {steam_id}"
                        else:
                            full_command = f"{command} {item} {amount} {steam_id}"

                        success = sender.send_scum_command(full_command)

                    if success:
                        items_received.append({
                            "command": command,
                            "item": item,
                            "amount": amount,
                            "status": "success",
                            "generated_at": datetime.utcnow().isoformat()
                        })
                    else:
                        failed_items.append({
                            "command": command,
                            "item": item,
                            "amount": amount,
                            "status": "failed",
                            "error": "命令执行失败"
                        })

                except Exception as e:
                    failed_items.append({
                        "command": command if 'command' in locals() else "unknown",
                        "item": item if 'item' in locals() else "unknown",
                        "amount": amount if 'amount' in locals() else 0,
                        "status": "failed",
                        "error": str(e)
                    })

        # 如果有失败的物品，记录到日志中
        if failed_items:
            print(f"礼包领取部分失败，Steam ID: {steam_id}, 失败物品: {failed_items}")

        return items_received

    def _parse_gift_price(self, gift_name: str) -> Optional[int]:
        """
        解析礼包名称中的价格（元）

        Args:
            gift_name: 礼包名称

        Returns:
            Optional[int]: 价格（元），如果不是付费礼包则返回None
        """
        # 检查是否包含付费字样
        paid_keywords = ['付费', '收费', '充值']
        if any(keyword in gift_name for keyword in paid_keywords):
            # 如果只是包含付费字样但没有具体价格，默认为1元
            return 1

        # 匹配中文数字 + 元（按长度排序，优先匹配长的）
        chinese_numbers = [
            ('二十', 20), ('三十', 30), ('四十', 40), ('五十', 50),
            ('一', 1), ('二', 2), ('三', 3), ('四', 4), ('五', 5),
            ('六', 6), ('七', 7), ('八', 8), ('九', 9), ('十', 10),
            ('两', 2)
        ]

        for chinese, number in chinese_numbers:
            if f"{chinese}元" in gift_name:
                return number

        # 匹配阿拉伯数字 + 元
        pattern = r'(\d+)元'
        match = re.search(pattern, gift_name)
        if match:
            return int(match.group(1))

        # 没有找到价格信息，不是付费礼包
        return None

    def _check_and_deduct_shop_coins(self, user_id: int, price_yuan: int) -> ServiceResult:
        """
        检查并扣除用户商城币

        Args:
            user_id: 用户ID
            price_yuan: 价格（元）

        Returns:
            ServiceResult: 扣除结果
        """
        try:
            # 计算需要的商城币数量（1元=10商城币）
            required_coins = price_yuan * 10

            # 获取用户资产服务
            assets_service = UserAssetsService(self.db)

            # 获取用户当前商城币余额
            assets_result = assets_service.get_user_assets(user_id)
            if not assets_result.success:
                return assets_result

            current_coins = assets_result.data['shop_coins']

            # 检查余额是否足够
            if current_coins < required_coins:
                return ServiceResult.error(
                    ServiceErrorType.INSUFFICIENT_BALANCE,
                    f"商城币余额不足，需要{required_coins}商城币，当前余额{current_coins}商城币"
                )

            # 扣除商城币
            deduct_result = assets_service.update_shop_coins(
                user_id=user_id,
                amount=required_coins,
                operation="subtract"
            )

            return deduct_result

        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"处理商城币扣除失败: {str(e)}"
            )

    def _send_feedback_enhanced(self, user: User, gift_package: GiftPackage, price_yuan: Optional[int], items_received: List[Dict[str, Any]]):
        """
        发送增强反馈信息

        Args:
            user: 用户对象
            gift_package: 礼包对象
            price_yuan: 价格（元），如果是免费礼包则为None
            items_received: 领取的物品列表
        """
        try:
            # 构建反馈消息
            feedback_data = {
                "event_type": "gift_claimed",
                "timestamp": datetime.utcnow().isoformat(),
                "user_info": {
                    "user_id": user.id,
                    "username": user.username,
                    "steam_id": user.steam_id
                },
                "gift_info": {
                    "gift_id": gift_package.id,
                    "gift_name": gift_package.name,
                    "gift_type": gift_package.gift_type.value if hasattr(gift_package.gift_type, 'value') else str(gift_package.gift_type),
                    "is_paid": price_yuan is not None
                },
                "items_received": items_received
            }

            # 如果是付费礼包，添加支付信息
            if price_yuan is not None:
                feedback_data["payment_info"] = {
                    "price_yuan": price_yuan,
                    "shop_coins_deducted": price_yuan * 10
                }

            # 构建用户友好的消息
            message = f"[INFO] 用户 {user.username} 成功领取礼包 '{gift_package.name}'"
            if price_yuan is not None:
                message += f" (消费 {price_yuan}元)"

            message += f"\n[INFO] 获得物品: {len(items_received)}件"
            for item in items_received[:3]:  # 只显示前3件物品
                command = item.get('command', '')
                item_name = item.get('item', '')
                amount = item.get('amount', 0)
                if command == '#spawnitem':
                    message += f"\n  - {item_name} x{amount}"
                elif command == '#ChangeCurrencyBalance':
                    message += f"\n  - 货币 +{amount}"
                elif command == '#ChangeFamePoints':
                    message += f"\n  - 声望点数 +{amount}"

            if len(items_received) > 3:
                message += f"\n  - ... 还有 {len(items_received) - 3} 件物品"

            # 记录详细日志
            print(f"[MCP反馈] {message}")
            print(f"[MCP数据] {json.dumps(feedback_data, ensure_ascii=False, indent=2)}")

            # TODO: 这里应该调用实际的mcp-feedback-enhanced工具
            # 由于当前环境中没有该工具，我们先用日志记录
            # 在实际部署时，应该替换为真正的MCP调用

        except Exception as e:
            print(f"发送反馈时发生错误: {e}")

    def _validate_gift_config(self, gift_type: GiftType, config: Dict[str, Any]) -> tuple:
        """
        验证礼包配置

        Args:
            gift_type: 礼包类型
            config: 配置参数

        Returns:
            tuple: (是否有效, 错误信息)
        """
        try:
            # 限量礼包必须设置total_quantity
            if gift_type in [GiftType.LIMITED_QUANTITY, GiftType.LIMITED_TIME_QUANTITY]:
                if config.get('total_quantity') is None or config.get('total_quantity') <= 0:
                    return False, "限量礼包必须设置有效的total_quantity"

            # 限时礼包必须设置时间范围
            if gift_type in [GiftType.LIMITED_TIME, GiftType.LIMITED_TIME_QUANTITY]:
                if not config.get('start_time') or not config.get('end_time'):
                    return False, "限时礼包必须设置start_time和end_time"

                if config.get('start_time') >= config.get('end_time'):
                    return False, "开始时间必须早于结束时间"

            # 一次性礼包配置建议
            if gift_type == GiftType.ONE_TIME:
                if config.get('max_claims', 1) != 1:
                    return False, "一次性礼包的max_claims应该为1"
                if config.get('cooldown_hours', 0) != 0:
                    return False, "一次性礼包的cooldown_hours应该为0"

            # 每日礼包配置建议
            if gift_type == GiftType.DAILY:
                if config.get('max_claims', -1) != -1:
                    return False, "每日礼包的max_claims应该为-1（无限制）"
                if config.get('cooldown_hours', 24) != 24:
                    return False, "每日礼包的cooldown_hours应该为24"

            return True, ""

        except Exception as e:
            return False, f"配置验证失败: {str(e)}"
