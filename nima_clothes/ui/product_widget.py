"""
Product Management Widget
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                                QLabel, QLineEdit, QComboBox, QPushButton, 
                                QTableWidget, QTableWidgetItem, QMessageBox,
                                QGroupBox, QHeaderView)
from PySide6.QtCore import Qt
from sqlalchemy.orm import Session

from models.product import Product, ProductCategory
from services.product_service import ProductService


class ProductWidget(QWidget):
    def __init__(self, session: Session, db_manager):
        super().__init__()
        
        self.session = session
        self.db_manager = db_manager
        self.product_service = ProductService(session)
        
        self._init_ui()
        self._load_products()
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("مدیریت کالاها")
        title.setFont(self.font())
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Form group
        form_group = QGroupBox("اطلاعات کالا")
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.setSpacing(10)
        
        # Product Code
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("کد کالا را وارد کنید")
        form_layout.addRow("کد کالا:", self.code_edit)
        
        # Product Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("نام کالا را وارد کنید")
        form_layout.addRow("نام کالا:", self.name_edit)
        
        # Category
        self.category_combo = QComboBox()
        self.category_combo.addItem("پارچه", ProductCategory.FABRIC)
        self.category_combo.addItem("شلوار", ProductCategory.PANTS)
        form_layout.addRow("دسته‌بندی:", self.category_combo)
        
        # Sub-category
        self.subcategory_edit = QLineEdit()
        self.subcategory_edit.setPlaceholderText("نوع فرعی (جین، رسمی، کتان، ...)")
        form_layout.addRow("زیردسته:", self.subcategory_edit)
        
        # Buy Price
        self.buy_price_edit = QLineEdit()
        self.buy_price_edit.setPlaceholderText("قیمت خرید")
        form_layout.addRow("قیمت خرید:", self.buy_price_edit)
        
        # Sell Price
        self.sell_price_edit = QLineEdit()
        self.sell_price_edit.setPlaceholderText("قیمت فروش")
        form_layout.addRow("قیمت فروش:", self.sell_price_edit)
        
        # Unit
        self.unit_edit = QLineEdit("عدد")
        form_layout.addRow("واحد:", self.unit_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.save_btn = QPushButton("ذخیره کالا")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self._save_product)
        btn_layout.addWidget(self.save_btn)
        
        self.update_btn = QPushButton("ویرایش")
        self.update_btn.setMinimumHeight(40)
        self.update_btn.clicked.connect(self._update_product)
        self.update_btn.setEnabled(False)
        btn_layout.addWidget(self.update_btn)
        
        self.delete_btn = QPushButton("حذف")
        self.delete_btn.setMinimumHeight(40)
        self.delete_btn.clicked.connect(self._delete_product)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)
        
        self.clear_btn = QPushButton("پاک کردن فرم")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self._clear_form)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        # Products table
        table_group = QGroupBox("لیست کالاها")
        table_layout = QVBoxLayout()
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "شناسه", "کد", "نام", "دسته‌بندی", "زیردسته", 
            "قیمت خرید", "قیمت فروش", "موجودی"
        ])
        
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.itemSelectionChanged.connect(self._on_table_selection)
        
        table_layout.addWidget(self.products_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Set RTL
        self.setLayoutDirection(Qt.RightToLeft)
    
    def _load_products(self):
        """Load products into table"""
        products = self.product_service.get_all_products()
        
        self.products_table.setRowCount(0)
        for product in products:
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)
            
            stock = self.product_service.get_current_stock(product.id)
            
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product.id)))
            self.products_table.setItem(row, 1, QTableWidgetItem(product.code))
            self.products_table.setItem(row, 2, QTableWidgetItem(product.name))
            self.products_table.setItem(row, 3, QTableWidgetItem(product.category.value))
            self.products_table.setItem(row, 4, QTableWidgetItem(product.sub_category or ""))
            self.products_table.setItem(row, 5, QTableWidgetItem(f"{product.buy_price:,.0f}"))
            self.products_table.setItem(row, 6, QTableWidgetItem(f"{product.sell_price:,.0f}"))
            self.products_table.setItem(row, 7, QTableWidgetItem(str(stock)))
    
    def _save_product(self):
        """Save new product"""
        try:
            code = self.code_edit.text().strip()
            name = self.name_edit.text().strip()
            
            if not code or not name:
                QMessageBox.warning(self, "خطا", "کد و نام کالا الزامی است")
                return
            
            category = self.category_combo.currentData()
            sub_category = self.subcategory_edit.text().strip() or None
            buy_price = float(self.buy_price_edit.text().strip() or 0)
            sell_price = float(self.sell_price_edit.text().strip() or 0)
            unit = self.unit_edit.text().strip() or "عدد"
            
            self.product_service.create_product(
                code=code,
                name=name,
                category=category,
                sub_category=sub_category,
                buy_price=buy_price,
                sell_price=sell_price,
                unit=unit
            )
            
            QMessageBox.information(self, "موفق", "کالا با موفقیت ذخیره شد")
            self._clear_form()
            self._load_products()
            
        except ValueError as e:
            QMessageBox.critical(self, "خطا", str(e))
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره کالا: {str(e)}")
    
    def _update_product(self):
        """Update selected product"""
        selected_rows = self.products_table.selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "خطا", "لطفاً یک کالا را انتخاب کنید")
            return
        
        row = selected_rows[0].row()
        product_id = int(self.products_table.item(row, 0).text())
        
        try:
            self.product_service.update_product(
                product_id=product_id,
                name=self.name_edit.text().strip(),
                sub_category=self.subcategory_edit.text().strip() or None,
                buy_price=float(self.buy_price_edit.text().strip() or 0),
                sell_price=float(self.sell_price_edit.text().strip() or 0),
                unit=self.unit_edit.text().strip() or "عدد"
            )
            
            QMessageBox.information(self, "موفق", "کالا با موفقیت ویرایش شد")
            self._load_products()
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ویرایش کالا: {str(e)}")
    
    def _delete_product(self):
        """Delete selected product"""
        selected_rows = self.products_table.selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "خطا", "لطفاً یک کالا را انتخاب کنید")
            return
        
        reply = QMessageBox.question(
            self, "تأیید حذف",
            "آیا از حذف این کالا اطمینان دارید؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            row = selected_rows[0].row()
            product_id = int(self.products_table.item(row, 0).text())
            
            try:
                self.product_service.delete_product(product_id)
                QMessageBox.information(self, "موفق", "کالا حذف شد")
                self._clear_form()
                self._load_products()
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در حذف کالا: {str(e)}")
    
    def _on_table_selection(self):
        """Handle table selection"""
        selected_rows = self.products_table.selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.update_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            self.code_edit.setText(self.products_table.item(row, 1).text())
            self.name_edit.setText(self.products_table.item(row, 2).text())
            self.subcategory_edit.setText(self.products_table.item(row, 4).text())
            self.buy_price_edit.setText(self.products_table.item(row, 5).text().replace(",", ""))
            self.sell_price_edit.setText(self.products_table.item(row, 6).text().replace(",", ""))
    
    def _clear_form(self):
        """Clear form fields"""
        self.code_edit.clear()
        self.name_edit.clear()
        self.subcategory_edit.clear()
        self.buy_price_edit.clear()
        self.sell_price_edit.clear()
        self.unit_edit.setText("عدد")
        self.category_combo.setCurrentIndex(0)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
