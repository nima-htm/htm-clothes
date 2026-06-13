"""
Product Model - Enhanced for Clothing Inventory
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from models.base import Base


class ProductCategory(enum.Enum):
    FABRIC = "پارچه"
    PANTS = "شلوار"
    JACKET = "کاپشن"


class ProductUnit(enum.Enum):
    METER = "متر"
    PIECE = "عدد"


class StockSourceType(enum.Enum):
    PRODUCTION = "تولید"
    PURCHASE = "خرید"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numeric_code = Column(String(20), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    category = Column(SQLEnum(ProductCategory), nullable=False)
    unit = Column(SQLEnum(ProductUnit), nullable=False)
    initial_stock = Column(Float, default=0, nullable=False)
    stock_quantity = Column(Float, default=0, nullable=False)
    default_price = Column(Float, default=0, nullable=False)
    stock_source = Column(SQLEnum(StockSourceType), nullable=False, default=StockSourceType.PURCHASE)

    created_at = Column(DateTime, default=datetime.utcnow)

    sales_items = relationship("SalesInvoiceItem", back_populates="product")
    purchase_items = relationship("PurchaseInvoiceItem", back_populates="product")

    def __repr__(self):
        return f"<Product(code='{self.numeric_code}', name='{self.name}', stock={self.stock_quantity} {self.unit.value})>"