"""
Party Model (Customers and Suppliers)
"""

from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from models.base import Base


class PartyType(enum.Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    BOTH = "both"


class Party(Base):
    __tablename__ = "parties"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    party_type = Column(SQLEnum(PartyType), default=PartyType.CUSTOMER)
    address = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sales_invoices = relationship("SalesInvoice", back_populates="customer")
    purchase_invoices = relationship("PurchaseInvoice", back_populates="supplier")
    
    def __repr__(self):
        return f"<Party(name='{self.name}', type='{self.party_type.value}')>"
