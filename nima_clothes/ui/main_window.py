"""
Main Window for Nima Clothes Application
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

from ui.product_widget import ProductWidget
from ui.party_widget import PartyWidget
from ui.sales_invoice_widget import SalesInvoiceWidget
from ui.purchase_invoice_widget import PurchaseInvoiceWidget
from ui.reports_widget import ReportsWidget


class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        
        self.db_manager = db_manager
        self.setWindowTitle("Nima Clothes - نرم‌افزار حسابداری فروشگاه پوشاک")
        self.setMinimumSize(1200, 800)
        
        # Set RTL layout for Persian
        self.setLayoutDirection(Qt.RightToLeft)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Create stacked widget for pages
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # Initialize pages
        self._initialize_pages()
        
        # Connect sidebar selection to page switching
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        
        # Apply styles
        self._apply_styles()
    
    def _create_sidebar(self) -> QListWidget:
        """Create sidebar navigation"""
        sidebar = QListWidget()
        sidebar.setFixedWidth(200)
        sidebar.setSpacing(5)
        
        # Add menu items with Persian labels
        items = [
            ("فاکتور فروش", "sales"),
            ("فاکتور خرید", "purchase"),
            ("کالاها", "products"),
            ("طرف حساب‌ها", "parties"),
            ("گزارش‌ها", "reports"),
        ]
        
        for label, key in items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            item.setFont(QFont("B Nazanin", 12, QFont.Bold))
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            sidebar.addItem(item)
        
        sidebar.setCurrentRow(0)
        return sidebar
    
    def _initialize_pages(self):
        """Initialize all pages"""
        session = self.db_manager.get_session()
        
        # Sales Invoice Page
        self.sales_widget = SalesInvoiceWidget(session, self.db_manager)
        self.stack.addWidget(self.sales_widget)
        
        # Purchase Invoice Page
        self.purchase_widget = PurchaseInvoiceWidget(session, self.db_manager)
        self.stack.addWidget(self.purchase_widget)
        
        # Products Page
        self.products_widget = ProductWidget(session, self.db_manager)
        self.stack.addWidget(self.products_widget)
        
        # Parties Page
        self.parties_widget = PartyWidget(session, self.db_manager)
        self.stack.addWidget(self.parties_widget)
        
        # Reports Page
        self.reports_widget = ReportsWidget(session, self.db_manager)
        self.stack.addWidget(self.reports_widget)
    
    def _apply_styles(self):
        """Apply application styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QListWidget {
                background-color: #2c3e50;
                color: white;
                border: none;
                outline: none;
            }
            
            QListWidget::item {
                padding: 15px 10px;
                border-bottom: 1px solid #34495e;
            }
            
            QListWidget::item:selected {
                background-color: #3498db;
            }
            
            QListWidget::item:hover {
                background-color: #34495e;
            }
            
            QStackedWidget {
                background-color: white;
            }
        """)
    
    def closeEvent(self, event):
        """Handle application close"""
        self.db_manager.close_session()
        event.accept()
