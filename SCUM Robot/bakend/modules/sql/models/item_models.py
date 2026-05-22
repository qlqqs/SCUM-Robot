"""
物品类目相关数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base, TimestampMixin


class Category(Base, TimestampMixin):
    """物品类目表"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='类目ID')
    name = Column(String(100), nullable=False, unique=True, comment='类目名称')
    description = Column(Text, comment='类目描述')
    sort_order = Column(Integer, default=0, comment='排序顺序，数值越小越靠前')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    subcategories = relationship("SubCategory", back_populates="category", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class SubCategory(Base, TimestampMixin):
    """子物品类目表"""
    __tablename__ = 'subcategories'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='子类目ID')
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False, comment='父类目ID')
    name = Column(String(100), nullable=False, comment='子类目名称')
    description = Column(Text, comment='子类目描述')
    sort_order = Column(Integer, default=0, comment='排序顺序，数值越小越靠前')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    category = relationship("Category", back_populates="subcategories")
    items = relationship("Item", back_populates="subcategory")
    
    def __repr__(self):
        return f"<SubCategory(id={self.id}, name='{self.name}', category_id={self.category_id})>"


class Item(Base, TimestampMixin):
    """物品表"""
    __tablename__ = 'items'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='物品ID')
    name = Column(String(200), nullable=False, comment='物品名称')
    item_code = Column(String(2000), nullable=False, unique=True, comment='物品代码，支持JSON格式')
    image_url = Column(String(500), comment='物品图片URL')
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False, comment='类目ID')
    subcategory_id = Column(Integer, ForeignKey('subcategories.id'), comment='子类目ID')
    price = Column(Float(precision=2), default=0.0, comment='价格')
    stock = Column(Integer, default=0, comment='库存数量')
    description = Column(Text, comment='物品描述')
    sort_order = Column(Integer, default=0, comment='排序顺序，数值越小越靠前')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    category = relationship("Category", back_populates="items")
    subcategory = relationship("SubCategory", back_populates="items")
    
    def __repr__(self):
        return f"<Item(id={self.id}, code='{self.item_code}', name='{self.name}', price={self.price}, stock={self.stock})>"
    
    def is_in_stock(self) -> bool:
        """检查是否有库存"""
        # -1表示无限库存，大于0表示有库存
        return bool(self.stock and (self.stock == -1 or self.stock > 0))
    
    def update_stock(self, quantity: int) -> bool:
        """更新库存
        Args:
            quantity: 库存变化量（正数增加，负数减少）
        Returns:
            bool: 更新是否成功
        """
        current_stock = getattr(self, 'stock', 0) or 0

        # 如果当前是无限库存(-1)，且要减少库存，则保持无限库存
        if current_stock == -1 and quantity < 0:
            return True

        new_stock = current_stock + quantity
        # 允许库存为-1（无限库存），但不能小于-1
        if new_stock < -1:
            return False
        self.stock = new_stock
        self.update_timestamp()
        return True