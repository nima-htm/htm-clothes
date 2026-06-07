"""
Inventory Transaction Model
Tracks all stock movements for accurate inventory management
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from models.base import Base


class TransactionType(enum.Enum):
    PURCHASE = "purchase"  # Stock increase from purchase
    SALE = "sale"  # Stock decrease from sale
    ADJUSTMENT = "adjustment"  # Manual adjustment
    RETURN = "return"  # Return from customer


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)  # Positive for increase, negative for decrease
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    reference_type = Column(String(50), nullable=True)  # e.g., "sales_invoice", "purchase_invoice"
    reference_id = Column(Integer, nullable=True)  # ID of the referencing document
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_transactions")
    
    def __repr__(self):
        return f"<InventoryTransaction(product_id={self.product_id}, qty={self.quantity}, type={self.transaction_type.value})>"
