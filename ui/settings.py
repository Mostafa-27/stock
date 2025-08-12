from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QMessageBox, QHBoxLayout, 
                               QComboBox, QCheckBox, QGroupBox,
                               QFormLayout)
from PySide6.QtCore import Qt, Signal

from models.settings import Settings
from utils.printer_utils import get_available_printers, get_default_printer

class PrinterSettingsWidget(QWidget):
    settings_updated = Signal()  # Signal emitted when settings are updated
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user  # Store the current user data
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        # Create main layout
        main_layout = QVBoxLayout(self)
        
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
        main_layout.addWidget(printer_group)
        
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
    
    def save_settings(self):
        # Save printer settings
        if self.printer_combo.currentText():
            Settings.update_setting('default_printer', self.printer_combo.currentText())
        
        # Save auto-print setting
        Settings.update_setting('auto_print', self.auto_print.isChecked(), 'boolean')
        
        # Notify that settings have been updated
        self.settings_updated.emit()
        
        QMessageBox.information(self, "نجح", "تم حفظ الإعدادات بنجاح.")