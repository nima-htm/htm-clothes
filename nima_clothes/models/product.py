"""
Product Model
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from models.base import Base


class ProductCategory(enum.Enum):
    FABRIC = "fabric"
    PANTS = "pants"


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    category = Column(SQLEnum(ProductCategory), nullable=False)
    sub_category = Column(String(100), nullable=True)  # e.g., jeans, formal, cotton, linen
    buy_price = Column(Float, default=0.0)
    sell_price = Column(Float, default=0.0)
    stock_quantity = Column(Integer, default=0)
    unit = Column(String(50), default="عدد")  # Unit of measurement
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sales_items = relationship("SalesInvoiceItem", back_populates="product")
    purchase_items = relationship("PurchaseInvoiceItem", back_populates="product")
    inventory_transactions = relationship("InventoryTransaction", back_populates="product")
    
    def __repr__(self):
        return f"<Product(code='{self.code}', name='{self.name}', stock={self.stock_quantity})>"
    
    def get_current_stock(self, session):
        """Calculate current stock from inventory transactions"""
        from sqlalchemy import func
        result = session.query(
            func.sum(InventoryTransaction.qty)
        ).filter(
            InventoryTransaction.product_id == self.id
        ).scalar()
        return result if result else 0
