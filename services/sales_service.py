"""
Sales Invoice Service - Direct Stock Management
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from models.sales import SalesInvoice, SalesInvoiceItem
from models.product import Product
from services.product_service import ProductService
from datetime import datetime


class SalesInvoiceService:
    def __init__(self, session: Session):
        self.session = session
        self.product_service = ProductService(session)

    def _generate_invoice_number(self) -> str:
        today = datetime.now().strftime("%Y%m%d")
        last_invoice = (
            self.session.query(SalesInvoice)
            .filter(SalesInvoice.invoice_number.like(f"S-{today}-%"))
            .order_by(SalesInvoice.id.desc())
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

        return f"S-{today}-{new_num:04d}"

    def create_invoice(self, customer_id: int, items: list[dict],
                       discount: float = 0.0, notes: str = None) -> SalesInvoice:
        """
        Create sales invoice with stock validation and direct stock update.

        Args:
            items: List of dicts with keys: product_id, quantity, unit_price
        """
        # ✅ اعتبارسنجی موجودی قبل از هر کاری
        for item_data in items:
            product = self.product_service.get_product_by_id(item_data["product_id"])
            if not product:
                raise ValueError(f"کالای شناسه {item_data['product_id']} یافت نشد")

            requested_qty = item_data["quantity"]
            if product.stock_quantity < requested_qty:
                raise ValueError(
                    f"موجودی '{product.name}' کافی نیست. "
                    f"موجود: {product.stock_quantity}، درخواست: {requested_qty}"
                )

        # تولید شماره فاکتور
        invoice_number = self._generate_invoice_number()

        invoice = SalesInvoice(
            invoice_number=invoice_number,
            customer_id=customer_id,
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

            # اگر قیمت ارسال نشده، از قیمت فروش کالا استفاده کن
            if unit_price is None:
                unit_price = product.sell_price

            item_total = quantity * unit_price
            total_price += item_total

            invoice_item = SalesInvoiceItem(
                invoice_id=invoice.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=item_total
            )
            self.session.add(invoice_item)

            # ✅ کاهش مستقیم موجودی
            self.product_service.adjust_stock(
                product_id=product_id,
                quantity_change=-quantity
            )

        invoice.total_price = total_price
        invoice.final_total = max(0, total_price - discount)

        self.session.commit()
        self.session.refresh(invoice)
        return invoice

    def get_all_invoices(self):
        return (
            self.session.query(SalesInvoice)
            .order_by(SalesInvoice.created_at.desc())
            .all()
        )

    def delete_invoice(self, invoice_id: int):
        """Delete invoice and restore stock"""
        invoice = (
            self.session.query(SalesInvoice)
            .filter(SalesInvoice.id == invoice_id)
            .first()
        )
        if not invoice:
            return

        # بازگرداندن موجودی
        for item in invoice.items:
            self.product_service.adjust_stock(
                product_id=item.product_id,
                quantity_change=item.quantity  # مثبت = بازگشت
            )

        self.session.delete(invoice)
        self.session.commit()