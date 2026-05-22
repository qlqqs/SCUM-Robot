"""
用户资产服务层
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import User, UserAssets
from .service_result import ServiceResult, ServiceErrorType


class UserAssetsService:
    """用户资产服务类"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_user_assets(self, user_id: int) -> ServiceResult:
        """
        获取用户资产信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            ServiceResult: 资产信息
        """
        try:
            assets = self.db.query(UserAssets).filter(UserAssets.user_id == user_id).first()
            if not assets:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "用户资产信息不存在"
                )
            
            return ServiceResult.success(
                data={
                    "user_id": assets.user_id,
                    "game_coins": assets.game_coins,
                    "shop_coins": assets.shop_coins,
                    "points": assets.points,
                    "total_recharge": float(assets.total_recharge),
                    "updated_at": assets.updated_at.isoformat()
                }
            )
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"获取用户资产失败: {str(e)}"
            )
    
    def update_game_coins(self, user_id: int, amount: int, operation: str = "add") -> ServiceResult:
        """
        更新游戏币
        
        Args:
            user_id: 用户ID
            amount: 变更数量
            operation: 操作类型 (add/subtract/set)
            
        Returns:
            ServiceResult: 更新结果
        """
        try:
            assets = self.db.query(UserAssets).filter(UserAssets.user_id == user_id).first()
            if not assets:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "用户资产信息不存在"
                )
            
            old_amount = assets.game_coins
            
            if operation == "add":
                assets.game_coins += amount
            elif operation == "subtract":
                if assets.game_coins < amount:
                    return ServiceResult.error(
                        ServiceErrorType.INSUFFICIENT_BALANCE,
                        "游戏币余额不足"
                    )
                assets.game_coins -= amount
            elif operation == "set":
                if amount < 0:
                    return ServiceResult.error(
                        ServiceErrorType.INVALID_PARAMETER,
                        "游戏币数量不能为负数"
                    )
                assets.game_coins = amount
            else:
                return ServiceResult.error(
                    ServiceErrorType.INVALID_PARAMETER,
                    "无效的操作类型"
                )
            
            assets.update_timestamp()
            self.db.commit()
            
            return ServiceResult.success(
                data={
                    "user_id": user_id,
                    "old_amount": old_amount,
                    "new_amount": assets.game_coins,
                    "change": assets.game_coins - old_amount
                },
                message=f"游戏币更新成功"
            )
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"更新游戏币失败: {str(e)}"
            )
    
    def update_shop_coins(self, user_id: int, amount: int, operation: str = "add") -> ServiceResult:
        """
        更新商城币
        
        Args:
            user_id: 用户ID
            amount: 变更数量
            operation: 操作类型 (add/subtract/set)
            
        Returns:
            ServiceResult: 更新结果
        """
        try:
            assets = self.db.query(UserAssets).filter(UserAssets.user_id == user_id).first()
            if not assets:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "用户资产信息不存在"
                )
            
            old_amount = assets.shop_coins
            
            if operation == "add":
                assets.shop_coins += amount
            elif operation == "subtract":
                if assets.shop_coins < amount:
                    return ServiceResult.error(
                        ServiceErrorType.INSUFFICIENT_BALANCE,
                        "商城币余额不足"
                    )
                assets.shop_coins -= amount
            elif operation == "set":
                if amount < 0:
                    return ServiceResult.error(
                        ServiceErrorType.INVALID_PARAMETER,
                        "商城币数量不能为负数"
                    )
                assets.shop_coins = amount
            else:
                return ServiceResult.error(
                    ServiceErrorType.INVALID_PARAMETER,
                    "无效的操作类型"
                )
            
            assets.update_timestamp()
            self.db.commit()
            
            return ServiceResult.success(
                data={
                    "user_id": user_id,
                    "old_amount": old_amount,
                    "new_amount": assets.shop_coins,
                    "change": assets.shop_coins - old_amount
                },
                message=f"商城币更新成功"
            )
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"更新商城币失败: {str(e)}"
            )
    
    def update_points(self, user_id: int, amount: int, operation: str = "add") -> ServiceResult:
        """
        更新积分
        
        Args:
            user_id: 用户ID
            amount: 变更数量
            operation: 操作类型 (add/subtract/set)
            
        Returns:
            ServiceResult: 更新结果
        """
        try:
            assets = self.db.query(UserAssets).filter(UserAssets.user_id == user_id).first()
            if not assets:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "用户资产信息不存在"
                )
            
            old_amount = assets.points
            
            if operation == "add":
                assets.points += amount
            elif operation == "subtract":
                if assets.points < amount:
                    return ServiceResult.error(
                        ServiceErrorType.INSUFFICIENT_BALANCE,
                        "积分余额不足"
                    )
                assets.points -= amount
            elif operation == "set":
                if amount < 0:
                    return ServiceResult.error(
                        ServiceErrorType.INVALID_PARAMETER,
                        "积分数量不能为负数"
                    )
                assets.points = amount
            else:
                return ServiceResult.error(
                    ServiceErrorType.INVALID_PARAMETER,
                    "无效的操作类型"
                )
            
            assets.update_timestamp()
            self.db.commit()

            # 如果是增加积分，检查VIP自动升级
            if operation == "add" and amount > 0:
                try:
                    from .vip_auto_upgrade_service import VIPAutoUpgradeService
                    upgrade_service = VIPAutoUpgradeService(self.db)
                    upgrade_service.check_and_upgrade_user(
                        user_id=user_id,
                        upgrade_type="auto",
                        upgrade_reason=f"积分增加{amount}，触发自动升级检查"
                    )
                except Exception as e:
                    # VIP升级失败不影响积分更新的成功
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"积分增加后VIP升级检查失败: {e}")

            return ServiceResult.success(
                data={
                    "user_id": user_id,
                    "old_amount": old_amount,
                    "new_amount": assets.points,
                    "change": assets.points - old_amount
                },
                message=f"积分更新成功"
            )
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"更新积分失败: {str(e)}"
            )
    
    def add_recharge(self, user_id: int, amount: float) -> ServiceResult:
        """
        添加充值记录
        
        Args:
            user_id: 用户ID
            amount: 充值金额
            
        Returns:
            ServiceResult: 更新结果
        """
        try:
            if amount <= 0:
                return ServiceResult.error(
                    ServiceErrorType.INVALID_PARAMETER,
                    "充值金额必须大于0"
                )
            
            assets = self.db.query(UserAssets).filter(UserAssets.user_id == user_id).first()
            if not assets:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "用户资产信息不存在"
                )
            
            old_total = assets.total_recharge
            assets.total_recharge += amount
            assets.update_timestamp()
            self.db.commit()
            
            return ServiceResult.success(
                data={
                    "user_id": user_id,
                    "recharge_amount": amount,
                    "old_total": float(old_total),
                    "new_total": float(assets.total_recharge)
                },
                message=f"充值记录添加成功"
            )
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"添加充值记录失败: {str(e)}"
            )
    
    def transfer_assets(self, from_user_id: int, to_user_id: int, 
                       asset_type: str, amount: int) -> ServiceResult:
        """
        资产转账
        
        Args:
            from_user_id: 转出用户ID
            to_user_id: 转入用户ID
            asset_type: 资产类型 (game_coins/shop_coins/points)
            amount: 转账数量
            
        Returns:
            ServiceResult: 转账结果
        """
        try:
            if amount <= 0:
                return ServiceResult.error(
                    ServiceErrorType.INVALID_PARAMETER,
                    "转账数量必须大于0"
                )
            
            if from_user_id == to_user_id:
                return ServiceResult.error(
                    ServiceErrorType.INVALID_PARAMETER,
                    "不能向自己转账"
                )
            
            # 获取转出用户资产
            from_assets = self.db.query(UserAssets).filter(UserAssets.user_id == from_user_id).first()
            if not from_assets:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "转出用户资产信息不存在"
                )
            
            # 获取转入用户资产
            to_assets = self.db.query(UserAssets).filter(UserAssets.user_id == to_user_id).first()
            if not to_assets:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND,
                    "转入用户资产信息不存在"
                )
            
            # 检查余额并执行转账
            if asset_type == "game_coins":
                if from_assets.game_coins < amount:
                    return ServiceResult.error(
                        ServiceErrorType.INSUFFICIENT_BALANCE,
                        "游戏币余额不足"
                    )
                from_assets.game_coins -= amount
                to_assets.game_coins += amount
            elif asset_type == "shop_coins":
                if from_assets.shop_coins < amount:
                    return ServiceResult.error(
                        ServiceErrorType.INSUFFICIENT_BALANCE,
                        "商城币余额不足"
                    )
                from_assets.shop_coins -= amount
                to_assets.shop_coins += amount
            elif asset_type == "points":
                if from_assets.points < amount:
                    return ServiceResult.error(
                        ServiceErrorType.INSUFFICIENT_BALANCE,
                        "积分余额不足"
                    )
                from_assets.points -= amount
                to_assets.points += amount
            else:
                return ServiceResult.error(
                    ServiceErrorType.INVALID_PARAMETER,
                    "无效的资产类型"
                )
            
            from_assets.update_timestamp()
            to_assets.update_timestamp()
            self.db.commit()
            
            return ServiceResult.success(
                data={
                    "from_user_id": from_user_id,
                    "to_user_id": to_user_id,
                    "asset_type": asset_type,
                    "amount": amount
                },
                message=f"{asset_type} 转账成功"
            )
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"转账失败: {str(e)}"
            )
