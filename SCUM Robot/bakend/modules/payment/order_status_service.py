"""
订单状态管理服务

负责订单状态的检查、更新和维护
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from ..sql.models.payment_order_models import PaymentOrder, PaymentOrderStatus
from ..sql.database.manager import DatabaseManager


class OrderStatusService:
    """订单状态管理服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def check_and_update_order_status(self, order: PaymentOrder, session: Session) -> bool:
        """
        检查并更新单个订单的状态
        
        Args:
            order: 订单对象
            session: 数据库会话
            
        Returns:
            bool: 是否更新了状态
        """
        # 只处理待支付和处理中的订单
        if order.status not in [PaymentOrderStatus.PENDING.value, PaymentOrderStatus.PROCESSING.value]:
            return False
        
        # 检查是否过期
        if order.expired_at and datetime.now() > order.expired_at:
            order.status = PaymentOrderStatus.EXPIRED.value
            order.update_timestamp()
            session.commit()
            return True
        
        return False
    
    def batch_update_expired_orders(self, limit: int = 100) -> int:
        """
        批量更新过期订单
        
        Args:
            limit: 每次处理的最大订单数
            
        Returns:
            int: 更新的订单数量
        """
        updated_count = 0
        
        with self.db_manager.get_db_session() as session:
            # 查询所有待支付和处理中的订单
            orders = session.query(PaymentOrder).filter(
                PaymentOrder.status.in_([
                    PaymentOrderStatus.PENDING.value,
                    PaymentOrderStatus.PROCESSING.value
                ]),
                PaymentOrder.expired_at.isnot(None),
                PaymentOrder.expired_at < datetime.now()
            ).limit(limit).all()
            
            for order in orders:
                order.status = PaymentOrderStatus.EXPIRED.value
                order.update_timestamp()
                updated_count += 1
            
            if updated_count > 0:
                session.commit()
        
        return updated_count
    
    def get_order_with_status_check(self, order_id: str) -> Optional[PaymentOrder]:
        """
        获取订单并检查状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            PaymentOrder: 订单对象（如果存在）
        """
        with self.db_manager.get_db_session() as session:
            order = session.query(PaymentOrder).filter(
                PaymentOrder.order_id == order_id
            ).first()
            
            if order:
                # 检查并更新状态
                self.check_and_update_order_status(order, session)
                # 刷新对象以获取最新状态
                session.refresh(order)
            
            return order
    
    def get_orders_with_status_check(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[PaymentOrder]:
        """
        获取订单列表并检查状态
        
        Args:
            user_id: 用户ID（可选）
            status: 订单状态（可选）
            limit: 最大返回数量
            
        Returns:
            List[PaymentOrder]: 订单列表
        """
        with self.db_manager.get_db_session() as session:
            query = session.query(PaymentOrder)
            
            if user_id is not None:
                query = query.filter(PaymentOrder.user_id == user_id)
            
            if status:
                query = query.filter(PaymentOrder.status == status)
            
            orders = query.order_by(PaymentOrder.created_at.desc()).limit(limit).all()
            
            # 检查并更新每个订单的状态
            for order in orders:
                self.check_and_update_order_status(order, session)
            
            # 刷新所有订单对象
            for order in orders:
                session.refresh(order)
            
            return orders
    
    def cancel_order(self, order_id: str, reason: str = "用户取消") -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            reason: 取消原因
            
        Returns:
            bool: 是否成功取消
        """
        with self.db_manager.get_db_session() as session:
            order = session.query(PaymentOrder).filter(
                PaymentOrder.order_id == order_id
            ).first()
            
            if not order:
                return False
            
            # 只能取消待支付和处理中的订单
            if order.status not in [PaymentOrderStatus.PENDING.value, PaymentOrderStatus.PROCESSING.value]:
                return False
            
            order.status = PaymentOrderStatus.CANCELLED.value
            order.update_timestamp()
            
            # 可以在这里记录取消原因到日志
            
            session.commit()
            return True
    
    def get_order_statistics(self, user_id: Optional[int] = None) -> dict:
        """
        获取订单统计信息
        
        Args:
            user_id: 用户ID（可选，不传则统计所有用户）
            
        Returns:
            dict: 统计信息
        """
        with self.db_manager.get_db_session() as session:
            query = session.query(PaymentOrder)
            
            if user_id is not None:
                query = query.filter(PaymentOrder.user_id == user_id)
            
            # 总订单数
            total_orders = query.count()
            
            # 各状态订单数
            pending_count = query.filter(PaymentOrder.status == PaymentOrderStatus.PENDING.value).count()
            processing_count = query.filter(PaymentOrder.status == PaymentOrderStatus.PROCESSING.value).count()
            success_count = query.filter(PaymentOrder.status == PaymentOrderStatus.SUCCESS.value).count()
            failed_count = query.filter(PaymentOrder.status == PaymentOrderStatus.FAILED.value).count()
            cancelled_count = query.filter(PaymentOrder.status == PaymentOrderStatus.CANCELLED.value).count()
            expired_count = query.filter(PaymentOrder.status == PaymentOrderStatus.EXPIRED.value).count()
            
            # 成功订单的总金额
            success_orders = query.filter(PaymentOrder.status == PaymentOrderStatus.SUCCESS.value).all()
            total_amount = sum(float(order.amount) for order in success_orders)
            total_coins = sum(order.coins_added for order in success_orders)
            
            return {
                'total_orders': total_orders,
                'pending_count': pending_count,
                'processing_count': processing_count,
                'success_count': success_count,
                'failed_count': failed_count,
                'cancelled_count': cancelled_count,
                'expired_count': expired_count,
                'total_amount': total_amount,
                'total_coins': total_coins,
                'success_rate': (success_count / total_orders * 100) if total_orders > 0 else 0
            }
    
    def cleanup_old_orders(self, days: int = 30) -> int:
        """
        清理旧订单（将过期订单标记为已过期）
        
        Args:
            days: 保留天数
            
        Returns:
            int: 清理的订单数量
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        with self.db_manager.get_db_session() as session:
            # 查询旧的待支付订单
            old_orders = session.query(PaymentOrder).filter(
                PaymentOrder.status.in_([
                    PaymentOrderStatus.PENDING.value,
                    PaymentOrderStatus.PROCESSING.value
                ]),
                PaymentOrder.created_at < cutoff_date
            ).all()
            
            for order in old_orders:
                order.status = PaymentOrderStatus.EXPIRED.value
                order.update_timestamp()
                cleaned_count += 1
            
            if cleaned_count > 0:
                session.commit()
        
        return cleaned_count

