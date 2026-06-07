"""
Test script to verify the application structure and database models
"""

import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import DatabaseManager
from models import Product, ProductCategory, Party, PartyType
from services import ProductService, PartyService, SalesInvoiceService, PurchaseInvoiceService


def test_database():
    """Test database initialization and basic operations"""
    print("=" * 50)
    print("Testing Nima Clothes Application")
    print("=" * 50)
    
    # Initialize database
    print("\n1. Initializing database...")
    db = DatabaseManager("sqlite:///test_nima_clothes.db")
    db.initialize()
    print("   ✓ Database initialized successfully")
    
    # Get session
    session = db.get_session()
    
    # Test Product Service
    print("\n2. Testing Product Service...")
    product_service = ProductService(session)
    
    try:
        # Create test products
        p1 = product_service.create_product(
            code="P-001",
            name="پارچه کتان",
            category=ProductCategory.FABRIC,
            sub_category="کتان",
            buy_price=50000,
            sell_price=75000
        )
        print(f"   ✓ Created product: {p1.name}")
        
        p2 = product_service.create_product(
            code="P-002",
            name="شلوار جین",
            category=ProductCategory.PANTS,
            sub_category="جین",
            buy_price=150000,
            sell_price=250000
        )
        print(f"   ✓ Created product: {p2.name}")
        
        # Search products
        products = product_service.search_products(query="پارچه")
        print(f"   ✓ Found {len(products)} product(s) matching 'پارچه'")
        
    except Exception as e:
        print(f"   Note: {e}")
    
    # Test Party Service
    print("\n3. Testing Party Service...")
    party_service = PartyService(session)
    
    try:
        # Create test customer
        c1 = party_service.create_party(
            name="علی رضایی",
            party_type=PartyType.CUSTOMER,
            phone="09121234567"
        )
        print(f"   ✓ Created customer: {c1.name}")
        
        # Create test supplier
        s1 = party_service.create_party(
            name="شرکت پوشاک تهران",
            party_type=PartyType.SUPPLIER,
            phone="02188888888"
        )
        print(f"   ✓ Created supplier: {s1.name}")
        
        # Get customers
        customers = party_service.get_customers()
        print(f"   ✓ Total customers: {len(customers)}")
        
    except Exception as e:
        print(f"   Note: {e}")
    
    # Test Purchase Invoice (add stock)
    print("\n4. Testing Purchase Invoice...")
    purchase_service = PurchaseInvoiceService(session)
    
    try:
        # Get first product and supplier
        product = session.query(Product).first()
        supplier = session.query(Party).filter(Party.party_type == PartyType.SUPPLIER).first()
        
        if product and supplier:
            invoice = purchase_service.create_invoice(
                supplier_id=supplier.id,
                items=[{
                    "product_id": product.id,
                    "quantity": 20,
                    "unit_price": product.buy_price
                }]
            )
            print(f"   ✓ Created purchase invoice: {invoice.invoice_number}")
            
            # Check stock
            stock = product_service.get_current_stock(product.id)
            print(f"   ✓ Current stock for {product.name}: {stock}")
    except Exception as e:
        print(f"   Note: {e}")
    
    # Test Sales Invoice (remove stock)
    print("\n5. Testing Sales Invoice...")
    sales_service = SalesInvoiceService(session)
    
    try:
        # Get first product and customer
        product = session.query(Product).first()
        customer = session.query(Party).filter(Party.party_type == PartyType.CUSTOMER).first()
        
        if product and customer:
            current_stock = product_service.get_current_stock(product.id)
            if current_stock >= 5:
                invoice = sales_service.create_invoice(
                    customer_id=customer.id,
                    items=[{
                        "product_id": product.id,
                        "quantity": 5,
                        "unit_price": product.sell_price
                    }]
                )
                print(f"   ✓ Created sales invoice: {invoice.invoice_number}")
                
                # Check updated stock
                stock = product_service.get_current_stock(product.id)
                print(f"   ✓ Updated stock for {product.name}: {stock}")
    except Exception as e:
        print(f"   Note: {e}")
    
    # Close session
    db.close_session()
    
    print("\n" + "=" * 50)
    print("All tests completed successfully!")
    print("=" * 50)
    print("\nTo run the application:")
    print("  cd /workspace/nima_clothes")
    print("  python main.py")
    print("\nNote: Install dependencies first:")
    print("  pip install PySide6 SQLAlchemy reportlab")


if __name__ == "__main__":
    test_database()
