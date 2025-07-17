from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                              QPushButton, QHBoxLayout, QStackedWidget,
                              QMessageBox, QToolBar, QDialog, QLabel,
                              QComboBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction
import datetime

from ui.add_item import AddItemWidget
from ui.extract_item import ExtractItemWidget
from ui.stock_view import StockViewWidget
from ui.invoice_view import InvoiceViewWidget
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
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create navigation buttons
        nav_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add New Item")
        self.extract_btn = QPushButton("Extract Items")
        self.view_btn = QPushButton("View Stock")
        self.invoice_btn = QPushButton("Manage Invoices")
        
        nav_layout.addWidget(self.add_btn)
        nav_layout.addWidget(self.extract_btn)
        nav_layout.addWidget(self.view_btn)
        nav_layout.addWidget(self.invoice_btn)
        
        # Create stacked widget for different screens
        self.stacked_widget = QStackedWidget()
        
        # Create the different screens
        self.add_item_widget = AddItemWidget()
        self.extract_item_widget = ExtractItemWidget()
        self.stock_view_widget = StockViewWidget()
        self.invoice_view_widget = InvoiceViewWidget()
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
        self.stacked_widget.addWidget(self.settings_widget)
        
        # Add layouts to main layout
        main_layout.addLayout(nav_layout)
        main_layout.addWidget(self.stacked_widget)
        
        # Connect signals
        self.add_btn.clicked.connect(self.show_add_item)
        self.extract_btn.clicked.connect(self.show_extract_item)
        self.view_btn.clicked.connect(self.show_stock_view)
        self.invoice_btn.clicked.connect(self.show_invoice_view)
        
        # Show stock view by default
        self.show_stock_view()
    
    def create_toolbar(self):
        """Create the application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
        
        # Print invoice action
        print_action = QAction("Print Invoice", self)
        print_action.triggered.connect(self.show_print_dialog)
        toolbar.addAction(print_action)
    
    def show_add_item(self):
        self.stacked_widget.setCurrentWidget(self.add_item_widget)
        self.add_btn.setEnabled(False)
        self.extract_btn.setEnabled(True)
        self.view_btn.setEnabled(True)
        self.invoice_btn.setEnabled(True)
    
    def show_extract_item(self):
        self.extract_item_widget.refresh_items()
        self.stacked_widget.setCurrentWidget(self.extract_item_widget)
        self.add_btn.setEnabled(True)
        self.extract_btn.setEnabled(False)
        self.view_btn.setEnabled(True)
        self.invoice_btn.setEnabled(True)
    
    def show_stock_view(self):
        self.stock_view_widget.refresh_items()
        self.stacked_widget.setCurrentWidget(self.stock_view_widget)
        self.add_btn.setEnabled(True)
        self.extract_btn.setEnabled(True)
        self.view_btn.setEnabled(False)
        self.invoice_btn.setEnabled(True)
        
    def show_invoice_view(self):
        self.invoice_view_widget.refresh_suppliers()
        self.stacked_widget.setCurrentWidget(self.invoice_view_widget)
        self.add_btn.setEnabled(True)
        self.extract_btn.setEnabled(True)
        self.view_btn.setEnabled(True)
        self.invoice_btn.setEnabled(False)
    
    def show_settings(self):
        self.stacked_widget.setCurrentWidget(self.settings_widget)
        self.add_btn.setEnabled(True)
        self.extract_btn.setEnabled(True)
        self.view_btn.setEnabled(True)
        self.invoice_btn.setEnabled(True)
    
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