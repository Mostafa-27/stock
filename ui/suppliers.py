from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QComboBox, QLabel, QMessageBox, QFrame, QGroupBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from database import get_db_connection
import pyodbc

class SuppliersWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_suppliers()
        
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("إدارة الموردين")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 8px;
                text-align: center;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Supplier selection section
        supplier_frame = QGroupBox("اختيار المورد")
        supplier_frame.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        supplier_layout = QHBoxLayout(supplier_frame)
        
        # Supplier dropdown
        supplier_label = QLabel("المورد:")
        supplier_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        self.supplier_combo = QComboBox()
        self.supplier_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #7f8c8d;
                margin-right: 5px;
            }
        """)
        self.supplier_combo.currentTextChanged.connect(self.on_supplier_changed)
        
        # Refresh button
        refresh_btn = QPushButton("تحديث")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        refresh_btn.clicked.connect(self.load_suppliers)
        
        supplier_layout.addWidget(supplier_label)
        supplier_layout.addWidget(self.supplier_combo)
        supplier_layout.addWidget(refresh_btn)
        supplier_layout.addStretch()
        
        main_layout.addWidget(supplier_frame)
        
        # Invoices table
        table_frame = QGroupBox("فواتير المورد")
        table_frame.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(6)
        self.invoices_table.setHorizontalHeaderLabels([
            "رقم الفاتورة", "المورد", "المبلغ الإجمالي", "حالة الدفع", "المبلغ المدفوع", "تاريخ الإصدار"
        ])
        
        # Style the table
        self.invoices_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                gridline-color: #ecf0f1;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        # Configure table
        header = self.invoices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        table_layout.addWidget(self.invoices_table)
        main_layout.addWidget(table_frame)
        
        # Summary section
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)
        
        self.total_invoices_label = QLabel("إجمالي الفواتير: 0")
        self.total_amount_label = QLabel("إجمالي المبلغ: 0.00")
        self.paid_amount_label = QLabel("المبلغ المدفوع: 0.00")
        self.remaining_amount_label = QLabel("المبلغ المتبقي: 0.00")
        
        for label in [self.total_invoices_label, self.total_amount_label, 
                     self.paid_amount_label, self.remaining_amount_label]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 5px;
                }
            """)
        
        summary_layout.addWidget(self.total_invoices_label)
        summary_layout.addWidget(self.total_amount_label)
        summary_layout.addWidget(self.paid_amount_label)
        summary_layout.addWidget(self.remaining_amount_label)
        
        main_layout.addWidget(summary_frame)
        
    def load_suppliers(self):
        """Load all suppliers from the database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get unique suppliers from invoices table
            cursor.execute("SELECT DISTINCT supplier_name FROM invoices ORDER BY supplier_name")
            suppliers = cursor.fetchall()
            
            self.supplier_combo.clear()
            self.supplier_combo.addItem("-- اختر المورد --")
            
            for supplier in suppliers:
                if supplier[0]:  # Check if supplier name is not None
                    self.supplier_combo.addItem(supplier[0])
            
            conn.close()
            
        except pyodbc.Error as e:
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"فشل في تحميل الموردين: {e}")
    
    def on_supplier_changed(self, supplier_name):
        """Handle supplier selection change"""
        if supplier_name == "-- اختر المورد --" or not supplier_name:
            self.clear_table()
            self.update_summary([], 0, 0, 0)
            return
            
        self.load_supplier_invoices(supplier_name)
    
    def load_supplier_invoices(self, supplier_name):
        """Load invoices for the selected supplier"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get invoices for the selected supplier
            cursor.execute("""
                SELECT invoice_number, supplier_name, total_amount, payment_status, 
                       paid_amount, issue_date
                FROM invoices 
                WHERE supplier_name = ?
                ORDER BY issue_date DESC
            """, (supplier_name,))
            
            invoices = cursor.fetchall()
            
            # Populate the table
            self.populate_table(invoices)
            
            # Calculate summary
            total_invoices = len(invoices)
            total_amount = sum(invoice[2] for invoice in invoices)
            paid_amount = sum(invoice[4] for invoice in invoices)
            remaining_amount = total_amount - paid_amount
            
            self.update_summary(invoices, total_amount, paid_amount, remaining_amount)
            
            conn.close()
            
        except pyodbc.Error as e:
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"فشل في تحميل فواتير المورد: {e}")
    
    def populate_table(self, invoices):
        """Populate the invoices table with data"""
        self.invoices_table.setRowCount(len(invoices))
        
        for row, invoice in enumerate(invoices):
            # Invoice number
            self.invoices_table.setItem(row, 0, QTableWidgetItem(str(invoice[0])))
            
            # Supplier name
            self.invoices_table.setItem(row, 1, QTableWidgetItem(str(invoice[1])))
            
            # Total amount
            self.invoices_table.setItem(row, 2, QTableWidgetItem(f"{invoice[2]:.2f}"))
            
            # Payment status
            status_item = QTableWidgetItem(str(invoice[3]))
            if invoice[3] == "مدفوع":
                status_item.setBackground(Qt.green)
            elif invoice[3] == "غير مدفوع":
                status_item.setBackground(Qt.red)
            else:
                status_item.setBackground(Qt.yellow)
            self.invoices_table.setItem(row, 3, status_item)
            
            # Paid amount
            self.invoices_table.setItem(row, 4, QTableWidgetItem(f"{invoice[4]:.2f}"))
            
            # Issue date
            date_str = invoice[5].strftime("%Y-%m-%d") if invoice[5] else ""
            self.invoices_table.setItem(row, 5, QTableWidgetItem(date_str))
    
    def clear_table(self):
        """Clear the invoices table"""
        self.invoices_table.setRowCount(0)
    
    def update_summary(self, invoices, total_amount, paid_amount, remaining_amount):
        """Update the summary labels"""
        self.total_invoices_label.setText(f"إجمالي الفواتير: {len(invoices)}")
        self.total_amount_label.setText(f"إجمالي المبلغ: {total_amount:.2f}")
        self.paid_amount_label.setText(f"المبلغ المدفوع: {paid_amount:.2f}")
        self.remaining_amount_label.setText(f"المبلغ المتبقي: {remaining_amount:.2f}")