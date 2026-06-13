"""
Party Management Widget - Enhanced UI & RTL Support
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                                QLabel, QLineEdit, QComboBox, QPushButton,
                                QTableWidget, QTableWidgetItem, QMessageBox,
                                QGroupBox, QHeaderView)
from PySide6.QtCore import Qt
from sqlalchemy.orm import Session

from models.party import PartyType
from services.party_service import PartyService


class PartyWidget(QWidget):
    WIDGET_STYLESHEET = """
        QLabel { color: #1e293b; font-size: 13px; background-color: transparent; }
        QLabel#title { font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
        
        QGroupBox {
            font-weight: bold; color: #334155; border: 1px solid #e2e8f0;
            border-radius: 8px; margin-top: 12px; padding: 15px 10px 10px 10px;
            background-color: #ffffff;
        }
        QGroupBox::title { subcontrol-origin: margin; right: 15px; padding: 0 8px; color: #1e293b; }
        
        QPushButton#save_btn { background-color: #10b981; }
        QPushButton#save_btn:hover { background-color: #059669; }
        QPushButton#update_btn { background-color: #3b82f6; }
        QPushButton#update_btn:hover { background-color: #2563eb; }
        QPushButton#delete_btn { background-color: #ef4444; }
        QPushButton#delete_btn:hover { background-color: #dc2626; }
        QPushButton#clear_btn { background-color: #64748b; }
        QPushButton#clear_btn:hover { background-color: #475569; }
        
        QTableWidget {
            border: 1px solid #e2e8f0; border-radius: 6px; gridline-color: #f1f5f9;
            selection-background-color: #dbeafe; selection-color: #1e293b;
            background-color: #ffffff; color: #334155;
        }
        QHeaderView::section {
            background-color: #f8fafc; color: #475569; padding: 10px;
            font-weight: bold; border: none; border-bottom: 2px solid #e2e8f0;
        }
    """

    def __init__(self, session: Session, db_manager):
        super().__init__()

        self.session = session
        self.db_manager = db_manager
        self.party_service = PartyService(session)

        self.setStyleSheet(self.WIDGET_STYLESHEET)

        self._init_ui()
        self._load_parties()

    @staticmethod
    def _to_persian_digits(text) -> str:
        return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

    @staticmethod
    def _to_english_digits(text: str) -> str:
        return text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        title = QLabel("مدیریت طرف حساب‌ها")
        title.setObjectName("title")
        layout.addWidget(title)

        form_group = QGroupBox("اطلاعات طرف حساب")
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("نام شخص یا شرکت")
        form_layout.addRow("نام:", self.name_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("شماره تماس (اختیاری)")
        form_layout.addRow("تلفن:", self.phone_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItem("مشتری", PartyType.CUSTOMER)
        self.type_combo.addItem("فروشنده", PartyType.SUPPLIER)
        self.type_combo.addItem("هر دو", PartyType.BOTH)
        form_layout.addRow("نوع:", self.type_combo)

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("آدرس کامل (اختیاری)")
        form_layout.addRow("آدرس:", self.address_edit)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.save_btn = QPushButton("ذخیره")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.setMinimumHeight(42)
        self.save_btn.clicked.connect(self._save_party)

        self.update_btn = QPushButton("ویرایش")
        self.update_btn.setObjectName("update_btn")
        self.update_btn.setMinimumHeight(42)
        self.update_btn.setEnabled(False)
        self.update_btn.clicked.connect(self._update_party)

        self.delete_btn = QPushButton("حذف")
        self.delete_btn.setObjectName("delete_btn")
        self.delete_btn.setMinimumHeight(42)
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_party)

        self.clear_btn = QPushButton("پاک کردن فرم")
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.setMinimumHeight(42)
        self.clear_btn.clicked.connect(self._clear_form)

        for btn in [self.save_btn, self.update_btn, self.delete_btn, self.clear_btn]:
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        table_group = QGroupBox("لیست طرف حساب‌ها")
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(8, 8, 8, 8)

        self.parties_table = QTableWidget()
        headers = ["شناسه", "نام", "تلفن", "نوع", "آدرس"]
        self.parties_table.setColumnCount(len(headers))
        self.parties_table.setHorizontalHeaderLabels(headers)

        header = self.parties_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.parties_table.verticalHeader().setVisible(False)
        self.parties_table.setAlternatingRowColors(True)
        self.parties_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.parties_table.itemSelectionChanged.connect(self._on_table_selection)

        table_layout.addWidget(self.parties_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

    def _load_parties(self):
        parties = self.party_service.get_all_parties()
        self.parties_table.setRowCount(0)

        for party in parties:
            row = self.parties_table.rowCount()
            self.parties_table.insertRow(row)

            items = [
                str(party.id),
                party.name,
                party.phone or "",
                party.party_type.value,
                party.address or ""
            ]

            for col, text in enumerate(items):
                display_text = self._to_persian_digits(text)
                item = QTableWidgetItem(display_text)
                if col == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self.parties_table.setItem(row, col, item)

    def _get_selected_party_id(self) -> int | None:
        selected_ranges = self.parties_table.selectedRanges()
        if not selected_ranges:
            return None
        row = selected_ranges[0].topRow()
        id_item = self.parties_table.item(row, 0)
        if not id_item:
            return None
        try:
            return int(self._to_english_digits(id_item.text()))
        except (ValueError, IndexError):
            return None

    def _save_party(self):
        try:
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "خطا", "نام طرف حساب الزامی است")
                return

            self.party_service.create_party(
                name=name,
                party_type=self.type_combo.currentData(),
                phone=self.phone_edit.text().strip() or None,
                address=self.address_edit.text().strip() or None
            )

            QMessageBox.information(self, "موفق", "طرف حساب با موفقیت ذخیره شد")
            self._clear_form()
            self._load_parties()

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره: {str(e)}")

    def _update_party(self):
        pid = self._get_selected_party_id()
        if pid is None:
            QMessageBox.warning(self, "خطا", "لطفاً یک مورد را انتخاب کنید")
            return

        try:
            self.party_service.update_party(
                party_id=pid,
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
        pid = self._get_selected_party_id()
        if pid is None:
            QMessageBox.warning(self, "خطا", "لطفاً یک مورد را انتخاب کنید")
            return

        reply = QMessageBox.question(
            self, "تأیید حذف",
            "آیا از حذف این طرف حساب اطمینان دارید؟",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.party_service.delete_party(pid)
                QMessageBox.information(self, "موفق", "طرف حساب حذف شد")
                self._clear_form()
                self._load_parties()
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در حذف: {str(e)}")

    def _on_table_selection(self):
        try:
            selected_ranges = self.parties_table.selectedRanges()
            if not selected_ranges:
                self.update_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                return

            row = selected_ranges[0].topRow()
            if row < 0 or row >= self.parties_table.rowCount():
                return

            id_item = self.parties_table.item(row, 0)
            if not id_item:
                return

            self.update_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)

            def _safe_text(r, c):
                item = self.parties_table.item(r, c)
                return item.text() if item else ""

            self.name_edit.setText(_safe_text(row, 1))
            self.phone_edit.setText(_safe_text(row, 2))
            self.address_edit.setText(_safe_text(row, 4))

            # تنظیم combobox بر اساس مقدار ذخیره شده
            type_value = _safe_text(row, 3)
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i).value == type_value:
                    self.type_combo.setCurrentIndex(i)
                    break

        except Exception as e:
            import traceback
            print(f"[ERROR] Party table selection failed: {e}")
            traceback.print_exc()

    def _clear_form(self):
        self.name_edit.clear()
        self.phone_edit.clear()
        self.address_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)