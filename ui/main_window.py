from PySide6.QtWidgets import (QHeaderView, QMainWindow, QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout, 
                              QPushButton, QHBoxLayout, QStackedWidget,
                              QMessageBox, QToolBar, QDialog, QLabel,
                              QComboBox, QSplitter, QListWidget, QListWidgetItem,
                              QFrame, QApplication)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QAction, QColor, QPalette, QFont
import datetime

from ui.add_item import AddItemWidget
from ui.extract_item import ExtractItemWidget
from ui.stock_view import StockViewWidget
from ui.invoice_view import InvoiceViewWidget
from models.extraction import Extraction
from ui.settings import SettingsWidget
from models.settings import Settings
from utils.printer_utils import print_invoice, show_print_dialog
from models.invoice import Invoice
from database import create_connection

class MainWindow(QMainWindow):
    def __init__(self, user_data=None):
        super().__init__()
        
        # Store user data
        self.user_data = user_data or {'id': 0, 'username': 'guest', 'is_admin': False}
        
        self.setWindowTitle(f"Stock Management System - {self.user_data['username']}")
        self.setMinimumSize(900, 700)
        
        # Apply modern styling to the application
        self.apply_modern_style()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for a cleaner look
        main_layout.setSpacing(0)  # Remove spacing between sidebar and content
        
        # Create toolbar
        self.create_toolbar()
        
        # Create sidebar container with border and enhanced styling
        sidebar_container = QFrame()
        sidebar_container.setObjectName("sidebarContainer")
        sidebar_container.setStyleSheet("""
            #sidebarContainer {
                background-color: #2c3e50;
                border-right: 1px solid #34495e;
                box-shadow: 2px 0px 5px rgba(0, 0, 0, 0.1);
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Create sidebar with enhanced styling
        self.sidebar = QListWidget()
        self.sidebar.setMaximumWidth(220)
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setFrameShape(QFrame.NoFrame)  # Remove border
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                border: none;
                outline: none;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item {
                color: #ecf0f1;
                height: 50px;
                padding-left: 15px;
                border-bottom: 1px solid #34495e;
                font-weight: 500;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                border-left: 5px solid #2980b9;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background-color: #34495e;
                border-left: 3px solid #7f8c8d;
            }
        """)
        
        # Add app title/logo to sidebar with enhanced styling
        logo_label = QLabel("Stock Management")
        logo_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            padding: 20px 15px;
            background-color: #1a2530;
            border-bottom: 2px solid #3498db;
        """)
        logo_label.setAlignment(Qt.AlignCenter)
        
        sidebar_layout.addWidget(logo_label)
        sidebar_layout.addWidget(self.sidebar)
        
        # Add items to sidebar
        self.add_sidebar_item("Add New Item")
        self.add_sidebar_item("Extract Items")
        self.add_sidebar_item("View Stock")
        self.add_sidebar_item("Manage Invoices")
        self.add_sidebar_item("History Operations")
        self.add_sidebar_item("Settings")
        
        # Create content container
        content_container = QFrame()
        content_container.setObjectName("contentContainer")
        content_container.setStyleSheet("""
            #contentContainer {
                background-color: #f5f5f5;
                border-left: 1px solid #ddd;
            }
        """)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create stacked widget for different screens
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
        """)
        
        # Create the different screens
        self.add_item_widget = AddItemWidget()
        self.extract_item_widget = ExtractItemWidget()
        self.stock_view_widget = StockViewWidget()
        self.invoice_view_widget = InvoiceViewWidget()
        self.history_widget = self.create_history_widget()
        self.settings_widget = SettingsWidget(self.user_data)
        
        # Connect print signals
        self.add_item_widget.item_added.connect(self.handle_item_added)
        self.extract_item_widget.extraction_completed.connect(self.handle_item_extracted)
        self.invoice_view_widget.invoice_updated.connect(self.handle_invoice_updated)
        
        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.add_item_widget)
        self.stacked_widget.addWidget(self.extract_item_widget)
        self.stacked_widget.addWidget(self.stock_view_widget)
        self.stacked_widget.addWidget(self.invoice_view_widget)
        self.stacked_widget.addWidget(self.history_widget)
        self.stacked_widget.addWidget(self.settings_widget)
        
        # Add stacked widget to content layout
        content_layout.addWidget(self.stacked_widget)
        
        # Add widgets to main layout
        main_layout.addWidget(sidebar_container)
        main_layout.addWidget(content_container, 1)  # Give content container more space
        
        # Connect sidebar signal
        self.sidebar.currentRowChanged.connect(self.change_page)
        
        # Show stock view by default
        self.sidebar.setCurrentRow(2)  # View Stock is at index 2
    
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
    
    def create_toolbar(self):
        """Create the application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)  # Make toolbar non-movable
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #3498db;
                border-bottom: 1px solid #2980b9;
                spacing: 10px;
                padding: 5px;
            }
        """)
        self.addToolBar(toolbar)
        
        # User info with improved styling
        user_label = QLabel(f"👤 {self.user_data['username']}")
        user_label.setStyleSheet("""
            color: white;
            font-weight: bold;
            padding: 5px 10px;
            background-color: rgba(0, 0, 0, 0.1);
            border-radius: 4px;
        """)
        toolbar.addWidget(user_label)
    
    def add_sidebar_item(self, text):
        """Add an item to the sidebar"""
        item = QListWidgetItem(text)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)  # Left align text with vertical centering
        self.sidebar.addItem(item)
    
    def change_page(self, index):
        """Change the current page based on sidebar selection"""
        # Refresh data as needed
        if index == 1:  # Extract Items
            self.extract_item_widget.refresh_items()
        elif index == 2:  # View Stock
            self.stock_view_widget.refresh_items()
        elif index == 3:  # Manage Invoices
            self.invoice_view_widget.refresh_suppliers()
        elif index == 4:  # History Operations
            self.refresh_history()
            
        # Change the page
        self.stacked_widget.setCurrentIndex(index)
    
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
                conn = create_connection()
                if conn:
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
                    
                    conn.close()
            except Exception as e:
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