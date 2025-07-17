from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                              QComboBox, QPushButton, QLabel, QHeaderView, QMessageBox,
                              QDoubleSpinBox, QDialog, QFormLayout, QDialogButtonBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from models.invoice import Invoice

class PaymentDialog(QDialog):
    def __init__(self, invoice_id, invoice_number, total_amount, current_paid=0, parent=None):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.total_amount = total_amount
        
        self.setWindowTitle(f"Update Payment - Invoice #{invoice_number}")
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Display total amount
        self.total_label = QLabel(f"${total_amount:.2f}")
        form_layout.addRow("Total Amount:", self.total_label)
        
        # Payment status selection
        self.status_combo = QComboBox()
        self.status_combo.addItem(Invoice.PAYMENT_STATUS['PAID'])
        self.status_combo.addItem(Invoice.PAYMENT_STATUS['PARTIALLY_PAID'])
        self.status_combo.addItem(Invoice.PAYMENT_STATUS['DELAYED'])
        form_layout.addRow("Payment Status:", self.status_combo)
        
        # Paid amount field
        self.paid_amount = QDoubleSpinBox()
        self.paid_amount.setMinimum(0)
        self.paid_amount.setMaximum(total_amount)
        self.paid_amount.setValue(current_paid)
        self.paid_amount.setDecimals(2)
        form_layout.addRow("Paid Amount:", self.paid_amount)
        
        # Connect signals
        self.status_combo.currentTextChanged.connect(self.on_status_changed)
        
        # Add form to layout
        layout.addLayout(form_layout)
        
        # Add buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # Initialize UI state
        self.on_status_changed(self.status_combo.currentText())
    
    def on_status_changed(self, status):
        if status == Invoice.PAYMENT_STATUS['PAID']:
            self.paid_amount.setValue(self.total_amount)
            self.paid_amount.setEnabled(False)
        elif status == Invoice.PAYMENT_STATUS['DELAYED']:
            self.paid_amount.setValue(0)
            self.paid_amount.setEnabled(False)
        else:  # Partially paid
            self.paid_amount.setEnabled(True)
    
    def get_payment_data(self):
        return {
            'status': self.status_combo.currentText(),
            'paid_amount': self.paid_amount.value()
        }

class InvoiceViewWidget(QWidget):
    # Signal to notify when an invoice payment is updated
    invoice_updated = Signal(str)  # invoice_number
    
    def __init__(self):
        super().__init__()
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create supplier selection
        supplier_layout = QHBoxLayout()
        supplier_label = QLabel("Select Supplier:")
        self.supplier_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh")
        
        supplier_layout.addWidget(supplier_label)
        supplier_layout.addWidget(self.supplier_combo)
        supplier_layout.addWidget(self.refresh_button)
        supplier_layout.addStretch()
        
        # Create table for invoices
        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(7)
        self.invoice_table.setHorizontalHeaderLabels([
            "Invoice #", "Total Amount", "Paid Amount", "Remaining", 
            "Status", "Issue Date", "Actions"
        ])
        
        # Set table properties
        header = self.invoice_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Add widgets to layout
        layout.addLayout(supplier_layout)
        layout.addWidget(self.invoice_table)
        
        # Connect signals
        self.supplier_combo.currentTextChanged.connect(self.load_invoices)
        self.refresh_button.clicked.connect(self.refresh_suppliers)
        
        # Initialize
        self.refresh_suppliers()
    
    def refresh_suppliers(self):
        # Get all suppliers
        suppliers = Invoice.get_all_suppliers()
        
        # Clear and update combo box
        current_supplier = self.supplier_combo.currentText()
        self.supplier_combo.clear()
        
        if suppliers:
            self.supplier_combo.addItems(suppliers)
            # Try to restore previous selection
            index = self.supplier_combo.findText(current_supplier)
            if index >= 0:
                self.supplier_combo.setCurrentIndex(index)
            else:
                # Load invoices for the first supplier
                self.load_invoices(self.supplier_combo.currentText())
        else:
            self.invoice_table.setRowCount(0)
            # Display a message in the table
            self.invoice_table.setRowCount(1)
            self.invoice_table.setColumnCount(1)
            self.invoice_table.setHorizontalHeaderLabels(["Status"])
            message_item = QTableWidgetItem("No invoices found. Add items with supplier information first.")
            self.invoice_table.setItem(0, 0, message_item)
            # Restore original headers after displaying the message
            self.invoice_table.setColumnCount(7)
            self.invoice_table.setHorizontalHeaderLabels([
                "Invoice #", "Total Amount", "Paid Amount", "Remaining", 
                "Status", "Issue Date", "Actions"
            ])
    
    def load_invoices(self, supplier_name):
        if not supplier_name:
            self.invoice_table.setRowCount(0)
            return
        
        # Get invoices for the selected supplier
        invoices = Invoice.get_invoices_by_supplier(supplier_name)
        
        # Clear table
        self.invoice_table.setRowCount(0)
        
        # Add invoices to table
        for invoice in invoices:
            row_position = self.invoice_table.rowCount()
            self.invoice_table.insertRow(row_position)
            
            # Extract invoice data
            invoice_id = invoice['id']
            invoice_number = invoice['invoice_number']
            total_amount = invoice['total_amount']
            payment_status = invoice['payment_status']
            paid_amount = invoice['paid_amount']
            issue_date = invoice['issue_date']
            
            # Calculate remaining amount
            remaining = total_amount - paid_amount
            
            # Create table items
            self.invoice_table.setItem(row_position, 0, QTableWidgetItem(invoice_number))
            self.invoice_table.setItem(row_position, 1, QTableWidgetItem(f"${total_amount:.2f}"))
            self.invoice_table.setItem(row_position, 2, QTableWidgetItem(f"${paid_amount:.2f}"))
            self.invoice_table.setItem(row_position, 3, QTableWidgetItem(f"${remaining:.2f}"))
            
            # Status with color coding
            status_item = QTableWidgetItem(payment_status)
            if payment_status == Invoice.PAYMENT_STATUS['PAID']:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif payment_status == Invoice.PAYMENT_STATUS['DELAYED']:
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            else:  # Partially paid
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow
            
            self.invoice_table.setItem(row_position, 4, status_item)
            self.invoice_table.setItem(row_position, 5, QTableWidgetItem(issue_date))
            
            # Add update payment button
            update_button = QPushButton("Update Payment")
            update_button.clicked.connect(lambda checked=False, id=invoice_id, num=invoice_number, 
                                         total=total_amount, paid=paid_amount: 
                                         self.update_payment(id, num, total, paid))
            
            self.invoice_table.setCellWidget(row_position, 6, update_button)
    
    def update_payment(self, invoice_id, invoice_number, total_amount, current_paid):
        dialog = PaymentDialog(invoice_id, invoice_number, total_amount, current_paid, self)
        if dialog.exec_() == QDialog.Accepted:
            payment_data = dialog.get_payment_data()
            
            # Update payment status
            success = Invoice.update_payment_status(
                invoice_id, 
                payment_data['status'], 
                payment_data['paid_amount']
            )
            
            if success:
                QMessageBox.information(self, "Success", "Payment updated successfully")
                # Emit signal with invoice number for printing
                self.invoice_updated.emit(invoice_number)
                self.load_invoices(self.supplier_combo.currentText())
            else:
                QMessageBox.critical(self, "Error", "Failed to update payment")