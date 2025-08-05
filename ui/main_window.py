from PySide6.QtWidgets import (QHeaderView, QMainWindow, QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout, 
                              QPushButton, QHBoxLayout, QStackedWidget,
                              QMessageBox, QToolBar, QDialog, QLabel,
                              QComboBox, QSplitter, QListWidget, QListWidgetItem,
                              QFrame, QApplication, QTabWidget)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QAction, QColor, QPalette, QFont, QPixmap
import datetime
import pyodbc

from ui.add_item import AddItemWidget
from ui.extract_item import ExtractItemWidget
from ui.stock_view import StockViewWidget
from ui.invoice_view import InvoiceViewWidget
from models.extraction import Extraction
from ui.settings import SettingsWidget
from ui.pizza_main import PizzaMainWidget
from ui.suppliers import SuppliersWidget
from models.settings import Settings
from utils.printer_utils import print_invoice, show_print_dialog
from models.invoice import Invoice
from database import get_db_connection

class MainWindow(QMainWindow):
    def __init__(self, user_data=None):
        super().__init__()
        
        # Store user data
        self.user_data = user_data or {'id': 0, 'username': 'guest', 'is_admin': False}
        
        self.setWindowTitle(f"Pizza Melano - {self.user_data['username']}")
        self.setMinimumSize(1200, 800)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Apply modern styling to the application
        self.apply_modern_style()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create custom title bar
        self.create_title_bar(main_layout)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create header bar
        header_bar = QFrame()
        header_bar.setFixedHeight(100)  # Increased height from 60 to 100
        header_bar.setStyleSheet("""
            QFrame {
                background-color: #663399;
                border-bottom: 3px solid #552288;
            }
        """)
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(30, 15, 30, 15)  # Increased margins
        
        # User info section with logout button
        user_section = QFrame()
        user_section_layout = QVBoxLayout(user_section)
        user_section_layout.setContentsMargins(0, 0, 0, 0)
        user_section_layout.setSpacing(5)
        
        user_info = QLabel(f"مستخدم: {self.user_data['username']}")
        user_info.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # Logout button
        self.logout_btn = QPushButton("تسجيل الخروج")
        self.logout_btn.setFixedSize(100, 25)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.logout_btn.clicked.connect(self.logout)
        
        user_section_layout.addWidget(user_info)
        user_section_layout.addWidget(self.logout_btn)
        
        # Current date and time
        current_date = QLabel("2025-08-05")
        current_time = QLabel("12:51:44 PM")
        invoice_label = QLabel("August-00004 :الفاتورة الحالي")
        
        for label in [current_date, current_time, invoice_label]:
            label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 16px;  /* Increased font size */
                    font-weight: bold;
                    background: transparent;
                }
            """)
        
        header_layout.addWidget(user_section)
        header_layout.addWidget(current_date)
        header_layout.addWidget(current_time)
        header_layout.addStretch()
        header_layout.addWidget(invoice_label)
        
        # Pizza Melano logo with actual image on the right
        logo_label = QLabel()
        logo_pixmap = QPixmap("logo.png")
        if not logo_pixmap.isNull():
            # Scale the logo to fit in the header
            scaled_pixmap = logo_pixmap.scaled(120, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            # Fallback text if image not found
            logo_label.setText("PIZZA\nMELANO")
            logo_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-size: 14px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
        
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedSize(120, 70)
        logo_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 2px solid #e74c3c;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        header_layout.addWidget(logo_label)
        
        # Add header to main layout
        main_layout.addWidget(header_bar)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #663399;
                color: white;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #e74c3c;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #552288;
            }
        """)
        
        # Create the different screens
        self.add_item_widget = AddItemWidget()
        self.extract_item_widget = ExtractItemWidget()
        self.stock_view_widget = StockViewWidget()
        self.invoice_view_widget = InvoiceViewWidget()
        self.pizza_main_widget = PizzaMainWidget()
        self.suppliers_widget = SuppliersWidget()
        self.settings_widget = SettingsWidget(self.user_data)
        
        # Connect print signals
        self.add_item_widget.item_added.connect(self.handle_item_added)
        self.extract_item_widget.extraction_completed.connect(self.handle_item_extracted)
        self.invoice_view_widget.invoice_updated.connect(self.handle_invoice_updated)
        
        # Add tabs with Arabic text
        # self.tab_widget.addTab(self.pizza_main_widget, "الطولات")  # Tables
        self.tab_widget.addTab(self.invoice_view_widget, "الفواتير")  # Food Menu
        self.tab_widget.addTab(self.stock_view_widget, "المخزون")  # Reports
        self.tab_widget.addTab(self.extract_item_widget, "تصدير منتجات")  # Add Products
        self.tab_widget.addTab(self.suppliers_widget, "الموردين")  # Suppliers
        self.tab_widget.addTab(self.add_item_widget, "إضافة منتجات")  # Settings
        self.tab_widget.addTab(self.settings_widget, "إعدادات")  # Logout
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.change_page)
        
        # Show pizza main view by default (الطولات)
        self.tab_widget.setCurrentIndex(0)  # Pizza main is at index 0
    
    def apply_modern_style(self):
        """Apply modern styling to the entire application"""
        # Set application font
        font = QFont("Segoe UI", 10)
        QApplication.setFont(font)
        
        # Set global stylesheet
        self.setStyleSheet("""
            /* General styles */
            QWidget {
                font-family: 'Segoe UI', sans-serif;
            }
            
            /* Button styles */
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
            
            /* Table styles */
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                alternate-background-color: #f9f9f9;
                gridline-color: #ddd;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 6px;
                font-weight: bold;
            }
            
            /* Input field styles */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #3498db;
            }
            
            /* Combobox styles */
            QComboBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            /* Scrollbar styles */
            QScrollBar:vertical {
                border: none;
                background: #f5f5f5;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a8a8a8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f5f5f5;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #c1c1c1;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #a8a8a8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
    
    def create_title_bar(self, main_layout):
        """Create custom title bar with window controls"""
        title_bar = QFrame()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-bottom: 1px solid #34495e;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        title_layout.setSpacing(0)
        
        # Window title
        title_label = QLabel(f"Pizza Melano - {self.user_data['username']}")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Window control buttons
        button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 16px;
                font-weight: bold;
                width: 30px;
                height: 30px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #34495e;
                border-radius: 3px;
            }
        """
        
        # Minimize button
        minimize_btn = QPushButton("−")
        minimize_btn.setStyleSheet(button_style)
        minimize_btn.clicked.connect(self.showMinimized)
        minimize_btn.setToolTip("Minimize")
        
        # Maximize/Restore button
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setStyleSheet(button_style)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.maximize_btn.setToolTip("Maximize")
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 18px;
                font-weight: bold;
                width: 30px;
                height: 30px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
                border-radius: 3px;
            }
        """)
        close_btn.clicked.connect(self.close)
        close_btn.setToolTip("Close")
        
        title_layout.addWidget(minimize_btn)
        title_layout.addWidget(self.maximize_btn)
        title_layout.addWidget(close_btn)
        
        # Make title bar draggable
        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move
        
        main_layout.addWidget(title_bar)
    
    def toggle_maximize(self):
        """Toggle between maximized and normal window state"""
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("□")
            self.maximize_btn.setToolTip("Maximize")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")
            self.maximize_btn.setToolTip("Restore")
    
    def title_bar_mouse_press(self, event):
        """Handle mouse press on title bar for dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def title_bar_mouse_move(self, event):
        """Handle mouse move on title bar for dragging"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def create_toolbar(self):
        """Create the application toolbar - hidden for Pizza Melano design"""
        # Hide toolbar for frameless design
        pass
    
    def change_page(self, index):
        """Change the current page based on tab selection"""
        # Refresh data as needed
        if index == 1:  # Food Menu (Invoice View)
            self.invoice_view_widget.refresh_suppliers()
        elif index == 2:  # Reports (Stock View)
            self.stock_view_widget.refresh_items()
        elif index == 3:  # Add Products (Extract Items)
            self.extract_item_widget.refresh_items()
        elif index == 4:  # Settings (Add Items)
            pass  # No refresh needed for add items
        elif index == 5:  # Logout (Settings)
            pass  # Settings widget handles its own refresh
    
    def create_history_widget(self):
        """Create the history operations widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title label
        title_label = QLabel("History Operations")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        # Create table for history
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Item Name", "Operation Type", "Quantity", "Details"
        ])
        self.history_table.setAlternatingRowColors(True)  # Alternate row colors
        
        # Set table properties
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.verticalHeader().setVisible(False)  # Hide vertical header
        
        layout.addWidget(self.history_table)
        
        # Add buttons in a horizontal layout
        buttons_layout = QHBoxLayout()
        
        # Add refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_history)
        
        # Add print button for history operations
        print_btn = QPushButton("🖨️ Print History")
        print_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        print_btn.clicked.connect(self.print_history)
        
        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addWidget(print_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        return widget
        
    def print_history(self):
        """Print the history operations table"""
        try:
            # Get all rows from the history table
            rows = []
            for row in range(self.history_table.rowCount()):
                row_data = {
                    'date': self.history_table.item(row, 0).text(),
                    'item_name': self.history_table.item(row, 1).text(),
                    'operation_type': self.history_table.item(row, 2).text(),
                    'quantity': self.history_table.item(row, 3).text(),
                    'details': self.history_table.item(row, 4).text()
                }
                rows.append(row_data)
            
            if not rows:
                QMessageBox.information(self, "No Data", "There is no history data to print.")
                return
            
            # Create a simplified invoice-like structure for history
            history_data = {
                'invoice_number': f"HIST-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                'supplier_name': "History Operations Report",
                'total_amount': 0,
                'payment_status': 'Report',
                'paid_amount': 0,
                'issue_date': datetime.datetime.now().strftime('%Y-%m-%d'),
                'due_date': None,
                'notes': f"History operations report generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            # Create items data for the report
            items_data = []
            for row in rows:
                items_data.append({
                    'id': 0,
                    'item_name': f"{row['item_name']} ({row['operation_type']})",
                    'quantity': row['quantity'],
                    'price_per_unit': 0,
                    'invoice_number': history_data['invoice_number'],
                    'supplier_name': row['details'],
                    'date_added': row['date']
                })
            
            # Print the history report
            from utils.printer_utils import show_print_dialog
            if show_print_dialog(self, history_data, items_data, is_history=True):
                QMessageBox.information(self, "Success", "History report sent to printer")
            else:
                QMessageBox.warning(self, "Printing Cancelled", "Printing was cancelled or failed.")
                
        except Exception as e:
            QMessageBox.critical(self, "Printing Error", f"Error printing history report: {e}")
    
    def refresh_history(self):
        """Refresh the history operations table"""
        # Clear table
        self.history_table.setRowCount(0)
        
        # Get all extractions
        extractions = Extraction.get_all_extractions()
        
        # Add extractions to table
        for extraction in extractions:
            row_position = self.history_table.rowCount()
            self.history_table.insertRow(row_position)
            
            self.history_table.setItem(row_position, 0, QTableWidgetItem(extraction['date_extracted']))
            self.history_table.setItem(row_position, 1, QTableWidgetItem(extraction['item_name']))
            self.history_table.setItem(row_position, 2, QTableWidgetItem("Extraction"))
            self.history_table.setItem(row_position, 3, QTableWidgetItem(str(extraction['quantity_extracted'])))
            self.history_table.setItem(row_position, 4, QTableWidgetItem(f"To: {extraction['branch_name']}"))
        
        # Get all items (additions)
        from models.item import Item
        items = Item.get_all_items()
        
        # Add items to table
        for item in items:
            row_position = self.history_table.rowCount()
            self.history_table.insertRow(row_position)
            
            self.history_table.setItem(row_position, 0, QTableWidgetItem(item.date_added))
            self.history_table.setItem(row_position, 1, QTableWidgetItem(item.item_name))
            self.history_table.setItem(row_position, 2, QTableWidgetItem("Addition"))
            self.history_table.setItem(row_position, 3, QTableWidgetItem(str(item.quantity)))
            self.history_table.setItem(row_position, 4, QTableWidgetItem(f"Invoice: {item.invoice_number}"))
        
        # Sort by date (newest first)
        self.history_table.sortItems(0, Qt.DescendingOrder)
    
    def handle_item_added(self, invoice_number):
        """Handle auto-printing when an item is added"""
        if Settings.get_setting('auto_print', True):
            try:
                # Get invoice data
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM invoices WHERE invoice_number = ?", 
                    (invoice_number,)
                )
                invoice_row = cursor.fetchone()
                
                if invoice_row:
                    invoice_data = {
                        'id': invoice_row[0],
                        'invoice_number': invoice_row[1],
                        'supplier_name': invoice_row[2],
                        'total_amount': invoice_row[3],
                        'payment_status': invoice_row[4],
                        'paid_amount': invoice_row[5],
                        'issue_date': invoice_row[6],
                        'due_date': invoice_row[7],
                        'notes': invoice_row[8]
                    }
                    
                    # Get items for this invoice
                    cursor.execute(
                        "SELECT * FROM items WHERE invoice_number = ?",
                        (invoice_number,)
                    )
                    items_data = []
                    for item_row in cursor.fetchall():
                        items_data.append({
                            'id': item_row[0],
                            'item_name': item_row[1],
                            'quantity': item_row[2],
                            'price_per_unit': item_row[3],
                            'invoice_number': item_row[4],
                            'supplier_name': item_row[5],
                            'date_added': item_row[6]
                        })
                    
                    # Print the invoice
                    print_invoice(invoice_data, items_data)
                
                if 'conn' in locals():
                    conn.close()
            except pyodbc.Error as e:
                QMessageBox.warning(self, "Printing Error", f"Error printing invoice: {e}")
    
    def handle_item_extracted(self, item_id, branch_name, quantity):
        """Handle auto-printing when an item is extracted"""
        if Settings.get_setting('auto_print', True):
            try:
                # Get item data from database
                from models.item import Item
                item = Item.get_item_by_id(item_id)
                
                if item:
                    # Create a simplified invoice-like structure for extraction
                    extraction_data = {
                        'invoice_number': f"EXT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                        'supplier_name': f"Extraction to {branch_name}",
                        'total_amount': item.price_per_unit * quantity,
                        'payment_status': 'Extraction',
                        'paid_amount': 0,
                        'issue_date': datetime.datetime.now().strftime('%Y-%m-%d'),
                        'due_date': None,
                        'notes': f"Item extracted from inventory to {branch_name}"
                    }
                    
                    # Create a single item entry
                    items_data = [{
                        'id': item.id,
                        'item_name': item.item_name,
                        'quantity': quantity,
                        'price_per_unit': item.price_per_unit,
                        'invoice_number': extraction_data['invoice_number'],
                        'supplier_name': extraction_data['supplier_name'],
                        'date_added': datetime.datetime.now().strftime('%Y-%m-%d')
                    }]
                    
                    # Print the extraction receipt
                    print_invoice(extraction_data, items_data)
            except Exception as e:
                QMessageBox.warning(self, "Printing Error", f"Error printing extraction receipt: {e}")
    
    def handle_invoice_updated(self, invoice_number):
        """Handle auto-printing when an invoice is updated"""
        if Settings.get_setting('auto_print', True):
            try:
                # Get invoice data and print
                invoice_data = Invoice.get_invoice_by_number(invoice_number)
                if invoice_data:
                    # Get items for this invoice
                    items_data = Invoice.get_items_by_invoice(invoice_number)
                    
                    # Print the invoice
                    print_invoice(invoice_data, items_data)
            except Exception as e:
                QMessageBox.warning(self, "Printing Error", f"Error printing invoice: {e}")
    
    def show_print_dialog(self):
        """Show dialog to select an invoice to print"""
        # Get all invoices
        invoices = Invoice.get_all_invoices()
        
        if not invoices:
            QMessageBox.information(self, "No Invoices", "There are no invoices to print.")
            return
        
        # Create a dialog to select an invoice
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Invoice to Print")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Create a combo box with invoice numbers
        combo = QComboBox()
        for invoice in invoices:
            combo.addItem(f"{invoice['invoice_number']} - {invoice['supplier_name']}", 
                         invoice['invoice_number'])
        
        layout.addWidget(QLabel("Select Invoice:"))
        layout.addWidget(combo)
        
        # Create buttons
        buttons = QHBoxLayout()
        print_btn = QPushButton("Print")
        cancel_btn = QPushButton("Cancel")
        
        buttons.addWidget(print_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
        
        # Connect buttons
        cancel_btn.clicked.connect(dialog.reject)
        
        def print_selected_invoice():
            invoice_number = combo.currentData()
            if invoice_number:
                # Get invoice data
                invoice_data = Invoice.get_invoice_by_number(invoice_number)
                if invoice_data:
                    # Get items for this invoice
                    items_data = Invoice.get_items_by_invoice(invoice_number)
                    
                    # Show print dialog
                    if show_print_dialog(self, invoice_data, items_data):
                        dialog.accept()
                    else:
                        QMessageBox.warning(self, "Printing Error", "Failed to print invoice.")
        
        print_btn.clicked.connect(print_selected_invoice)
        
        # Show the dialog
        dialog.exec()
    
    def logout(self):
        """Handle logout functionality"""
        reply = QMessageBox.question(self, 'تسجيل الخروج', 
                                   'هل أنت متأكد من تسجيل الخروج؟',
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Close the main window
            self.close()
            
            # Import and show login widget
            from ui.login import LoginWidget
            self.login_widget = LoginWidget()
            self.login_widget.show()