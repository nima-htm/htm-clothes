"""
Nima Clothes - Accounting Software for Clothing Store
Main Application Entry Point
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from core.database import DatabaseManager
from ui.main_window import MainWindow


def main():
    # Initialize application
    app = QApplication(sys.argv)
    app.setApplicationName("Nima Clothes")
    app.setOrganizationName("Nima Software")
    
    # Set RTL for Persian support
    app.setLayoutDirection(Qt.RightToLeft)
    
    # Initialize database
    db = DatabaseManager()
    db.initialize()
    
    # Create and show main window
    window = MainWindow(db)
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
