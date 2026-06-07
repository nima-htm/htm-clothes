"""
Sales Invoice Service
Handles sales invoice creation and management
"""

from sqlalchemy.orm import Session
from models.sales import SalesInvoice, SalesInvoiceItem
from models.product import Product
from services.product_service import ProductService
from datetime import datetime


class SalesInvoiceService:
    def __init__(self, session: Session):
        self.session = session
        self.product_service = ProductService(session)
    
    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        today = datetime.now().strftime("%Y%m%d")
        last_invoice = self.session.query(SalesInvoice).filter(
            SalesInvoice.invoice_number.like(f"S-{today}-%")
        ).order_by(SalesInvoice.id.desc()).first()
        
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"S-{today}-{new_num:04d}"
    
    def create_invoice(self, customer_id: int, items: list, discount: float = 0.0,
                       notes: str = None) -> SalesInvoice:
        """
        Create a new sales invoice
        
        Args:
            customer_id: ID of the customer
            items: List of dicts with keys: product_id, quantity, unit_price
            discount: Discount amount
            notes: Optional notes
        """
        # Generate invoice number
        invoice_number = self._generate_invoice_number()
        
        # Create invoice
        invoice = SalesInvoice(
            invoice_number=invoice_number,
            customer_id=customer_id,
            discount=discount,
            notes=notes,
            total_price=0,
            final_total=0
        )
        
        self.session.add(invoice)
        self.session.flush()  # Get invoice ID
        
        # Add items and calculate totals
        total_price = 0
        for item_data in items:
            product_id = item_data["product_id"]
            quantity = item_data["quantity"]
            unit_price = item_data.get("unit_price")
            
            # Get product
            product = self.product_service.get_product_by_id(product_id)
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            # Use provided price or default to product sell price
            if unit_price is None:
                unit_price = product.sell_price
            
            item_total = quantity * unit_price
            total_price += item_total
            
            # Create invoice item
            invoice_item = SalesInvoiceItem(
                invoice_id=invoice.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=item_total
            )
            
            self.session.add(invoice_item)
            
            # Remove stock
            self.product_service.remove_stock(
                product_id=product_id,
                quantity=quantity,
                reference_type="sales_invoice",
                reference_id=invoice.id
            )
        
        # Update invoice totals
        invoice.total_price = total_price
        invoice.final_total = total_price - discount
        
        self.session.commit()
        self.session.refresh(invoice)
        
        return invoice
    
    def get_invoice_by_id(self, invoice_id: int) -> SalesInvoice:
        """Get invoice by ID"""
        return self.session.query(SalesInvoice).filter(
            SalesInvoice.id == invoice_id
        ).first()
    
    def get_invoice_by_number(self, invoice_number: str) -> SalesInvoice:
        """Get invoice by invoice number"""
        return self.session.query(SalesInvoice).filter(
            SalesInvoice.invoice_number == invoice_number
        ).first()
    
    def get_all_invoices(self):
        """Get all sales invoices"""
        return self.session.query(SalesInvoice).order_by(
            SalesInvoice.created_at.desc()
        ).all()
    
    def search_invoices(self, customer_id: int = None, start_date: datetime = None,
                        end_date: datetime = None):
        """Search invoices with filters"""
        query = self.session.query(SalesInvoice)
        
        if customer_id:
            query = query.filter(SalesInvoice.customer_id == customer_id)
        
        if start_date:
            query = query.filter(SalesInvoice.created_at >= start_date)
        
        if end_date:
            query = query.filter(SalesInvoice.created_at <= end_date)
        
        return query.order_by(SalesInvoice.created_at.desc()).all()
    
    def delete_invoice(self, invoice_id: int):
        """Delete an invoice (and restore stock)"""
        invoice = self.get_invoice_by_id(invoice_id)
        if invoice:
            # Restore stock for each item
            for item in invoice.items:
                self.product_service.add_stock(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    reference_type="sales_invoice_cancelled",
                    reference_id=invoice_id,
                    notes=f"Cancelled invoice {invoice.invoice_number}"
                )
            
            self.session.delete(invoice)
            self.session.commit()
