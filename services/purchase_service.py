"""
Purchase Invoice Service - Direct Stock Management
"""

from sqlalchemy.orm import Session
from models.purchase import PurchaseInvoice, PurchaseInvoiceItem
from services.product_service import ProductService
from datetime import datetime


class PurchaseInvoiceService:
    def __init__(self, session: Session):
        self.session = session
        self.product_service = ProductService(session)

    def _generate_invoice_number(self) -> str:
        today = datetime.now().strftime("%Y%m%d")
        last_invoice = (
            self.session.query(PurchaseInvoice)
            .filter(PurchaseInvoice.invoice_number.like(f"P-{today}-%"))
            .order_by(PurchaseInvoice.id.desc())
            .first()
        )
        if last_invoice:
            try:
                last_num = int(last_invoice.invoice_number.split("-")[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1
        return f"P-{today}-{new_num:04d}"

    def create_invoice(self, supplier_id: int, items: list[dict],
                       discount: float = 0.0, notes: str = None) -> PurchaseInvoice:
        invoice_number = self._generate_invoice_number()

        invoice = PurchaseInvoice(
            invoice_number=invoice_number,
            supplier_id=supplier_id,
            discount=max(0, discount),
            notes=notes,
            total_price=0,
            final_total=0
        )
        self.session.add(invoice)
        self.session.flush()

        total_price = 0
        for item_data in items:
            product_id = item_data["product_id"]
            quantity = item_data["quantity"]
            unit_price = item_data.get("unit_price")

            product = self.product_service.get_product_by_id(product_id)
            if not product:
                raise ValueError(f"کالای شناسه {product_id} یافت نشد")

            if unit_price is None:
                unit_price = product.buy_price

            item_total = quantity * unit_price
            total_price += item_total

            invoice_item = PurchaseInvoiceItem(
                invoice_id=invoice.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=item_total
            )
            self.session.add(invoice_item)

            # ✅ افزایش مستقیم موجودی
            self.product_service.adjust_stock(
                product_id=product_id,
                quantity_change=quantity
            )

        invoice.total_price = total_price
        invoice.final_total = max(0, total_price - discount)

        self.session.commit()
        self.session.refresh(invoice)
        return invoice

    def get_all_invoices(self):
        return (
            self.session.query(PurchaseInvoice)
            .order_by(PurchaseInvoice.created_at.desc())
            .all()
        )

    def delete_invoice(self, invoice_id: int):
        invoice = (
            self.session.query(PurchaseInvoice)
            .filter(PurchaseInvoice.id == invoice_id)
            .first()
        )
        if not invoice:
            return

        for item in invoice.items:
            self.product_service.adjust_stock(
                product_id=item.product_id,
                quantity_change=-item.quantity
            )

        self.session.delete(invoice)
        self.session.commit()