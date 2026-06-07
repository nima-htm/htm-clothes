"""
Reports Widget
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                                QLabel, QLineEdit, QComboBox, QPushButton, 
                                QTableWidget, QTableWidgetItem, QMessageBox,
                                QGroupBox, QHeaderView, QDateEdit, QFileDialog)
from PySide6.QtCore import Qt, QDate
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from models.product import Product, ProductCategory
from models.party import Party, PartyType
from models.sales import SalesInvoice, SalesInvoiceItem
from models.purchase import PurchaseInvoice, PurchaseInvoiceItem
from models.inventory import InventoryTransaction, TransactionType
from services.product_service import ProductService
from services.party_service import PartyService


class ReportsWidget(QWidget):
    def __init__(self, session: Session, db_manager):
        super().__init__()
        
        self.session = session
        self.db_manager = db_manager
        self.product_service = ProductService(session)
        self.party_service = PartyService(session)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("گزارش‌ها")
        title.setFont(self.font())
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Report type selection
        type_group = QGroupBox("نوع گزارش")
        type_layout = QHBoxLayout()
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItem("گزارش موجودی کالا", "inventory")
        self.report_type_combo.addItem("گزارش فروش", "sales")
        self.report_type_combo.addItem("گزارش خرید", "purchase")
        self.report_type_combo.addItem("گزارش بر اساس شخص", "party")
        self.report_type_combo.currentIndexChanged.connect(self._on_report_type_changed)
        type_layout.addWidget(QLabel("انتخاب گزارش:"))
        type_layout.addWidget(self.report_type_combo)
        type_layout.addStretch()
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Filters
        self.filters_group = QGroupBox("فیلترها")
        self.filters_layout = QFormLayout()
        self.filters_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # Date filters
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.filters_layout.addRow("از تاریخ:", self.start_date_edit)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.filters_layout.addRow("تا تاریخ:", self.end_date_edit)
        
        # Party filter
        self.party_filter_edit = QLineEdit()
        self.party_filter_edit.setPlaceholderText("جستجوی نام شخص")
        self.filters_layout.addRow("نام شخص:", self.party_filter_edit)
        
        # Product filter
        self.product_filter_edit = QLineEdit()
        self.product_filter_edit.setPlaceholderText("جستجوی نام کالا")
        self.filters_layout.addRow("نام کالا:", self.product_filter_edit)
        
        # Category filter
        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItem("همه", None)
        self.category_filter_combo.addItem("پارچه", ProductCategory.FABRIC)
        self.category_filter_combo.addItem("شلوار", ProductCategory.PANTS)
        self.filters_layout.addRow("دسته‌بندی:", self.category_filter_combo)
        
        self.filters_group.setLayout(self.filters_layout)
        layout.addWidget(self.filters_group)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.run_report_btn = QPushButton("اجرای گزارش")
        self.run_report_btn.setMinimumHeight(40)
        self.run_report_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        self.run_report_btn.clicked.connect(self._run_report)
        btn_layout.addWidget(self.run_report_btn)
        
        self.export_btn = QPushButton("خروجی Excel")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.clicked.connect(self._export_report)
        btn_layout.addWidget(self.export_btn)
        
        self.print_btn = QPushButton("چاپ")
        self.print_btn.setMinimumHeight(40)
        self.print_btn.clicked.connect(self._print_report)
        btn_layout.addWidget(self.print_btn)
        
        layout.addLayout(btn_layout)
        
        # Results table
        results_group = QGroupBox("نتایج")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        results_layout.addWidget(self.results_table)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Set RTL
        self.setLayoutDirection(Qt.RightToLeft)
        
        # Initialize filters visibility
        self._on_report_type_changed(0)
    
    def _on_report_type_changed(self, index):
        """Handle report type change"""
        report_type = self.report_type_combo.currentData()
        
        # Show/hide filters based on report type
        visible_filters = {
            'inventory': ['category'],
            'sales': ['date', 'party', 'product'],
            'purchase': ['date', 'party', 'product'],
            'party': ['date', 'party'],
        }
        
        current_filters = visible_filters.get(report_type, [])
        
        # This is simplified - in a real app you'd show/hide specific rows
        pass
    
    def _run_report(self):
        """Run the selected report"""
        report_type = self.report_type_combo.currentData()
        
        if report_type == 'inventory':
            self._run_inventory_report()
        elif report_type == 'sales':
            self._run_sales_report()
        elif report_type == 'purchase':
            self._run_purchase_report()
        elif report_type == 'party':
            self._run_party_report()
    
    def _run_inventory_report(self):
        """Run inventory report"""
        category = self.category_filter_combo.currentData()
        
        products = self.session.query(Product)
        if category:
            products = products.filter(Product.category == category)
        
        products = products.all()
        
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "کد", "نام کالا", "دسته‌بندی", "زیردسته", "موجودی", "ارزش موجودی"
        ])
        
        self.results_table.setRowCount(0)
        total_value = 0
        
        for product in products:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            stock = self.product_service.get_current_stock(product.id)
            value = stock * product.sell_price
            total_value += value
            
            self.results_table.setItem(row, 0, QTableWidgetItem(product.code))
            self.results_table.setItem(row, 1, QTableWidgetItem(product.name))
            self.results_table.setItem(row, 2, QTableWidgetItem(product.category.value))
            self.results_table.setItem(row, 3, QTableWidgetItem(product.sub_category or ""))
            self.results_table.setItem(row, 4, QTableWidgetItem(str(stock)))
            self.results_table.setItem(row, 5, QTableWidgetItem(f"{value:,.0f}"))
        
        # Add total row
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 4, QTableWidgetItem("جمع کل"))
        self.results_table.setItem(row, 5, QTableWidgetItem(f"{total_value:,.0f}"))
    
    def _run_sales_report(self):
        """Run sales report"""
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        
        query = self.session.query(SalesInvoice).filter(
            SalesInvoice.created_at >= start_date,
            SalesInvoice.created_at <= end_date
        )
        
        if self.party_filter_edit.text().strip():
            party_name = self.party_filter_edit.text().strip()
            from sqlalchemy import or_
            query = query.join(SalesInvoice.customer).filter(
                Party.name.contains(party_name)
            )
        
        invoices = query.order_by(SalesInvoice.created_at.desc()).all()
        
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "شماره فاکتور", "مشتری", "تاریخ", "جمع کل", "تخفیف"
        ])
        
        self.results_table.setRowCount(0)
        total_sales = 0
        
        for invoice in invoices:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            total_sales += invoice.final_total
            
            self.results_table.setItem(row, 0, QTableWidgetItem(invoice.invoice_number))
            self.results_table.setItem(row, 1, QTableWidgetItem(invoice.customer.name))
            self.results_table.setItem(row, 2, QTableWidgetItem(invoice.created_at.strftime("%Y/%m/%d")))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{invoice.total_price:,.0f}"))
            self.results_table.setItem(row, 4, QTableWidgetItem(f"{invoice.discount:,.0f}"))
        
        # Add total row
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 3, QTableWidgetItem("جمع کل فروش"))
        self.results_table.setItem(row, 3, QTableWidgetItem(f"{total_sales:,.0f}"))
    
    def _run_purchase_report(self):
        """Run purchase report"""
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        
        query = self.session.query(PurchaseInvoice).filter(
            PurchaseInvoice.created_at >= start_date,
            PurchaseInvoice.created_at <= end_date
        )
        
        if self.party_filter_edit.text().strip():
            party_name = self.party_filter_edit.text().strip()
            query = query.join(PurchaseInvoice.supplier).filter(
                Party.name.contains(party_name)
            )
        
        invoices = query.order_by(PurchaseInvoice.created_at.desc()).all()
        
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "شماره فاکتور", "فروشنده", "تاریخ", "جمع کل", "تخفیف"
        ])
        
        self.results_table.setRowCount(0)
        total_purchases = 0
        
        for invoice in invoices:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            total_purchases += invoice.final_total
            
            self.results_table.setItem(row, 0, QTableWidgetItem(invoice.invoice_number))
            self.results_table.setItem(row, 1, QTableWidgetItem(invoice.supplier.name))
            self.results_table.setItem(row, 2, QTableWidgetItem(invoice.created_at.strftime("%Y/%m/%d")))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{invoice.total_price:,.0f}"))
            self.results_table.setItem(row, 4, QTableWidgetItem(f"{invoice.discount:,.0f}"))
        
        # Add total row
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 3, QTableWidgetItem("جمع کل خرید"))
        self.results_table.setItem(row, 3, QTableWidgetItem(f"{total_purchases:,.0f}"))
    
    def _run_party_report(self):
        """Run party transactions report"""
        party_name = self.party_filter_edit.text().strip()
        
        if not party_name:
            QMessageBox.warning(self, "خطا", "لطفاً نام شخص را وارد کنید")
            return
        
        parties = self.party_service.search_parties(query=party_name)
        
        if not parties:
            QMessageBox.warning(self, "خطا", "شخصی با این نام یافت نشد")
            return
        
        party = parties[0]
        
        # Get sales
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        
        sales = self.session.query(SalesInvoice).filter(
            SalesInvoice.customer_id == party.id,
            SalesInvoice.created_at >= start_date,
            SalesInvoice.created_at <= end_date
        ).all()
        
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "نوع", "شماره فاکتور", "تاریخ", "مبلغ"
        ])
        
        self.results_table.setRowCount(0)
        total = 0
        
        for invoice in sales:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            total += invoice.final_total
            
            self.results_table.setItem(row, 0, QTableWidgetItem("فروش"))
            self.results_table.setItem(row, 1, QTableWidgetItem(invoice.invoice_number))
            self.results_table.setItem(row, 2, QTableWidgetItem(invoice.created_at.strftime("%Y/%m/%d")))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{invoice.final_total:,.0f}"))
        
        # Add total row
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 2, QTableWidgetItem("جمع کل"))
        self.results_table.setItem(row, 3, QTableWidgetItem(f"{total:,.0f}"))
    
    def _export_report(self):
        """Export report to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره گزارش", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    # Write headers
                    headers = []
                    for col in range(self.results_table.columnCount()):
                        header = self.results_table.horizontalHeaderItem(col)
                        headers.append(header.text() if header else "")
                    f.write(",".join(headers) + "\n")
                    
                    # Write data
                    for row in range(self.results_table.rowCount()):
                        row_data = []
                        for col in range(self.results_table.columnCount()):
                            item = self.results_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        f.write(",".join(row_data) + "\n")
                
                QMessageBox.information(self, "موفق", "گزارش با موفقیت ذخیره شد")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در ذخیره گزارش: {str(e)}")
    
    def _print_report(self):
        """Print report (placeholder)"""
        QMessageBox.information(self, "چاپ", "قابلیت چاپ در حال توسعه است")
