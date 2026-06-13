"""
Sales Invoice Widget - Advanced Search & RTL (Layout Fix Only)
"""
import os, subprocess
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                                QLabel, QLineEdit, QPushButton,
                                QTableWidget, QTableWidgetItem, QMessageBox,
                                QGroupBox, QHeaderView, QDialog, QListWidget,
                                QTextEdit)
from PySide6.QtCore import Qt, Signal
from sqlalchemy.orm import Session

from models.party import PartyType
from services.sales_service import SalesInvoiceService
from services.product_service import ProductService
from services.party_service import PartyService
from services.printer_service import PrintService
from models.sales import SalesInvoice
class SearchDialog(QDialog):
    """Advanced search dialog supporting name AND code search"""
    item_selected = Signal(object)

    SEARCH_STYLESHEET = """
        QDialog { background-color: #ffffff; font-family: 'Vazirmatn', 'Tahoma'; }
        QLineEdit {
            padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px;
            font-size: 14px; background-color: #f8fafc; color: #000000;
        }
        QLineEdit:focus { border-color: #3b82f6; background-color: #fff; }
        QListWidget {
            border: 1px solid #cbd5e1; border-radius: 6px;
            font-size: 14px; color: #000000; background-color: #ffffff;
            outline: none; padding: 4px;
        }
        QListWidget::item {
            padding: 12px; border-bottom: 1px solid #e2e8f0; color: #000000;
        }
        QListWidget::item:selected {
            background-color: #2563eb; color: #ffffff;
        }
        QListWidget::item:hover:!selected {
            background-color: #eff6ff; color: #000000;
        }
        QPushButton {
            padding: 10px 20px; border-radius: 6px; font-weight: 600;
            background-color: #3b82f6; color: white; border: none; min-width: 80px;
        }
        QPushButton:hover { background-color: #2563eb; }
        QPushButton#cancel_btn { background-color: #64748b; }
        QPushButton#cancel_btn:hover { background-color: #475569; }
    """

    def __init__(self, parent, items, search_fields=('name', 'code'), display_format=None):
        super().__init__(parent)
        self.all_items = items
        self.search_fields = search_fields
        self.display_format = display_format or (lambda x: x.name)

        self.setWindowTitle("جستجو و انتخاب")
        self.setMinimumSize(500, 400)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(self.SEARCH_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("جستجو...")
        self.search_edit.textChanged.connect(self._filter_items)
        layout.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(lambda _: self._select_current())
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        select_btn = QPushButton("انتخاب")
        select_btn.clicked.connect(self._select_current)
        btn_layout.addWidget(select_btn)

        cancel_btn = QPushButton("انصراف")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self._filtered_items = []
        self._filter_items("")
        self.search_edit.setFocus()

    def _format_display(self, item) -> str:
        if hasattr(item, 'code') and hasattr(item, 'name'):
            stock_info = ""
            if hasattr(item, 'stock_quantity'):
                persian_stock = str(item.stock_quantity).translate(
                    str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
                )
                stock_info = f" | موجودی: {persian_stock}"
            return f"[{item.code}] {item.name}{stock_info}"
        return self.display_format(item)

    def _filter_items(self, query: str):
        self.list_widget.clear()
        query_lower = query.strip().lower()
        filtered = []
        for item in self.all_items:
            if not query_lower:
                filtered.append(item)
                continue
            match = False
            for field in self.search_fields:
                value = getattr(item, field, "")
                if value and query_lower in str(value).lower():
                    match = True
                    break
            if match:
                filtered.append(item)
        for item in filtered:
            self.list_widget.addItem(self._format_display(item))
        self._filtered_items = filtered

    def _select_current(self):
        row = self.list_widget.currentRow()

        if row < 0:
            return

        filtered = getattr(self, '_filtered_items', [])
        if not filtered or row >= len(filtered):
            print(f"[WARN] Row {row} out of range. Filtered items: {len(filtered)}")
            return

        selected_item = filtered[row]
        print(f"[DEBUG] Emitting item: {selected_item}")
        self.item_selected.emit(selected_item)
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._select_current()
        else:
            super().keyPressEvent(event)


class SalesInvoiceWidget(QWidget):
    WIDGET_STYLESHEET = """
        QLabel { color: #1e293b; font-size: 13px; background-color: transparent; }
        QLabel#title { font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
        QLabel#total_lbl { font-size: 16px; font-weight: bold; color: #1e293b; }
        QLabel#final_lbl { font-size: 20px; font-weight: 800; color: #059669; }
        QLabel#info_lbl { color: #059669; font-weight: bold; font-size: 13px; }
        QLabel#supplier_lbl { color: #1e40af; font-weight: bold; font-size: 13px; }

        QGroupBox {
            font-weight: bold; color: #334155; border: 1px solid #e2e8f0;
            border-radius: 8px; margin-top: 6px; padding: 12px 10px 8px 10px;
            background-color: #ffffff;
        }
        QGroupBox::title { subcontrol-origin: margin; right: 15px; padding: 0 8px; color: #1e293b; }

        QPushButton#save_btn { background-color: #10b981; font-size: 14px; font-weight: bold; }
        QPushButton#save_btn:hover { background-color: #059669; }
        QPushButton#print_btn { background-color: #3b82f6; }
        QPushButton#print_btn:hover { background-color: #2563eb; }
        QPushButton#clear_btn { background-color: #64748b; }
        QPushButton#clear_btn:hover { background-color: #475569; }
        QPushButton#select_btn { background-color: #6366f1; min-width: 100px; }
        QPushButton#select_btn:hover { background-color: #4f46e5; }

        QTableWidget {
            border: 1px solid #e2e8f0; border-radius: 6px; gridline-color: #f1f5f9;
            selection-background-color: #fee2e2; selection-color: #1e293b;
            background-color: #ffffff; color: #000000;
        }
        QHeaderView::section {
            background-color: #f8fafc; color: #475569; padding: 10px;
            font-weight: bold; border: none; border-bottom: 2px solid #e2e8f0;
        }

        QTextEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 6px;
            font-size: 13px;
        }
        QTextEdit:focus { border-color: #3b82f6; }
    """

    @staticmethod
    def _to_persian_digits(text) -> str:
        return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

    @staticmethod
    def _to_english_digits(text: str) -> str:
        return text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))

    @staticmethod
    def _clean_number(text: str) -> float:
        cleaned = SalesInvoiceWidget._to_english_digits(text).replace(",", "").strip()
        return float(cleaned or 0)

    def __init__(self, session: Session, db_manager):
        super().__init__()

        self.session = session
        self.db_manager = db_manager
        self.sales_service = SalesInvoiceService(session)
        self.product_service = ProductService(session)
        self.party_service = PartyService(session)

        self.invoice_items: list[dict] = []
        self.current_customer = None
        self.current_product = None
        self._current_invoice_id = None
        self.setStyleSheet(self.WIDGET_STYLESHEET)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(8)

        title = QLabel("فاکتور فروش")
        title.setObjectName("title")
        layout.addWidget(title)

        # ─── انتخاب مشتری (فشرده و افقی) ───
        customer_group = QGroupBox("مشتری")
        customer_layout = QHBoxLayout()
        customer_layout.setContentsMargins(8, 8, 8, 8)
        customer_layout.setSpacing(8)

        self.customer_select_btn = QPushButton("انتخاب مشتری")
        self.customer_select_btn.setObjectName("select_btn")
        self.customer_select_btn.setMinimumHeight(36)
        self.customer_select_btn.clicked.connect(self._show_customer_dialog)
        customer_layout.addWidget(self.customer_select_btn)

        self.customer_label = QLabel("هیچ مشتری انتخاب نشده")
        self.customer_label.setObjectName("supplier_lbl")
        customer_layout.addWidget(self.customer_label, 1)

        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)

        # ─── افزودن کالا (فشرده و افقی در یک ردیف) ───
        product_group = QGroupBox("افزودن کالا")
        product_layout = QHBoxLayout()
        product_layout.setContentsMargins(8, 8, 8, 8)
        product_layout.setSpacing(6)

        self.product_search_edit = QLineEdit()


        self.product_select_btn = QPushButton("جست و جوی کالا")
        self.product_select_btn.setObjectName("select_btn")
        self.product_select_btn.setMinimumHeight(36)
        self.product_select_btn.clicked.connect(self._show_product_dialog)
        product_layout.addWidget(self.product_select_btn)

        self.selected_product_label = QLabel("")
        self.selected_product_label.setObjectName("info_lbl")
        product_layout.addWidget(self.selected_product_label, 5)

        product_layout.addWidget(QLabel("تعداد:"))
        self.quantity_edit = QLineEdit("1")
        self.quantity_edit.setPlaceholderText("تعداد")
        self.quantity_edit.setFixedWidth(60)
        product_layout.addWidget(self.quantity_edit)

        product_layout.addWidget(QLabel("قیمت:"))
        self.price_edit = QLineEdit()
        self.price_edit.setPlaceholderText("قیمت واحد")
        self.price_edit.setFixedWidth(100)
        product_layout.addWidget(self.price_edit)

        self.add_item_btn = QPushButton("افزودن به فاکتور")
        self.add_item_btn.setObjectName("select_btn")
        self.add_item_btn.setMinimumHeight(36)
        self.add_item_btn.clicked.connect(self._add_item_to_invoice)
        product_layout.addWidget(self.add_item_btn)

        product_group.setLayout(product_layout)
        layout.addWidget(product_group)

        # ─── جدول اقلام ───
        items_group = QGroupBox("اقلام فاکتور")
        items_layout = QVBoxLayout()
        items_layout.setContentsMargins(8, 8, 8, 8)

        self.items_table = QTableWidget()
        self.items_table.setLayoutDirection(Qt.RightToLeft)

        headers = ["کد کالا", "نام کالا", "تعداد", "قیمت واحد", "جمع کل"]
        self.items_table.setColumnCount(len(headers))
        self.items_table.setHorizontalHeaderLabels(headers)

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        items_layout.addWidget(self.items_table)

        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        totals_layout.setSpacing(15)

        totals_layout.addWidget(QLabel("جمع کل:"))
        self.total_label = QLabel("۰")
        self.total_label.setObjectName("total_lbl")
        totals_layout.addWidget(self.total_label)

        totals_layout.addWidget(QLabel("تخفیف:"))
        self.discount_edit = QLineEdit("0")
        self.discount_edit.setFixedWidth(150)
        self.discount_edit.textChanged.connect(self._update_totals)
        totals_layout.addWidget(self.discount_edit)

        totals_layout.addWidget(QLabel("قابل پرداخت:"))
        self.final_total_label = QLabel("۰")
        self.final_total_label.setObjectName("final_lbl")
        totals_layout.addWidget(self.final_total_label)

        items_layout.addLayout(totals_layout)
        items_group.setLayout(items_layout)
        layout.addWidget(items_group, stretch=1)

        # توضیحات
        notes_group = QGroupBox("توضیحات")
        notes_layout = QVBoxLayout()
        notes_layout.setContentsMargins(8, 8, 8, 8)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("توضیحات اختیاری فاکتور...")
        notes_layout.addWidget(self.notes_edit)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # دکمه‌های عملیات
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.save_btn = QPushButton("ثبت فاکتور")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.setMinimumHeight(45)
        self.save_btn.clicked.connect(self._save_invoice)

        self.print_btn = QPushButton("چاپ فاکتور")
        self.print_btn.setObjectName("print_btn")
        self.print_btn.setMinimumHeight(45)
        self.print_btn.clicked.connect(self._print_invoice)

        self.clear_btn = QPushButton("فاکتور جدید")
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.setMinimumHeight(45)
        self.clear_btn.clicked.connect(self._clear_invoice)


        for btn in [self.save_btn, self.print_btn, self.clear_btn]:
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        font_path = os.path.join(os.path.dirname(__file__), ".." ,"static", "fonts", "Arad-Regular.ttf")
        self.print_service = PrintService(font_path=font_path)
    # ─── Dialogs ──────────────────────────────────────────────

    def _show_customer_dialog(self):
        customers = self.party_service.search_parties(party_type=PartyType.CUSTOMER)
        if not customers:
            try:
                customers = self.party_service.get_all_parties()
            except AttributeError:
                customers = []

        if not customers:
            QMessageBox.warning(self, "خطا", "هیچ مشتری ثبت نشده است")
            return

        dialog = SearchDialog(self, customers, search_fields=('name', 'phone'))
        dialog.item_selected.connect(self._on_customer_selected)
        dialog.exec()

    def _on_customer_selected(self, customer):
        self.current_customer = customer
        phone = customer.phone or ""
        self.customer_label.setText(f"{customer.name} | تلفن: {phone}")

    def _show_product_dialog(self):
        products = self.product_service.get_all_products()
        if not products:
            QMessageBox.warning(self, "خطا", "هیچ کالایی ثبت نشده است")
            return

        prefill = self.product_search_edit.text().strip()

        dialog = SearchDialog(
            self, products,
            search_fields=('name', 'code', 'sub_category')
        )
        if prefill:
            dialog.search_edit.setText(prefill)
        dialog.item_selected.connect(self._on_product_selected)
        dialog.exec()

    def _on_product_selected(self, product):
        self.current_product = product
        persian_stock = self._to_persian_digits(product.stock_quantity)


        self.selected_product_label.setText(
            f"[{product.code}] {product.name} | "
            f"قیمت: {persian_stock} | موجودی: {persian_stock}"
        )

        self.quantity_edit.setFocus()
        self.quantity_edit.selectAll()

    # ─── Invoice Items ────────────────────────────────────────

    def _add_item_to_invoice(self):
        if not self.current_product:
            QMessageBox.warning(self, "خطا", "لطفاً یک کالا انتخاب کنید")
            return

        try:
            quantity = int(self._to_english_digits(self.quantity_edit.text().strip() or "1"))
            price_text = self.price_edit.text().strip()
            price = self._clean_number(price_text) if price_text else self.current_product.sell_price
        except ValueError:
            QMessageBox.warning(self, "خطا", "تعداد و قیمت باید عدد معتبر باشند")
            return

        if quantity <= 0:
            QMessageBox.warning(self, "خطا", "تعداد باید بیشتر از صفر باشد")
            return

        if self.current_product.stock_quantity < quantity:
            QMessageBox.warning(
                self, "موجودی ناکافی",
                f"موجودی فعلی: {self._to_persian_digits(self.current_product.stock_quantity)}\n"
                f"تعداد درخواستی: {self._to_persian_digits(quantity)}"
            )
            return

        total = quantity * price

        self.invoice_items.append({
            'product_id': self.current_product.id,
            'product_code': self.current_product.code,
            'product_name': self.current_product.name,
            'quantity': quantity,
            'unit_price': price,
            'total': total
        })

        self._update_items_table()

        self.current_product = None
        self.selected_product_label.setText("")
        self.product_search_edit.clear()
        self.quantity_edit.setText("1")
        self.price_edit.clear()
        self.product_search_edit.setFocus()

    def _update_items_table(self):
        self.items_table.setRowCount(0)

        total = 0
        for item in self.invoice_items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)

            values = [
                item['product_code'],
                item['product_name'],
                str(item['quantity']),
                f"{item['unit_price']:,.0f}",
                f"{item['total']:,.0f}"
            ]

            for col, text in enumerate(values):
                display = self._to_persian_digits(text)
                cell = QTableWidgetItem(display)
                if col in (2, 3, 4):
                    cell.setTextAlignment(Qt.AlignCenter)
                self.items_table.setItem(row, col, cell)

            total += item['total']

        self._update_totals(total_override=total)

    def _update_totals(self, *_, total_override=None):
        if total_override is not None:
            total = total_override
        else:
            total = sum(item['total'] for item in self.invoice_items)

        discount = self._clean_number(self.discount_edit.text())
        final = max(0, total - discount)

        self.total_label.setText(self._to_persian_digits(f"{total:,.0f}"))
        self.final_total_label.setText(self._to_persian_digits(f"{final:,.0f}"))

    # ─── Actions ──────────────────────────────────────────────

    def _save_invoice(self):
        if not self.current_customer:
            QMessageBox.warning(self, "خطا", "لطفاً یک مشتری انتخاب کنید")
            return
        if not self.invoice_items:
            QMessageBox.warning(self, "خطا", "فاکتور خالی است")
            return

        try:
            discount = self._clean_number(self.discount_edit.text())
            notes = self.notes_edit.toPlainText().strip() or None

            # ✅ تشخیص حالت ویرایش یا ثبت جدید
            if self._current_invoice_id:
                # حالت ویرایش: حذف فاکتور قدیمی (برگشت موجودی) + ثبت جدید
                reply = QMessageBox.question(
                    self, "تأیید ویرایش",
                    "با ویرایش این فاکتور، نسخه قبلی حذف و فاکتور جدید جایگزین می‌شود.\n"
                    "آیا ادامه می‌دهید؟",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return

                self.sales_service.delete_invoice(self._current_invoice_id)

            # ثبت فاکتور (چه جدید چه جایگزین ویرایش)
            invoice = self.sales_service.create_invoice(
                customer_id=self.current_customer.id,
                items=self.invoice_items,
                discount=discount,
                notes=notes
            )

            self._current_invoice_id = invoice.id

            persian_number = self._to_persian_digits(invoice.invoice_number)
            persian_total = self._to_persian_digits(f"{invoice.final_total:,.0f}")

            msg_title = "ویرایش موفق" if self._current_invoice_id else "ثبت موفق"
            QMessageBox.information(
                self, msg_title,
                f"فاکتور فروش با موفقیت {'ویرایش' if self._current_invoice_id else 'ثبت'} شد\n\n"
                f"شماره فاکتور: {persian_number}\n"
                f"مبلغ قابل پرداخت: {persian_total} تومان"
            )

            main_window = self.window()
            if hasattr(main_window, 'stock_changed'):
                main_window.stock_changed.emit()

        except ValueError as e:
            QMessageBox.warning(self, "خطای اعتبارسنجی", str(e))
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره فاکتور: {str(e)}")
    def _print_invoice(self):
        """✅ چاپ فاکتور - بدون نیاز به ثبت مجدد، بدون duplicate"""
        if not self._current_invoice_id:
            QMessageBox.warning(
                self, "خطا",
                "ابتدا فاکتور را ثبت کنید یا از بخش گزارش انتخاب نمایید"
            )
            return

        try:
            from models.sales import SalesInvoice
            invoice = self.session.query(SalesInvoice).filter(
                SalesInvoice.id == self._current_invoice_id
            ).first()

            if not invoice:
                QMessageBox.warning(self, "خطا", "فاکتور در دیتابیس یافت نشد")
                return

            pdf_path = self.print_service.generate_invoice_pdf(
                invoice, invoice_type="sales"
            )
            # ✅ استفاده از متد مشترک باز کردن PDF
            self.print_service.open_pdf(pdf_path)

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در چاپ: {str(e)}")

    def _clear_invoice(self):
        self.current_customer = None
        self.current_product = None
        self.invoice_items = []
        self._current_invoice_id = None  # ✅ ریست شناسه فاکتور

        self.customer_label.setText("هیچ مشتری انتخاب نشده")
        self.selected_product_label.setText("")
        self.product_search_edit.clear()
        self.quantity_edit.setText("1")
        self.price_edit.clear()
        self.discount_edit.setText("0")
        self.notes_edit.clear()

        self._update_items_table()
        self.product_search_edit.setFocus()

    def load_existing_invoice(self, invoice_id: int):
        """بارگذاری فاکتور فروش موجود برای مشاهده/چاپ از گزارش"""
        try:
            from models.sales import SalesInvoice

            invoice = self.session.query(SalesInvoice).filter(
                SalesInvoice.id == invoice_id
            ).first()

            if not invoice:
                QMessageBox.warning(self, "خطا", "فاکتور فروش مورد نظر یافت نشد")
                return

            self._clear_invoice()

            # ✅ ست کردن ID برای امکان چاپ مستقیم
            self._current_invoice_id = invoice.id

            customer = invoice.customer
            self.current_customer = customer
            phone = customer.phone or ""
            self.customer_label.setText(f"{customer.name} | تلفن: {phone}")

            self.invoice_items = []
            for item in invoice.items:
                product = item.product
                self.invoice_items.append({
                    'product_id': product.id,
                    'product_code': product.code,
                    'product_name': product.name,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'total': item.total_price
                })

            self._update_items_table()
            self.discount_edit.setText(str(int(invoice.discount)))
            self.notes_edit.setPlainText(invoice.notes or "")

            QMessageBox.information(
                self, "فاکتور بارگذاری شد",
                f"فاکتور فروش شماره {invoice.invoice_number} بارگذاری شد.\n\n"
                f"💡 اکنون می‌توانید مستقیماً چاپ بگیرید."
            )

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری فاکتور: {str(e)}")

