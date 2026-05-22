"""
VIP等级系统服务层
"""

import json
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..models.user_models import User, VIPConfig
from .service_result import ServiceResult, ServiceError, ServiceErrorType


class VIPService:
    """VIP等级系统服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_vip_config(self, level: int) -> ServiceResult:
        """获取指定VIP等级配置"""
        try:
            vip_config = self.db.query(VIPConfig).filter(
                VIPConfig.level == level
            ).first()
            
            if not vip_config:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND, f"VIP{level}配置不存在"
                )

            return ServiceResult.success(
                data=vip_config.to_dict(),
                message="获取VIP配置成功"
            )

        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"数据库错误: {str(e)}"
            )
    
    def get_all_vip_configs(self) -> ServiceResult:
        """获取所有VIP配置"""
        try:
            vip_configs = self.db.query(VIPConfig).order_by(VIPConfig.level).all()
            
            configs_data = [config.to_dict() for config in vip_configs]
            
            return ServiceResult.success(data={
                'configs': configs_data,
                'total_count': len(configs_data)
            }, message="获取所有VIP配置成功")
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"数据库错误: {str(e)}"
            )
    
    def create_vip_config(self, config_data: Dict[str, Any]) -> ServiceResult:
        """创建VIP配置"""
        try:
            # 检查等级是否已存在
            existing_config = self.db.query(VIPConfig).filter(
                VIPConfig.level == config_data['level']
            ).first()
            
            if existing_config:
                return ServiceResult.error(
                    ServiceErrorType.ALREADY_EXISTS, f"VIP{config_data['level']}配置已存在"
                )
            
            # 创建新配置
            vip_config = VIPConfig(
                level=config_data['level'],
                name=config_data['name'],
                daily_gift_id=config_data.get('daily_gift_id'),
                level_gift_id=config_data.get('level_gift_id'),
                upgrade_required_points=config_data.get('upgrade_required_points', 0),
                enable_login_announcement=config_data.get('enable_login_announcement', False)
            )
            
            self.db.add(vip_config)
            self.db.commit()
            
            return ServiceResult.success(data=vip_config.to_dict(), message="创建VIP配置成功")
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"创建VIP配置失败: {str(e)}"
            )
    
    def update_vip_config(self, level: int, config_data: Dict[str, Any]) -> ServiceResult:
        """更新VIP配置"""
        try:
            vip_config = self.db.query(VIPConfig).filter(
                VIPConfig.level == level
            ).first()
            
            if not vip_config:
                return ServiceResult.error(ServiceErrorType.NOT_FOUND, f"VIP{level}配置不存在")
            
            # 更新配置
            if 'name' in config_data:
                vip_config.name = config_data['name']
            if 'daily_gift_id' in config_data:
                vip_config.daily_gift_id = config_data['daily_gift_id']
            if 'level_gift_id' in config_data:
                vip_config.level_gift_id = config_data['level_gift_id']
            if 'upgrade_required_points' in config_data:
                vip_config.upgrade_required_points = config_data['upgrade_required_points']
            if 'enable_login_announcement' in config_data:
                vip_config.enable_login_announcement = config_data['enable_login_announcement']
            
            vip_config.updated_at = datetime.utcnow()
            self.db.commit()
            
            return ServiceResult.success(data=vip_config.to_dict(), message="更新VIP配置成功")
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"更新VIP配置失败: {str(e)}"
            )
    
    def delete_vip_config(self, level: int) -> ServiceResult:
        """删除VIP配置"""
        try:
            # 保护VIP0配置，不允许删除
            if level == 0:
                return ServiceResult.error(ServiceErrorType.VALIDATION_ERROR, "VIP0配置不可删除")

            vip_config = self.db.query(VIPConfig).filter(
                VIPConfig.level == level
            ).first()

            if not vip_config:
                return ServiceResult.error(ServiceErrorType.NOT_FOUND, f"VIP{level}配置不存在")

            # 检查是否有用户使用此VIP等级
            users_count = self.db.query(User).filter(User.vip_level == level).count()
            if users_count > 0:
                return ServiceResult.error(ServiceErrorType.VALIDATION_ERROR, f"有{users_count}个用户正在使用VIP{level}，无法删除")
            
            self.db.delete(vip_config)
            self.db.commit()
            
            return ServiceResult.success(message="删除VIP配置成功")
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"删除VIP配置失败: {str(e)}"
            )
    
    def get_user_vip_status(self, user_id: int) -> ServiceResult:
        """获取用户VIP状态"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ServiceResult.error(ServiceErrorType.NOT_FOUND, "用户不存在")
            
            # 获取VIP配置
            vip_config = None
            if user.vip_level > 0:
                vip_config = self.db.query(VIPConfig).filter(
                    VIPConfig.level == user.vip_level
                ).first()
            
            # 检查VIP是否过期
            is_expired = False
            if user.vip_expire_date and user.vip_expire_date != date(9999, 12, 31):
                is_expired = user.vip_expire_date < date.today()
            
            vip_status = {
                'user_id': user_id,
                'vip_level': user.vip_level,
                'vip_name': vip_config.name if vip_config else "普通用户",
                'vip_expire_date': user.vip_expire_date.isoformat() if user.vip_expire_date else None,
                'is_permanent': user.vip_expire_date == date(9999, 12, 31),
                'is_expired': is_expired,
                'config': vip_config.to_dict() if vip_config else None
            }
            
            return ServiceResult.success(data=vip_status, message="获取用户VIP状态成功")
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"数据库错误: {str(e)}"
            )
    
    def upgrade_user_vip(self, user_id: int, new_level: int, expire_date: Optional[date] = None) -> ServiceResult:
        """升级用户VIP等级"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ServiceResult.error(ServiceErrorType.NOT_FOUND, "用户不存在")
            
            # 检查VIP配置是否存在
            if new_level > 0:
                vip_config = self.db.query(VIPConfig).filter(
                    VIPConfig.level == new_level
                ).first()
                
                if not vip_config:
                    return ServiceResult.error(ServiceErrorType.NOT_FOUND, f"VIP{new_level}配置不存在")
            
            # 更新用户VIP等级
            old_level = user.vip_level
            user.vip_level = new_level
            
            # 设置过期时间
            if expire_date:
                user.vip_expire_date = expire_date
            elif new_level > 0:
                # 默认永不过期
                user.vip_expire_date = date(9999, 12, 31)
            else:
                # 降级为普通用户
                user.vip_expire_date = None
            
            user.updated_at = datetime.utcnow()
            self.db.commit()
            
            upgrade_data = {
                'user_id': user_id,
                'old_level': old_level,
                'new_level': new_level,
                'expire_date': user.vip_expire_date.isoformat() if user.vip_expire_date else None,
                'is_permanent': user.vip_expire_date == date(9999, 12, 31) if user.vip_expire_date else False
            }
            
            return ServiceResult.success(data=upgrade_data, message="VIP升级成功")
            
        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"VIP升级失败: {str(e)}"
            )
    

    
    def get_vip_statistics(self, min_level: int = 2) -> ServiceResult:
        """获取VIP用户统计"""
        try:
            # 按VIP等级统计用户数量
            vip_stats = {}

            # 获取指定等级及以上的VIP配置
            vip_configs = self.db.query(VIPConfig).filter(
                VIPConfig.level >= min_level
            ).all()

            for config in vip_configs:
                user_count = self.db.query(User).filter(User.vip_level == config.level).count()
                vip_stats[f"vip_{config.level}"] = {
                    'level': config.level,
                    'name': config.name,
                    'user_count': user_count
                }

            # 普通用户统计（VIP0）
            normal_user_count = self.db.query(User).filter(User.vip_level == 0).count()
            vip_stats['vip_0'] = {
                'level': 0,
                'name': '普通用户',
                'user_count': normal_user_count
            }

            # VIP1用户统计（如果min_level <= 1）
            if min_level <= 1:
                vip1_config = self.db.query(VIPConfig).filter(VIPConfig.level == 1).first()
                vip1_count = self.db.query(User).filter(User.vip_level == 1).count()
                vip_stats['vip_1'] = {
                    'level': 1,
                    'name': vip1_config.name if vip1_config else 'VIP1',
                    'user_count': vip1_count
                }

            # 总用户数
            total_users = self.db.query(User).count()
            # 计算指定等级及以上的VIP用户数
            total_vip_users = sum(
                self.db.query(User).filter(User.vip_level == config.level).count()
                for config in vip_configs
            )
            
            statistics = {
                'total_users': total_users,
                'total_vip_users': total_vip_users,
                'normal_users': normal_user_count,
                'vip_distribution': vip_stats,
                'vip_ratio': round(total_vip_users / total_users * 100, 2) if total_users > 0 else 0
            }
            
            return ServiceResult.success(data=statistics, message="获取VIP统计成功")
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"获取VIP统计失败: {str(e)}"
            )
    
    def batch_update_vip(self, updates: List[Dict[str, Any]]) -> ServiceResult:
        """批量更新用户VIP等级"""
        try:
            updated_users = []
            failed_updates = []
            
            for update_data in updates:
                try:
                    user_id = update_data['user_id']
                    new_level = update_data['new_level']
                    expire_date = update_data.get('expire_date')
                    
                    if expire_date and isinstance(expire_date, str):
                        expire_date = datetime.strptime(expire_date, '%Y-%m-%d').date()
                    
                    result = self.upgrade_user_vip(user_id, new_level, expire_date)
                    if result.success:
                        updated_users.append(result.data)
                    else:
                        failed_updates.append({
                            'user_id': user_id,
                            'error': result.error.message
                        })
                        
                except Exception as e:
                    failed_updates.append({
                        'user_id': update_data.get('user_id', 'unknown'),
                        'error': str(e)
                    })
            
            batch_result = {
                'updated_count': len(updated_users),
                'failed_count': len(failed_updates),
                'updated_users': updated_users,
                'failed_updates': failed_updates
            }
            
            return ServiceResult.success(data=batch_result, message="批量更新VIP完成")
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"批量更新VIP失败: {str(e)}"
            )
