"""
Purchase Invoice Widget - Fixed Print & Load
"""
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QLineEdit, QPushButton,
                                QTableWidget, QTableWidgetItem, QMessageBox,
                                QGroupBox, QHeaderView, QTextEdit)
from PySide6.QtCore import Qt
from sqlalchemy.orm import Session

from models.party import PartyType
from services.purchase_service import PurchaseInvoiceService
from services.product_service import ProductService
from services.party_service import PartyService
from services.printer_service import PrintService
from ui.sales_invoice_widget import SearchDialog


class PurchaseInvoiceWidget(QWidget):
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
            selection-background-color: #dbeafe; selection-color: #1e293b;
            background-color: #ffffff; color: #000000;
        }
        QHeaderView::section {
            background-color: #f8fafc; color: #475569; padding: 10px;
            font-weight: bold; border: none; border-bottom: 2px solid #e2e8f0;
        }

        QTextEdit {
            background-color: #ffffff; color: #000000;
            border: 1px solid #cbd5e1; border-radius: 6px;
            padding: 6px; font-size: 13px;
        }
        QTextEdit:focus { border-color: #3b82f6; }
    """

    @staticmethod
    def _pd(text) -> str:
        return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

    @staticmethod
    def _ed(text: str) -> str:
        return text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))

    @staticmethod
    def _cn(text: str) -> float:
        c = PurchaseInvoiceWidget._ed(text).replace(",", "").strip()
        return float(c or 0)

    def __init__(self, session: Session, db_manager):
        super().__init__()
        self.session = session
        self.db_manager = db_manager
        self.purchase_service = PurchaseInvoiceService(session)
        self.product_service = ProductService(session)
        self.party_service = PartyService(session)

        self.invoice_items: list[dict] = []
        self.current_supplier = None
        self.current_product = None
        # ✅ شناسه فاکتور فعلی (چه تازه ثبت شده، چه لود شده از گزارش)
        self._current_invoice_id = None

        self.setStyleSheet(self.WIDGET_STYLESHEET)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(8)

        title = QLabel("فاکتور خرید")
        title.setObjectName("title")
        layout.addWidget(title)

        # ─── انتخاب تامین کننده ───
        supplier_group = QGroupBox("تامین کننده")
        sl = QHBoxLayout()
        sl.setContentsMargins(8, 8, 8, 8)
        sl.setSpacing(8)

        self.supplier_select_btn = QPushButton("انتخاب تامین کننده")
        self.supplier_select_btn.setObjectName("select_btn")
        self.supplier_select_btn.setMinimumHeight(36)
        self.supplier_select_btn.clicked.connect(self._show_supplier_dialog)
        sl.addWidget(self.supplier_select_btn)

        self.supplier_label = QLabel("هیچ تامین کننده ای انتخاب نشده")
        self.supplier_label.setObjectName("supplier_lbl")
        sl.addWidget(self.supplier_label, 1)

        supplier_group.setLayout(sl)
        layout.addWidget(supplier_group)

        # ─── افزودن کالا ───
        product_group = QGroupBox("افزودن کالا")
        pl = QHBoxLayout()
        pl.setContentsMargins(8, 8, 8, 8)
        pl.setSpacing(6)

        self.product_search_edit = QLineEdit()
        self.product_search_edit.setPlaceholderText("جستجوی کالا...")
        self.product_search_edit.returnPressed.connect(self._show_product_dialog)
        pl.addWidget(self.product_search_edit, 2)

        self.product_select_btn = QPushButton("جست و جوی کالا")
        self.product_select_btn.setObjectName("select_btn")
        self.product_select_btn.setMinimumHeight(36)
        self.product_select_btn.clicked.connect(self._show_product_dialog)
        pl.addWidget(self.product_select_btn)

        self.selected_product_label = QLabel("")
        self.selected_product_label.setObjectName("info_lbl")
        pl.addWidget(self.selected_product_label, 2)

        pl.addWidget(QLabel("تعداد:"))
        self.quantity_edit = QLineEdit("1")
        self.quantity_edit.setFixedWidth(60)
        pl.addWidget(self.quantity_edit)

        pl.addWidget(QLabel("قیمت:"))
        self.price_edit = QLineEdit()
        self.price_edit.setPlaceholderText("قیمت خرید")
        self.price_edit.setFixedWidth(100)
        pl.addWidget(self.price_edit)

        self.add_item_btn = QPushButton("افزودن به فاکتور")
        self.add_item_btn.setObjectName("select_btn")
        self.add_item_btn.setMinimumHeight(36)
        self.add_item_btn.clicked.connect(self._add_item_to_invoice)
        pl.addWidget(self.add_item_btn)

        product_group.setLayout(pl)
        layout.addWidget(product_group)

        # ─── جدول اقلام ───
        items_group = QGroupBox("اقلام فاکتور")
        il = QVBoxLayout()
        il.setContentsMargins(8, 8, 8, 8)

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
        il.addWidget(self.items_table)

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

        il.addLayout(totals_layout)
        items_group.setLayout(il)
        layout.addWidget(items_group, stretch=1)

        # توضیحات
        notes_group = QGroupBox("توضیحات")
        nl = QVBoxLayout()
        nl.setContentsMargins(8, 8, 8, 8)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("توضیحات اختیاری فاکتور...")
        nl.addWidget(self.notes_edit)
        notes_group.setLayout(nl)
        layout.addWidget(notes_group)

        # دکمه‌ها
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

        font_path = os.path.join(os.path.dirname(__file__), "..", "static", "fonts", "Arad-Regular.ttf")
        self.print_service = PrintService(font_path=font_path)

    # ─── Dialogs ──────────────────────────────────────────────

    def _show_supplier_dialog(self):
        suppliers = self.party_service.search_parties(party_type=PartyType.SUPPLIER)
        if not suppliers:
            try:
                suppliers = self.party_service.get_all_parties()
            except AttributeError:
                suppliers = []

        if not suppliers:
            QMessageBox.warning(self, "خطا", "هیچ تامین کننده ای ثبت نشده است")
            return

        dialog = SearchDialog(self, suppliers, search_fields=('name', 'phone'))
        dialog.item_selected.connect(self._on_supplier_selected)
        dialog.exec()

    def _on_supplier_selected(self, supplier):
        self.current_supplier = supplier
        phone = supplier.phone or ""
        self.supplier_label.setText(f"{supplier.name} | تلفن: {phone}")

    def _show_product_dialog(self):
        products = self.product_service.get_all_products()
        if not products:
            QMessageBox.warning(self, "خطا", "هیچ کالایی ثبت نشده است")
            return

        prefill = self.product_search_edit.text().strip()
        dialog = SearchDialog(parent=self, items=products,
                              search_fields=('name', 'code', 'sub_category'))
        if prefill:
            dialog.search_edit.setText(prefill)
            dialog._filter_items(prefill)
        dialog.item_selected.connect(self._on_product_selected)
        dialog.exec()

    def _on_product_selected(self, product):
        if product is None or not hasattr(product, 'id'):
            return

        self.current_product = product
     
        persian_stock = self._pd(product.stock_quantity)

        self.selected_product_label.setText(
            f"[{product.code}] {product.name} | "
            f"   موجودی: {persian_stock}"
        )

        self.quantity_edit.setFocus()
        self.quantity_edit.selectAll()

    # ─── Invoice Items ────────────────────────────────────────

    def _add_item_to_invoice(self):
        if not self.current_product:
            QMessageBox.warning(self, "خطا", "لطفاً یک کالا انتخاب کنید")
            return

        try:
            quantity = int(self._ed(self.quantity_edit.text().strip() or "1"))
            price_text = self.price_edit.text().strip()
            price = self._cn(price_text) if price_text else self.current_product.buy_price
        except ValueError:
            QMessageBox.warning(self, "خطا", "تعداد و قیمت باید عدد معتبر باشند")
            return

        if quantity <= 0:
            QMessageBox.warning(self, "خطا", "تعداد باید بیشتر از صفر باشد")
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
                item['product_code'], item['product_name'],
                str(item['quantity']), f"{item['unit_price']:,.0f}", f"{item['total']:,.0f}"
            ]
            for col, text in enumerate(values):
                display = self._pd(text)
                cell = QTableWidgetItem(display)
                if col in (2, 3, 4):
                    cell.setTextAlignment(Qt.AlignCenter)
                self.items_table.setItem(row, col, cell)
            total += item['total']
        self._update_totals(total_override=total)

    def _update_totals(self, *_, total_override=None):
        total = total_override if total_override is not None else sum(i['total'] for i in self.invoice_items)
        discount = self._cn(self.discount_edit.text())
        final = max(0, total - discount)
        self.total_label.setText(self._pd(f"{total:,.0f}"))
        self.final_total_label.setText(self._pd(f"{final:,.0f}"))

    # ─── Actions ──────────────────────────────────────────────

    def _save_invoice(self):
        if not self.current_supplier:
            QMessageBox.warning(self, "خطا", "لطفاً یک تامین کننده انتخاب کنید")
            return
        if not self.invoice_items:
            QMessageBox.warning(self, "خطا", "فاکتور خالی است")
            return

        try:
            discount = self._cn(self.discount_edit.text())
            notes = self.notes_edit.toPlainText().strip() or None

            # ✅ تشخیص حالت ویرایش یا ثبت جدید
            is_editing = self._current_invoice_id is not None

            if is_editing:
                reply = QMessageBox.question(
                    self, "تأیید ویرایش",
                    "با ویرایش این فاکتور، نسخه قبلی حذف و فاکتور جدید جایگزین می‌شود.\n"
                    "آیا ادامه می‌دهید؟",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return

                self.purchase_service.delete_invoice(self._current_invoice_id)

            invoice = self.purchase_service.create_invoice(
                supplier_id=self.current_supplier.id,
                items=self.invoice_items,
                discount=discount,
                notes=notes
            )

            self._current_invoice_id = invoice.id

            pn = self._pd(invoice.invoice_number)
            pt = self._pd(f"{invoice.final_total:,.0f}")

            QMessageBox.information(
                self, "موفق",
                f"فاکتور خرید با موفقیت {'ویرایش' if is_editing else 'ثبت'} شد\n\n"
                f"شماره فاکتور: {pn}\nمبلغ کل: {pt} تومان"
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
            from models.purchase import PurchaseInvoice
            invoice = self.session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == self._current_invoice_id
            ).first()

            if not invoice:
                QMessageBox.warning(self, "خطا", "فاکتور در دیتابیس یافت نشد")
                return

            # ✅ همیشه purchase برای ویجت خرید
            pdf_path = self.print_service.generate_invoice_pdf(
                invoice, invoice_type="purchase"
            )
            self.print_service.open_pdf(pdf_path)

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در چاپ: {str(e)}")

    def _clear_invoice(self):
        self.current_supplier = None
        self.current_product = None
        self.invoice_items = []
        self._current_invoice_id = None  # ✅ ریست شناسه فاکتور

        self.supplier_label.setText("هیچ تامین کننده ای انتخاب نشده")
        self.selected_product_label.setText("")
        self.product_search_edit.clear()
        self.quantity_edit.setText("1")
        self.price_edit.clear()
        self.discount_edit.setText("0")
        self.notes_edit.clear()
        self._update_items_table()
        self.product_search_edit.setFocus()

    def load_existing_invoice(self, invoice_id: int):
        """بارگذاری فاکتور خرید از گزارش برای مشاهده/چاپ"""
        try:
            from models.purchase import PurchaseInvoice
            invoice = self.session.query(PurchaseInvoice).filter(
                PurchaseInvoice.id == invoice_id
            ).first()

            if not invoice:
                QMessageBox.warning(self, "خطا", "فاکتور خرید مورد نظر یافت نشد")
                return

            self._clear_invoice()

            # ✅ ست کردن ID برای امکان چاپ مستقیم
            self._current_invoice_id = invoice.id

            supplier = invoice.supplier
            self.current_supplier = supplier
            phone = supplier.phone or ""
            self.supplier_label.setText(f"{supplier.name} | تلفن: {phone}")

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
                f"فاکتور خرید شماره {invoice.invoice_number} بارگذاری شد.\n\n"
                f"💡 اکنون می‌توانید مستقیماً چاپ بگیرید."
            )

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری فاکتور: {str(e)}")