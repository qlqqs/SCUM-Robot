"""
人物能力系统服务层
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.user_models import User, UserCharacterStats
from .service_result import ServiceResult, ServiceError, ServiceErrorType


class CharacterService:
    """人物能力系统服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_character_stats(self, user_id: int) -> ServiceResult:
        """获取用户人物能力"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND, "用户不存在"
                )
            
            character_stats = self.db.query(UserCharacterStats).filter(
                UserCharacterStats.user_id == user_id
            ).first()
            
            if not character_stats:
                # 创建默认人物能力数据
                character_stats = UserCharacterStats(
                    user_id=user_id,
                    steam_id=user.steam_id,
                    strength=10,
                    stamina=10,
                    intelligence=10,
                    agility=10
                )
                self.db.add(character_stats)
                self.db.commit()
            
            return ServiceResult.success(
                data=character_stats.to_dict(),
                message="获取人物能力成功"
            )
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"数据库错误: {str(e)}"
            )
    
    def get_character_stats_by_steam_id(self, steam_id: int) -> ServiceResult:
        """通过Steam ID获取人物能力"""
        try:
            character_stats = self.db.query(UserCharacterStats).filter(
                UserCharacterStats.steam_id == steam_id
            ).first()
            
            if not character_stats:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND, "未找到该Steam ID的人物能力数据"
                )

            return ServiceResult.success(
                data=character_stats.to_dict(),
                message="获取人物能力成功"
            )
            
        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"数据库错误: {str(e)}"
            )
    
    def update_character_stats(self, user_id: int, strength: Optional[int] = None, 
                             stamina: Optional[int] = None, intelligence: Optional[int] = None, 
                             agility: Optional[int] = None) -> ServiceResult:
        """更新用户人物能力（管理员功能）"""
        try:
            character_stats = self.db.query(UserCharacterStats).filter(
                UserCharacterStats.user_id == user_id
            ).first()
            
            if not character_stats:
                # 获取用户信息创建默认数据
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user:
                    return ServiceResult.error(
                        ServiceErrorType.NOT_FOUND, "用户不存在"
                    )
                
                character_stats = UserCharacterStats(
                    user_id=user_id,
                    steam_id=user.steam_id
                )
                self.db.add(character_stats)
                self.db.flush()
            
            # 验证能力值范围
            stats_to_update = {}
            if strength is not None:
                if not (1 <= strength <= 100):
                    return ServiceResult.error(
                        ServiceErrorType.VALIDATION_ERROR, "力量值必须在1-100之间"
                    )
                stats_to_update['strength'] = strength
            
            if stamina is not None:
                if not (1 <= stamina <= 100):
                    return ServiceResult.error(
                        ServiceErrorType.VALIDATION_ERROR, "体力值必须在1-100之间"
                    )
                stats_to_update['stamina'] = stamina
            
            if intelligence is not None:
                if not (1 <= intelligence <= 100):
                    return ServiceResult.error(
                        ServiceErrorType.VALIDATION_ERROR, "智力值必须在1-100之间"
                    )
                stats_to_update['intelligence'] = intelligence
            
            if agility is not None:
                if not (1 <= agility <= 100):
                    return ServiceResult.error(
                        ServiceErrorType.VALIDATION_ERROR, "敏捷值必须在1-100之间"
                    )
                stats_to_update['agility'] = agility
            
            # 更新能力值
            for stat_name, stat_value in stats_to_update.items():
                setattr(character_stats, stat_name, stat_value)
            
            character_stats.updated_at = datetime.utcnow()
            self.db.commit()
            
            return ServiceResult.success(
                data=character_stats.to_dict(),
                message="更新人物能力成功"
            )

        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"更新人物能力失败: {str(e)}"
            )
    
    def sync_character_stats_from_game(self, steam_id: int, game_stats: Dict[str, int]) -> ServiceResult:
        """从游戏同步人物能力数据"""
        try:
            character_stats = self.db.query(UserCharacterStats).filter(
                UserCharacterStats.steam_id == steam_id
            ).first()
            
            if not character_stats:
                # 通过Steam ID查找用户
                user = self.db.query(User).filter(User.steam_id == steam_id).first()
                if not user:
                    return ServiceResult.error(
                        ServiceErrorType.NOT_FOUND, "未找到对应的用户"
                    )
                
                character_stats = UserCharacterStats(
                    user_id=user.id,
                    steam_id=steam_id
                )
                self.db.add(character_stats)
                self.db.flush()
            
            # 验证并更新游戏数据
            if 'strength' in game_stats:
                character_stats.strength = max(1, min(100, game_stats['strength']))
            if 'stamina' in game_stats:
                character_stats.stamina = max(1, min(100, game_stats['stamina']))
            if 'intelligence' in game_stats:
                character_stats.intelligence = max(1, min(100, game_stats['intelligence']))
            if 'agility' in game_stats:
                character_stats.agility = max(1, min(100, game_stats['agility']))
            
            character_stats.last_sync_time = datetime.utcnow()
            character_stats.updated_at = datetime.utcnow()
            self.db.commit()
            
            return ServiceResult.success(
                data=character_stats.to_dict(),
                message="同步人物能力成功"
            )

        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"同步人物能力失败: {str(e)}"
            )
    
    def reset_character_stats(self, user_id: int) -> ServiceResult:
        """重置用户人物能力为默认值"""
        try:
            character_stats = self.db.query(UserCharacterStats).filter(
                UserCharacterStats.user_id == user_id
            ).first()
            
            if not character_stats:
                return ServiceResult.error(
                    ServiceErrorType.NOT_FOUND, "未找到人物能力数据"
                )
            
            # 重置为默认值
            character_stats.strength = 10
            character_stats.stamina = 10
            character_stats.intelligence = 10
            character_stats.agility = 10
            character_stats.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return ServiceResult.success(
                data=character_stats.to_dict(),
                message="重置人物能力成功"
            )

        except Exception as e:
            self.db.rollback()
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"重置人物能力失败: {str(e)}"
            )
    
    def get_character_stats_list(self, limit: int = 50, offset: int = 0, 
                               order_by: str = "total_stats") -> ServiceResult:
        """获取人物能力列表（排行榜）"""
        try:
            # 构建查询
            query = self.db.query(UserCharacterStats, User).join(
                User, UserCharacterStats.user_id == User.id
            )
            
            # 排序
            if order_by == "strength":
                query = query.order_by(desc(UserCharacterStats.strength))
            elif order_by == "stamina":
                query = query.order_by(desc(UserCharacterStats.stamina))
            elif order_by == "intelligence":
                query = query.order_by(desc(UserCharacterStats.intelligence))
            elif order_by == "agility":
                query = query.order_by(desc(UserCharacterStats.agility))
            else:  # total_stats
                # 按总能力值排序
                query = query.order_by(desc(
                    UserCharacterStats.strength + 
                    UserCharacterStats.stamina + 
                    UserCharacterStats.intelligence + 
                    UserCharacterStats.agility
                ))
            
            # 分页
            results = query.offset(offset).limit(limit).all()
            
            # 构建返回数据
            stats_list = []
            for character_stats, user in results:
                stats_data = character_stats.to_dict()
                stats_data['username'] = user.username
                stats_data['vip_level'] = user.vip_level
                stats_list.append(stats_data)
            
            # 获取总数
            total_count = self.db.query(UserCharacterStats).count()
            
            result_data = {
                'stats_list': stats_list,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'order_by': order_by
            }
            
            return ServiceResult.success(
                data=result_data,
                message="获取人物能力列表成功"
            )

        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"获取人物能力列表失败: {str(e)}"
            )
    
    def batch_update_character_stats(self, updates: List[Dict[str, Any]]) -> ServiceResult:
        """批量更新人物能力"""
        try:
            updated_stats = []
            failed_updates = []
            
            for update_data in updates:
                try:
                    user_id = update_data['user_id']
                    strength = update_data.get('strength')
                    stamina = update_data.get('stamina')
                    intelligence = update_data.get('intelligence')
                    agility = update_data.get('agility')
                    
                    result = self.update_character_stats(user_id, strength, stamina, intelligence, agility)
                    if result.success:
                        updated_stats.append(result.data)
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
                'updated_count': len(updated_stats),
                'failed_count': len(failed_updates),
                'updated_stats': updated_stats,
                'failed_updates': failed_updates
            }
            
            return ServiceResult.success(
                data=batch_result,
                message="批量更新人物能力完成"
            )

        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"批量更新人物能力失败: {str(e)}"
            )
    
    def get_character_stats_summary(self) -> ServiceResult:
        """获取人物能力统计摘要"""
        try:
            # 总用户数
            total_users = self.db.query(UserCharacterStats).count()
            
            if total_users == 0:
                return ServiceResult.success(data={
                    'total_users': 0,
                    'average_stats': {},
                    'max_stats': {},
                    'min_stats': {}
                }, message="获取人物能力统计成功")
            
            # 计算平均值、最大值、最小值
            from sqlalchemy import func
            
            stats_summary = self.db.query(
                func.avg(UserCharacterStats.strength).label('avg_strength'),
                func.avg(UserCharacterStats.stamina).label('avg_stamina'),
                func.avg(UserCharacterStats.intelligence).label('avg_intelligence'),
                func.avg(UserCharacterStats.agility).label('avg_agility'),
                func.max(UserCharacterStats.strength).label('max_strength'),
                func.max(UserCharacterStats.stamina).label('max_stamina'),
                func.max(UserCharacterStats.intelligence).label('max_intelligence'),
                func.max(UserCharacterStats.agility).label('max_agility'),
                func.min(UserCharacterStats.strength).label('min_strength'),
                func.min(UserCharacterStats.stamina).label('min_stamina'),
                func.min(UserCharacterStats.intelligence).label('min_intelligence'),
                func.min(UserCharacterStats.agility).label('min_agility')
            ).first()
            
            summary_data = {
                'total_users': total_users,
                'average_stats': {
                    'strength': round(stats_summary.avg_strength, 2),
                    'stamina': round(stats_summary.avg_stamina, 2),
                    'intelligence': round(stats_summary.avg_intelligence, 2),
                    'agility': round(stats_summary.avg_agility, 2)
                },
                'max_stats': {
                    'strength': stats_summary.max_strength,
                    'stamina': stats_summary.max_stamina,
                    'intelligence': stats_summary.max_intelligence,
                    'agility': stats_summary.max_agility
                },
                'min_stats': {
                    'strength': stats_summary.min_strength,
                    'stamina': stats_summary.min_stamina,
                    'intelligence': stats_summary.min_intelligence,
                    'agility': stats_summary.min_agility
                }
            }
            
            return ServiceResult.success(
                data=summary_data,
                message="获取人物能力统计成功"
            )

        except Exception as e:
            return ServiceResult.error(
                ServiceErrorType.DATABASE_ERROR, f"获取人物能力统计失败: {str(e)}"
            )
