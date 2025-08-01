from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                              QSpinBox, QDoubleSpinBox, QPushButton, QLabel,
                              QMessageBox, QDateEdit, QComboBox)
from PySide6.QtCore import Qt, QDate, Signal
import sqlite3

from models.item import Item
from models.invoice import Invoice
from database import create_connection

class AddItemWidget(QWidget):
    # Signal to notify when an item is added successfully
    item_added = Signal(str)  # Signal with invoice number
    
    def __init__(self):
        super().__init__()
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Create form fields
        self.invoice_number = QLineEdit()
        self.item_name = QLineEdit()
        self.quantity = QSpinBox()
        self.quantity.setMinimum(1)
        self.quantity.setMaximum(10000)
        
        self.price = QDoubleSpinBox()
        self.price.setMinimum(0.01)
        self.price.setMaximum(1000000.00)
        self.price.setDecimals(2)
        
        self.supplier_name = QLineEdit()
        
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        
        # Payment status dropdown
        self.payment_status = QComboBox()
        self.payment_status.addItem(Invoice.PAYMENT_STATUS['PAID'])
        self.payment_status.addItem(Invoice.PAYMENT_STATUS['PARTIALLY_PAID'])
        self.payment_status.addItem(Invoice.PAYMENT_STATUS['DELAYED'])
        self.payment_status.setCurrentText(Invoice.PAYMENT_STATUS['DELAYED'])
        
        # Paid amount field (only visible for partially paid)
        self.paid_amount = QDoubleSpinBox()
        self.paid_amount.setMinimum(0.00)
        self.paid_amount.setMaximum(1000000.00)
        self.paid_amount.setDecimals(2)
        self.paid_amount.setVisible(False)
        
        # Add fields to form layout
        form_layout.addRow("Invoice Number *:", self.invoice_number)
        form_layout.addRow("Item Name *:", self.item_name)
        form_layout.addRow("Quantity *:", self.quantity)
        form_layout.addRow("Price per Unit *:", self.price)
        form_layout.addRow("Supplier Name:", self.supplier_name)
        form_layout.addRow("Date:", self.date)
        form_layout.addRow("Payment Status:", self.payment_status)
        form_layout.addRow("Paid Amount:", self.paid_amount)
        
        # Create buttons
        button_layout = QVBoxLayout()
        self.save_button = QPushButton("Save")
        self.clear_button = QPushButton("Clear")
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.clear_button)
        
        # Add layouts to main layout
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        # Add stretch to push form to the top
        layout.addStretch()
        
        # Connect signals
        self.save_button.clicked.connect(self.save_item)
        self.clear_button.clicked.connect(self.clear_form)
        self.payment_status.currentTextChanged.connect(self.on_payment_status_changed)
    
    def on_payment_status_changed(self, status):
        # Show paid amount field only for partially paid status
        self.paid_amount.setVisible(status == Invoice.PAYMENT_STATUS['PARTIALLY_PAID'])
    
    def save_item(self):
        # Validate form
        if not self.invoice_number.text():
            QMessageBox.warning(self, "Validation Error", "Invoice Number is required")
            return
        
        if not self.item_name.text():
            QMessageBox.warning(self, "Validation Error", "Item Name is required")
            return
        
        # Get form values
        invoice_number = self.invoice_number.text()
        item_name = self.item_name.text()
        quantity = self.quantity.value()
        price = self.price.value()
        supplier_name = self.supplier_name.text()
        payment_status = self.payment_status.currentText()
        
        # Get paid amount if partially paid
        paid_amount = None
        if payment_status == Invoice.PAYMENT_STATUS['PARTIALLY_PAID']:
            paid_amount = self.paid_amount.value()
            if paid_amount >= (quantity * price):
                QMessageBox.warning(self, "Validation Error", "Paid amount must be less than total amount for partially paid status")
                return
        
        # Add item to database
        item_id = Item.add_item(item_name, quantity, price, invoice_number, supplier_name, payment_status)
        
        if item_id:
            # Update paid amount if needed
            if payment_status == Invoice.PAYMENT_STATUS['PARTIALLY_PAID']:
                # Get the invoice ID
                conn = create_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,))
                        result = cursor.fetchone()
                        if result:
                            invoice_id = result[0]
                            # Update the paid amount
                            Invoice.update_payment_status(invoice_id, payment_status, paid_amount)
                    except sqlite3.Error as e:
                        print(f"Database error when updating payment: {e}")
                    finally:
                        conn.close()
            
            QMessageBox.information(self, "Success", "Item added successfully")
            # Emit signal with invoice number for printing
            self.item_added.emit(invoice_number)
            self.clear_form()
        else:
            QMessageBox.critical(self, "Error", "Failed to add item")
    
    def clear_form(self):
        self.invoice_number.clear()
        self.item_name.clear()
        self.quantity.setValue(1)
        self.price.setValue(0.01)
        self.supplier_name.clear()
        self.date.setDate(QDate.currentDate())
        self.payment_status.setCurrentText(Invoice.PAYMENT_STATUS['DELAYED'])
        self.paid_amount.setValue(0.00)
        self.paid_amount.setVisible(False)