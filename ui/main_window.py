"""
Main Window for Nima Clothes Application - Classic Dark Red/Orange Theme
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QStackedWidget,
                                QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ui.product_widget import ProductWidget
from ui.party_widget import PartyWidget
from ui.sales_invoice_widget import SalesInvoiceWidget
from ui.purchase_invoice_widget import PurchaseInvoiceWidget
from ui.reports_widget import ReportsWidget
from ui.setting_widget import SettingsWidget


class MainWindow(QMainWindow):
    stock_changed = Signal()

    GLOBAL_STYLESHEET = """
        /* ===== تم کلاسیک قرمز-نارنجی تیره ===== */
        * {
            color: #2d1b1b;
        }
        
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1a0f0f, stop:1 #2d1b1b);
        }

        /* ===== RTL سراسری ===== */
       
  
   

        /* ===== MessageBox ===== */
        QMessageBox {
            background-color: #f5e6d3;
            border: 2px solid #8b4513;
            border-radius: 10px;
        }
        
        QMessageBox QLabel {
            color: #2d1b1b;
            background-color: transparent;
            min-width: 300px;
            padding: 15px;
            font-size: 13px;
        }
        
        QMessageBox QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #d2691e, stop:1 #a0522d);
            color: #fff;
            border: 1px solid #8b4513;
            border-radius: 6px;
            padding: 10px 20px;
            min-width: 90px;
            font-weight: bold;
            font-size: 12px;
        }
        
        QMessageBox QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ff7f50, stop:1 #d2691e);
        }
        
        QMessageBox QPushButton:pressed {
            background: #8b4513;
        }

        /* ===== سایدبار کلاسیک ===== */
        QListWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #2d1810, stop:1 #3d2418);
            color: #f5deb3;
            border: none;
            border-left: 3px solid #8b4513;
            outline: none;
            font-size: 14px;
            font-weight: 500;
            padding: 15px 0;
        }

        QListWidget::item {
            padding: 18px 25px;
            margin: 4px 8px;
            border-radius: 8px;
            border-right: 4px solid transparent;
            color: #f5deb3;
        }

        QListWidget::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #8b4513, stop:1 #a0522d);
            color: #ffffff;
            border-right: 4px solid #ff7f50;
            font-weight: bold;
        }

        QListWidget::item:hover:!selected {
            background: rgba(160, 82, 45, 0.3);
            color: #ffd700;
        }

        /* ===== محتوای اصلی ===== */
        QStackedWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #f5e6d3, stop:1 #faebd7);
        }

        /* ===== دکمه‌ها - یکپارچه و حرفه‌ای ===== */
        QPushButton {
             background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                 stop:0 #d2691e, stop:1 #a0522d);
            color: white;
            border: 2px solid #d99a93;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 13px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ff7f50, stop:1 #d2691e);
            border-color: #471d10;
        }
        
        QPushButton:pressed {
            background: #8b4513;
            border-color: #654321;
        }
        
        QPushButton:disabled {
            background: #c8b89f;
            color: white;
            border-color: #a89885;
        }

        /* ===== کنترل‌های ورودی - منسجم ===== */
        QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
            border: 2px solid #a0522d;
            border-radius: 6px;
            padding: 10px 14px;
            background-color: #fff8f0;
            color: #2d1b1b;
            font-size: 14px;
            
        }
        
        QComboBox:focus, QLineEdit:focus, QSpinBox:focus, 
        QDoubleSpinBox:focus, QDateEdit:focus {
            border-color: #d2691e;
            background-color: #ffffff;
            border-width: 2px;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 30px;
        }
        
        QComboBox::down-arrow {
            image: url(down_arrow.png);
            width: 12px;
            height: 12px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #fff8f0;
            color: #2d1b1b;
            selection-background-color: #d2691e;
            selection-color: white;
            border: 2px solid #8b4513;
            outline: none;
            padding: 5px;
        }

        /* ===== GroupBox کلاسیک ===== */
        QGroupBox {
            color: #5d4037;
            border: 1px #a0522d;
            border-radius: 10px;
            margin-top: 2px;
            padding: 20px 15px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ffffff, stop:1 #fef5e7);
            font-weight: bold;
            font-size: 15px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top right;
            right: 20px;
            padding: 5px 15px;
            background-color: #d2691e;
            color: white;
            border-radius: 6px;
            font-weight: bold;
        }

        /* ===== لیبل‌ها ===== */
        QLabel {
            color: #3e2723;
            background-color: transparent;
            font-size: 15px;
        }

        /* ===== جداول حرفه‌ای ===== */
        QTableWidget {
            border: 2px solid #a0522d;
            border-radius: 8px;
            gridline-color: #d7ccc8;
            selection-background-color: #d2691e;
            selection-color: white;
            background-color: #ffffff;
            color: #2d1b1b;
            alternate-background-color: #fef5e7;
        }
        
        QHeaderView::section {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #8b4513, stop:1 #654321);
            color: #ffffff;
            padding: 12px;
            font-weight: bold;
            font-size: 13px;
            border: none;
            border-right: 1px solid #5d4037;
            text-align: center;
        }
        
        QHeaderView::section:first {
            border-top-right-radius: 6px;
        }
        
        QHeaderView::section:last {
            border-top-left-radius: 6px;
        }

        /* ===== QTextEdit ===== */
        QTextEdit {
            background-color: #fff8f0;
            color: #2d1b1b;
            border: 2px solid #a0522d;
            border-radius: 6px;
            padding: 10px;
            font-size: 13px;
        }
        
        QTextEdit:focus {
            border-color: #d2691e;
            background-color: #ffffff;
        }

        /* ===== اسکرول‌بار کلاسیک ===== */
        QScrollBar:vertical {
            border: 1px solid #a0522d;
            background: #f5e6d3;
            width: 14px;
            border-radius: 7px;
        }
        
        QScrollBar::handle:vertical {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #d2691e, stop:1 #a0522d);
            border-radius: 6px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #ff7f50;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """

    def __init__(self, db_manager, config_service):
        super().__init__()

        self.db_manager = db_manager
        self.config_service = config_service
        self.setWindowTitle("Nima Clothes - نرم‌افزار حسابداری کلاسیک")
        self.setMinimumSize(1280, 850)

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(self.GLOBAL_STYLESHEET)

        central_widget = QWidget()
        central_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.sidebar = self._create_sidebar()

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)

        self._initialize_pages()
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)

    def _create_sidebar(self) -> QListWidget:
        sidebar = QListWidget()
        sidebar.setFixedWidth(240)
        # ✅ ONLY set RTL on the sidebar itself
        sidebar.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        items = [
             "انبار", "فاکتور فروش", "فاکتور خرید",
            "مدیریت اشخاص", "گزارش‌ها", "تنظیمات"
        ]

        for label in items:
            item = QListWidgetItem(label)
            sidebar.addItem(item)

        sidebar.setCurrentRow(0)
        return sidebar

    def _initialize_pages(self):
        session = self.db_manager.get_session()

        self.products_widget = ProductWidget(session, self.db_manager)
        self.stack.addWidget(self.products_widget)
        self.stock_changed.connect(self.products_widget._load_products)

        self.sales_widget = SalesInvoiceWidget(session, self.db_manager)
        self.stack.addWidget(self.sales_widget)

        self.purchase_widget = PurchaseInvoiceWidget(session, self.db_manager)
        self.stack.addWidget(self.purchase_widget)

        self.parties_widget = PartyWidget(session, self.db_manager)
        self.stack.addWidget(self.parties_widget)

        self.reports_widget = ReportsWidget(session, self.db_manager)
        self.stack.addWidget(self.reports_widget)

        self.settings_widget = SettingsWidget(self.config_service)
        self.stack.addWidget(self.settings_widget)

    def closeEvent(self, event):
        self.db_manager.close_session()
        event.accept()

    def open_invoice_for_edit(self, invoice_id: int, invoice_type: str):
        if invoice_type == 'sales':
            self.sidebar.setCurrentRow(1)
            self.sales_widget.load_existing_invoice(invoice_id)
        elif invoice_type == 'purchase':
            self.sidebar.setCurrentRow(2)
            self.purchase_widget.load_existing_invoice(invoice_id)