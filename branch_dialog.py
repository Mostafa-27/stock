from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                                QLineEdit, QTextEdit, QPushButton, QLabel, 
                                QMessageBox, QDateEdit, QCheckBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from models.branch import Branch
from datetime import datetime

class BranchDialog(QDialog):
    def __init__(self, parent=None, branch_data=None):
        super().__init__(parent)
        self.branch_data = branch_data
        self.is_edit_mode = branch_data is not None
        self.init_ui()
        
        if self.is_edit_mode:
            self.load_branch_data()
    
    def init_ui(self):
        self.setWindowTitle("تعديل الفرع" if self.is_edit_mode else "إضافة فرع جديد")
        self.setModal(True)
        self.resize(500, 600)
        
        # Set Arabic font
        font = QFont("Arial", 10)
        self.setFont(font)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("تعديل بيانات الفرع" if self.is_edit_mode else "إضافة فرع جديد")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Branch name (required)
        self.branch_name_edit = QLineEdit()
        self.branch_name_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("اسم الفرع *:", self.branch_name_edit)
        
        # Branch code
        self.branch_code_edit = QLineEdit()
        self.branch_code_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("كود الفرع:", self.branch_code_edit)
        
        # Manager name
        self.manager_name_edit = QLineEdit()
        self.manager_name_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("اسم المدير:", self.manager_name_edit)
        
        # Phone
        self.phone_edit = QLineEdit()
        self.phone_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("رقم الهاتف:", self.phone_edit)
        
        # Address
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.address_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("العنوان:", self.address_edit)
        
        # Opening date
        self.opening_date_edit = QDateEdit()
        self.opening_date_edit.setDate(QDate.currentDate())
        self.opening_date_edit.setCalendarPopup(True)
        self.opening_date_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("تاريخ الافتتاح:", self.opening_date_edit)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("ملاحظات:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("حفظ التعديلات" if self.is_edit_mode else "إضافة الفرع")
        self.save_button.setStyleSheet(self.get_button_style("#27ae60"))
        self.save_button.clicked.connect(self.save_branch)
        
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.setStyleSheet(self.get_button_style("#e74c3c"))
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_input_style(self):
        return """
            QLineEdit, QTextEdit, QDateEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 12px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus {
                border-color: #3498db;
                outline: none;
            }
        """
    
    def get_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
            }}
        """
    
    def darken_color(self, color, factor=0.9):
        """Darken a hex color"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def load_branch_data(self):
        """Load existing branch data into form fields"""
        if self.branch_data:
            self.branch_name_edit.setText(self.branch_data.get('branch_name', ''))
            self.branch_code_edit.setText(self.branch_data.get('branch_code', '') or '')
            self.manager_name_edit.setText(self.branch_data.get('manager_name', '') or '')
            self.phone_edit.setText(self.branch_data.get('phone', '') or '')
            self.address_edit.setPlainText(self.branch_data.get('address', '') or '')
            self.notes_edit.setPlainText(self.branch_data.get('notes', '') or '')
            
            # Set opening date if available
            if self.branch_data.get('opening_date'):
                opening_date = self.branch_data['opening_date']
                if isinstance(opening_date, datetime):
                    qdate = QDate(opening_date.year, opening_date.month, opening_date.day)
                    self.opening_date_edit.setDate(qdate)
    
    def save_branch(self):
        """Save branch data to database"""
        # Validate required fields
        branch_name = self.branch_name_edit.text().strip()
        if not branch_name:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم الفرع")
            return
        
        # Get form data
        branch_code = self.branch_code_edit.text().strip() or None
        manager_name = self.manager_name_edit.text().strip() or None
        phone = self.phone_edit.text().strip() or None
        address = self.address_edit.toPlainText().strip() or None
        notes = self.notes_edit.toPlainText().strip() or None
        
        # Convert QDate to datetime
        qdate = self.opening_date_edit.date()
        opening_date = datetime(qdate.year(), qdate.month(), qdate.day())
        
        try:
            if self.is_edit_mode:
                # Update existing branch
                success = Branch.update_branch(
                    self.branch_data['id'],
                    branch_name,
                    branch_code,
                    manager_name,
                    phone,
                    address,
                    opening_date,
                    notes
                )
                if success:
                    QMessageBox.information(self, "نجح", "تم تحديث بيانات الفرع بنجاح")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في تحديث بيانات الفرع")
            else:
                # Add new branch
                branch_id = Branch.add_branch(
                    branch_name,
                    branch_code,
                    manager_name,
                    phone,
                    address,
                    opening_date,
                    notes
                )
                if branch_id:
                    QMessageBox.information(self, "نجح", "تم إضافة الفرع بنجاح")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في إضافة الفرع")
        
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")