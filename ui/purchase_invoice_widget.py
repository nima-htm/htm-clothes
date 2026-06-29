"""
Purchase Invoice Widget - همگام با تمام تغییرات فاکتور فروش
"""

import os

import jdatetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qjalalicalendarwidget import QJalaliCalendarWidget
from sqlalchemy.orm import Session

from models.party import PartyType
from services.party_service import PartyService
from services.printer_service import PrintService
from services.product_service import ProductService
from services.purchase_service import PurchaseInvoiceService
from ui.sales_invoice_widget import SearchDialog


class PurchaseInvoiceWidget(QWidget):
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

        QLabel#supplier_lbl {
            color: #1a3a6b;
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
        return float(
            PurchaseInvoiceWidget._to_english(text).replace(",", "").strip() or 0
        )

    def _format_jdate(self, jdate: jdatetime.date) -> str:
        persian = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
        return f"{jdate.year}/{jdate.month:02d}/{jdate.day:02d}".translate(persian)

    def __init__(self, session: Session, db_manager):
        super().__init__()
        self.session = session
        self.db_manager = db_manager
        self.purchase_service = PurchaseInvoiceService(session)
        self.product_service = ProductService(session)
        self.party_service = PartyService(session)

        self.invoice_items: list[dict] = []
        self.current_supplier = None
        self._current_invoice_id = None
        self._selected_jdate = jdatetime.date.today()

        self.setStyleSheet(self.WIDGET_STYLESHEET)
        self._init_ui()

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("فاکتور خرید")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # ─── هدر: تامین‌کننده | تاریخ | جستجوی کالا ─────────────────────
        header_group = QGroupBox("اطلاعات فاکتور")
        header_row = QHBoxLayout()
        header_row.setContentsMargins(12, 10, 12, 10)
        header_row.setSpacing(10)

        # انتخاب تامین‌کننده
        self.supplier_btn = QPushButton("انتخاب تامین‌کننده")
        self.supplier_btn.setObjectName("select_btn")
        self.supplier_btn.setMinimumHeight(36)
        self.supplier_btn.clicked.connect(self._show_supplier_dialog)
        header_row.addWidget(self.supplier_btn)

        self.supplier_label = QLabel("تامین‌کننده انتخاب نشده")
        self.supplier_label.setObjectName("supplier_lbl")
        header_row.addWidget(self.supplier_label, 3)

        sep1 = QLabel("|")
        sep1.setFixedWidth(10)
        header_row.addWidget(sep1)

        # تاریخ شمسی
        date_lbl = QLabel("تاریخ:")
        header_row.addWidget(date_lbl)

        self.date_btn = QPushButton(self._format_jdate(jdatetime.date.today()))
        self.date_btn.setObjectName("clear_btn")
        self.date_btn.setFixedWidth(130)
        self.date_btn.setMinimumHeight(36)
        self.date_btn.clicked.connect(self._show_date_picker)
        header_row.addWidget(self.date_btn)

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

    # ─── Date Picker ─────────────────────────────────────────────────────────

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
            QComboBox::drop-down { border: none; }
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
        parent_geo = self.window().geometry()
        cal_size = self._calendar.sizeHint()
        x = parent_geo.x() + (parent_geo.width() - cal_size.width()) // 2
        y = parent_geo.y() + (parent_geo.height() - cal_size.height()) // 2
        self._calendar.move(x, y)
        self._calendar.show()

    def _on_date_selected(self, selected_date: jdatetime.date):
        self._selected_jdate = selected_date
        self.date_btn.setText(self._format_jdate(selected_date))

    # ─── Dialogs ─────────────────────────────────────────────────────────────

    def _show_supplier_dialog(self):
        try:
            suppliers = self.party_service.search_parties(party_type=PartyType.SUPPLIER)
        except AttributeError:
            suppliers = self.party_service.get_all_parties()

        if not suppliers:
            QMessageBox.warning(self, "خطا", "هیچ تامین‌کننده‌ای ثبت نشده است")
            return

        dlg = SearchDialog(self, suppliers, search_fields=("name", "phone"))
        dlg.item_selected.connect(self._on_supplier_selected)
        dlg.exec()

    def _on_supplier_selected(self, supplier):
        self.current_supplier = supplier
        phone = supplier.phone or ""
        self.supplier_label.setText(
            f"{supplier.name}" + (f" | {phone}" if phone else "")
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
        """افزودن کالا با تعداد پیش‌فرض ۵ و قیمت خرید پیش‌فرض"""
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
        self.items_table.setRowCount(0)

        for idx, item in enumerate(self.invoice_items):
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)

            self.items_table.setItem(
                row,
                self.COL_CODE,
                QTableWidgetItem(self._to_persian(item["product_code"])),
            )

            self.items_table.setItem(
                row, self.COL_NAME, QTableWidgetItem(item["product_name"])
            )

            qty_edit = QLineEdit(self._to_persian(item["quantity"]))
            qty_edit.setAlignment(Qt.AlignCenter)
            qty_edit.textChanged.connect(
                lambda text, i=idx: self._on_qty_changed(i, text)
            )
            self.items_table.setCellWidget(row, self.COL_QTY, qty_edit)

            price_edit = QLineEdit(self._to_persian(f"{item['unit_price']:,.0f}"))
            price_edit.setAlignment(Qt.AlignCenter)
            price_edit.textChanged.connect(
                lambda text, i=idx: self._on_price_changed(i, text)
            )
            self.items_table.setCellWidget(row, self.COL_PRICE, price_edit)

            total_item = QTableWidgetItem(self._to_persian(f"{item['total']:,.0f}"))
            total_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, self.COL_TOTAL, total_item)

            del_btn = QPushButton("×")
            del_btn.setObjectName("remove_btn")
            del_btn.clicked.connect(lambda _, i=idx: self._remove_item(i))
            self.items_table.setCellWidget(row, self.COL_DEL, del_btn)

        self._refresh_totals()

    def _on_qty_changed(self, idx: int, text: str):
        try:
            qty = int(self._to_english(text).replace(",", "").strip())
            if qty < 0:
                return
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
        if not self.current_supplier:
            QMessageBox.warning(self, "خطا", "لطفاً یک تامین‌کننده انتخاب کنید")
            return
        if not self.invoice_items:
            QMessageBox.warning(self, "خطا", "فاکتور خالی است")
            return

        zero_items = [
            i["product_name"] for i in self.invoice_items if i["quantity"] <= 0
        ]
        if zero_items:
            QMessageBox.warning(
                self,
                "خطا",
                "تعداد کالاهای زیر صفر یا نامعتبر است:\n" + "\n".join(zero_items),
            )
            return

        try:
            discount = self._clean(self.discount_edit.text())
            notes = self.notes_edit.toPlainText().strip() or None
            is_editing = self._current_invoice_id is not None

            if is_editing:
                reply = QMessageBox.question(
                    self,
                    "تأیید ویرایش",
                    "با ویرایش این فاکتور، نسخه قبلی جایگزین می‌شود. ادامه می‌دهید؟",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return
                self.purchase_service.delete_invoice(self._current_invoice_id)

            invoice = self.purchase_service.create_invoice(
                supplier_id=self.current_supplier.id,
                items=self.invoice_items,
                discount=discount,
                notes=notes,
            )
            self._current_invoice_id = invoice.id

            QMessageBox.information(
                self,
                "موفق",
                f"فاکتور خرید با موفقیت {'ویرایش' if is_editing else 'ثبت'} شد\n\n"
                f"شماره فاکتور: {self._to_persian(invoice.invoice_number)}\n"
                f"مبلغ کل: {self._to_persian(f'{invoice.final_total:,.0f}')} تومان",
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
            from models.purchase import PurchaseInvoice

            invoice = (
                self.session.query(PurchaseInvoice)
                .filter(PurchaseInvoice.id == self._current_invoice_id)
                .first()
            )
            if not invoice:
                QMessageBox.warning(self, "خطا", "فاکتور یافت نشد")
                return
            pdf_path = self.print_service.generate_invoice_pdf(
                invoice, invoice_type="purchase"
            )
            self.print_service.open_pdf(pdf_path)
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در چاپ: {str(e)}")

    def _clear_invoice(self):
        self.current_supplier = None
        self.invoice_items = []
        self._current_invoice_id = None

        self.supplier_label.setText("تامین‌کننده انتخاب نشده")
        self.product_search_edit.clear()
        self.discount_edit.setText("0")
        self.notes_edit.clear()

        today = jdatetime.date.today()
        self._selected_jdate = today
        self.date_btn.setText(self._format_jdate(today))

        self._rebuild_table()
        self.product_search_edit.setFocus()

    def load_existing_invoice(self, invoice_id: int):
        try:
            from models.purchase import PurchaseInvoice

            invoice = (
                self.session.query(PurchaseInvoice)
                .filter(PurchaseInvoice.id == invoice_id)
                .first()
            )
            if not invoice:
                QMessageBox.warning(self, "خطا", "فاکتور خرید مورد نظر یافت نشد")
                return

            self._clear_invoice()
            self._current_invoice_id = invoice.id

            supplier = invoice.supplier
            self.current_supplier = supplier
            phone = supplier.phone or ""
            self.supplier_label.setText(
                f"{supplier.name}" + (f" | {phone}" if phone else "")
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
                f"فاکتور خرید شماره {invoice.invoice_number} بارگذاری شد.",
            )
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری: {str(e)}")
