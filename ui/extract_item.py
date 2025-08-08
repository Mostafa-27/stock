from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                              QSpinBox, QPushButton, QLabel, QMessageBox,
                              QComboBox, QTableWidget, QTableWidgetItem, 
                              QHBoxLayout, QGroupBox, QHeaderView, QScrollArea)
from PySide6.QtCore import Qt, Signal

from models.item import Item
from models.extraction import Extraction
from models.branch import Branch

class ExtractItemWidget(QWidget):
    # Signal to notify when an extraction is completed successfully
    extraction_completed = Signal(list, str, str)  # items_list, branch_name, extracted_by
    
    def __init__(self):
        super().__init__()
        self.items_to_extract = []  # List to store items before extraction
        
        # Create scroll area for the widget
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        
        # Create layout for scroll widget
        layout = QVBoxLayout(scroll_widget)
        
        # Extraction Information Group
        extraction_group = QGroupBox("معلومات الاستخراج")
        extraction_layout = QFormLayout(extraction_group)
        
        # Branch selection
        self.branch_combo = QComboBox()
        extraction_layout.addRow("الفرع *:", self.branch_combo)
        
        # Extracted by field
        self.extracted_by = QLineEdit()
        self.extracted_by.setPlaceholderText("أدخل اسم الشخص الذي يستخرج المنتجات")
        extraction_layout.addRow("مستخرج بواسطة *:", self.extracted_by)
        
        # Item Selection Group
        item_group = QGroupBox("إضافة منتجات للاستخراج")
        item_layout = QFormLayout(item_group)
        
        # Create form fields
        self.item_combo = QComboBox()
        self.quantity = QSpinBox()
        self.quantity.setMinimum(1)
        self.quantity.setMaximum(10000)
        
        # Add fields to form layout
        item_layout.addRow("المنتج *:", self.item_combo)
        item_layout.addRow("الكمية للاستخراج *:", self.quantity)
        
        # Create available quantity label
        self.available_label = QLabel("متاح: 0")
        item_layout.addRow("حالة المخزون:", self.available_label)
        
        # Add item button
        self.add_item_button = QPushButton("إضافة منتج للقائمة")
        item_layout.addRow("", self.add_item_button)
        
        # Items List Table
        list_group = QGroupBox("المنتجات للاستخراج")
        list_layout = QVBoxLayout(list_group)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(['اسم المنتج', 'المخزون الحالي', 'الكمية للاستخراج', 'المتبقي'])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Table buttons
        table_buttons_layout = QHBoxLayout()
        self.remove_item_button = QPushButton("حذف المحدد")
        self.clear_all_button = QPushButton("مسح الكل")
        
        table_buttons_layout.addWidget(self.remove_item_button)
        table_buttons_layout.addWidget(self.clear_all_button)
        table_buttons_layout.addStretch()
        
        list_layout.addWidget(self.items_table)
        list_layout.addLayout(table_buttons_layout)
        
        # Main Action Buttons
        button_layout = QHBoxLayout()
        self.extract_button = QPushButton("استخراج جميع المنتجات")
        self.clear_form_button = QPushButton("مسح النموذج")
        
        self.extract_button.setStyleSheet("font-weight: bold; padding: 10px;")
        
        button_layout.addWidget(self.extract_button)
        button_layout.addWidget(self.clear_form_button)
        
        # Add all groups to main layout
        layout.addWidget(extraction_group)
        layout.addWidget(item_group)
        layout.addWidget(list_group)
        layout.addLayout(button_layout)
        
        # Add stretch to push content to the top
        layout.addStretch()
        
        # Connect signals
        self.extract_button.clicked.connect(self.extract_all_items)
        self.clear_form_button.clicked.connect(self.clear_form)
        self.add_item_button.clicked.connect(self.add_item_to_list)
        self.remove_item_button.clicked.connect(self.remove_selected_item)
        self.clear_all_button.clicked.connect(self.clear_items_list)
        self.item_combo.currentIndexChanged.connect(self.update_available_quantity)
        
        # Initialize items and branches
        self.items = []
        self.refresh_items()
        self.load_branches()
    
    def refresh_items(self):
        # Get all items
        self.items = Item.get_all_items()
        
        # Clear and repopulate combo box
        self.item_combo.clear()
        
        for item in self.items:
            if item.quantity > 0:  # Only show items with stock
                self.item_combo.addItem(f"{item.item_name} (#{item.id})", item.id)
        
        # Update available quantity
        self.update_available_quantity()
    
    def update_available_quantity(self):
        if self.item_combo.count() == 0:
            self.available_label.setText("متاح: 0")
            return
        
        item_id = self.item_combo.currentData()
        
        for item in self.items:
            if item.id == item_id:
                # Calculate how much is already allocated in the list
                allocated = sum(item_data['quantity'] for item_data in self.items_to_extract 
                              if item_data['item_id'] == item_id)
                available = item.quantity - allocated
                self.available_label.setText(f"متاح: {available}")
                self.quantity.setMaximum(max(1, available))
                break
    
    def add_item_to_list(self):
        # Validate form
        if self.item_combo.count() == 0:
            QMessageBox.warning(self, "خطأ في التحقق", "لا توجد منتجات متاحة للاستخراج")
            return
        
        item_id = self.item_combo.currentData()
        quantity = self.quantity.value()
        
        # Find the item details
        item_name = ""
        current_stock = 0
        for item in self.items:
            if item.id == item_id:
                item_name = item.item_name
                current_stock = item.quantity
                break
        
        # Check if item is already in the list
        for i, item_data in enumerate(self.items_to_extract):
            if item_data['item_id'] == item_id:
                # Update existing item
                self.items_to_extract[i]['quantity'] += quantity
                self.update_items_table()
                self.update_available_quantity()
                return
        
        # Calculate how much is already allocated
        allocated = sum(item_data['quantity'] for item_data in self.items_to_extract 
                       if item_data['item_id'] == item_id)
        available = current_stock - allocated
        
        if quantity > available:
            QMessageBox.warning(self, "خطأ في التحقق", f"لا يوجد مخزون كافي متاح. المتاح: {available}")
            return
        
        # Add new item to the list
        self.items_to_extract.append({
            'item_id': item_id,
            'item_name': item_name,
            'current_stock': current_stock,
            'quantity': quantity
        })
        
        self.update_items_table()
        self.update_available_quantity()
        self.quantity.setValue(1)  # Reset quantity
    
    def remove_selected_item(self):
        current_row = self.items_table.currentRow()
        if current_row >= 0 and current_row < len(self.items_to_extract):
            self.items_to_extract.pop(current_row)
            self.update_items_table()
            self.update_available_quantity()
    
    def clear_items_list(self):
        self.items_to_extract.clear()
        self.update_items_table()
        self.update_available_quantity()
    
    def update_items_table(self):
        self.items_table.setRowCount(len(self.items_to_extract))
        
        for row, item_data in enumerate(self.items_to_extract):
            # Item name
            name_item = QTableWidgetItem(item_data['item_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 0, name_item)
            
            # Current stock
            stock_item = QTableWidgetItem(str(item_data['current_stock']))
            stock_item.setFlags(stock_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 1, stock_item)
            
            # Quantity to extract
            quantity_item = QTableWidgetItem(str(item_data['quantity']))
            quantity_item.setFlags(quantity_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 2, quantity_item)
            
            # Remaining after extraction
            remaining = item_data['current_stock'] - item_data['quantity']
            remaining_item = QTableWidgetItem(str(remaining))
            remaining_item.setFlags(remaining_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 3, remaining_item)
    
    def extract_all_items(self):
        # Validate form
        if not self.items_to_extract:
            QMessageBox.warning(self, "خطأ في التحقق", "لا توجد منتجات للاستخراج")
            return
        
        if self.branch_combo.currentData() is None:
            QMessageBox.warning(self, "خطأ في التحقق", "يرجى اختيار فرع")
            return
        
        extracted_by = self.extracted_by.text().strip()
        if not extracted_by:
            QMessageBox.warning(self, "خطأ في التحقق", "يرجى إدخال من يستخرج المنتجات")
            return
        
        # Get form values
        branch_id = self.branch_combo.currentData()
        branch_name = self.branch_combo.currentText()
        
        # Prepare items list for extraction
        items_list = [
            {'item_id': item['item_id'], 'quantity': item['quantity']}
            for item in self.items_to_extract
        ]
        
        # Also keep the single item extraction for backward compatibility
        if len(self.items_to_extract) == 1:
            item = self.items_to_extract[0]
            # Extract single item using the original method with extracted_by
            success, message = Extraction.extract_item(item['item_id'], branch_id, item['quantity'], extracted_by)
        else:
            # Extract items using the new multiple extraction method
            success, message = Extraction.extract_multiple_items(items_list, branch_id, extracted_by)
        
        if success:
            QMessageBox.information(self, "نجح", message)
            # Emit signal with extraction details for printing
            self.extraction_completed.emit(self.items_to_extract, branch_name, extracted_by)
            self.clear_form()
            self.refresh_items()
        else:
            QMessageBox.warning(self, "خطأ", message)
    
    def load_branches(self):
        """Load branches from the new branches table"""
        try:
            branches = Branch.get_all_branches()
            self.branch_combo.clear()
            self.branch_combo.addItem("-- اختر الفرع --", None)
            
            for branch in branches:
                self.branch_combo.addItem(branch['branch_name'], branch['id'])
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل الفروع: {e}")
    
    def clear_form(self):
        self.branch_combo.setCurrentIndex(0)  # Reset to "-- اختر الفرع --"
        self.extracted_by.clear()
        self.quantity.setValue(1)
        self.clear_items_list()