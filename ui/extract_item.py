from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                              QSpinBox, QPushButton, QLabel, QMessageBox,
                              QComboBox)
from PySide6.QtCore import Qt, Signal

from models.item import Item
from models.extraction import Extraction
from models.branch import Branch

class ExtractItemWidget(QWidget):
    # Signal to notify when an extraction is completed successfully
    extraction_completed = Signal(int, str, int)  # item_id, branch_name, quantity
    
    def __init__(self):
        super().__init__()
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Create form fields
        self.item_combo = QComboBox()
        self.branch_combo = QComboBox()
        self.quantity = QSpinBox()
        self.quantity.setMinimum(1)
        self.quantity.setMaximum(10000)
        
        # Add fields to form layout
        form_layout.addRow("Item *:", self.item_combo)
        form_layout.addRow("Branch *:", self.branch_combo)
        form_layout.addRow("Quantity to Extract *:", self.quantity)
        
        # Create available quantity label
        self.available_label = QLabel("Available: 0")
        form_layout.addRow("Stock Status:", self.available_label)
        
        # Create buttons
        button_layout = QVBoxLayout()
        self.extract_button = QPushButton("Extract Item")
        self.clear_button = QPushButton("Clear")
        
        button_layout.addWidget(self.extract_button)
        button_layout.addWidget(self.clear_button)
        
        # Add layouts to main layout
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        # Add stretch to push form to the top
        layout.addStretch()
        
        # Connect signals
        self.extract_button.clicked.connect(self.extract_item)
        self.clear_button.clicked.connect(self.clear_form)
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
            self.available_label.setText("Available: 0")
            return
        
        item_id = self.item_combo.currentData()
        
        for item in self.items:
            if item.id == item_id:
                self.available_label.setText(f"Available: {item.quantity}")
                self.quantity.setMaximum(item.quantity)
                break
    
    def extract_item(self):
        # Validate form
        if self.item_combo.count() == 0:
            QMessageBox.warning(self, "Validation Error", "No items available for extraction")
            return
        
        if self.branch_combo.currentText() == "-- اختر الفرع --":
            QMessageBox.warning(self, "Validation Error", "Please select a branch")
            return
        
        # Get form values
        item_id = self.item_combo.currentData()
        branch_name = self.branch_combo.currentText()
        quantity = self.quantity.value()
        
        # Extract item
        success, message = Extraction.extract_item(item_id, branch_name, quantity)
        
        if success:
            QMessageBox.information(self, "Success", message)
            # Emit signal with extraction details for printing
            self.extraction_completed.emit(item_id, branch_name, quantity)
            self.clear_form()
            self.refresh_items()
        else:
            QMessageBox.warning(self, "Error", message)
    
    def load_branches(self):
        """Load branches from the new branches table"""
        try:
            branch_names = Branch.get_branch_names()
            self.branch_combo.clear()
            self.branch_combo.addItem("-- اختر الفرع --")
            self.branch_combo.addItems(branch_names)
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل الفروع: {e}")
    
    def clear_form(self):
        self.branch_combo.setCurrentIndex(0)  # Reset to "-- اختر الفرع --"
        self.quantity.setValue(1)