"""
Reports Widget - Paginated, Editable & Printable
"""
import os
import subprocess
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QLineEdit, QComboBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QMessageBox,
                               QGroupBox, QHeaderView, QDateEdit, QFileDialog,
                               QCompleter, QSpinBox, QGridLayout)
from PySide6.QtCore import Qt, QDate, QStringListModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta

from models.product import Product, ProductCategory
from models.party import Party
from models.sales import SalesInvoice
from models.purchase import PurchaseInvoice

from services.party_service import PartyService
from services.product_service import ProductService
from services.printer_service import PrintService


class ReportsWidget(QWidget):
    PAGE_SIZE = 50

    WIDGET_STYLESHEET = """
        QLabel { color: #1e293b; font-size: 13px; background-color: transparent; }
        QLabel#title { font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
        QLabel#summary_lbl { font-size: 15px; font-weight: bold; color: #059669; padding: 8px 0; }
        QLabel#page_lbl { font-size: 13px; font-weight: bold; color: #475569; }

        QGroupBox {
            font-weight: bold; color: #334155; border: 1px solid #e2e8f0;
            border-radius: 8px; margin-top: 6px; padding: 12px 10px 8px 10px;
            background-color: #ffffff;
        }
        QGroupBox::title { subcontrol-origin: margin; right: 15px; padding: 0 8px; color: #1e293b; }

        QComboBox, QDateEdit, QLineEdit, QSpinBox {
            padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px;
            background-color: #f8fafc; color: #000000; font-size: 13px;
        }
        QComboBox:focus, QDateEdit:focus, QLineEdit:focus, QSpinBox:focus {
            border-color: #3b82f6; background-color: #ffffff;
        }

        QPushButton#run_btn { background-color: #3b82f6; font-weight: bold; }
        QPushButton#run_btn:hover { background-color: #2563eb; }
        QPushButton#export_btn { background-color: #10b981; }
        QPushButton#export_btn:hover { background-color: #059669; }
        QPushButton#print_btn { background-color: #64748b; }
        QPushButton#print_btn:hover { background-color: #475569; }
        QPushButton#nav_btn { background-color: #e2e8f0; color: #334155; min-width: 40px; }
        QPushButton#nav_btn:hover { background-color: #cbd5e1; }
        QPushButton#action_btn { 
            background-color: transparent; border: 1px solid #3b82f6; 
            color: #3b82f6; padding: 4px 10px; font-size: 12px; border-radius: 4px;
        }
        QPushButton#action_btn:hover { background-color: #eff6ff; }

        QTableWidget {
            border: 1px solid #e2e8f0; border-radius: 6px; gridline-color: #f1f5f9;
            selection-background-color: #dbeafe; selection-color: #1e293b;
            background-color: #ffffff; color: #000000; font-size: 13px;
        }
        QHeaderView::section {
            background-color: #f8fafc; color: #475569; padding: 10px;
            font-weight: bold; border: none; border-bottom: 2px solid #e2e8f0;
        }
    """

    @staticmethod
    def _pd(text) -> str:
        return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

    @staticmethod
    def _format_date(dt) -> str:
        if isinstance(dt, datetime):
            return ReportsWidget._pd(dt.strftime("%Y/%m/%d"))
        return str(dt)

    def __init__(self, session: Session, db_manager, print_service: PrintService = None):
        super().__init__()
        self.session = session
        self.db_manager = db_manager
        self.product_service = ProductService(session)
        self.party_service = PartyService(session)

        # ✅ سرویس چاپ
        font_path = os.path.join(os.path.dirname(__file__), "..", "static", "fonts", "Arad-Regular.ttf")
        self.print_service = print_service or PrintService(font_path=font_path)

        # ✅ داده‌های صفحه‌بندی
        self._all_rows: list[list[str]] = []       # تمام ردیف‌های نمایشی
        self._raw_data: list[dict] = []            # داده‌های خام (شامل ID فاکتور)
        self._current_page: int = 0
        self._total_pages: int = 0
        self._current_report_type: str = ""

        self.setStyleSheet(self.WIDGET_STYLESHEET)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(8)

        title = QLabel("گزارش‌ها")
        title.setObjectName("title")
        layout.addWidget(title)

        # ─── فیلترها ───
        self.filters_group = QGroupBox("تنظیمات گزارش")
        fl = QFormLayout()
        fl.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        fl.setSpacing(10)
        fl.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.report_type_combo = QComboBox()
        self.report_type_combo.addItem("گزارش موجودی کالا", "inventory")
        self.report_type_combo.addItem("گزارش فروش", "sales")
        self.report_type_combo.addItem("گزارش خرید", "purchase")
        self.report_type_combo.addItem("گزارش حساب شخص", "party")
        self.report_type_combo.currentIndexChanged.connect(self._on_report_type_changed)
        fl.addRow("نوع گزارش:", self.report_type_combo)

        # ایجاد یک افق‌چین (horizontal layout)

        # ایجاد یک ویجت کانتینر برای تاریخ
        self.date_container = QWidget()
        date_layout = QHBoxLayout(self.date_container)
        date_layout.setContentsMargins(0, 0, 0, 0)  # حذف حاشیه‌ها
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(self.end_date_edit)
        fl.addRow("بازه تاریخ:", self.date_container)

        # ایجاد افق‌چین برای فیلدهای شخص و کالا
        horizontal_layout = QHBoxLayout()

        # ساخت ویجت شخص
        self.party_filter_edit = QLineEdit()
        self.party_filter_edit.setPlaceholderText("نام شخص را وارد کنید...")
        self._party_completer_model = QStringListModel()
        self._party_completer = QCompleter(self._party_completer_model, self)
        self._party_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._party_completer.setFilterMode(Qt.MatchContains)
        self._party_completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.party_filter_edit.setCompleter(self._party_completer)

        # ساخت ویجت کالا
        self.product_filter_edit = QLineEdit()
        self.product_filter_edit.setPlaceholderText("نام یا کد کالا...")
        self._product_completer_model = QStringListModel()
        self._product_completer = QCompleter(self._product_completer_model, self)
        self._product_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._product_completer.setFilterMode(Qt.MatchContains)
        self._product_completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.product_filter_edit.setCompleter(self._product_completer)

        # اضافه کردن ویجت‌ها به افق‌چین
        horizontal_layout.addWidget(self.party_filter_edit)
        horizontal_layout.addWidget(self.product_filter_edit)

        # اضافه کردن به فرم اصلی با یک لیبل مشترک
        fl.addRow("جستجو:", horizontal_layout)

        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItem("همه دسته‌ها", None)
        self.category_filter_combo.addItem("پارچه", ProductCategory.FABRIC)
        self.category_filter_combo.addItem("شلوار", ProductCategory.PANTS)
        fl.addRow("دسته‌بندی:", self.category_filter_combo)

        self.filters_group.setLayout(fl)
        layout.addWidget(self.filters_group)

        # ─── دکمه‌ها + تنظیمات چاپ ───
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.run_report_btn = QPushButton("اجرای گزارش")
        self.run_report_btn.setObjectName("run_btn")
        self.run_report_btn.setMinimumHeight(40)
        self.run_report_btn.clicked.connect(self._run_report)
        btn_layout.addWidget(self.run_report_btn)

        self.export_btn = QPushButton("خروجی Excel")
        self.export_btn.setObjectName("export_btn")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.clicked.connect(self._export_report)
        btn_layout.addWidget(self.export_btn)

        # ✅ تنظیمات چاپ
        btn_layout.addSpacing(20)
        btn_layout.addWidget(QLabel("تعداد آیتم چاپ:"))
        self.print_count_spin = QSpinBox()
        self.print_count_spin.setRange(1, 10000)
        self.print_count_spin.setValue(100)
        self.print_count_spin.setFixedWidth(180)
        self.print_count_spin.setButtonSymbols(QSpinBox.NoButtons)  # حذف دکمه‌های up-down
        btn_layout.addWidget(self.print_count_spin)

        self.print_btn = QPushButton("چاپ")
        self.print_btn.setObjectName("print_btn")
        self.print_btn.setMinimumHeight(40)
        self.print_btn.clicked.connect(self._print_report)
        btn_layout.addWidget(self.print_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # ─── جدول نتایج ───
        results_group = QGroupBox("نتایج")
        rl = QVBoxLayout()
        rl.setContentsMargins(8, 8, 8, 8)

        self.results_table = QTableWidget()
        self.results_table.setLayoutDirection(Qt.RightToLeft)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        rl.addWidget(self.results_table)

        # ✅ نوار صفحه‌بندی
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(8)

        self.prev_page_btn = QPushButton("◀ قبلی")
        self.prev_page_btn.setObjectName("nav_btn")
        self.prev_page_btn.clicked.connect(lambda: self._go_to_page(self._current_page - 1))
        pagination_layout.addWidget(self.prev_page_btn)

        self.page_label = QLabel("")
        self.page_label.setObjectName("page_lbl")
        pagination_layout.addWidget(self.page_label)

        self.next_page_btn = QPushButton("بعدی ▶")
        self.next_page_btn.setObjectName("nav_btn")
        self.next_page_btn.clicked.connect(lambda: self._go_to_page(self._current_page + 1))
        pagination_layout.addWidget(self.next_page_btn)

        pagination_layout.addStretch()
        rl.addLayout(pagination_layout)

        self.summary_label = QLabel("")
        self.summary_label.setObjectName("summary_lbl")
        rl.addWidget(self.summary_label)

        results_group.setLayout(rl)
        layout.addWidget(results_group, stretch=1)

        self._on_report_type_changed(0)

    # ─── Pagination Logic ──────────────────────────────────────

    def _set_table_data(self, headers: list[str], rows: list[list[str]],
                        raw_data: list[dict] = None, summary: str = ""):
        """ذخیره داده‌ها و نمایش صفحه اول"""
        self._all_rows = rows
        self._raw_data = raw_data or []
        self._current_report_type = self.report_type_combo.currentData()
        self._current_page = 0
        self._total_pages = max(1, (len(rows) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

        # ذخیره هدرها برای استفاده در صفحه‌بندی
        self._headers = headers

        self._render_current_page()
        self.summary_label.setText(summary)

    def _render_current_page(self):
        """رندر صفحه فعلی جدول"""
        start = self._current_page * self.PAGE_SIZE
        end = min(start + self.PAGE_SIZE, len(self._all_rows))
        page_rows = self._all_rows[start:end]

        has_action = self._current_report_type in ('sales', 'purchase')

        if has_action:
            display_headers = self._headers + ["عملیات"]
        else:
            display_headers = self._headers

        self.results_table.setColumnCount(len(display_headers))
        self.results_table.setHorizontalHeaderLabels(display_headers)
        self.results_table.setRowCount(len(page_rows))

        for r, row_data in enumerate(page_rows):
            for c, text in enumerate(row_data):
                item = QTableWidgetItem(self._pd(text))
                if c >= 2:
                    item.setTextAlignment(Qt.AlignCenter)
                self.results_table.setItem(r, c, item)

            # ✅ دکمه عملیات برای گزارش‌های فاکتور
            if has_action and r < len(self._raw_data) - start:
                raw_idx = start + r
                invoice_id = self._raw_data[raw_idx].get('id')
                invoice_type = self._raw_data[raw_idx].get('type', self._current_report_type)

                btn = QPushButton("👁️ مشاهده / ویرایش")
                btn.setObjectName("action_btn")
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(lambda checked, iid=invoice_id, itype=invoice_type:
                                    self._open_invoice(iid, itype))
                self.results_table.setCellWidget(r, len(row_data), btn)

        # به‌روزرسانی وضعیت صفحه‌بندی
        self.page_label.setText(
            f"صفحه {self._pd(self._current_page + 1)} از {self._pd(self._total_pages)} "
            f"(نمایش {self._pd(start + 1)}-{self._pd(end)} از {self._pd(len(self._all_rows))})"
        )
        self.prev_page_btn.setEnabled(self._current_page > 0)
        self.next_page_btn.setEnabled(self._current_page < self._total_pages - 1)

    def _go_to_page(self, page: int):
        if 0 <= page < self._total_pages:
            self._current_page = page
            self._render_current_page()

    def _open_invoice(self, invoice_id: int, invoice_type: str):
        """هدایت به ویجت فاکتور برای مشاهده/ویرایش"""
        main_window = self.window()
        if hasattr(main_window, 'open_invoice_for_edit'):
            main_window.open_invoice_for_edit(invoice_id, invoice_type)
        else:
            QMessageBox.warning(self, "خطا", "قابلیت باز کردن فاکتور در دسترس نیست")

    # ─── Autocomplete & Filters ────────────────────────────────

    def _update_party_suggestions(self):
        try:
            parties = self.session.query(Party.name).all()
            self._party_completer_model.setStringList([p.name for p in parties])
        except Exception:
            self._party_completer_model.setStringList([])

    def _update_product_suggestions(self):
        try:
            products = self.session.query(Product.code, Product.name).all()
            self._product_completer_model.setStringList([f"[{p.code}] {p.name}" for p in products])
        except Exception:
            self._product_completer_model.setStringList([])

    def _on_report_type_changed(self, index):
        report_type = self.report_type_combo.currentData()
        visible = {
            'inventory': {'category': True, 'date': False, 'party': False, 'product': True},
            'sales': {'category': False, 'date': True, 'party': True, 'product': True},
            'purchase': {'category': False, 'date': True, 'party': True, 'product': True},
            'party': {'category': False, 'date': True, 'party': True, 'product': False},
        }
        v = visible.get(report_type, {})

        if v.get('party', False):
            self._update_party_suggestions()
        if v.get('product', False):
            self._update_product_suggestions()

        # مدیریت تاریخ (حالا با کانتینر)
        date_visible = v.get('date', False)
        self.date_container.setVisible(date_visible)
        # پیدا کردن و مخفی/نمایش لیبل تاریخ
        label_date = self.filters_group.layout().labelForField(self.date_container)
        if label_date:
            label_date.setVisible(date_visible)

        # مدیریت شخص
        party_visible = v.get('party', False)
        self.party_filter_edit.setVisible(party_visible)
        label_party = self.filters_group.layout().labelForField(self.party_filter_edit)
        if label_party:
            label_party.setVisible(party_visible)

        # مدیریت کالا
        product_visible = v.get('product', False)
        self.product_filter_edit.setVisible(product_visible)
        label_product = self.filters_group.layout().labelForField(self.product_filter_edit)
        if label_product:
            label_product.setVisible(product_visible)

        # مدیریت دسته‌بندی
        category_visible = v.get('category', False)
        self.category_filter_combo.setVisible(category_visible)
        label_category = self.filters_group.layout().labelForField(self.category_filter_combo)
        if label_category:
            label_category.setVisible(category_visible)
    # ─── Report Execution ──────────────────────────────────────

    def _run_report(self):
        report_type = self.report_type_combo.currentData()
        self.summary_label.setText("")
        try:
            if report_type == 'inventory':
                self._run_inventory_report()
            elif report_type == 'sales':
                self._run_sales_report()
            elif report_type == 'purchase':
                self._run_purchase_report()
            elif report_type == 'party':
                self._run_party_report()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در اجرای گزارش: {str(e)}")

    def _run_inventory_report(self):
        category = self.category_filter_combo.currentData()
        product_filter = self.product_filter_edit.text().strip().lower()

        query = self.session.query(Product)
        if category:
            query = query.filter(Product.category == category)
        if product_filter:
            query = query.filter(or_(
                Product.name.contains(product_filter),
                Product.code.contains(product_filter)
            ))

        products = query.all()
        headers = ["کد", "نام کالا", "دسته‌بندی", "زیردسته", "موجودی"]
        rows = []
        for p in products:
            rows.append([p.code, p.name, p.category.value, p.sub_category or "-", str(p.stock_quantity)])

        summary = f"تعداد کالا: {self._pd(len(products))}"
        self._set_table_data(headers, rows, summary=summary)

    def _run_sales_report(self):
        start = self.start_date_edit.date().toPython()
        end = self.end_date_edit.date().toPython() + timedelta(days=1)

        query = self.session.query(SalesInvoice).filter(
            SalesInvoice.created_at >= start, SalesInvoice.created_at < end
        )
        party_name = self.party_filter_edit.text().strip()
        if party_name:
            query = query.join(SalesInvoice.customer).filter(Party.name.contains(party_name))

        invoices = query.order_by(SalesInvoice.created_at.desc()).all()

        headers = ["شماره فاکتور", "مشتری", "تاریخ", "جمع کل", "تخفیف", "قابل پرداخت"]
        rows = []
        raw_data = []
        total = 0
        for inv in invoices:
            total += inv.final_total
            rows.append([
                inv.invoice_number, inv.customer.name,
                self._format_date(inv.created_at),
                f"{inv.total_price:,.0f}", f"{inv.discount:,.0f}", f"{inv.final_total:,.0f}"
            ])
            raw_data.append({'id': inv.id, 'type': 'sales'})

        summary = f"تعداد فاکتور: {self._pd(len(invoices))} | جمع فروش: {self._pd(f'{total:,.0f}')} تومان"
        self._set_table_data(headers, rows, raw_data=raw_data, summary=summary)

    def _run_purchase_report(self):
        start = self.start_date_edit.date().toPython()
        end = self.end_date_edit.date().toPython() + timedelta(days=1)

        query = self.session.query(PurchaseInvoice).filter(
            PurchaseInvoice.created_at >= start, PurchaseInvoice.created_at < end
        )
        party_name = self.party_filter_edit.text().strip()
        if party_name:
            query = query.join(PurchaseInvoice.supplier).filter(Party.name.contains(party_name))

        invoices = query.order_by(PurchaseInvoice.created_at.desc()).all()

        headers = ["شماره فاکتور", "فروشنده", "تاریخ", "جمع کل", "تخفیف", "قابل پرداخت"]
        rows = []
        raw_data = []
        total = 0
        for inv in invoices:
            total += inv.final_total
            rows.append([
                inv.invoice_number, inv.supplier.name,
                self._format_date(inv.created_at),
                f"{inv.total_price:,.0f}", f"{inv.discount:,.0f}", f"{inv.final_total:,.0f}"
            ])
            raw_data.append({'id': inv.id, 'type': 'purchase'})

        summary = f"تعداد فاکتور: {self._pd(len(invoices))} | جمع خرید: {self._pd(f'{total:,.0f}')} تومان"
        self._set_table_data(headers, rows, raw_data=raw_data, summary=summary)

    def _run_party_report(self):
        party_name = self.party_filter_edit.text().strip()
        if not party_name:
            QMessageBox.warning(self, "خطا", "لطفاً نام شخص را وارد کنید")
            return

        parties = self.party_service.search_parties(query=party_name)
        if not parties:
            QMessageBox.warning(self, "خطا", "شخصی با این نام یافت نشد")
            return

        party = parties[0]
        start = self.start_date_edit.date().toPython()
        end = self.end_date_edit.date().toPython() + timedelta(days=1)

        sales = self.session.query(SalesInvoice).filter(
            SalesInvoice.customer_id == party.id,
            SalesInvoice.created_at >= start, SalesInvoice.created_at < end
        ).all()

        purchases = self.session.query(PurchaseInvoice).filter(
            PurchaseInvoice.supplier_id == party.id,
            PurchaseInvoice.created_at >= start, PurchaseInvoice.created_at < end
        ).all()

        headers = ["نوع", "شماره فاکتور", "تاریخ", "مبلغ"]
        rows = []
        raw_data = []
        total_in = total_out = 0

        for inv in purchases:
            total_in += inv.final_total
            rows.append(["خرید", inv.invoice_number, self._format_date(inv.created_at), f"{inv.final_total:,.0f}"])
            raw_data.append({'id': inv.id, 'type': 'purchase'})
        for inv in sales:
            total_out += inv.final_total
            rows.append(["فروش", inv.invoice_number, self._format_date(inv.created_at), f"{inv.final_total:,.0f}"])
            raw_data.append({'id': inv.id, 'type': 'sales'})

        # مرتب‌سازی همزمان rows و raw_data بر اساس تاریخ
        combined = list(zip(rows, raw_data))
        combined.sort(key=lambda x: x[0][2], reverse=True)
        rows = [c[0] for c in combined]
        raw_data = [c[1] for c in combined]

        balance = total_in - total_out
        summary = (
            f"جمع خرید: {self._pd(f'{total_in:,.0f}')} | "
            f"جمع فروش: {self._pd(f'{total_out:,.0f}')} | "
            f"مانده: {self._pd(f'{balance:,.0f}')} تومان"
        )
        self._set_table_data(headers, rows, raw_data=raw_data, summary=summary)

    # ─── Export & Print ────────────────────────────────────────

    def _export_report(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره گزارش", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                headers = []
                for col in range(min(len(self._headers), self.results_table.columnCount())):
                    h = self.results_table.horizontalHeaderItem(col)
                    headers.append(h.text() if h else "")
                f.write(",".join(headers) + "\n")
                # ✅ خروجی از تمام داده‌ها، نه فقط صفحه فعلی
                for row_data in self._all_rows:
                    vals = [v.replace(",", "") for v in row_data]
                    f.write(",".join(vals) + "\n")
            QMessageBox.information(self, "موفق", "گزارش با موفقیت ذخیره شد")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره: {str(e)}")

    def _print_report(self):
        if not self._all_rows:
            QMessageBox.warning(self, "خطا", "ابتدا یک گزارش اجرا کنید")
            return

        count = self.print_count_spin.value()
        rows_to_print = self._all_rows[:count]

        try:
            title = self.report_type_combo.currentText()
            summary = self.summary_label.text()

            pdf_path = self.print_service.generate_report_pdf(
                headers=self._headers,
                rows=rows_to_print,
                title=title,
                summary=f"{summary} (چاپ {self._pd(len(rows_to_print))} مورد از {self._pd(len(self._all_rows))})"
            )

            self.print_service.open_pdf(pdf_path)

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در تولید PDF: {str(e)}")