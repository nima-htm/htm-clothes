"""
Party Management Widget (Customers and Suppliers)
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                                QLabel, QLineEdit, QComboBox, QPushButton, 
                                QTableWidget, QTableWidgetItem, QMessageBox,
                                QGroupBox, QHeaderView)
from PySide6.QtCore import Qt
from sqlalchemy.orm import Session

from models.party import Party, PartyType
from services.party_service import PartyService


class PartyWidget(QWidget):
    def __init__(self, session: Session, db_manager):
        super().__init__()
        
        self.session = session
        self.db_manager = db_manager
        self.party_service = PartyService(session)
        
        self._init_ui()
        self._load_parties()
    
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("مدیریت طرف حساب‌ها")
        title.setFont(self.font())
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Form group
        form_group = QGroupBox("اطلاعات طرف حساب")
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.setSpacing(10)
        
        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("نام را وارد کنید")
        form_layout.addRow("نام:", self.name_edit)
        
        # Phone
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("شماره تماس")
        form_layout.addRow("تلفن:", self.phone_edit)
        
        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItem("مشتری", PartyType.CUSTOMER)
        self.type_combo.addItem("فروشنده", PartyType.SUPPLIER)
        self.type_combo.addItem("هر دو", PartyType.BOTH)
        form_layout.addRow("نوع:", self.type_combo)
        
        # Address
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("آدرس (اختیاری)")
        form_layout.addRow("آدرس:", self.address_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.save_btn = QPushButton("ذخیره")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self._save_party)
        btn_layout.addWidget(self.save_btn)
        
        self.update_btn = QPushButton("ویرایش")
        self.update_btn.setMinimumHeight(40)
        self.update_btn.clicked.connect(self._update_party)
        self.update_btn.setEnabled(False)
        btn_layout.addWidget(self.update_btn)
        
        self.delete_btn = QPushButton("حذف")
        self.delete_btn.setMinimumHeight(40)
        self.delete_btn.clicked.connect(self._delete_party)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)
        
        self.clear_btn = QPushButton("پاک کردن فرم")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self._clear_form)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        # Parties table
        table_group = QGroupBox("لیست طرف حساب‌ها")
        table_layout = QVBoxLayout()
        
        self.parties_table = QTableWidget()
        self.parties_table.setColumnCount(5)
        self.parties_table.setHorizontalHeaderLabels([
            "شناسه", "نام", "تلفن", "نوع", "آدرس"
        ])
        
        header = self.parties_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        self.parties_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.parties_table.itemSelectionChanged.connect(self._on_table_selection)
        
        table_layout.addWidget(self.parties_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Set RTL
        self.setLayoutDirection(Qt.RightToLeft)
    
    def _load_parties(self):
        """Load parties into table"""
        parties = self.party_service.get_all_parties()
        
        self.parties_table.setRowCount(0)
        for party in parties:
            row = self.parties_table.rowCount()
            self.parties_table.insertRow(row)
            
            self.parties_table.setItem(row, 0, QTableWidgetItem(str(party.id)))
            self.parties_table.setItem(row, 1, QTableWidgetItem(party.name))
            self.parties_table.setItem(row, 2, QTableWidgetItem(party.phone or ""))
            self.parties_table.setItem(row, 3, QTableWidgetItem(party.party_type.value))
            self.parties_table.setItem(row, 4, QTableWidgetItem(party.address or ""))
    
    def _save_party(self):
        """Save new party"""
        try:
            name = self.name_edit.text().strip()
            
            if not name:
                QMessageBox.warning(self, "خطا", "نام الزامی است")
                return
            
            party_type = self.type_combo.currentData()
            phone = self.phone_edit.text().strip() or None
            address = self.address_edit.text().strip() or None
            
            self.party_service.create_party(
                name=name,
                party_type=party_type,
                phone=phone,
                address=address
            )
            
            QMessageBox.information(self, "موفق", "طرف حساب با موفقیت ذخیره شد")
            self._clear_form()
            self._load_parties()
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره: {str(e)}")
    
    def _update_party(self):
        """Update selected party"""
        selected_rows = self.parties_table.selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "خطا", "لطفاً یک مورد را انتخاب کنید")
            return
        
        row = selected_rows[0].row()
        party_id = int(self.parties_table.item(row, 0).text())
        
        try:
            self.party_service.update_party(
                party_id=party_id,
                name=self.name_edit.text().strip(),
                party_type=self.type_combo.currentData(),
                phone=self.phone_edit.text().strip() or None,
                address=self.address_edit.text().strip() or None
            )
            
            QMessageBox.information(self, "موفق", "اطلاعات با موفقیت ویرایش شد")
            self._load_parties()
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ویرایش: {str(e)}")
    
    def _delete_party(self):
        """Delete selected party"""
        selected_rows = self.parties_table.selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "خطا", "لطفاً یک مورد را انتخاب کنید")
            return
        
        reply = QMessageBox.question(
            self, "تأیید حذف",
            "آیا از حذف این طرف حساب اطمینان دارید؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            row = selected_rows[0].row()
            party_id = int(self.parties_table.item(row, 0).text())
            
            try:
                self.party_service.delete_party(party_id)
                QMessageBox.information(self, "موفق", "طرف حساب حذف شد")
                self._clear_form()
                self._load_parties()
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در حذف: {str(e)}")
    
    def _on_table_selection(self):
        """Handle table selection"""
        selected_rows = self.parties_table.selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.update_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            self.name_edit.setText(self.parties_table.item(row, 1).text())
            self.phone_edit.setText(self.parties_table.item(row, 2).text())
            self.address_edit.setText(self.parties_table.item(row, 4).text())
    
    def _clear_form(self):
        """Clear form fields"""
        self.name_edit.clear()
        self.phone_edit.clear()
        self.address_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
