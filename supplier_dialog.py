from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                                QLineEdit, QTextEdit, QPushButton, QLabel, 
                                QMessageBox, QDateEdit, QCheckBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from models.supplier import Supplier

class SupplierDialog(QDialog):
    def __init__(self, parent=None, supplier_data=None):
        super().__init__(parent)
        self.supplier_data = supplier_data
        self.is_edit_mode = supplier_data is not None
        self.init_ui()
        
        if self.is_edit_mode:
            self.load_supplier_data()
    
    def init_ui(self):
        self.setWindowTitle("تعديل المورد" if self.is_edit_mode else "إضافة مورد جديد")
        self.setModal(True)
        self.resize(500, 600)
        
        # Set Arabic font
        font = QFont("Arial", 10)
        self.setFont(font)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("تعديل بيانات المورد" if self.is_edit_mode else "إضافة مورد جديد")
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
        
        # Supplier name (required)
        self.supplier_name_edit = QLineEdit()
        self.supplier_name_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("اسم المورد *:", self.supplier_name_edit)
        
        # Contact person
        self.contact_person_edit = QLineEdit()
        self.contact_person_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("الشخص المسؤول:", self.contact_person_edit)
        
        # Phone
        self.phone_edit = QLineEdit()
        self.phone_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("رقم الهاتف:", self.phone_edit)
        
        # Email
        self.email_edit = QLineEdit()
        self.email_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("البريد الإلكتروني:", self.email_edit)
        
        # Address
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.address_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("العنوان:", self.address_edit)
        
        # Payment terms
        self.payment_terms_edit = QLineEdit()
        self.payment_terms_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("شروط الدفع:", self.payment_terms_edit)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("ملاحظات:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("حفظ التعديلات" if self.is_edit_mode else "إضافة المورد")
        self.save_button.setStyleSheet(self.get_button_style("#27ae60"))
        self.save_button.clicked.connect(self.save_supplier)
        
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.setStyleSheet(self.get_button_style("#e74c3c"))
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_input_style(self):
        return """
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 12px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus {
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
    
    def load_supplier_data(self):
        """Load existing supplier data into form fields"""
        if self.supplier_data:
            self.supplier_name_edit.setText(self.supplier_data.get('supplier_name', ''))
            self.contact_person_edit.setText(self.supplier_data.get('contact_person', '') or '')
            self.phone_edit.setText(self.supplier_data.get('phone', '') or '')
            self.email_edit.setText(self.supplier_data.get('email', '') or '')
            self.address_edit.setPlainText(self.supplier_data.get('address', '') or '')
            self.payment_terms_edit.setText(self.supplier_data.get('payment_terms', '') or '')
            self.notes_edit.setPlainText(self.supplier_data.get('notes', '') or '')
    
    def save_supplier(self):
        """Save supplier data to database"""
        # Validate required fields
        supplier_name = self.supplier_name_edit.text().strip()
        if not supplier_name:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم المورد")
            return
        
        # Get form data
        contact_person = self.contact_person_edit.text().strip() or None
        phone = self.phone_edit.text().strip() or None
        email = self.email_edit.text().strip() or None
        address = self.address_edit.toPlainText().strip() or None
        payment_terms = self.payment_terms_edit.text().strip() or None
        notes = self.notes_edit.toPlainText().strip() or None
        
        try:
            if self.is_edit_mode:
                # Update existing supplier
                success = Supplier.update_supplier(
                    self.supplier_data['id'],
                    supplier_name,
                    contact_person,
                    phone,
                    email,
                    address,
                    payment_terms,
                    notes
                )
                if success:
                    QMessageBox.information(self, "نجح", "تم تحديث بيانات المورد بنجاح")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في تحديث بيانات المورد")
            else:
                # Add new supplier
                supplier_id = Supplier.add_supplier(
                    supplier_name,
                    contact_person,
                    phone,
                    email,
                    address,
                    payment_terms,
                    notes
                )
                if supplier_id:
                    QMessageBox.information(self, "نجح", "تم إضافة المورد بنجاح")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في إضافة المورد")
        
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")