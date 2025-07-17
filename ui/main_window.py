from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                              QPushButton, QHBoxLayout, QStackedWidget)
from PySide6.QtCore import Qt

from ui.add_item import AddItemWidget
from ui.extract_item import ExtractItemWidget
from ui.stock_view import StockViewWidget
from ui.invoice_view import InvoiceViewWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Stock Management System")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
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
        
        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.add_item_widget)
        self.stacked_widget.addWidget(self.extract_item_widget)
        self.stacked_widget.addWidget(self.stock_view_widget)
        self.stacked_widget.addWidget(self.invoice_view_widget)
        
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