from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                              QTableWidgetItem, QLineEdit, QPushButton, QLabel,
                              QComboBox, QHeaderView)
from PySide6.QtCore import Qt, QDate

from models.item import Item

class StockViewWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create search and filter controls
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("البحث بواسطة اسم المنتج...")
        
        self.invoice_filter = QLineEdit()
        self.invoice_filter.setPlaceholderText("تصفية بواسطة رقم الفاتورة...")
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("ترتيب بالاسم", "name")
        self.sort_combo.addItem("ترتيب بالكمية (من الأقل للأكبر)", "quantity_asc")
        self.sort_combo.addItem("ترتيب بالكمية (من الأكبر للأقل)", "quantity_desc")
        self.sort_combo.addItem("ترتيب بالتاريخ (الأحدث أولا)", "date_desc")
        self.sort_combo.addItem("ترتيب بالتاريخ (الأقدم أولا)", "date_asc")
        
        self.search_button = QPushButton("بحث")
        self.reset_button = QPushButton("إعادة تعيين")
        
        filter_layout.addWidget(QLabel("بحث:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("فاتورة:"))
        filter_layout.addWidget(self.invoice_filter)
        filter_layout.addWidget(QLabel("ترتيب:"))
        filter_layout.addWidget(self.sort_combo)
        filter_layout.addWidget(self.search_button)
        filter_layout.addWidget(self.reset_button)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["رقم", "اسم المنتج", "الكمية", "السعر لكل وحدة", "رقم الفاتورة", "تاريخ الإضافة"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Add widgets to layout
        layout.addLayout(filter_layout)
        layout.addWidget(self.table)
        
        # Connect signals
        self.search_button.clicked.connect(self.apply_filters)
        self.reset_button.clicked.connect(self.reset_filters)
        
        # Initialize table
        self.refresh_items()
    
    def refresh_items(self):
        # Get all items
        items = Item.get_all_items()
        self.populate_table(items)
    
    def apply_filters(self):
        search_term = self.search_input.text()
        invoice_filter = self.invoice_filter.text()
        
        # Apply filters
        if search_term and invoice_filter:
            # If both filters are applied, we need to filter manually
            all_items = Item.get_all_items()
            filtered_items = []
            
            for item in all_items:
                if (search_term.lower() in item.item_name.lower() and 
                    invoice_filter.lower() in item.invoice_number.lower()):
                    filtered_items.append(item)
            
            self.populate_table(filtered_items)
        elif search_term:
            items = Item.search_items(search_term)
            self.populate_table(items)
        elif invoice_filter:
            items = Item.filter_by_invoice(invoice_filter)
            self.populate_table(items)
        else:
            self.refresh_items()
    
    def reset_filters(self):
        self.search_input.clear()
        self.invoice_filter.clear()
        self.sort_combo.setCurrentIndex(0)
        self.refresh_items()
    
    def populate_table(self, items):
        # Sort items based on selected sort option
        sort_option = self.sort_combo.currentData()
        
        if sort_option == "name":
            items.sort(key=lambda x: x.item_name)
        elif sort_option == "quantity_asc":
            items.sort(key=lambda x: x.quantity)
        elif sort_option == "quantity_desc":
            items.sort(key=lambda x: x.quantity, reverse=True)
        elif sort_option == "date_desc":
            items.sort(key=lambda x: x.date_added, reverse=True)
        elif sort_option == "date_asc":
            items.sort(key=lambda x: x.date_added)
        
        # Clear table
        self.table.setRowCount(0)
        
        # Populate table
        for row, item in enumerate(items):
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(item.id)))
            self.table.setItem(row, 1, QTableWidgetItem(item.item_name))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.quantity)))
            self.table.setItem(row, 3, QTableWidgetItem(f"${item.price_per_unit:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(item.invoice_number))
            self.table.setItem(row, 5, QTableWidgetItem(str(item.date_added) if item.date_added else ""))