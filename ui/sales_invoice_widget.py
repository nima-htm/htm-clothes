"""
Sales Invoice Widget - Brown theme, inline-editable table, compact header
"""

import os
from datetime import date

import jdatetime
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qjalalicalendarwidget import QJalaliCalendarWidget
from sqlalchemy.orm import Session

from models.party import PartyType
from models.sales import SalesInvoice
from services.party_service import PartyService
from services.printer_service import PrintService
from services.product_service import ProductService
from services.sales_service import SalesInvoiceService


# ─── دیالوگ جستجو ────────────────────────────────────────────────────────────
class SearchDialog(QDialog):
    item_selected = Signal(object)

    SEARCH_STYLESHEET = """
        QDialog { background-color: #FDF5F0; }
        QLineEdit {
            padding: 8px; border: 1px solid #CD853F; border-radius: 3px;
            font-size: 14px; background-color: #FFE4E1; color: #2d1b1b;
        }
        QListWidget {
            border: 1px solid #CD853F; border-radius: 3px;
            font-size: 14px; color: #2d1b1b; background-color: #FFF8F5;
            outline: none; padding: 4px;
        }
        QListWidget::item { padding: 10px; border-bottom: 1px solid #F0D0C0; color: #2d1b1b; }
        QListWidget::item:selected { background-color: #A0522D; color: white; }
        QListWidget::item:hover:!selected { background-color: #FFE4D6; }
        QPushButton {
            padding: 8px 18px; border-radius: 3px; font-weight: bold;
            background-color: #6B8E6B; color: white; border: 1px solid #5d4037;
        }
        QPushButton:hover { border: 1px solid white; }
        QPushButton#cancel_btn { background-color: #8B4513; }
    """

    def __init__(self, parent, items, search_fields=("name",), display_format=None):
        super().__init__(parent)
        self.all_items = items
        self.search_fields = search_fields
        self.display_format = display_format or (lambda x: x.name)
        self._filtered_items = []

        self.setWindowTitle("جستجو و انتخاب")
        self.setMinimumSize(520, 420)

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

        self._filter_items("")
        self.search_edit.setFocus()

    def _format_display(self, item) -> str:
        if hasattr(item, "numeric_code") and hasattr(item, "name"):
            stock = getattr(item, "stock_quantity", "")
            persian_stock = str(stock).translate(
                str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
            )
            return f"[{item.numeric_code}] {item.name} | موجودی: {persian_stock}"
        if hasattr(item, "name"):
            phone = getattr(item, "phone", "") or ""
            return f"{item.name}" + (f" | {phone}" if phone else "")
        return self.display_format(item)

    def _filter_items(self, query: str):
        self.list_widget.clear()
        q = query.strip().lower()
        self._filtered_items = []
        for item in self.all_items:
            if not q:
                self._filtered_items.append(item)
                continue
            for field in self.search_fields:
                if q in str(getattr(item, field, "") or "").lower():
                    self._filtered_items.append(item)
                    break
        for item in self._filtered_items:
            self.list_widget.addItem(self._format_display(item))

    def _select_current(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self._filtered_items):
            return
        self.item_selected.emit(self._filtered_items[row])
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._select_current()
        else:
            super().keyPressEvent(event)


# ─── ویجت اصلی فاکتور فروش ───────────────────────────────────────────────────
class SalesInvoiceWidget(QWidget):
    WIDGET_STYLESHEET = """
        QWidget {
            background-color: #A0522D;
        }

        QLabel#title {
            font-size: 22px;
            font-weight: bold;
            color: #592302;
            background: transparent;
            padding: 10px;
        }

        QLabel {
            color: #592302;
            font-size: 14px;
            font-weight: bold;
            background: transparent;
        }

        QLabel#info_lbl {
            color: #1a5c1a;
            font-weight: bold;
            font-size: 13px;
            background: transparent;
        }

        QLabel#total_lbl {
            font-size: 15px;
            font-weight: bold;
            color: #2d1b1b;
            background: transparent;
        }

        QLabel#final_lbl {
            font-size: 18px;
            font-weight: 800;
            color: #1a5c1a;
            background: transparent;
        }

        QLabel#date_value_lbl {
            font-size: 15px;
            font-weight: bold;
            color: #2d1b1b;
            background-color: #FFE4E1;
            border: 1px solid #CD853F;
            border-radius: 2px;
            padding: 4px 10px;
            min-height: 24px;
        }

        QLineEdit, QComboBox {
            background-color: #FFE4E1;
            border: 1px solid #CD853F;
            border-radius: 2px;
            padding: 4px 8px;
            color: #2d1b1b;
            font-size: 14px;
            min-height: 24px;
        }

        QLineEdit:disabled {
            background-color: #E8D5D0;
            color: #666;
        }

        QPushButton {
            color: white;
            border: 1px solid #5d4037;
            border-radius: 3px;
            padding: 5px 16px;
            font-size: 14px;
            font-weight: bold;
            min-width: 80px;
        }

        QPushButton#select_btn  { background-color: #7B68A0; }
        QPushButton#save_btn    { background-color: #6B8E6B; }
        QPushButton#print_btn   { background-color: #5B7FA0; }
        QPushButton#clear_btn   { background-color: #8B4513; }
        QPushButton#remove_btn  { background-color: #CD5C5C; min-width: 50px; padding: 2px 8px; }

        QPushButton:hover    { border: 1px solid white; }
        QPushButton:disabled { background-color: #8B7355; color: #ccc; }

        QGroupBox {
            border: 1px solid #CD853F;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            background-color: transparent;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top right;
            right: 15px;
            padding: 0 5px;
        }

        QTableWidget {
            background-color: white;
            border: 1px solid #CD853F;
            gridline-color: #DEB887;
            font-size: 14px;
            color: #2d1b1b;
        }

        QHeaderView::section {
            background-color: #D2B48C;
            color: #2d1b1b;
            padding: 6px;
            border: 1px solid #8B4513;
            font-weight: bold;
        }

        QTableWidget QLineEdit {
            border: 1px solid #A0522D;
            border-radius: 0px;
            background-color: #FFFACD;
            padding: 2px 4px;
            min-height: 0px;
        }

        QTextEdit {
            background-color: #FFE4E1;
            color: #2d1b1b;
            border: 1px solid #CD853F;
            border-radius: 2px;
            padding: 6px;
            font-size: 13px;
        }
    """

    # ستون‌های جدول
    COL_CODE = 0
    COL_NAME = 1
    COL_QTY = 2
    COL_PRICE = 3
    COL_TOTAL = 4
    COL_DEL = 5

    @staticmethod
    def _to_persian(text) -> str:
        return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

    @staticmethod
    def _to_english(text: str) -> str:
        return text.translate(
            str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
        )

    @staticmethod
    def _clean(text: str) -> float:
        return float(SalesInvoiceWidget._to_english(text).replace(",", "").strip() or 0)

    def _format_jdate(self, jdate: jdatetime.date) -> str:
        persian = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
        return f"{jdate.year}/{jdate.month:02d}/{jdate.day:02d}".translate(persian)

    def __init__(self, session: Session, db_manager):
        super().__init__()
        self.session = session
        self.db_manager = db_manager
        self.sales_service = SalesInvoiceService(session)
        self.product_service = ProductService(session)
        self.party_service = PartyService(session)
        self._selected_jdate = jdatetime.date.today()
        self.invoice_items: list[dict] = []
        self.current_customer = None
        self._current_invoice_id = None

        self.setStyleSheet(self.WIDGET_STYLESHEET)
        self._init_ui()

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # عنوان
        title = QLabel("فاکتور فروش")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # ─── هدر: مشتری | تاریخ | جستجوی کالا ───────────────────────────
        header_group = QGroupBox("اطلاعات فاکتور")
        header_row = QHBoxLayout()
        header_row.setContentsMargins(12, 10, 12, 10)
        header_row.setSpacing(10)

        # انتخاب مشتری
        self.customer_btn = QPushButton("انتخاب مشتری")
        self.customer_btn.setObjectName("select_btn")
        self.customer_btn.setMinimumHeight(36)
        self.customer_btn.clicked.connect(self._show_customer_dialog)
        header_row.addWidget(self.customer_btn)

        self.customer_label = QLabel("مشتری انتخاب نشده")
        self.customer_label.setObjectName("info_lbl")
        header_row.addWidget(self.customer_label, 3)

        # جداکننده
        sep1 = QLabel("|")
        sep1.setFixedWidth(10)
        header_row.addWidget(sep1)

        # تاریخ شمسی
        date_lbl = QLabel("تاریخ:")
        header_row.addWidget(date_lbl)
        self.date_btn = QPushButton(self._format_jdate(jdatetime.date.today()))
        self.date_btn.setObjectName("clear_btn")  # همرنگ با تم
        self.date_btn.setFixedWidth(130)
        self.date_btn.setMinimumHeight(36)
        self.date_btn.clicked.connect(self._show_date_picker)
        header_row.addWidget(self.date_btn)

        # جداکننده
        sep2 = QLabel("|")
        sep2.setFixedWidth(10)
        header_row.addWidget(sep2)

        # جستجوی کالا
        self.product_btn = QPushButton("جستجوی کالا")
        self.product_btn.setObjectName("select_btn")
        self.product_btn.setMinimumHeight(36)
        self.product_btn.clicked.connect(self._show_product_dialog)
        header_row.addWidget(self.product_btn)

        self.product_search_edit = QLineEdit()
        self.product_search_edit.setPlaceholderText("نام یا کد کالا...")
        self.product_search_edit.setFixedWidth(160)
        # Enter در فیلد جستجو مستقیم دیالوگ را باز می‌کند
        self.product_search_edit.returnPressed.connect(self._show_product_dialog)
        header_row.addWidget(self.product_search_edit)

        header_group.setLayout(header_row)
        layout.addWidget(header_group)

        # ─── جدول اقلام (قابل ویرایش) ───────────────────────────────────
        items_group = QGroupBox("اقلام فاکتور")
        items_layout = QVBoxLayout()
        items_layout.setContentsMargins(6, 6, 6, 6)
        items_layout.setSpacing(6)

        self.items_table = QTableWidget()
        self.items_table.setLayoutDirection(Qt.RightToLeft)
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(
            ["کد کالا", "نام کالا", "تعداد", "قیمت واحد", "جمع کل", ""]
        )

        hdr = self.items_table.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_CODE, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_NAME, QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.COL_QTY, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_PRICE, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_TOTAL, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_DEL, QHeaderView.ResizeToContents)

        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        # ویرایش مستقیم فقط از طریق widget های داخل سلول‌ها انجام می‌شود
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        items_layout.addWidget(self.items_table)

        # جمع / تخفیف / قابل پرداخت
        totals_row = QHBoxLayout()
        totals_row.addStretch()

        totals_row.addWidget(QLabel("جمع کل:"))
        self.total_label = QLabel("۰")
        self.total_label.setObjectName("total_lbl")
        totals_row.addWidget(self.total_label)

        totals_row.addWidget(QLabel("  تخفیف:"))
        self.discount_edit = QLineEdit("0")
        self.discount_edit.setFixedWidth(130)
        self.discount_edit.textChanged.connect(self._refresh_totals)
        totals_row.addWidget(self.discount_edit)

        totals_row.addWidget(QLabel("  قابل پرداخت:"))
        self.final_label = QLabel("۰")
        self.final_label.setObjectName("final_lbl")
        totals_row.addWidget(self.final_label)

        items_layout.addLayout(totals_row)
        items_group.setLayout(items_layout)
        layout.addWidget(items_group, stretch=1)

        # ─── توضیحات ─────────────────────────────────────────────────────
        notes_group = QGroupBox("توضیحات")
        notes_layout = QVBoxLayout()
        notes_layout.setContentsMargins(8, 6, 8, 8)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(70)
        self.notes_edit.setPlaceholderText("توضیحات اختیاری فاکتور...")
        notes_layout.addWidget(self.notes_edit)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # ─── دکمه‌های پایین ──────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self.save_btn = QPushButton("ثبت فاکتور")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self._save_invoice)

        self.print_btn = QPushButton("چاپ فاکتور")
        self.print_btn.setObjectName("print_btn")
        self.print_btn.setMinimumHeight(40)
        self.print_btn.clicked.connect(self._print_invoice)

        self.clear_btn = QPushButton("فاکتور جدید")
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self._clear_invoice)

        for btn in [self.save_btn, self.print_btn, self.clear_btn]:
            btn_row.addWidget(btn)

        layout.addLayout(btn_row)

        font_path = os.path.join(
            os.path.dirname(__file__), "..", "static", "fonts", "Arad-Regular.ttf"
        )
        self.print_service = PrintService(font_path=font_path)

    # ─── Dialogs ─────────────────────────────────────────────────────────────

    def _show_customer_dialog(self):
        try:
            customers = self.party_service.search_parties(party_type=PartyType.CUSTOMER)
        except AttributeError:
            customers = self.party_service.get_all_parties()

        if not customers:
            QMessageBox.warning(self, "خطا", "هیچ مشتری ثبت نشده است")
            return

        dlg = SearchDialog(self, customers, search_fields=("name", "phone"))
        dlg.item_selected.connect(self._on_customer_selected)
        dlg.exec()

    def _on_customer_selected(self, customer):
        self.current_customer = customer
        phone = customer.phone or ""
        self.customer_label.setText(
            f"{customer.name}" + (f" | {phone}" if phone else "")
        )

    def _show_product_dialog(self):
        products = self.product_service.get_all_products()
        if not products:
            QMessageBox.warning(self, "خطا", "هیچ کالایی ثبت نشده است")
            return

        dlg = SearchDialog(self, products, search_fields=("name", "numeric_code"))
        prefill = self.product_search_edit.text().strip()
        if prefill:
            dlg.search_edit.setText(prefill)
        dlg.item_selected.connect(self._on_product_selected)
        dlg.exec()

    def _on_product_selected(self, product):
        """افزودن کالا به جدول با تعداد پیش‌فرض ۵ و قیمت پیش‌فرض انبار"""
        default_qty = 5
        default_price = getattr(product, "default_price", 0) or 0

        self.invoice_items.append(
            {
                "product_id": product.id,
                "product_code": product.numeric_code,
                "product_name": product.name,
                "quantity": default_qty,
                "unit_price": default_price,
                "total": default_qty * default_price,
                "stock": product.stock_quantity,
            }
        )
        self.product_search_edit.clear()
        self._rebuild_table()

    # ─── جدول ────────────────────────────────────────────────────────────────

    def _rebuild_table(self):
        """ساخت مجدد جدول با widget های قابل ویرایش برای تعداد و قیمت"""
        self.items_table.setRowCount(0)

        for idx, item in enumerate(self.invoice_items):
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)

            # کد کالا
            self.items_table.setItem(
                row,
                self.COL_CODE,
                QTableWidgetItem(self._to_persian(item["product_code"])),
            )

            # نام کالا
            self.items_table.setItem(
                row, self.COL_NAME, QTableWidgetItem(item["product_name"])
            )

            # تعداد — QLineEdit قابل ویرایش
            qty_edit = QLineEdit(self._to_persian(item["quantity"]))
            qty_edit.setAlignment(Qt.AlignCenter)
            qty_edit.textChanged.connect(
                lambda text, i=idx: self._on_qty_changed(i, text)
            )
            self.items_table.setCellWidget(row, self.COL_QTY, qty_edit)

            # قیمت واحد — QLineEdit قابل ویرایش
            price_edit = QLineEdit(self._to_persian(f"{item['unit_price']:,.0f}"))
            price_edit.setAlignment(Qt.AlignCenter)
            price_edit.textChanged.connect(
                lambda text, i=idx: self._on_price_changed(i, text)
            )
            self.items_table.setCellWidget(row, self.COL_PRICE, price_edit)

            # جمع کل — فقط خواندنی
            total_item = QTableWidgetItem(self._to_persian(f"{item['total']:,.0f}"))
            total_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, self.COL_TOTAL, total_item)

            # دکمه حذف
            del_btn = QPushButton("×")
            del_btn.setObjectName("remove_btn")
            del_btn.clicked.connect(lambda _, i=idx: self._remove_item(i))
            self.items_table.setCellWidget(row, self.COL_DEL, del_btn)

        self._refresh_totals()

    def _on_qty_changed(self, idx: int, text: str):
        try:
            qty = int(self._to_english(text).replace(",", "").strip())
            if qty < 0:
                return  # تعداد منفی قبول نمی‌شود
        except ValueError:
            return

        self.invoice_items[idx]["quantity"] = qty
        self.invoice_items[idx]["total"] = qty * self.invoice_items[idx]["unit_price"]
        self._update_row_total(idx)
        self._refresh_totals()

    def _on_price_changed(self, idx: int, text: str):
        try:
            price = float(self._to_english(text).replace(",", "").strip())
            if price < 0:
                return
        except ValueError:
            return

        self.invoice_items[idx]["unit_price"] = price
        self.invoice_items[idx]["total"] = self.invoice_items[idx]["quantity"] * price
        self._update_row_total(idx)
        self._refresh_totals()

    def _update_row_total(self, idx: int):
        """بروزرسانی سلول جمع کل در همان ردیف بدون rebuild کامل"""
        total = self.invoice_items[idx]["total"]
        item = self.items_table.item(idx, self.COL_TOTAL)
        if item:
            item.setText(self._to_persian(f"{total:,.0f}"))

    def _remove_item(self, idx: int):
        self.invoice_items.pop(idx)
        self._rebuild_table()

    def _refresh_totals(self, *_):
        total = sum(i["total"] for i in self.invoice_items)
        discount = self._clean(self.discount_edit.text())
        final = max(0.0, total - discount)
        self.total_label.setText(self._to_persian(f"{total:,.0f}"))
        self.final_label.setText(self._to_persian(f"{final:,.0f}"))

    # ─── اقدامات ─────────────────────────────────────────────────────────────

    def _save_invoice(self):
        if not self.current_customer:
            QMessageBox.warning(self, "خطا", "لطفاً یک مشتری انتخاب کنید")
            return
        if not self.invoice_items:
            QMessageBox.warning(self, "خطا", "فاکتور خالی است")
            return

        # بررسی تعداد صفر
        zero_items = [
            i["product_name"] for i in self.invoice_items if i["quantity"] <= 0
        ]
        if zero_items:
            QMessageBox.warning(
                self,
                "خطا",
                f"تعداد کالاهای زیر صفر یا نامعتبر است:\n" + "\n".join(zero_items),
            )
            return

        try:
            discount = self._clean(self.discount_edit.text())
            notes = self.notes_edit.toPlainText().strip() or None

            if self._current_invoice_id:
                reply = QMessageBox.question(
                    self,
                    "تأیید ویرایش",
                    "با ویرایش این فاکتور، نسخه قبلی جایگزین می‌شود. ادامه می‌دهید؟",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return
                self.sales_service.delete_invoice(self._current_invoice_id)

            invoice = self.sales_service.create_invoice(
                customer_id=self.current_customer.id,
                items=self.invoice_items,
                discount=discount,
                notes=notes,
            )
            self._current_invoice_id = invoice.id

            QMessageBox.information(
                self,
                "ثبت موفق",
                f"فاکتور شماره {self._to_persian(invoice.invoice_number)} ثبت شد\n"
                f"قابل پرداخت: {self._to_persian(f'{invoice.final_total:,.0f}')} تومان",
            )

            main_window = self.window()
            if hasattr(main_window, "stock_changed"):
                main_window.stock_changed.emit()

        except ValueError as e:
            QMessageBox.warning(self, "خطای اعتبارسنجی", str(e))
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره فاکتور: {str(e)}")

    def _print_invoice(self):
        if not self._current_invoice_id:
            QMessageBox.warning(self, "خطا", "ابتدا فاکتور را ثبت کنید")
            return
        try:
            invoice = (
                self.session.query(SalesInvoice)
                .filter(SalesInvoice.id == self._current_invoice_id)
                .first()
            )
            if not invoice:
                QMessageBox.warning(self, "خطا", "فاکتور یافت نشد")
                return
            pdf_path = self.print_service.generate_invoice_pdf(
                invoice, invoice_type="sales"
            )
            self.print_service.open_pdf(pdf_path)
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در چاپ: {str(e)}")

    def _clear_invoice(self):
        self.current_customer = None
        self.invoice_items = []
        self._current_invoice_id = None

        self.customer_label.setText("مشتری انتخاب نشده")
        self.product_search_edit.clear()
        self.discount_edit.setText("0")
        self.notes_edit.clear()
        today = jdatetime.date.today()
        self.date_btn.setText(self._format_jdate(today))
        self._selected_jdate = today

        self._rebuild_table()
        self.product_search_edit.setFocus()

    def load_existing_invoice(self, invoice_id: int):
        try:
            invoice = (
                self.session.query(SalesInvoice)
                .filter(SalesInvoice.id == invoice_id)
                .first()
            )
            if not invoice:
                QMessageBox.warning(self, "خطا", "فاکتور مورد نظر یافت نشد")
                return

            self._clear_invoice()
            self._current_invoice_id = invoice.id

            customer = invoice.customer
            self.current_customer = customer
            phone = customer.phone or ""
            self.customer_label.setText(
                f"{customer.name}" + (f" | {phone}" if phone else "")
            )

            self.invoice_items = []
            for item in invoice.items:
                product = item.product
                self.invoice_items.append(
                    {
                        "product_id": product.id,
                        "product_code": product.numeric_code,
                        "product_name": product.name,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total": item.total_price,
                        "stock": product.stock_quantity,
                    }
                )

            self._rebuild_table()
            self.discount_edit.setText(str(int(invoice.discount)))
            self.notes_edit.setPlainText(invoice.notes or "")

            QMessageBox.information(
                self,
                "بارگذاری موفق",
                f"فاکتور شماره {invoice.invoice_number} بارگذاری شد.",
            )
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری: {str(e)}")

    def _show_date_picker(self):
        self._calendar = QJalaliCalendarWidget()
        self._calendar.setWindowTitle("انتخاب تاریخ")
        self._calendar.setDigitMode("fa")
        self._calendar.setThemeColors(
            selected_bg="#8B4513",
            selected_fg="#ffffff",
            today_bg="#FFE4E1",
            friday_fg="#CD5C5C",
        )
        self._calendar.setStyleSheet("""
            QComboBox {
                background-color: #8B4513;
                color: white;
                border: 1px solid #5d4037;
                border-radius: 3px;
                padding: 3px 8px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #FDF5F0;
                color: #2d1b1b;
                selection-background-color: #8B4513;
                selection-color: white;
                border: 1px solid #CD853F;
            }
        """)
        self._calendar.confirmed.connect(self._on_date_selected)

        self._calendar.adjustSize()
        parent_window = self.window()
        parent_geo = parent_window.geometry()
        cal_size = self._calendar.sizeHint()

        x = parent_geo.x() + (parent_geo.width() - cal_size.width()) // 2
        y = parent_geo.y() + (parent_geo.height() - cal_size.height()) // 2

        self._calendar.move(x, y)
        self._calendar.show()

    def _on_date_selected(self, selected_date):
        # selected_date یک jdatetime.date است
        persian = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
        label = f"{selected_date.year}/{selected_date.month:02d}/{selected_date.day:02d}".translate(
            persian
        )
        self.date_btn.setText(label)
        self._selected_jdate = selected_date  # برای ذخیره در دیتابیس
