from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QMessageBox, QHBoxLayout, 
                               QComboBox, QCheckBox, QFileDialog, QGroupBox,
                               QFormLayout, QTabWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from models.user import User
from models.settings import Settings
from utils.printer_utils import get_available_printers, get_default_printer

class SettingsWidget(QWidget):
    settings_updated = Signal()  # Signal emitted when settings are updated
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user  # Store the current user data
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create tabs
        tabs = QTabWidget()
        
        # Create user tab
        user_tab = QWidget()
        user_layout = QVBoxLayout(user_tab)
        
        # Password change group
        password_group = QGroupBox("تغيير كلمة المرور")
        password_layout = QFormLayout()
        
        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.Password)
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        
        password_layout.addRow("كلمة المرور الحالية:", self.current_password)
        password_layout.addRow("كلمة المرور الجديدة:", self.new_password)
        password_layout.addRow("تأكيد كلمة المرور:", self.confirm_password)
        
        self.change_password_btn = QPushButton("تغيير كلمة المرور")
        self.change_password_btn.clicked.connect(self.change_password)
        password_layout.addRow("", self.change_password_btn)
        
        password_group.setLayout(password_layout)
        user_layout.addWidget(password_group)
        
        # Add user management if admin
        if self.current_user.get('is_admin', False):
            admin_group = QGroupBox("إدارة المستخدمين (للمدير)")
            admin_layout = QVBoxLayout()
            
            # TODO: Add user management UI here if needed
            admin_note = QLabel("يمكن توسيع وظائف إدارة المستخدمين هنا.")
            admin_layout.addWidget(admin_note)
            
            admin_group.setLayout(admin_layout)
            user_layout.addWidget(admin_group)
        
        # Create printer tab
        printer_tab = QWidget()
        printer_layout = QVBoxLayout(printer_tab)
        
        # Printer selection
        printer_group = QGroupBox("إعدادات الطابعة")
        printer_form = QFormLayout()
        
        self.printer_combo = QComboBox()
        self.refresh_printers_btn = QPushButton("تحديث")
        self.refresh_printers_btn.clicked.connect(self.load_printers)
        
        printer_selector = QHBoxLayout()
        printer_selector.addWidget(self.printer_combo)
        printer_selector.addWidget(self.refresh_printers_btn)
        
        printer_form.addRow("الطابعة الافتراضية:", printer_selector)
        
        # Auto-print option
        self.auto_print = QCheckBox("طباعة تلقائية بعد المعاملات")
        printer_form.addRow("", self.auto_print)
        
        printer_group.setLayout(printer_form)
        printer_layout.addWidget(printer_group)
        
        # Create company tab
        company_tab = QWidget()
        company_layout = QVBoxLayout(company_tab)
        
        # Logo settings
        logo_group = QGroupBox("شعار الشركة")
        logo_layout = QVBoxLayout()
        
        # Logo preview
        self.logo_preview = QLabel("لم يتم اختيار شعار")
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setMinimumHeight(150)
        self.logo_preview.setStyleSheet("border: 1px solid #ccc;")
        logo_layout.addWidget(self.logo_preview)
        
        # Logo selection
        logo_buttons = QHBoxLayout()
        self.select_logo_btn = QPushButton("اختيار شعار")
        self.select_logo_btn.clicked.connect(self.select_logo)
        self.clear_logo_btn = QPushButton("مسح الشعار")
        self.clear_logo_btn.clicked.connect(self.clear_logo)
        
        logo_buttons.addWidget(self.select_logo_btn)
        logo_buttons.addWidget(self.clear_logo_btn)
        logo_layout.addLayout(logo_buttons)
        
        logo_group.setLayout(logo_layout)
        company_layout.addWidget(logo_group)
        
        # Add tabs
        tabs.addTab(user_tab, "إعدادات المستخدم")
        tabs.addTab(printer_tab, "إعدادات الطابعة")
        tabs.addTab(company_tab, "إعدادات الشركة")
        
        main_layout.addWidget(tabs)
        
        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_btn = QPushButton("حفظ الإعدادات")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;"
        )
        save_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(save_layout)
    
    def load_settings(self):
        # Load printer settings
        self.load_printers()
        
        # Set default printer
        default_printer = Settings.get_setting('default_printer')
        if default_printer:
            index = self.printer_combo.findText(default_printer)
            if index >= 0:
                self.printer_combo.setCurrentIndex(index)
        
        # Set auto-print option
        auto_print = Settings.get_setting('auto_print', True)
        self.auto_print.setChecked(auto_print)
        
        # Load logo
        logo_path = Settings.get_setting('company_logo', '')
        if logo_path and logo_path.strip():
            self.update_logo_preview(logo_path)
    
    def load_printers(self):
        # Clear current items
        self.printer_combo.clear()
        
        # Get available printers
        printers = get_available_printers()
        
        # Add printers to combo box
        for printer in printers:
            self.printer_combo.addItem(printer)
        
        # Select system default printer if none is set
        if self.printer_combo.count() > 0 and self.printer_combo.currentText() == "":
            default_printer = get_default_printer()
            if default_printer:
                index = self.printer_combo.findText(default_printer)
                if index >= 0:
                    self.printer_combo.setCurrentIndex(index)
    
    def change_password(self):
        current_pwd = self.current_password.text()
        new_pwd = self.new_password.text()
        confirm_pwd = self.confirm_password.text()
        
        # Validate inputs
        if not current_pwd or not new_pwd or not confirm_pwd:
            QMessageBox.warning(self, "خطأ في الإدخال", "جميع حقول كلمة المرور مطلوبة.")
            return
        
        if new_pwd != confirm_pwd:
            QMessageBox.warning(self, "خطأ في الإدخال", "كلمات المرور الجديدة غير متطابقة.")
            return
        
        # Verify current password
        status, _ = User.login(self.current_user['username'], current_pwd)
        if status != User.LOGIN_SUCCESS:
            QMessageBox.warning(self, "خطأ في المصادقة", "كلمة المرور الحالية غير صحيحة.")
            return
        
        # Change password
        if User.change_password(self.current_user['id'], new_pwd):
            QMessageBox.information(self, "نجح", "تم تغيير كلمة المرور بنجاح.")
            # Clear password fields
            self.current_password.clear()
            self.new_password.clear()
            self.confirm_password.clear()
        else:
            QMessageBox.critical(self, "خطأ", "فشل في تغيير كلمة المرور.")
    
    def select_logo(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("الصور (*.png *.jpg *.jpeg *.bmp *.gif)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                logo_path = selected_files[0]
                self.update_logo_preview(logo_path)
    
    def clear_logo(self):
        self.logo_preview.setPixmap(QPixmap())
        self.logo_preview.setText("لم يتم اختيار شعار")
    
    def update_logo_preview(self, logo_path):
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_preview.setPixmap(pixmap)
            self.logo_preview.setText("")  # Clear text when showing image
            # Store the path for saving later
            self.logo_path = logo_path
        else:
            self.logo_preview.setText("فشل في تحميل الصورة")
    
    def save_settings(self):
        # Save printer settings
        if self.printer_combo.currentText():
            Settings.update_setting('default_printer', self.printer_combo.currentText())
        
        # Save auto-print setting
        Settings.update_setting('auto_print', self.auto_print.isChecked(), 'boolean')
        
        # Save logo path if set
        if hasattr(self, 'logo_path') and self.logo_path:
            Settings.update_setting('company_logo', self.logo_path, 'file_path')
        elif self.logo_preview.text() == "لم يتم اختيار شعار":
            # Clear logo path if no logo is selected
            Settings.update_setting('company_logo', '', 'file_path')
        
        # Notify that settings have been updated
        self.settings_updated.emit()
        
        QMessageBox.information(self, "نجح", "تم حفظ الإعدادات بنجاح.")