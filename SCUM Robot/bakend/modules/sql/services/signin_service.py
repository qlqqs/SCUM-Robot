"""
签到系统服务层
"""

import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import pytz

from ..models.user_models import User, VIPConfig
from ..models import UserAssets
from .service_result import ServiceResult, ServiceError, ServiceErrorType


class SigninService:
    """签到系统服务"""
    
    def __init__(self, db: Session):
        self.db = db
        # 北京时区
        self.beijing_tz = pytz.timezone('Asia/Shanghai')
    
    def get_beijing_date(self) -> date:
        """获取北京时间的日期"""
        beijing_now = datetime.now(self.beijing_tz)
        return beijing_now.date()
    
    def get_beijing_datetime(self) -> datetime:
        """获取北京时间"""
        return datetime.now(self.beijing_tz)
    
    def check_signin_status(self, user_id: int) -> ServiceResult:
        """检查用户签到状态"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ServiceResult.error(
                    ServiceError(ServiceErrorType.NOT_FOUND, "用户不存在")
                )
            
            today = self.get_beijing_date()
            can_signin = not user.today_signed_in or user.last_signin_date != today
            
            # 检查连续签到是否中断
            if user.last_signin_date and user.last_signin_date < today - timedelta(days=1):
                # 连续签到中断，但不在这里重置，在签到时重置
                pass
            
            status_data = {
                'user_id': user_id,
                'today_signed': user.today_signed_in and user.last_signin_date == today,
                'consecutive_days': user.consecutive_signin_days,
                'total_days': user.total_signin_days,
                'last_signin_date': user.last_signin_date.isoformat() if user.last_signin_date else None,
                'pass_level': user.pass_level,
                'pass_exp': user.pass_exp,
                'vip_level': user.vip_level,
                'can_signin': can_signin,
                'beijing_date': today.isoformat()
            }
            
            return ServiceResult.success("获取签到状态成功", status_data)
            
        except Exception as e:
            return ServiceResult.error(
                ServiceError(ServiceErrorType.DATABASE_ERROR, f"数据库错误: {str(e)}")
            )
    
    def daily_signin(self, user_id: int) -> ServiceResult:
        """执行每日签到"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ServiceResult.error(
                    ServiceError(ServiceErrorType.NOT_FOUND, "用户不存在")
                )
            
            today = self.get_beijing_date()
            
            # 检查今日是否已签到
            if user.today_signed_in and user.last_signin_date == today:
                return ServiceResult.error(
                    ServiceError(ServiceErrorType.BUSINESS_ERROR, "今日已签到")
                )
            
            # 检查连续签到
            if user.last_signin_date:
                if user.last_signin_date == today - timedelta(days=1):
                    # 连续签到
                    user.consecutive_signin_days += 1
                elif user.last_signin_date < today - timedelta(days=1):
                    # 连续签到中断
                    user.consecutive_signin_days = 1
                else:
                    # 同一天重复签到（理论上不会到这里）
                    return ServiceResult.error(
                        ServiceError(ServiceErrorType.BUSINESS_ERROR, "今日已签到")
                    )
            else:
                # 首次签到
                user.consecutive_signin_days = 1
            
            # 更新签到信息
            user.today_signed_in = True
            user.total_signin_days += 1
            user.last_signin_date = today
            
            # 获取VIP配置
            vip_config = self.db.query(VIPConfig).filter(
                VIPConfig.level == user.vip_level,
                VIPConfig.is_active == True
            ).first()
            
            # 计算签到奖励
            rewards = self._calculate_signin_rewards(user, vip_config)
            
            # 发放奖励
            self._grant_signin_rewards(user_id, rewards)
            
            # 计算通行证经验和等级
            pass_exp_gained = self._calculate_pass_exp(user, vip_config)
            user.pass_exp += pass_exp_gained
            
            # 检查通行证升级
            level_up = self._check_pass_level_up(user)
            
            # 重置今日签到标志（为明天准备）
            # 注意：这里不重置，在新的一天检查时重置
            
            self.db.commit()
            
            signin_data = {
                'user_id': user_id,
                'signin_date': today.isoformat(),
                'consecutive_days': user.consecutive_signin_days,
                'total_days': user.total_signin_days,
                'pass_level': user.pass_level,
                'pass_exp': user.pass_exp,
                'pass_exp_gained': pass_exp_gained,
                'level_up': level_up,
                'vip_level': user.vip_level,
                'rewards': rewards
            }
            
            return ServiceResult.success("签到成功", signin_data)
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceError(ServiceErrorType.DATABASE_ERROR, f"签到失败: {str(e)}")
            )
    
    def _calculate_signin_rewards(self, user: User, vip_config: Optional[VIPConfig]) -> Dict[str, Any]:
        """计算签到奖励"""
        # 基础奖励
        base_rewards = {
            'points': 10,
            'game_coins': 50
        }

        # VIP倍数加成 - 简化为基于VIP等级的固定倍数
        multiplier = 1.0
        if vip_config:
            # 根据VIP等级设置倍数
            if vip_config.level >= 3:
                multiplier = 2.0
            elif vip_config.level >= 2:
                multiplier = 1.5
            elif vip_config.level >= 1:
                multiplier = 1.2
        
        # 连续签到加成
        consecutive_bonus = {}
        if user.consecutive_signin_days >= 7:
            consecutive_bonus['points'] = 100
        if user.consecutive_signin_days >= 30:
            consecutive_bonus['game_coins'] = 1000
        
        # 里程碑奖励
        milestone_bonus = {}
        if user.total_signin_days in [10, 30, 100, 365]:
            milestone_bonus['shop_coins'] = user.total_signin_days * 10
        
        # 应用VIP倍数到基础奖励
        final_base_rewards = {
            key: int(value * multiplier) 
            for key, value in base_rewards.items()
        }
        
        return {
            'base_rewards': final_base_rewards,
            'consecutive_bonus': consecutive_bonus,
            'milestone_bonus': milestone_bonus,
            'vip_multiplier': multiplier
        }
    
    def _grant_signin_rewards(self, user_id: int, rewards: Dict[str, Any]):
        """发放签到奖励"""
        user_assets = self.db.query(UserAssets).filter(UserAssets.user_id == user_id).first()
        if not user_assets:
            # 创建用户资产记录
            user_assets = UserAssets(user_id=user_id)
            self.db.add(user_assets)
            self.db.flush()
        
        # 发放基础奖励
        base_rewards = rewards.get('base_rewards', {})
        user_assets.points += base_rewards.get('points', 0)
        user_assets.game_coins += base_rewards.get('game_coins', 0)
        user_assets.shop_coins += base_rewards.get('shop_coins', 0)
        
        # 发放连续奖励
        consecutive_bonus = rewards.get('consecutive_bonus', {})
        user_assets.points += consecutive_bonus.get('points', 0)
        user_assets.game_coins += consecutive_bonus.get('game_coins', 0)
        user_assets.shop_coins += consecutive_bonus.get('shop_coins', 0)
        
        # 发放里程碑奖励
        milestone_bonus = rewards.get('milestone_bonus', {})
        user_assets.points += milestone_bonus.get('points', 0)
        user_assets.game_coins += milestone_bonus.get('game_coins', 0)
        user_assets.shop_coins += milestone_bonus.get('shop_coins', 0)
    
    def _calculate_pass_exp(self, user: User, vip_config: Optional[VIPConfig]) -> int:
        """计算通行证经验"""
        base_exp = 10  # 基础经验

        # VIP加成 - 简化为基于VIP等级的固定倍数
        if vip_config:
            if vip_config.level >= 3:
                base_exp = int(base_exp * 2.0)
            elif vip_config.level >= 2:
                base_exp = int(base_exp * 1.5)
            elif vip_config.level >= 1:
                base_exp = int(base_exp * 1.2)
        
        # 连续签到加成
        if user.consecutive_signin_days >= 7:
            base_exp += 5
        if user.consecutive_signin_days >= 30:
            base_exp += 10
        
        return base_exp
    
    def _check_pass_level_up(self, user: User) -> bool:
        """检查通行证是否升级"""
        # 简单的升级逻辑：每100经验升1级
        required_exp_per_level = 100
        new_level = user.pass_exp // required_exp_per_level
        
        if new_level > user.pass_level:
            user.pass_level = new_level
            return True
        
        return False
    
    def get_signin_history(self, user_id: int, limit: int = 30) -> ServiceResult:
        """获取签到历史"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ServiceResult.error(
                    ServiceError(ServiceErrorType.NOT_FOUND, "用户不存在")
                )
            
            # 这里简化处理，实际可能需要单独的签到历史表
            history_data = {
                'user_id': user_id,
                'total_signin_days': user.total_signin_days,
                'consecutive_signin_days': user.consecutive_signin_days,
                'last_signin_date': user.last_signin_date.isoformat() if user.last_signin_date else None,
                'pass_level': user.pass_level,
                'pass_exp': user.pass_exp
            }
            
            return ServiceResult.success("获取签到历史成功", history_data)
            
        except Exception as e:
            return ServiceResult.error(
                ServiceError(ServiceErrorType.DATABASE_ERROR, f"数据库错误: {str(e)}")
            )
    
    def get_signin_rewards_config(self) -> ServiceResult:
        """获取签到奖励配置"""
        try:
            # 获取所有VIP配置
            vip_configs = self.db.query(VIPConfig).order_by(VIPConfig.level).all()
            
            rewards_config = {
                'base_rewards': {
                    'points': 10,
                    'game_coins': 50
                },
                'consecutive_rewards': {
                    7: {'points': 100},
                    30: {'game_coins': 1000}
                },
                'milestone_rewards': {
                    10: {'shop_coins': 100},
                    30: {'shop_coins': 300},
                    100: {'shop_coins': 1000},
                    365: {'shop_coins': 3650}
                },
                'vip_configs': [config.to_dict() for config in vip_configs]
            }
            
            return ServiceResult.success("获取签到奖励配置成功", rewards_config)
            
        except Exception as e:
            return ServiceResult.error(
                ServiceError(ServiceErrorType.DATABASE_ERROR, f"数据库错误: {str(e)}")
            )
    
    def get_signin_leaderboard(self, leaderboard_type: str = "total", limit: int = 50) -> ServiceResult:
        """获取签到排行榜"""
        try:
            if leaderboard_type == "total":
                # 累计签到排行榜
                users = self.db.query(User).filter(
                    User.total_signin_days > 0
                ).order_by(User.total_signin_days.desc()).limit(limit).all()
                
                leaderboard = []
                for i, user in enumerate(users, 1):
                    leaderboard.append({
                        'rank': i,
                        'user_id': user.id,
                        'username': user.username,
                        'total_days': user.total_signin_days,
                        'consecutive_days': user.consecutive_signin_days,
                        'vip_level': user.vip_level
                    })
                    
            elif leaderboard_type == "consecutive":
                # 连续签到排行榜
                users = self.db.query(User).filter(
                    User.consecutive_signin_days > 0
                ).order_by(User.consecutive_signin_days.desc()).limit(limit).all()
                
                leaderboard = []
                for i, user in enumerate(users, 1):
                    leaderboard.append({
                        'rank': i,
                        'user_id': user.id,
                        'username': user.username,
                        'consecutive_days': user.consecutive_signin_days,
                        'total_days': user.total_signin_days,
                        'vip_level': user.vip_level
                    })
            else:
                return ServiceResult.error(
                    ServiceError(ServiceErrorType.VALIDATION_ERROR, "无效的排行榜类型")
                )
            
            result_data = {
                'type': leaderboard_type,
                'leaderboard': leaderboard,
                'total_count': len(leaderboard)
            }
            
            return ServiceResult.success("获取签到排行榜成功", result_data)
            
        except Exception as e:
            return ServiceResult.error(
                ServiceError(ServiceErrorType.DATABASE_ERROR, f"数据库错误: {str(e)}")
            )
    
    def reset_daily_signin_flags(self) -> ServiceResult:
        """重置所有用户的今日签到标志（定时任务用）"""
        try:
            today = self.get_beijing_date()
            
            # 重置所有不是今天签到的用户的今日签到标志
            self.db.query(User).filter(
                User.last_signin_date < today
            ).update({
                User.today_signed_in: False
            })
            
            self.db.commit()
            
            return ServiceResult.success("重置今日签到标志成功")
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceError(ServiceErrorType.DATABASE_ERROR, f"重置失败: {str(e)}")
            )
