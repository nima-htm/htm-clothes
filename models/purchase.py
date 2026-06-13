"""
Purchase Invoice Models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("parties.id"), nullable=False)
    total_price = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    final_total = Column(Float, default=0.0)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    supplier = relationship("Party", back_populates="purchase_invoices")
    items = relationship("PurchaseInvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PurchaseInvoice(number='{self.invoice_number}', total={self.final_total})>"


class PurchaseInvoiceItem(Base):
    __tablename__ = "purchase_invoice_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("purchase_invoices.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Relationships
    invoice = relationship("PurchaseInvoice", back_populates="items")
    product = relationship("Product", back_populates="purchase_items")
    
    def __repr__(self):
        return f"<PurchaseInvoiceItem(product_id={self.product_id}, qty={self.quantity})>"
