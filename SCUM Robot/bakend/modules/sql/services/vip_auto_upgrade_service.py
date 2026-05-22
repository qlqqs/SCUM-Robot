"""
VIP自动升级服务

基于用户积分自动升级VIP等级的服务类
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.user_models import User, UserAssets, VIPConfig, VIPUpgradeHistory
from .service_result import ServiceResult, ServiceError, ServiceErrorType


class VIPAutoUpgradeService:
    """VIP自动升级服务类"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def check_and_upgrade_user(self, user_id: int, upgrade_type: str = "auto", upgrade_reason: str = None) -> ServiceResult:
        """
        检查并升级用户VIP等级
        
        Args:
            user_id: 用户ID
            upgrade_type: 升级类型 (auto/manual)
            upgrade_reason: 升级原因说明
            
        Returns:
            ServiceResult: 升级结果
        """
        try:
            # 获取用户信息
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ServiceResult.error(ServiceErrorType.NOT_FOUND, "用户不存在")
            
            # 获取用户资产信息
            assets = self.db.query(UserAssets).filter(UserAssets.user_id == user_id).first()
            if not assets:
                return ServiceResult.error(ServiceErrorType.NOT_FOUND, "用户资产信息不存在")
            
            current_points = assets.points
            current_level = user.vip_level
            
            # 查找符合条件的最高VIP等级
            eligible_level = self.get_eligible_vip_level(current_points)
            
            if not eligible_level or eligible_level.level <= current_level:
                # 无需升级
                return ServiceResult.success(
                    data={
                        'user_id': user_id,
                        'current_level': current_level,
                        'current_points': current_points,
                        'upgrade_needed': False,
                        'message': '当前积分不满足升级条件或已是最高等级'
                    },
                    message="无需升级"
                )
            
            # 执行升级
            upgrade_result = self.execute_upgrade(
                user_id=user_id,
                old_level=current_level,
                new_level=eligible_level.level,
                trigger_points=current_points,
                required_points=eligible_level.upgrade_required_points,
                upgrade_type=upgrade_type,
                upgrade_reason=upgrade_reason or f"积分达到{eligible_level.upgrade_required_points}，自动升级到{eligible_level.name}"
            )
            
            return upgrade_result
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"检查VIP升级失败: {str(e)}"
            )
    
    def get_eligible_vip_level(self, current_points: int) -> Optional[VIPConfig]:
        """
        根据积分获取符合条件的最高VIP等级
        
        Args:
            current_points: 当前积分
            
        Returns:
            VIPConfig: 符合条件的最高VIP配置，如果没有则返回None
        """
        try:
            # 查找所有VIP配置，按等级降序排列
            vip_configs = self.db.query(VIPConfig).filter(
                VIPConfig.upgrade_required_points <= current_points
            ).order_by(VIPConfig.level.desc()).all()
            
            # 返回最高等级的配置
            return vip_configs[0] if vip_configs else None
            
        except Exception:
            return None
    
    def execute_upgrade(self, user_id: int, old_level: int, new_level: int, 
                       trigger_points: int, required_points: int,
                       upgrade_type: str = "auto", upgrade_reason: str = None) -> ServiceResult:
        """
        执行VIP升级
        
        Args:
            user_id: 用户ID
            old_level: 原VIP等级
            new_level: 新VIP等级
            trigger_points: 触发升级时的积分
            required_points: 升级所需积分
            upgrade_type: 升级类型
            upgrade_reason: 升级原因
            
        Returns:
            ServiceResult: 升级结果
        """
        try:
            # 获取用户
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ServiceResult.error(ServiceErrorType.NOT_FOUND, "用户不存在")
            
            # 获取新等级配置
            new_vip_config = self.db.query(VIPConfig).filter(
                VIPConfig.level == new_level
            ).first()
            
            if not new_vip_config:
                return ServiceResult.error(ServiceErrorType.NOT_FOUND, f"VIP{new_level}配置不存在")
            
            # 更新用户VIP等级
            user.vip_level = new_level
            user.updated_at = datetime.utcnow()
            
            # 记录升级历史
            upgrade_history = VIPUpgradeHistory(
                user_id=user_id,
                old_level=old_level,
                new_level=new_level,
                upgrade_type=upgrade_type,
                trigger_points=trigger_points,
                required_points=required_points,
                upgrade_reason=upgrade_reason
            )

            self.db.add(upgrade_history)
            self.db.commit()

            upgrade_data = {
                'user_id': user_id,
                'old_level': old_level,
                'new_level': new_level,
                'vip_name': new_vip_config.name,
                'trigger_points': trigger_points,
                'required_points': required_points,
                'upgrade_type': upgrade_type,
                'upgrade_reason': upgrade_reason,
                'upgrade_time': upgrade_history.created_at.isoformat()
            }
            
            return ServiceResult.success(
                data=upgrade_data,
                message=f"VIP升级成功！从{old_level}级升级到{new_level}级({new_vip_config.name})"
            )
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"执行VIP升级失败: {str(e)}"
            )
    

    
    def get_upgrade_history(self, user_id: int, limit: int = 20, offset: int = 0) -> ServiceResult:
        """
        获取用户VIP升级历史
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            ServiceResult: 升级历史
        """
        try:
            histories = self.db.query(VIPUpgradeHistory).filter(
                VIPUpgradeHistory.user_id == user_id
            ).order_by(VIPUpgradeHistory.created_at.desc()).offset(offset).limit(limit).all()
            
            history_data = []
            for history in histories:
                history_item = history.to_dict()
                history_data.append(history_item)
            
            return ServiceResult.success(
                data={
                    'user_id': user_id,
                    'total_count': len(history_data),
                    'histories': history_data
                },
                message="获取VIP升级历史成功"
            )
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"获取VIP升级历史失败: {str(e)}"
            )
    
    def batch_check_upgrades(self, user_ids: List[int] = None, force_check: bool = False) -> ServiceResult:
        """
        批量检查用户VIP升级
        
        Args:
            user_ids: 用户ID列表，为空则检查所有用户
            force_check: 是否强制检查
            
        Returns:
            ServiceResult: 批量检查结果
        """
        try:
            if user_ids is None:
                # 获取所有有积分的用户
                users_with_assets = self.db.query(User.id).join(UserAssets).filter(
                    UserAssets.points > 0
                ).all()
                user_ids = [user.id for user in users_with_assets]
            
            upgrade_results = []
            success_count = 0
            error_count = 0
            
            for user_id in user_ids:
                try:
                    result = self.check_and_upgrade_user(
                        user_id=user_id,
                        upgrade_type="batch",
                        upgrade_reason="批量升级检查"
                    )
                    
                    upgrade_results.append({
                        'user_id': user_id,
                        'success': result.success,
                        'message': result.message,
                        'data': result.data
                    })
                    
                    if result.success and result.data.get('upgrade_needed', False):
                        success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    upgrade_results.append({
                        'user_id': user_id,
                        'success': False,
                        'message': f"检查失败: {str(e)}",
                        'data': None
                    })
            
            return ServiceResult.success(
                data={
                    'total_checked': len(user_ids),
                    'success_upgrades': success_count,
                    'errors': error_count,
                    'results': upgrade_results
                },
                message=f"批量检查完成，共检查{len(user_ids)}个用户，成功升级{success_count}个"
            )
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR,
                f"批量检查VIP升级失败: {str(e)}"
            )
