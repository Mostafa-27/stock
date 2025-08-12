from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                QTableWidget, QTableWidgetItem, 
                                QPushButton, QLabel, QMessageBox, QHeaderView,
                                QAbstractItemView, QMenu, QDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QAction
from models.supplier import Supplier
from supplier_dialog import SupplierDialog

class SuppliersManagementWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        self.setWindowTitle("إدارة الموردين")
        self.setGeometry(100, 100, 1000, 700)
        
        # Set Arabic font
        font = QFont("Arial", 10)
        self.setFont(font)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("إدارة الموردين")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                background-color: #ecf0f1;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Suppliers management content directly (no tabs)
        self.suppliers_widget = self.create_suppliers_tab()
        layout.addWidget(self.suppliers_widget)
        
        central_widget.setLayout(layout)
    
    def create_suppliers_tab(self):
        """Create suppliers management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        self.add_supplier_btn = QPushButton("إضافة مورد جديد")
        self.add_supplier_btn.setStyleSheet(self.get_button_style("#27ae60"))
        self.add_supplier_btn.clicked.connect(self.add_supplier)
        
        self.edit_supplier_btn = QPushButton("تعديل المورد")
        self.edit_supplier_btn.setStyleSheet(self.get_button_style("#3498db"))
        self.edit_supplier_btn.clicked.connect(self.edit_supplier)
        
        self.delete_supplier_btn = QPushButton("حذف المورد")
        self.delete_supplier_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        self.delete_supplier_btn.clicked.connect(self.delete_supplier)
        
        self.refresh_suppliers_btn = QPushButton("تحديث")
        self.refresh_suppliers_btn.setStyleSheet(self.get_button_style("#f39c12"))
        self.refresh_suppliers_btn.clicked.connect(self.load_suppliers)
        
        buttons_layout.addWidget(self.add_supplier_btn)
        buttons_layout.addWidget(self.edit_supplier_btn)
        buttons_layout.addWidget(self.delete_supplier_btn)
        buttons_layout.addWidget(self.refresh_suppliers_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Suppliers table
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(6)
        self.suppliers_table.setHorizontalHeaderLabels([
            "اسم المورد", "الشخص المسؤول", "الهاتف", "البريد الإلكتروني", "شروط الدفع", "تاريخ الإضافة"
        ])
        
        # Table styling
        self.suppliers_table.setStyleSheet(self.get_table_style())
        self.suppliers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.suppliers_table.setAlternatingRowColors(True)
        
        # Auto resize columns
        header = self.suppliers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Double click to edit
        self.suppliers_table.doubleClicked.connect(self.edit_supplier)
        
        layout.addWidget(self.suppliers_table)
        widget.setLayout(layout)
        return widget
    
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
    
    def get_table_style(self):
        return """
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """
    
    def darken_color(self, color, factor=0.9):
        """Darken a hex color"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def load_data(self):
        """Load suppliers data"""
        self.load_suppliers()
    
    def load_suppliers(self):
        """Load suppliers data into table"""
        suppliers = Supplier.get_all_suppliers()
        self.suppliers_table.setRowCount(len(suppliers))
        
        for row, supplier in enumerate(suppliers):
            self.suppliers_table.setItem(row, 0, QTableWidgetItem(supplier['supplier_name']))
            self.suppliers_table.setItem(row, 1, QTableWidgetItem(supplier['contact_person'] or ''))
            self.suppliers_table.setItem(row, 2, QTableWidgetItem(supplier['phone'] or ''))
            self.suppliers_table.setItem(row, 3, QTableWidgetItem(supplier['email'] or ''))
            self.suppliers_table.setItem(row, 4, QTableWidgetItem(supplier['payment_terms'] or ''))
            
            date_added = supplier['date_added']
            if date_added:
                date_str = date_added.strftime('%Y-%m-%d') if hasattr(date_added, 'strftime') else str(date_added)
                self.suppliers_table.setItem(row, 5, QTableWidgetItem(date_str))
            else:
                self.suppliers_table.setItem(row, 5, QTableWidgetItem(''))
            
            # Store supplier data in the first item for easy access
            self.suppliers_table.item(row, 0).setData(Qt.UserRole, supplier)
    
    def add_supplier(self):
        """Add new supplier"""
        dialog = SupplierDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_suppliers()
    
    def edit_supplier(self):
        """Edit selected supplier"""
        current_row = self.suppliers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار مورد للتعديل")
            return
        
        supplier_data = self.suppliers_table.item(current_row, 0).data(Qt.UserRole)
        dialog = SupplierDialog(self, supplier_data)
        if dialog.exec() == QDialog.Accepted:
            self.load_suppliers()
    
    def delete_supplier(self):
        """Delete selected supplier"""
        current_row = self.suppliers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار مورد للحذف")
            return
        
        supplier_data = self.suppliers_table.item(current_row, 0).data(Qt.UserRole)
        supplier_name = supplier_data['supplier_name']
        
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   f"هل أنت متأكد من حذف المورد '{supplier_name}'؟",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if Supplier.delete_supplier(supplier_data['id']):
                QMessageBox.information(self, "نجح", "تم حذف المورد بنجاح")
                self.load_suppliers()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف المورد")