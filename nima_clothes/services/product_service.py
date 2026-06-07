"""
Product Service
Handles all product-related business logic
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.product import Product, ProductCategory
from models.inventory import InventoryTransaction, TransactionType
from datetime import datetime


class ProductService:
    def __init__(self, session: Session):
        self.session = session
    
    def create_product(self, code: str, name: str, category: ProductCategory,
                      sub_category: str = None, buy_price: float = 0.0,
                      sell_price: float = 0.0, unit: str = "عدد") -> Product:
        """Create a new product"""
        # Check if code already exists
        existing = self.session.query(Product).filter(Product.code == code).first()
        if existing:
            raise ValueError(f"Product code '{code}' already exists")
        
        product = Product(
            code=code,
            name=name,
            category=category,
            sub_category=sub_category,
            buy_price=buy_price,
            sell_price=sell_price,
            unit=unit
        )
        
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product
    
    def get_product_by_id(self, product_id: int) -> Product:
        """Get product by ID"""
        return self.session.query(Product).filter(Product.id == product_id).first()
    
    def get_product_by_code(self, code: str) -> Product:
        """Get product by code"""
        return self.session.query(Product).filter(Product.code == code).first()
    
    def search_products(self, query: str = None, category: ProductCategory = None):
        """Search products by name, code, or category"""
        db_query = self.session.query(Product)
        
        if query:
            db_query = db_query.filter(
                or_(
                    Product.name.contains(query),
                    Product.code.contains(query),
                    Product.sub_category.contains(query)
                )
            )
        
        if category:
            db_query = db_query.filter(Product.category == category)
        
        return db_query.all()
    
    def get_all_products(self):
        """Get all products"""
        return self.session.query(Product).all()
    
    def update_product(self, product_id: int, **kwargs) -> Product:
        """Update product information"""
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, value)
        
        self.session.commit()
        self.session.refresh(product)
        return product
    
    def delete_product(self, product_id: int):
        """Delete a product"""
        product = self.get_product_by_id(product_id)
        if product:
            self.session.delete(product)
            self.session.commit()
    
    def get_current_stock(self, product_id: int) -> int:
        """Calculate current stock from inventory transactions"""
        result = self.session.query(
            func.sum(InventoryTransaction.quantity)
        ).filter(
            InventoryTransaction.product_id == product_id
        ).scalar()
        return result if result else 0
    
    def add_stock(self, product_id: int, quantity: int, reference_type: str = None,
                  reference_id: int = None, notes: str = None):
        """Add stock (positive transaction)"""
        transaction = InventoryTransaction(
            product_id=product_id,
            quantity=quantity,
            transaction_type=TransactionType.PURCHASE,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes
        )
        self.session.add(transaction)
        self.session.commit()
    
    def remove_stock(self, product_id: int, quantity: int, reference_type: str = None,
                     reference_id: int = None, notes: str = None):
        """Remove stock (negative transaction)"""
        current_stock = self.get_current_stock(product_id)
        if current_stock < quantity:
            raise ValueError(f"Insufficient stock. Available: {current_stock}, Requested: {quantity}")
        
        transaction = InventoryTransaction(
            product_id=product_id,
            quantity=-quantity,  # Negative for removal
            transaction_type=TransactionType.SALE,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes
        )
        self.session.add(transaction)
        self.session.commit()
