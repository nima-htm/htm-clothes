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

        QPushButton {
            color: white;
            border: 1px solid #5d4037;
            border-radius: 3px;
            padding: 5px 20px;
            font-size: 14px;
            font-weight: bold;
            min-width: 80px;
        }

        QPushButton#save_btn   { background-color: #6B8E6B; }
        QPushButton#update_btn { background-color: #6B8E6B; }
        QPushButton#delete_btn { background-color: #CD5C5C; }
        QPushButton#clear_btn  { background-color: #8B4513; }

        QPushButton:hover    { border: 1px solid white; }
        QPushButton:disabled { background-color: #8B7355; color: #ccc; }

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
        self.party_service = PartyService(session)
        self._suppress_search = False
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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("مدیریت طرف حساب‌ها")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        form_group = QGroupBox("اطلاعات طرف حساب")
        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(15, 10, 15, 15)
        form_layout.setSpacing(12)

        # ================================
        # یک خط: نام | تلفن | نوع | آدرس
        # ================================
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        name_label = QLabel("نام:")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("نام شخص یا شرکت")
        self.name_edit.textChanged.connect(self._on_name_search)
        row1.addWidget(name_label)
        row1.addWidget(self.name_edit, 3)

        phone_label = QLabel("تلفن:")
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("شماره تماس")
        row1.addWidget(phone_label)
        row1.addWidget(self.phone_edit, 2)

        type_label = QLabel("نوع:")
        self.type_combo = QComboBox()
        self.type_combo.addItem("مشتری", PartyType.CUSTOMER)
        self.type_combo.addItem("فروشنده", PartyType.SUPPLIER)
        self.type_combo.addItem("هر دو", PartyType.BOTH)
        self.type_combo.setFixedWidth(110)
        row1.addWidget(type_label)
        row1.addWidget(self.type_combo)

        address_label = QLabel("آدرس:")
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("آدرس کامل")
        row1.addWidget(address_label)
        row1.addWidget(self.address_edit, 4)

        form_layout.addLayout(row1)


        # دکمه‌ها
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.save_btn = QPushButton("ذخیره")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.setMinimumHeight(36)
        self.save_btn.clicked.connect(self._save_party)

        self.update_btn = QPushButton("ویرایش")
        self.update_btn.setObjectName("update_btn")
        self.update_btn.setMinimumHeight(36)
        self.update_btn.setEnabled(False)
        self.update_btn.clicked.connect(self._update_party)

        self.delete_btn = QPushButton("حذف")
        self.delete_btn.setObjectName("delete_btn")
        self.delete_btn.setMinimumHeight(36)
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_party)

        self.clear_btn = QPushButton("پاک کردن فرم")
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.setMinimumHeight(36)
        self.clear_btn.clicked.connect(self._clear_form)


        btn_layout.addStretch()
        for btn in [self.save_btn, self.update_btn, self.delete_btn, self.clear_btn]:
            btn_layout.addWidget(btn)
        form_layout.addLayout(btn_layout)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # جدول
        table_group = QGroupBox("لیست طرف حساب‌ها")
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)

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
        self.parties_table.setEditTriggers(QTableWidget.NoEditTriggers)
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
        self._suppress_search = True
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

            type_value = _safe_text(row, 3)
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i).value == type_value:
                    self.type_combo.setCurrentIndex(i)
                    break

        except Exception as e:
            import traceback
            print(f"[ERROR] Party table selection failed: {e}")
            traceback.print_exc()
        finally:
            self._suppress_search = False  # همیشه اجرا می‌شه

    def _clear_form(self):
        self._suppress_search = True
        self.name_edit.clear()
        self.phone_edit.clear()
        self.address_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self._suppress_search = False
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self._filter_table()

    def _on_name_search(self, text: str):
        if self._suppress_search:
            return
        query = text.strip().lower()
        for row in range(self.parties_table.rowCount()):
            item = self.parties_table.item(row, 1)  # ستون نام
            match = query in (item.text().lower() if item else "")
            self.parties_table.setRowHidden(row, not match)

    def _filter_table(self, name_query: str = ""):
        query = name_query.strip().lower()
        for row in range(self.parties_table.rowCount()):
            item = self.parties_table.item(row, 1)
            match = query in (item.text().lower() if item else "") if query else True
            self.parties_table.setRowHidden(row, not match)