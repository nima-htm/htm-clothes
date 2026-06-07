"""
Purchase Invoice Widget
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                                QLabel, QLineEdit, QPushButton, 
                                QTableWidget, QTableWidgetItem, QMessageBox,
                                QGroupBox, QHeaderView, QDialog, QListWidget, QTextEdit)
from PySide6.QtCore import Qt, Signal
from sqlalchemy.orm import Session

from models.party import PartyType
from services.purchase_service import PurchaseInvoiceService
from services.product_service import ProductService
from services.party_service import PartyService


class AutoCompleteDialog(QDialog):
    """Dialog for autocomplete selection"""
    item_selected = Signal(object)
    
    def __init__(self, parent, items, display_field='name'):
        super().__init__(parent)
        self.items = items
        self.display_field = display_field
        
        self.setWindowTitle("انتخاب")
        self.setMinimumSize(400, 300)
        self.setLayoutDirection(Qt.RightToLeft)
        
        layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        for item in items:
            display_value = getattr(item, display_field, str(item))
            self.list_widget.addItem(display_value)
        
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        
        select_btn = QPushButton("انتخاب")
        select_btn.clicked.connect(self._select_item)
        btn_layout.addWidget(select_btn)
        
        cancel_btn = QPushButton("انصراف")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_item_double_clicked(self, item):
        self._select_item()
    
    def _select_item(self):
        current_row = self.list_widget.currentRow()
        if current_row >= 0 and current_row < len(self.items):
            self.item_selected.emit(self.items[current_row])
            self.accept()


class PurchaseInvoiceWidget(QWidget):
    def __init__(self, session: Session, db_manager):
        super().__init__()
        
        self.session = session
        self.db_manager = db_manager
        self.purchase_service = PurchaseInvoiceService(session)
        self.product_service = ProductService(session)
        self.party_service = PartyService(session)
        
        self.invoice_items = []
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("فاکتور خرید")
        title.setFont(self.font())
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Supplier selection
        supplier_group = QGroupBox("فروشنده")
        supplier_layout = QHBoxLayout()
        
        self.supplier_edit = QLineEdit()
        self.supplier_edit.setPlaceholderText("جستجوی فروشنده (نام یا تلفن)")
        supplier_layout.addWidget(self.supplier_edit)
        
        self.supplier_select_btn = QPushButton("انتخاب فروشنده")
        self.supplier_select_btn.clicked.connect(self._show_supplier_dialog)
        supplier_layout.addWidget(self.supplier_select_btn)
        
        self.supplier_label = QLabel("")
        self.supplier_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        supplier_layout.addWidget(self.supplier_label)
        
        supplier_group.setLayout(supplier_layout)
        layout.addWidget(supplier_group)
        
        # Product selection
        product_group = QGroupBox("افزودن کالا")
        product_form = QFormLayout()
        product_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        self.product_search_edit = QLineEdit()
        self.product_search_edit.setPlaceholderText("جستجوی کالا (کد یا نام)")
        product_form.addRow("جستجوی کالا:", self.product_search_edit)
        
        self.product_select_btn = QPushButton("انتخاب کالا")
        self.product_select_btn.clicked.connect(self._show_product_dialog)
        product_form.addRow("", self.product_select_btn)
        
        self.selected_product_label = QLabel("")
        self.selected_product_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        product_form.addRow("کالای انتخابی:", self.selected_product_label)
        
        self.quantity_edit = QLineEdit()
        self.quantity_edit.setPlaceholderText("تعداد")
        self.quantity_edit.setText("1")
        product_form.addRow("تعداد:", self.quantity_edit)
        
        self.price_edit = QLineEdit()
        self.price_edit.setPlaceholderText("قیمت واحد")
        product_form.addRow("قیمت خرید:", self.price_edit)
        
        self.add_item_btn = QPushButton("افزودن به فاکتور")
        self.add_item_btn.clicked.connect(self._add_item_to_invoice)
        product_form.addRow("", self.add_item_btn)
        
        product_group.setLayout(product_form)
        layout.addWidget(product_group)
        
        # Invoice items table
        items_group = QGroupBox("اقلام فاکتور")
        items_layout = QVBoxLayout()
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            "کد کالا", "نام کالا", "تعداد", "قیمت واحد", "جمع کل"
        ])
        
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        items_layout.addWidget(self.items_table)
        
        # Totals
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        
        totals_layout.addWidget(QLabel("جمع کل:"))
        self.total_label = QLabel("0")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        totals_layout.addWidget(self.total_label)
        
        totals_layout.addWidget(QLabel("تخفیف:"))
        self.discount_edit = QLineEdit()
        self.discount_edit.setText("0")
        self.discount_edit.setFixedWidth(150)
        totals_layout.addWidget(self.discount_edit)
        
        totals_layout.addWidget(QLabel("قابل پرداخت:"))
        self.final_total_label = QLabel("0")
        self.final_total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
        totals_layout.addWidget(self.final_total_label)
        
        items_layout.addLayout(totals_layout)
        items_group.setLayout(items_layout)
        layout.addWidget(items_group)
        
        # Notes
        notes_group = QGroupBox("توضیحات")
        notes_layout = QVBoxLayout()
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.save_btn = QPushButton("ثبت فاکتور")
        self.save_btn.setMinimumHeight(45)
        self.save_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; font-size: 14px;")
        self.save_btn.clicked.connect(self._save_invoice)
        btn_layout.addWidget(self.save_btn)
        
        self.print_btn = QPushButton("چاپ فاکتور")
        self.print_btn.setMinimumHeight(45)
        self.print_btn.clicked.connect(self._print_invoice)
        btn_layout.addWidget(self.print_btn)
        
        self.clear_btn = QPushButton("فاکتور جدید")
        self.clear_btn.setMinimumHeight(45)
        self.clear_btn.clicked.connect(self._clear_invoice)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        # Set RTL
        self.setLayoutDirection(Qt.RightToLeft)
        
        self.current_supplier = None
        self.current_product = None
    
    def _show_supplier_dialog(self):
        """Show supplier selection dialog"""
        suppliers = self.party_service.get_suppliers()
        
        if not suppliers:
            QMessageBox.warning(self, "خطا", "هیچ فروشنده‌ای ثبت نشده است")
            return
        
        dialog = AutoCompleteDialog(self, suppliers, 'name')
        dialog.item_selected.connect(self._on_supplier_selected)
        dialog.exec()
    
    def _on_supplier_selected(self, supplier):
        """Handle supplier selection"""
        self.current_supplier = supplier
        self.supplier_label.setText(f"فروشنده: {supplier.name} - {supplier.phone or ''}")
    
    def _show_product_dialog(self):
        """Show product selection dialog"""
        products = self.product_service.get_all_products()
        
        if not products:
            QMessageBox.warning(self, "خطا", "هیچ کالایی ثبت نشده است")
            return
        
        dialog = AutoCompleteDialog(self, products, 'name')
        dialog.item_selected.connect(self._on_product_selected)
        dialog.exec()
    
    def _on_product_selected(self, product):
        """Handle product selection"""
        self.current_product = product
        self.selected_product_label.setText(
            f"{product.name} (کد: {product.code}) - قیمت خرید: {product.buy_price:,.0f}"
        )
        self.price_edit.setText(str(int(product.buy_price)))
    
    def _add_item_to_invoice(self):
        """Add selected product to invoice"""
        if not self.current_product:
            QMessageBox.warning(self, "خطا", "لطفاً یک کالا انتخاب کنید")
            return
        
        try:
            quantity = int(self.quantity_edit.text().strip() or 1)
            price = float(self.price_edit.text().strip() or self.current_product.buy_price)
        except ValueError:
            QMessageBox.warning(self, "خطا", "تعداد و قیمت باید عدد باشند")
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
    
    def _update_items_table(self):
        """Update items table and totals"""
        self.items_table.setRowCount(0)
        
        total = 0
        for item in self.invoice_items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            
            self.items_table.setItem(row, 0, QTableWidgetItem(item['product_code']))
            self.items_table.setItem(row, 1, QTableWidgetItem(item['product_name']))
            self.items_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{item['unit_price']:,.0f}"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{item['total']:,.0f}"))
            
            total += item['total']
        
        self.total_label.setText(f"{total:,.0f}")
        
        discount = float(self.discount_edit.text().strip() or 0)
        final_total = total - discount
        self.final_total_label.setText(f"{final_total:,.0f}")
    
    def _save_invoice(self):
        """Save the invoice"""
        if not self.current_supplier:
            QMessageBox.warning(self, "خطا", "لطفاً یک فروشنده انتخاب کنید")
            return
        
        if not self.invoice_items:
            QMessageBox.warning(self, "خطا", "فاکتور خالی است")
            return
        
        try:
            discount = float(self.discount_edit.text().strip() or 0)
            notes = self.notes_edit.toPlainText().strip() or None
            
            invoice = self.purchase_service.create_invoice(
                supplier_id=self.current_supplier.id,
                items=self.invoice_items,
                discount=discount,
                notes=notes
            )
            
            QMessageBox.information(
                self, "موفق",
                f"فاکتور با موفقیت ثبت شد\nشماره فاکتور: {invoice.invoice_number}"
            )
            
            self._clear_invoice()
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ثبت فاکتور: {str(e)}")
    
    def _print_invoice(self):
        """Print invoice (placeholder)"""
        QMessageBox.information(self, "چاپ", "قابلیت چاپ در حال توسعه است")
    
    def _clear_invoice(self):
        """Clear current invoice"""
        self.current_supplier = None
        self.current_product = None
        self.invoice_items = []
        
        self.supplier_label.setText("")
        self.supplier_edit.clear()
        self.selected_product_label.setText("")
        self.product_search_edit.clear()
        self.quantity_edit.setText("1")
        self.price_edit.clear()
        self.discount_edit.setText("0")
        self.notes_edit.clear()
        
        self._update_items_table()
