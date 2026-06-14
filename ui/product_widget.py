"""
Product Management Widget - با قابلیت جستجوی real-time روی نام و کد کالا
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QLineEdit, QComboBox, QPushButton,
                                QTableWidget, QTableWidgetItem, QMessageBox,
                                QGroupBox, QHeaderView, QRadioButton)
from PySide6.QtCore import Qt
from sqlalchemy.orm import Session

from models.product import ProductCategory, StockSourceType
from services.product_service import ProductService


class ProductWidget(QWidget):
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
        
        QLineEdit, QComboBox {
            background-color: #FFE4E1;
            border: 1px solid #CD853F;
            border-radius: 2px;
            padding: 4px 8px;
            color: #2d1b1b;
            font-size: 16px;
            min-height: 24px;
        }

        QLineEdit#search_active {
            background-color: #FFF8DC;
            border: 1px solid #DAA520;
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
        
        QRadioButton {
            color: #FFFFFF;
            font-size: 14px;
            spacing: 4px;
        }
        
        QRadioButton::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #333;
            background-color: #FFE4E1;
        }
        
        QRadioButton::indicator:checked {
            background-color: #333;
            border: 2px solid #FFE4E1;
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
        
        QPushButton#save_btn { background-color: #6B8E6B; }
        QPushButton#update_btn { background-color: #6B8E6B; }
        QPushButton#delete_btn { background-color: #CD5C5C; }
        QPushButton#clear_btn { background-color: #8B4513; }
        
        QPushButton:hover { border: 1px solid white; }
        
        QPushButton:disabled {
            background-color: #8B7355;
            color: #ccc;
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
        
        QTableWidget {
            background-color: white;
            border: 1px solid #CD853F;
            gridline-color: #DEB887;
            font-size: 15px;
        }
        
        QHeaderView::section {
            background-color: #D2B48C;
            color: #2d1b1b;
            padding: 6px;
            border: 1px solid #8B4513;
            font-weight: bold;
        }
    """

    def __init__(self, session: Session, db_manager):
        super().__init__()
        self.session = session
        self.db_manager = db_manager
        self.product_service = ProductService(session)

        # Flag to prevent search triggering during programmatic fill (e.g. row selection)
        self._suppress_search = False

        self.setStyleSheet(self.WIDGET_STYLESHEET)
        self._init_ui()
        self._load_products()

    # ✅ تبدیل اعداد
    @staticmethod
    def _to_persian_digits(text) -> str:
        return str(text).translate(str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹."))

    @staticmethod
    def _to_english_digits(text: str) -> str:
        return text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))

    def _get_cell_text(self, row: int, col: int) -> str:
        """Read cell text from table"""
        item = self.products_table.item(row, col)
        return item.text() if item else ""

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # عنوان
        title = QLabel("انبار")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # فرم ورودی
        form_group = QGroupBox("اطلاعات کالا")
        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(15, 10, 15, 15)
        form_layout.setSpacing(12)

        # ================================
        # ✅ خط اول: کد | نام | دسته | نوع موجودی
        # ================================
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # کد کالا — حالا قابل ویرایش با جستجوی real-time
        self.numeric_code_edit = QLineEdit()
        self.numeric_code_edit.setPlaceholderText("کد کالا")
        self.numeric_code_edit.setFixedWidth(90)
        # جستجوی real-time روی ستون کد (ستون 1)
        self.numeric_code_edit.textChanged.connect(
            lambda text: self._on_search_field_changed(text, col=1)
        )
        row1.addWidget(self.numeric_code_edit)

        # نام کالا — با جستجوی real-time
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("نام کامل کالا")
        # جستجوی real-time روی ستون نام (ستون 2)
        self.name_edit.textChanged.connect(
            lambda text: self._on_search_field_changed(text, col=2)
        )
        row1.addWidget(self.name_edit, 3)

        # دسته بندی
        self.category_combo = QComboBox()
        self.category_combo.addItem("شلوار", ProductCategory.PANTS)
        self.category_combo.addItem("پارچه", ProductCategory.FABRIC)
        self.category_combo.addItem("کاپشن", ProductCategory.JACKET)
        self.category_combo.setFixedWidth(110)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        row1.addWidget(self.category_combo)

        # نوع موجودی اولیه
        source_label = QLabel("نوع موجودی اولیه:")
        self.production_radio = QRadioButton("تولید")
        self.purchase_radio = QRadioButton("خرید")
        self.purchase_radio.setChecked(True)

        row1.addWidget(source_label)
        row1.addWidget(self.production_radio)
        row1.addWidget(self.purchase_radio)
        row1.addStretch()

        form_layout.addLayout(row1)

        # ================================
        # ✅ خط دوم: موجودی اولیه | قیمت | دکمه‌ها
        # ================================
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        # موجودی اولیه
        stock_label = QLabel("موجودی اولیه:")
        self.stock_edit = QLineEdit("0")
        self.stock_edit.setFixedWidth(100)
        row2.addWidget(stock_label)
        row2.addWidget(self.stock_edit)

        # قیمت
        price_label = QLabel("قیمت(ریال):")
        self.price_edit = QLineEdit("0")
        self.price_edit.textChanged.connect(self._format_price_input)
        self.price_edit.setFixedWidth(130)
        row2.addWidget(price_label)
        row2.addWidget(self.price_edit)

        row2.addStretch()

        # دکمه‌ها
        self.save_btn = QPushButton("جدید")
        self.save_btn.setObjectName("save_btn")

        self.update_btn = QPushButton("ویرایش")
        self.update_btn.setObjectName("update_btn")
        self.update_btn.setEnabled(False)

        self.delete_btn = QPushButton("حذف")
        self.delete_btn.setObjectName("delete_btn")
        self.delete_btn.setEnabled(False)

        self.clear_btn = QPushButton("پاک کردن")
        self.clear_btn.setObjectName("clear_btn")

        self.save_btn.clicked.connect(self._save_product)
        self.update_btn.clicked.connect(self._update_product)
        self.delete_btn.clicked.connect(self._delete_product)
        self.clear_btn.clicked.connect(self._clear_form)

        for btn in [self.save_btn, self.update_btn, self.delete_btn, self.clear_btn]:
            row2.addWidget(btn)

        form_layout.addLayout(row2)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # ================================
        # ✅ جدول
        # ================================
        table_group = QGroupBox("لیست کالاها")
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "شناسه", "کد", "نام", "دسته", "واحد", "موجودی", "قیمت", "منبع"
        ])

        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

        self.products_table.verticalHeader().setVisible(False)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_table.itemSelectionChanged.connect(self._on_table_selection)

        table_layout.addWidget(self.products_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

    # ================================
    # ✅ جستجوی real-time
    # ================================
    def _on_search_field_changed(self, text: str, col: int):
        """
        وقتی متن فیلد نام یا کد تغییر می‌کند، ردیف‌های جدول را فیلتر می‌کند.
        col=1 → جستجو روی ستون کد
        col=2 → جستجو روی ستون نام
        اگر suppress_search فعال باشد (مثلاً هنگام انتخاب ردیف)، جستجو انجام نمی‌شود.
        """
        if self._suppress_search:
            return

        # ترکیب هر دو فیلتر همزمان: هم کد و هم نام را در نظر می‌گیریم
        name_query = self.name_edit.text().strip()
        code_query = self.numeric_code_edit.text().strip()

        self._filter_table(name_query=name_query, code_query=code_query)

    def _filter_table(self, name_query: str = "", code_query: str = ""):
        """
        نمایش یا پنهان کردن ردیف‌های جدول بر اساس فیلترهای نام و کد.
        هر دو فیلتر با AND ترکیب می‌شوند.
        """
        name_lower = name_query.lower()
        code_lower = code_query.lower()

        for row in range(self.products_table.rowCount()):
            row_name = self._get_cell_text(row, 2).lower()
            row_code = self._get_cell_text(row, 1).lower()

            name_match = name_lower in row_name if name_lower else True
            code_match = code_lower in row_code if code_lower else True

            self.products_table.setRowHidden(row, not (name_match and code_match))

    def _on_category_changed(self, index):
        """تغییر placeholder موجودی بر اساس دسته‌بندی"""
        category = self.category_combo.currentData()
        if category == ProductCategory.FABRIC:
            self.stock_edit.setPlaceholderText("متر")
        else:
            self.stock_edit.setPlaceholderText("عدد")

    def _load_products(self):
        products = self.product_service.get_all_products()
        self.products_table.setRowCount(0)

        for product in products:
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)

            items = [
                str(product.id),
                product.numeric_code,
                product.name,
                product.category.value,
                product.unit.value,
                str(product.stock_quantity),
                f"{product.default_price:,.0f}",
                product.stock_source.value
            ]

            for col, text in enumerate(items):
                display_text = self._to_persian_digits(text)
                item = QTableWidgetItem(display_text)
                self.products_table.setItem(row, col, item)

        # بعد از بارگذاری مجدد، فیلتر فعلی را اعمال کن
        self._filter_table(
            name_query=self.name_edit.text().strip(),
            code_query=self.numeric_code_edit.text().strip()
        )

    def _save_product(self):
        try:
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "خطا", "نام کالا الزامی است")
                return

            stock_source = (StockSourceType.PRODUCTION if self.production_radio.isChecked()
                            else StockSourceType.PURCHASE)

            self.product_service.create_product(
                name=name,
                category=self.category_combo.currentData(),
                initial_stock=float(
                    self._to_english_digits(self.stock_edit.text().strip() or "0")
                ),
                default_price=float(
                    self._to_english_digits(
                        self.price_edit.text().strip().replace(",", "") or "0"
                    )
                ),
                stock_source=stock_source
            )

            QMessageBox.information(self, "موفق", "کالا با موفقیت ذخیره شد")
            self._clear_form()
            self._load_products()

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره: {str(e)}")

    def _update_product(self):
        selected_ranges = self.products_table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self, "خطا", "ابتدا یک کالا را انتخاب کنید")
            return

        row = selected_ranges[0].topRow()
        item = self.products_table.item(row, 0)
        pid = int(self._to_english_digits(item.text())) if item else 0

        try:
            stock_source = (StockSourceType.PRODUCTION if self.production_radio.isChecked()
                            else StockSourceType.PURCHASE)

            self.product_service.update_product(
                product_id=pid,
                name=self.name_edit.text().strip(),
                initial_stock=float(
                    self._to_english_digits(self.stock_edit.text().strip() or "0")
                ),
                stock_quantity=float(
                    self._to_english_digits(self.stock_edit.text().strip() or "0")
                ),
                default_price=float(
                    self._to_english_digits(
                        self.price_edit.text().strip().replace(",", "") or "0"
                    )
                ),
                stock_source=stock_source
            )
            QMessageBox.information(self, "موفق", "کالا با موفقیت ویرایش شد")
            self._load_products()

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ویرایش: {str(e)}")

    def _delete_product(self):
        selected_ranges = self.products_table.selectedRanges()
        if not selected_ranges:
            return

        reply = QMessageBox.question(
            self, "تأیید حذف",
            "آیا از حذف این کالا اطمینان دارید؟",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            row = selected_ranges[0].topRow()
            item = self.products_table.item(row, 0)
            pid = int(self._to_english_digits(item.text())) if item else 0

            try:
                self.product_service.delete_product(pid)
                QMessageBox.information(self, "موفق", "کالا حذف شد")
                self._clear_form()
                self._load_products()
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در حذف: {str(e)}")

    def _on_table_selection(self):
        selected_ranges = self.products_table.selectedRanges()
        if not selected_ranges:
            self.update_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return

        row = selected_ranges[0].topRow()
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

        # پر کردن فرم بدون فعال شدن جستجو
        self._suppress_search = True

        item = self.products_table.item(row, 1)
        numeric_code = item.text() if item else ""

        item = self.products_table.item(row, 2)
        name_text = item.text() if item else ""

        item = self.products_table.item(row, 5)
        stock_text = item.text() if item else "0"

        item = self.products_table.item(row, 6)
        price_text = item.text() if item else "0"

        self.numeric_code_edit.setText(numeric_code)
        self.name_edit.setText(name_text)
        self.stock_edit.setText(self._to_english_digits(stock_text))
        self.price_edit.setText(
            self._to_english_digits(price_text.replace(",", ""))
        )

        # دسته‌بندی
        category_text = self._get_cell_text(row, 3)
        if "پارچه" in category_text:
            self.category_combo.setCurrentIndex(1)
        elif "شلوار" in category_text:
            self.category_combo.setCurrentIndex(0)
        else:
            self.category_combo.setCurrentIndex(2)

        # منبع
        source_text = self._get_cell_text(row, 7)
        if "تولید" in source_text:
            self.production_radio.setChecked(True)
        else:
            self.purchase_radio.setChecked(True)

        self._suppress_search = False

    def _clear_form(self):
        self._suppress_search = True

        self.numeric_code_edit.clear()
        self.name_edit.clear()
        self.stock_edit.setText("0")
        self.price_edit.setText("0")
        self.category_combo.setCurrentIndex(0)
        self.purchase_radio.setChecked(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.products_table.clearSelection()

        self._suppress_search = False

        # بازنمایی همه ردیف‌ها بعد از پاک کردن فرم
        self._filter_table()

    def _format_price_input(self, text: str):
        """افزودن جداکننده هزار هنگام تایپ قیمت"""
        # جلوگیری از loop بازگشتی
        self.price_edit.blockSignals(True)

        # حذف همه کاماها و تبدیل به انگلیسی
        clean = self._to_english_digits(text).replace(",", "")

        if clean and clean != "0":
            try:
                formatted = f"{int(clean):,}"
            except ValueError:
                formatted = clean
        else:
            formatted = clean

        cursor_pos = self.price_edit.cursorPosition()
        self.price_edit.setText(formatted)

        # تنظیم مجدد موقعیت cursor (تعداد کاماهای اضافه‌شده را جبران می‌کند)
        extra_commas = formatted.count(",") - text.count(",")
        self.price_edit.setCursorPosition(cursor_pos + extra_commas)

        self.price_edit.blockSignals(False)