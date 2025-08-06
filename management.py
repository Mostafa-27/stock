from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                QTabWidget, QTableWidget, QTableWidgetItem, 
                                QPushButton, QLabel, QMessageBox, QHeaderView,
                                QAbstractItemView, QMenu, QDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QAction
from models.supplier import Supplier
from models.branch import Branch
from supplier_dialog import SupplierDialog
from branch_dialog import BranchDialog

class ManagementWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        self.setWindowTitle("إدارة الموردين والفروع")
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
        title = QLabel("إدارة الموردين والفروع")
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
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #5dade2;
                color: white;
            }
        """)
        
        # Suppliers tab
        self.suppliers_tab = self.create_suppliers_tab()
        self.tab_widget.addTab(self.suppliers_tab, "الموردين")
        
        # Branches tab
        self.branches_tab = self.create_branches_tab()
        self.tab_widget.addTab(self.branches_tab, "الفروع")
        
        layout.addWidget(self.tab_widget)
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
    
    def create_branches_tab(self):
        """Create branches management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        self.add_branch_btn = QPushButton("إضافة فرع جديد")
        self.add_branch_btn.setStyleSheet(self.get_button_style("#27ae60"))
        self.add_branch_btn.clicked.connect(self.add_branch)
        
        self.edit_branch_btn = QPushButton("تعديل الفرع")
        self.edit_branch_btn.setStyleSheet(self.get_button_style("#3498db"))
        self.edit_branch_btn.clicked.connect(self.edit_branch)
        
        self.delete_branch_btn = QPushButton("حذف الفرع")
        self.delete_branch_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        self.delete_branch_btn.clicked.connect(self.delete_branch)
        
        self.refresh_branches_btn = QPushButton("تحديث")
        self.refresh_branches_btn.setStyleSheet(self.get_button_style("#f39c12"))
        self.refresh_branches_btn.clicked.connect(self.load_branches)
        
        buttons_layout.addWidget(self.add_branch_btn)
        buttons_layout.addWidget(self.edit_branch_btn)
        buttons_layout.addWidget(self.delete_branch_btn)
        buttons_layout.addWidget(self.refresh_branches_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Branches table
        self.branches_table = QTableWidget()
        self.branches_table.setColumnCount(6)
        self.branches_table.setHorizontalHeaderLabels([
            "اسم الفرع", "كود الفرع", "المدير", "الهاتف", "تاريخ الافتتاح", "تاريخ الإضافة"
        ])
        
        # Table styling
        self.branches_table.setStyleSheet(self.get_table_style())
        self.branches_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.branches_table.setAlternatingRowColors(True)
        
        # Auto resize columns
        header = self.branches_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Double click to edit
        self.branches_table.doubleClicked.connect(self.edit_branch)
        
        layout.addWidget(self.branches_table)
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
        """Load both suppliers and branches data"""
        self.load_suppliers()
        self.load_branches()
    
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
    
    def load_branches(self):
        """Load branches data into table"""
        branches = Branch.get_all_branches()
        self.branches_table.setRowCount(len(branches))
        
        for row, branch in enumerate(branches):
            self.branches_table.setItem(row, 0, QTableWidgetItem(branch['branch_name']))
            self.branches_table.setItem(row, 1, QTableWidgetItem(branch['branch_code'] or ''))
            self.branches_table.setItem(row, 2, QTableWidgetItem(branch['manager_name'] or ''))
            self.branches_table.setItem(row, 3, QTableWidgetItem(branch['phone'] or ''))
            
            opening_date = branch['opening_date']
            if opening_date:
                date_str = opening_date.strftime('%Y-%m-%d') if hasattr(opening_date, 'strftime') else str(opening_date)
                self.branches_table.setItem(row, 4, QTableWidgetItem(date_str))
            else:
                self.branches_table.setItem(row, 4, QTableWidgetItem(''))
            
            date_added = branch['date_added']
            if date_added:
                date_str = date_added.strftime('%Y-%m-%d') if hasattr(date_added, 'strftime') else str(date_added)
                self.branches_table.setItem(row, 5, QTableWidgetItem(date_str))
            else:
                self.branches_table.setItem(row, 5, QTableWidgetItem(''))
            
            # Store branch data in the first item for easy access
            self.branches_table.item(row, 0).setData(Qt.UserRole, branch)
    
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
    
    def add_branch(self):
        """Add new branch"""
        dialog = BranchDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_branches()
    
    def edit_branch(self):
        """Edit selected branch"""
        current_row = self.branches_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار فرع للتعديل")
            return
        
        branch_data = self.branches_table.item(current_row, 0).data(Qt.UserRole)
        dialog = BranchDialog(self, branch_data)
        if dialog.exec() == QDialog.Accepted:
            self.load_branches()
    
    def delete_branch(self):
        """Delete selected branch"""
        current_row = self.branches_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار فرع للحذف")
            return
        
        branch_data = self.branches_table.item(current_row, 0).data(Qt.UserRole)
        branch_name = branch_data['branch_name']
        
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   f"هل أنت متأكد من حذف الفرع '{branch_name}'؟",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if Branch.delete_branch(branch_data['id']):
                QMessageBox.information(self, "نجح", "تم حذف الفرع بنجاح")
                self.load_branches()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف الفرع")