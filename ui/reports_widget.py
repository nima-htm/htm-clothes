"""
Reports Widget - Paginated, Editable & Printable
Updated: Persian calendar, new theme (matching ProductWidget), clear form button,
         synced with new Product/Sales/Purchase models
"""
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QLineEdit, QComboBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QMessageBox,
                               QGroupBox, QHeaderView, QFileDialog,
                               QCompleter, QSpinBox)
from PySide6.QtCore import Qt, QStringListModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta, date

from models.product import Product, ProductCategory
from models.party import Party
from models.sales import SalesInvoice
from models.purchase import PurchaseInvoice

from services.party_service import PartyService
from services.product_service import ProductService
from services.printer_service import PrintService

try:
    from persiantools.jdatetime import JalaliDate
    HAS_PERSIAN_CALENDAR = True
except ImportError:
    HAS_PERSIAN_CALENDAR = False

# ─── Persian Date Edit Widget ───────────────────────────────────────────────

class PersianDateEdit(QLineEdit):
    """
    ورودی تاریخ شمسی ساده.
    فرمت: YYYY/MM/DD  (مثلاً ۱۴۰۳/۰۱/۰۱)
    اگر کتابخانه persiantools نصب نباشد، تاریخ میلادی نمایش می‌دهد.
    """

    _PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    _ENGLISH_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

    def __init__(self, initial: date = None, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("YYYY/MM/DD")
        self.setMaxLength(10)
        self.setFixedWidth(130)
        d = initial or date.today()
        self.set_date(d)

    # ──────────────────────────────────
    def set_date(self, d: date):
        if HAS_PERSIAN_CALENDAR:
            jd = JalaliDate(d)
            text = f"{jd.year}/{jd.month:02d}/{jd.day:02d}"
        else:
            text = d.strftime("%Y/%m/%d")
        self.setText(text.translate(self._PERSIAN_DIGITS))

    def get_date(self) -> date:
        raw = self.text().translate(self._ENGLISH_DIGITS).strip()
        try:
            y, m, d = map(int, raw.split("/"))
            if HAS_PERSIAN_CALENDAR:
                return JalaliDate(y, m, d).to_gregorian()
            else:
                return date(y, m, d)
        except Exception:
            return date.today()


# ─── Reports Widget ──────────────────────────────────────────────────────────

class ReportsWidget(QWidget):
    PAGE_SIZE = 50

    # ✅ تم هماهنگ با ProductWidget (قهوه‌ای گرم)
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

        QLabel#summary_lbl {
            font-size: 14px;
            font-weight: bold;
            color: #FFFFFF;
            background: transparent;
            padding: 6px 0;
        }

        QLabel#page_lbl {
            font-size: 13px;
            font-weight: bold;
            color: #FFFFFF;
            background: transparent;
        }

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

        QLineEdit, QComboBox, QSpinBox {
            background-color: #FFE4E1;
            border: 1px solid #CD853F;
            border-radius: 2px;
            padding: 4px 8px;
            color: #2d1b1b;
            font-size: 14px;
            min-height: 24px;
        }

        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
            border: 1px solid #DAA520;
            background-color: #FFF8DC;
        }

        QLineEdit:disabled {
            background-color: #E8D5D0;
            color: #666;
        }

        QComboBox::drop-down {
            border: none;
            width: 20px;
        }

        QComboBox QAbstractItemView {
            background-color: #FFE4E1;
            color: #2d1b1b;
            selection-background-color: #D2691E;
        }

        QPushButton {
            color: white;
            border: 1px solid #5d4037;
            border-radius: 3px;
            padding: 5px 20px;
            font-size: 14px;
            font-weight: bold;
            min-width: 80px;
        }

        QPushButton#run_btn    { background-color: #6B8E6B; }
        QPushButton#export_btn { background-color: #5B7FA6; }
        QPushButton#print_btn  { background-color: #7A6B5A; }
        QPushButton#clear_btn  { background-color: #8B4513; }
        QPushButton#nav_btn    {
            background-color: #8B4513;
            min-width: 40px;
            padding: 4px 12px;
        }
        QPushButton#action_btn {
            background-color: transparent;
            border: 1px solid #CD853F;
            color: #332a29;
            padding: 3px 10px;
            font-size: 12px;
            min-width: 0;
        }

        QPushButton:hover { border: 1px solid white; }

        QPushButton:disabled {
            background-color: #8B7355;
            color: #ccc;
        }

        QTableWidget {
            background-color: white;
            border: 1px solid #CD853F;
            gridline-color: #DEB887;
            font-size: 13px;
            color: #000000;
        }

        QHeaderView::section {
            background-color: #D2B48C;
            color: #2d1b1b;
            padding: 6px;
            border: 1px solid #8B4513;
            font-weight: bold;
        }

        QTableWidget::item:selected {
            background-color: #D2691E;
            color: white;
        }
    """

    # ──────────────────────────────────────────────────────────────
    # helpers
    # ──────────────────────────────────────────────────────────────
    @staticmethod
    def _pd(text) -> str:
        return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

    @staticmethod
    def _format_date(dt) -> str:
        if not isinstance(dt, datetime):
            return str(dt)
        if HAS_PERSIAN_CALENDAR:
            jd = JalaliDate(dt.date())
            return ReportsWidget._pd(f"{jd.year}/{jd.month:02d}/{jd.day:02d}")
        return ReportsWidget._pd(dt.strftime("%Y/%m/%d"))

    # ──────────────────────────────────────────────────────────────
    # init
    # ──────────────────────────────────────────────────────────────
    def __init__(self, session: Session, db_manager, print_service: PrintService = None):
        super().__init__()
        self.session = session
        self.db_manager = db_manager
        self.product_service = ProductService(session)
        self.party_service = PartyService(session)

        font_path = os.path.join(
            os.path.dirname(__file__), "..", "static", "fonts", "Arad-Regular.ttf"
        )
        self.print_service = print_service or PrintService(font_path=font_path)

        self._all_rows: list[list[str]] = []
        self._raw_data: list[dict] = []
        self._headers: list[str] = []
        self._current_page: int = 0
        self._total_pages: int = 0
        self._current_report_type: str = ""

        self.setStyleSheet(self.WIDGET_STYLESHEET)
        self._init_ui()

    # ──────────────────────────────────────────────────────────────
    # UI build
    # ──────────────────────────────────────────────────────────────
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("گزارش‌ها")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # ─── فیلترها ───
        filters_group = QGroupBox("تنظیمات گزارش")
        fl = QFormLayout()
        fl.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        fl.setSpacing(10)
        fl.setContentsMargins(15, 10, 15, 15)
        fl.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # نوع گزارش
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItem("گزارش موجودی کالا", "inventory")
        self.report_type_combo.addItem("گزارش فروش", "sales")
        self.report_type_combo.addItem("گزارش خرید", "purchase")
        self.report_type_combo.addItem("گزارش حساب شخص", "party")
        self.report_type_combo.currentIndexChanged.connect(self._on_report_type_changed)
        fl.addRow("نوع گزارش:", self.report_type_combo)

        # ✅ تاریخ — با PersianDateEdit
        self.date_container = QWidget()
        date_layout = QHBoxLayout(self.date_container)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(8)
        self.start_date_edit = PersianDateEdit(
            initial=date.today() - timedelta(days=30)
        )
        self.end_date_edit = PersianDateEdit(initial=date.today())
        lbl_to = QLabel("تا")
        lbl_to.setFixedWidth(16)
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(lbl_to)
        date_layout.addWidget(self.end_date_edit)
        date_layout.addStretch()
        fl.addRow("بازه تاریخ:", self.date_container)

        # جستجو — شخص و کالا کنار هم
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)

        self.party_filter_edit = QLineEdit()
        self.party_filter_edit.setPlaceholderText("نام شخص...")
        self._party_completer_model = QStringListModel()
        self._party_completer = QCompleter(self._party_completer_model, self)
        self._party_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._party_completer.setFilterMode(Qt.MatchContains)
        self.party_filter_edit.setCompleter(self._party_completer)

        self.product_filter_edit = QLineEdit()
        self.product_filter_edit.setPlaceholderText("نام یا کد کالا...")
        self._product_completer_model = QStringListModel()
        self._product_completer = QCompleter(self._product_completer_model, self)
        self._product_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._product_completer.setFilterMode(Qt.MatchContains)
        self.product_filter_edit.setCompleter(self._product_completer)

        search_layout.addWidget(self.party_filter_edit)
        search_layout.addWidget(self.product_filter_edit)
        fl.addRow("جستجو:", search_container)

        # دسته‌بندی
        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItem("همه دسته‌ها", None)
        self.category_filter_combo.addItem("پارچه", ProductCategory.FABRIC)
        self.category_filter_combo.addItem("شلوار", ProductCategory.PANTS)
        self.category_filter_combo.addItem("کاپشن", ProductCategory.JACKET)
        fl.addRow("دسته‌بندی:", self.category_filter_combo)

        filters_group.setLayout(fl)
        self.filters_group = filters_group
        layout.addWidget(filters_group)

        # ─── دکمه‌ها ───
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.run_report_btn = QPushButton("اجرای گزارش")
        self.run_report_btn.setObjectName("run_btn")
        self.run_report_btn.clicked.connect(self._run_report)
        btn_layout.addWidget(self.run_report_btn)

        # ✅ دکمه پاک کردن فرم
        self.clear_btn = QPushButton("پاک کردن")
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.clicked.connect(self._clear_form)
        btn_layout.addWidget(self.clear_btn)

        self.export_btn = QPushButton("خروجی Excel")
        self.export_btn.setObjectName("export_btn")
        self.export_btn.clicked.connect(self._export_report)
        btn_layout.addWidget(self.export_btn)

        btn_layout.addSpacing(10)
        count_lbl = QLabel("تعداد چاپ:")
        count_lbl.setFixedWidth(80)
        btn_layout.addWidget(count_lbl)
        self.print_count_spin = QSpinBox()
        self.print_count_spin.setRange(1, 10000)
        self.print_count_spin.setValue(100)
        self.print_count_spin.setFixedWidth(100)
        self.print_count_spin.setButtonSymbols(QSpinBox.NoButtons)
        btn_layout.addWidget(self.print_count_spin)

        self.print_btn = QPushButton("چاپ")
        self.print_btn.setObjectName("print_btn")
        self.print_btn.clicked.connect(self._print_report)
        btn_layout.addWidget(self.print_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # ─── جدول نتایج ───
        results_group = QGroupBox("نتایج")
        rl = QVBoxLayout()
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(6)

        self.results_table = QTableWidget()
        self.results_table.setLayoutDirection(Qt.RightToLeft)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        rl.addWidget(self.results_table)

        # صفحه‌بندی
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

    # ──────────────────────────────────────────────────────────────
    # Pagination
    # ──────────────────────────────────────────────────────────────
    def _set_table_data(self, headers: list[str], rows: list[list[str]],
                        raw_data: list[dict] = None, summary: str = ""):
        self._all_rows = rows
        self._raw_data = raw_data or []
        self._headers = headers
        self._current_report_type = self.report_type_combo.currentData()
        self._current_page = 0
        self._total_pages = max(1, (len(rows) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self._render_current_page()
        self.summary_label.setText(summary)

    def _render_current_page(self):
        start = self._current_page * self.PAGE_SIZE
        end = min(start + self.PAGE_SIZE, len(self._all_rows))
        page_rows = self._all_rows[start:end]

        has_action = self._current_report_type in ('sales', 'purchase', 'party')

        display_headers = self._headers + (["عملیات"] if has_action else [])
        self.results_table.setColumnCount(len(display_headers))
        self.results_table.setHorizontalHeaderLabels(display_headers)
        self.results_table.setRowCount(len(page_rows))

        for r, row_data in enumerate(page_rows):
            for c, text in enumerate(row_data):
                item = QTableWidgetItem(self._pd(str(text)))
                if c >= 2:
                    item.setTextAlignment(Qt.AlignCenter)
                self.results_table.setItem(r, c, item)

            if has_action:
                raw_idx = start + r
                if raw_idx < len(self._raw_data):
                    invoice_id = self._raw_data[raw_idx].get('id')
                    invoice_type = self._raw_data[raw_idx].get('type', self._current_report_type)
                    btn = QPushButton("👁 مشاهده / ویرایش")
                    btn.setObjectName("action_btn")
                    btn.setCursor(Qt.PointingHandCursor)
                    btn.clicked.connect(
                        lambda checked, iid=invoice_id, itype=invoice_type:
                        self._open_invoice(iid, itype)
                    )
                    self.results_table.setCellWidget(r, len(row_data), btn)

        total = len(self._all_rows)
        if total == 0:
            self.page_label.setText("نتیجه‌ای یافت نشد")
        else:
            self.page_label.setText(
                f"صفحه {self._pd(self._current_page + 1)} از {self._pd(self._total_pages)} "
                f"({self._pd(start + 1)}–{self._pd(end)} از {self._pd(total)})"
            )
        self.prev_page_btn.setEnabled(self._current_page > 0)
        self.next_page_btn.setEnabled(self._current_page < self._total_pages - 1)

    def _go_to_page(self, page: int):
        if 0 <= page < self._total_pages:
            self._current_page = page
            self._render_current_page()

    def _open_invoice(self, invoice_id: int, invoice_type: str):
        main_window = self.window()
        if hasattr(main_window, 'open_invoice_for_edit'):
            main_window.open_invoice_for_edit(invoice_id, invoice_type)
        else:
            QMessageBox.warning(self, "خطا", "قابلیت باز کردن فاکتور در دسترس نیست")

    # ──────────────────────────────────────────────────────────────
    # Autocomplete & visibility
    # ──────────────────────────────────────────────────────────────
    def _update_party_suggestions(self):
        try:
            parties = self.session.query(Party.name).all()
            self._party_completer_model.setStringList([p.name for p in parties])
        except Exception:
            self._party_completer_model.setStringList([])

    def _update_product_suggestions(self):
        try:
            # ✅ مدل جدید از numeric_code استفاده می‌کند
            products = self.session.query(Product.numeric_code, Product.name).all()
            self._product_completer_model.setStringList(
                [f"[{p.numeric_code}] {p.name}" for p in products]
            )
        except Exception:
            self._product_completer_model.setStringList([])

    def _on_report_type_changed(self, index):
        report_type = self.report_type_combo.currentData()
        visible = {
            'inventory': {'category': True,  'date': False, 'party': False, 'product': True},
            'sales':     {'category': False, 'date': True,  'party': True,  'product': True},
            'purchase':  {'category': False, 'date': True,  'party': True,  'product': True},
            'party':     {'category': False, 'date': True,  'party': True,  'product': False},
        }
        v = visible.get(report_type, {})

        if v.get('party'):
            self._update_party_suggestions()
        if v.get('product'):
            self._update_product_suggestions()

        fl = self.filters_group.layout()

        def _set_row_visible(widget, show: bool):
            widget.setVisible(show)
            lbl = fl.labelForField(widget)
            if lbl:
                lbl.setVisible(show)

        _set_row_visible(self.date_container,         v.get('date', False))
        _set_row_visible(self.party_filter_edit,      v.get('party', False))
        _set_row_visible(self.product_filter_edit,    v.get('product', False))
        _set_row_visible(self.category_filter_combo,  v.get('category', False))

    # ──────────────────────────────────────────────────────────────
    # Clear form  ✅ جدید
    # ──────────────────────────────────────────────────────────────
    def _clear_form(self):
        self.report_type_combo.setCurrentIndex(0)
        self.party_filter_edit.clear()
        self.product_filter_edit.clear()
        self.category_filter_combo.setCurrentIndex(0)
        self.start_date_edit.set_date(date.today() - timedelta(days=30))
        self.end_date_edit.set_date(date.today())

        # پاک کردن جدول
        self._all_rows = []
        self._raw_data = []
        self._headers = []
        self._current_page = 0
        self._total_pages = 0
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        self.summary_label.setText("")
        self.page_label.setText("")
        self.prev_page_btn.setEnabled(False)
        self.next_page_btn.setEnabled(False)

    # ──────────────────────────────────────────────────────────────
    # Report runners
    # ──────────────────────────────────────────────────────────────
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
        """
        ✅ هماهنگ با مدل جدید Product:
        - numeric_code به جای code برای نمایش کد عددی
        - stock_source و unit از مدل جدید
        - sub_category حذف شده (در مدل جدید وجود ندارد)
        """
        category = self.category_filter_combo.currentData()
        product_filter = self.product_filter_edit.text().strip().lower()

        query = self.session.query(Product)
        if category:
            query = query.filter(Product.category == category)
        if product_filter:
            query = query.filter(or_(
                Product.name.ilike(f"%{product_filter}%"),
                Product.numeric_code.ilike(f"%{product_filter}%"),
                Product.code.ilike(f"%{product_filter}%"),
            ))

        products = query.order_by(Product.numeric_code).all()

        headers = ["کد", "نام کالا", "دسته‌بندی", "واحد", "موجودی", "قیمت پایه", "منبع"]
        rows = []
        for p in products:
            rows.append([
                p.numeric_code,
                p.name,
                p.category.value,
                p.unit.value,
                str(p.stock_quantity),
                f"{p.default_price:,.0f}",
                p.stock_source.value,
            ])

        summary = f"تعداد کالا: {self._pd(len(products))}"
        self._set_table_data(headers, rows, summary=summary)

    def _run_sales_report(self):
        start = self.start_date_edit.get_date()
        end = self.end_date_edit.get_date() + timedelta(days=1)

        query = self.session.query(SalesInvoice).filter(
            SalesInvoice.created_at >= datetime.combine(start, datetime.min.time()),
            SalesInvoice.created_at <  datetime.combine(end,   datetime.min.time()),
        )

        party_name = self.party_filter_edit.text().strip()
        if party_name:
            query = query.join(SalesInvoice.customer).filter(
                Party.name.ilike(f"%{party_name}%")
            )

        product_filter = self.product_filter_edit.text().strip()
        if product_filter:
            # فیلتر روی آیتم‌های فاکتور
            from models.sales import SalesInvoiceItem
            query = query.join(SalesInvoice.items).join(SalesInvoiceItem.product).filter(
                or_(
                    Product.name.ilike(f"%{product_filter}%"),
                    Product.numeric_code.ilike(f"%{product_filter}%"),
                )
            ).distinct()

        invoices = query.order_by(SalesInvoice.created_at.desc()).all()

        headers = ["شماره فاکتور", "مشتری", "تاریخ", "جمع کل", "تخفیف", "قابل پرداخت"]
        rows, raw_data = [], []
        total = 0
        for inv in invoices:
            total += inv.final_total
            rows.append([
                inv.invoice_number,
                inv.customer.name,
                self._format_date(inv.created_at),
                f"{inv.total_price:,.0f}",
                f"{inv.discount:,.0f}",
                f"{inv.final_total:,.0f}",
            ])
            raw_data.append({'id': inv.id, 'type': 'sales'})

        summary = (
            f"تعداد فاکتور: {self._pd(len(invoices))} | "
            f"جمع فروش: {self._pd(f'{total:,.0f}')} ریال"
        )
        self._set_table_data(headers, rows, raw_data=raw_data, summary=summary)

    def _run_purchase_report(self):
        start = self.start_date_edit.get_date()
        end = self.end_date_edit.get_date() + timedelta(days=1)

        query = self.session.query(PurchaseInvoice).filter(
            PurchaseInvoice.created_at >= datetime.combine(start, datetime.min.time()),
            PurchaseInvoice.created_at <  datetime.combine(end,   datetime.min.time()),
        )

        party_name = self.party_filter_edit.text().strip()
        if party_name:
            query = query.join(PurchaseInvoice.supplier).filter(
                Party.name.ilike(f"%{party_name}%")
            )

        product_filter = self.product_filter_edit.text().strip()
        if product_filter:
            from models.purchase import PurchaseInvoiceItem
            query = query.join(PurchaseInvoice.items).join(PurchaseInvoiceItem.product).filter(
                or_(
                    Product.name.ilike(f"%{product_filter}%"),
                    Product.numeric_code.ilike(f"%{product_filter}%"),
                )
            ).distinct()

        invoices = query.order_by(PurchaseInvoice.created_at.desc()).all()

        headers = ["شماره فاکتور", "فروشنده", "تاریخ", "جمع کل", "تخفیف", "قابل پرداخت"]
        rows, raw_data = [], []
        total = 0
        for inv in invoices:
            total += inv.final_total
            rows.append([
                inv.invoice_number,
                inv.supplier.name,
                self._format_date(inv.created_at),
                f"{inv.total_price:,.0f}",
                f"{inv.discount:,.0f}",
                f"{inv.final_total:,.0f}",
            ])
            raw_data.append({'id': inv.id, 'type': 'purchase'})

        summary = (
            f"تعداد فاکتور: {self._pd(len(invoices))} | "
            f"جمع خرید: {self._pd(f'{total:,.0f}')} ریال"
        )
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
        start = self.start_date_edit.get_date()
        end = self.end_date_edit.get_date() + timedelta(days=1)
        dt_start = datetime.combine(start, datetime.min.time())
        dt_end   = datetime.combine(end,   datetime.min.time())

        sales = self.session.query(SalesInvoice).filter(
            SalesInvoice.customer_id == party.id,
            SalesInvoice.created_at >= dt_start,
            SalesInvoice.created_at <  dt_end,
        ).all()

        purchases = self.session.query(PurchaseInvoice).filter(
            PurchaseInvoice.supplier_id == party.id,
            PurchaseInvoice.created_at >= dt_start,
            PurchaseInvoice.created_at <  dt_end,
        ).all()

        headers = ["نوع", "شماره فاکتور", "تاریخ", "مبلغ"]
        rows, raw_data = [], []
        total_in = total_out = 0

        for inv in purchases:
            total_in += inv.final_total
            rows.append(["خرید", inv.invoice_number,
                          self._format_date(inv.created_at), f"{inv.final_total:,.0f}"])
            raw_data.append({'id': inv.id, 'type': 'purchase'})

        for inv in sales:
            total_out += inv.final_total
            rows.append(["فروش", inv.invoice_number,
                          self._format_date(inv.created_at), f"{inv.final_total:,.0f}"])
            raw_data.append({'id': inv.id, 'type': 'sales'})

        # مرتب‌سازی بر اساس تاریخ
        combined = sorted(zip(rows, raw_data), key=lambda x: x[0][2], reverse=True)
        rows     = [c[0] for c in combined]
        raw_data = [c[1] for c in combined]

        balance = total_in - total_out
        summary = (
            f"جمع خرید: {self._pd(f'{total_in:,.0f}')} | "
            f"جمع فروش: {self._pd(f'{total_out:,.0f}')} | "
            f"مانده: {self._pd(f'{balance:,.0f}')} ریال"
        )
        self._set_table_data(headers, rows, raw_data=raw_data, summary=summary)

    # ──────────────────────────────────────────────────────────────
    # Export & Print
    # ──────────────────────────────────────────────────────────────
    def _export_report(self):
        if not self._all_rows:
            QMessageBox.warning(self, "خطا", "ابتدا یک گزارش اجرا کنید")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره گزارش", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                f.write(",".join(self._headers) + "\n")
                for row_data in self._all_rows:
                    vals = [str(v).replace(",", "") for v in row_data]
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
