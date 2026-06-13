"""
Nima Clothes - Accounting Software for Clothing Store

Main Application Entry Point

"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from core.database import DatabaseManager
from ui.main_window import MainWindow
from core.config import ConfigService

def main():
    # Initialize application
    app = QApplication(sys.argv)
    app.setApplicationName("htm Clothes")
    app.setOrganizationName("htm")
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    font_path = os.path.join(os.path.dirname(__file__), "static", "fonts","Arad-Regular.ttf")

    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font = QFont(font_families[0], 10)
                app.setFont(font)
                print(f"Font loaded from file: {font_families[0]}")
            else:
                app.setFont(QFont("Tahoma", 10))
        else:
            app.setFont(QFont("Tahoma", 10))
    else:
        available_fonts = QFontDatabase.families()
        if "Vazir" in available_fonts:
            app.setFont(QFont("Vazir", 10))
        elif "Tahoma" in available_fonts:
            app.setFont(QFont("Tahoma", 10))
        else:
            app.setFont(QFont("Arial", 10))
        print(f"Font file not found: {font_path}, using system font")

    # Initialize database
    config_service = ConfigService()

    # ✅ ارسال به DatabaseManager
    db = DatabaseManager(config_service=config_service)

    db.initialize()

    # Create and show main window
    window = MainWindow(db, config_service)
    window.showMaximized()
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()