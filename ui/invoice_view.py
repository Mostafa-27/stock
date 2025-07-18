from PySide6.QtWidgets import (QFrame, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                              QComboBox, QPushButton, QLabel, QHeaderView, QMessageBox,
                              QDoubleSpinBox, QDialog, QFormLayout, QDialogButtonBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from models.invoice import Invoice
from utils.printer_utils import print_invoice as print_invoice_util

class PaymentDialog(QDialog):
    def __init__(self, invoice_id, invoice_number, total_amount, current_paid=0, current_status="", parent=None):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.total_amount = total_amount
        self.current_paid = current_paid
        self.current_status = current_status
        
        self.setWindowTitle(f"Update Payment - Invoice #{invoice_number}")
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                font-size: 12px;
            }
            QLabel#totalLabel, QLabel#statusLabel {
                font-weight: bold;
                font-size: 14px;
            }
            QLabel#warningLabel {
                color: #e74c3c;
                font-weight: bold;
            }
            QLabel#paidLabel {
                color: #27ae60;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Check if invoice is already paid
        if current_status == Invoice.PAYMENT_STATUS['PAID']:
            # Show message that invoice is already paid
            paid_label = QLabel("This invoice is already fully paid and cannot be edited.")
            paid_label.setObjectName("paidLabel")
            layout.addWidget(paid_label)
            
            # Add close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(self.reject)
            layout.addWidget(close_button)
            return
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Display total amount
        self.total_label = QLabel(f"${total_amount:.2f}")
        self.total_label.setObjectName("totalLabel")
        form_layout.addRow("Total Amount:", self.total_label)
        
        # Display current paid amount
        current_paid_label = QLabel(f"${current_paid:.2f}")
        form_layout.addRow("Currently Paid:", current_paid_label)
        
        # Display remaining amount
        remaining_label = QLabel(f"${(total_amount - current_paid):.2f}")
        form_layout.addRow("Remaining Amount:", remaining_label)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addLayout(form_layout)
        layout.addWidget(separator)
        
        # Payment status selection
        status_label = QLabel("Select Payment Status:")
        status_label.setObjectName("statusLabel")
        layout.addWidget(status_label)
        
        self.status_combo = QComboBox()
        self.status_combo.addItem(Invoice.PAYMENT_STATUS['PAID'])
        self.status_combo.addItem(Invoice.PAYMENT_STATUS['PARTIALLY_PAID'])
        # self.status_combo.addItem(Invoice.PAYMENT_STATUS['DELAYED'])
        # Set current status if available
        if self.current_status:
            index = self.status_combo.findText(self.current_status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
        layout.addWidget(self.status_combo)
        
        # Paid amount field with label
        amount_label = QLabel("Enter Additional Payment:")
        layout.addWidget(amount_label)
        
        self.paid_amount = QDoubleSpinBox()
        self.paid_amount.setMinimum(0)
        self.paid_amount.setMaximum(total_amount - current_paid)  # Limit to remaining amount
        self.paid_amount.setValue(0)  # Start with 0 for additional payment
        self.paid_amount.setDecimals(2)
        self.paid_amount.setSingleStep(0.5)  # Add step value for better usability
        self.paid_amount.setStyleSheet("""
            QDoubleSpinBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.paid_amount)
        
        # Display total payment after this transaction
        self.total_payment_label = QLabel(f"${current_paid:.2f}")
        form_layout.addRow("Total Payment After Transaction:", self.total_payment_label)
        
        # Connect value changed to update total payment label
        self.paid_amount.valueChanged.connect(self.update_total_payment_label)
        
        # Warning label for validation
        self.warning_label = QLabel("")
        self.warning_label.setObjectName("warningLabel")
        self.warning_label.setWordWrap(True)
        layout.addWidget(self.warning_label)
        
        # Connect signals
        self.status_combo.currentTextChanged.connect(self.on_status_changed)
        self.paid_amount.valueChanged.connect(self.validate_amount)
        
        # Add buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.validate_and_accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)
        
        # Initialize UI state
        self.on_status_changed(self.status_combo.currentText())
    
    def on_status_changed(self, status):
        if status == Invoice.PAYMENT_STATUS['PAID']:
            # For paid status, set the additional payment to cover the remaining amount
            remaining = self.total_amount - self.current_paid
            self.paid_amount.setValue(remaining)
            self.paid_amount.setEnabled(False)
            self.total_payment_label.setText(f"${self.total_amount:.2f}")
            self.warning_label.setText("")
        elif status == Invoice.PAYMENT_STATUS['DELAYED']:
            # For delayed status, no additional payment
            self.paid_amount.setValue(0)
            self.paid_amount.setEnabled(False)
            self.total_payment_label.setText(f"${self.current_paid:.2f}")
            self.warning_label.setText("")
        else:  # Partially paid
            self.paid_amount.setEnabled(True)
            # Update the validation based on the current additional amount
            self.validate_amount(self.paid_amount.value())
    
    def update_total_payment_label(self, additional_amount):
        # Update the total payment label based on current paid + additional amount
        total_payment = self.current_paid + additional_amount
        self.total_payment_label.setText(f"${total_payment:.2f}")
        
    def validate_amount(self, additional_amount):
        total_payment = self.current_paid + additional_amount
        
        if self.status_combo.currentText() == Invoice.PAYMENT_STATUS['PARTIALLY_PAID']:
            if total_payment <= 0:
                self.warning_label.setText("Total paid amount must be greater than zero for partially paid status.")
                self.save_button.setEnabled(False)
            elif total_payment >= self.total_amount:
                self.warning_label.setText("For partially paid status, total amount should be less than invoice total. Consider using 'Paid' status instead.")
                self.save_button.setEnabled(False)
            else:
                self.warning_label.setText("")
                self.save_button.setEnabled(True)
    
    def validate_and_accept(self):
        # Final validation before accepting
        status = self.status_combo.currentText()
        additional_amount = self.paid_amount.value()
        total_payment = self.current_paid + additional_amount
        
        if status == Invoice.PAYMENT_STATUS['PARTIALLY_PAID']:
            if total_payment <= 0:
                self.warning_label.setText("Total paid amount must be greater than zero for partially paid status.")
                return
            elif total_payment >= self.total_amount:
                self.warning_label.setText("For partially paid status, total amount should be less than invoice total. Consider using 'Paid' status instead.")
                return
        elif status == Invoice.PAYMENT_STATUS['PAID']:
            # Force correct amount for PAID status
            total_payment = self.total_amount
        
        # All validations passed
        self.accept()
    
    def get_payment_data(self):
        status = self.status_combo.currentText()
        additional_amount = self.paid_amount.value()
        
        # Calculate total payment based on current paid + additional amount
        if status == Invoice.PAYMENT_STATUS['PAID']:
            total_payment = self.total_amount
        elif status == Invoice.PAYMENT_STATUS['DELAYED']:
            # For delayed status, we keep the current paid amount
            total_payment = self.current_paid
        else:  # Partially paid
            total_payment = self.current_paid + additional_amount
        
        return {
            'status': status,
            'paid_amount': total_payment
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
            
            # Create a widget to hold both buttons
            buttons_widget = QWidget()
            buttons_layout = QHBoxLayout(buttons_widget)
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            
            # Add update payment button with styling based on payment status
            update_button = QPushButton("Update Payment")
            
            # Style the update button based on payment status
            if payment_status == Invoice.PAYMENT_STATUS['PAID']:
                update_button.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60;
                        color: white;
                        border: none;
                        padding: 6px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #2ecc71;
                    }
                """)
            elif payment_status == Invoice.PAYMENT_STATUS['DELAYED']:
                update_button.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c;
                        color: white;
                        border: none;
                        padding: 6px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #c0392b;
                    }
                """)
            else:  # Partially paid
                update_button.setStyleSheet("""
                    QPushButton {
                        background-color: #f39c12;
                        color: white;
                        border: none;
                        padding: 6px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #d35400;
                    }
                """)
            
            update_button.clicked.connect(lambda checked=False, id=invoice_id, num=invoice_number, 
                                         total=total_amount, paid=paid_amount, status=payment_status: 
                                         self.update_payment(id, num, total, paid, status))
            
            # Add print button with styling
            print_button = QPushButton("🖨️ Print")
            print_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 6px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            print_button.clicked.connect(lambda checked=False, num=invoice_number: self.print_invoice(num))
            
            buttons_layout.addWidget(update_button)
            buttons_layout.addWidget(print_button)
            
            self.invoice_table.setCellWidget(row_position, 6, buttons_widget)
    
    def update_payment(self, invoice_id, invoice_number, total_amount, current_paid, payment_status=None):
        # Get current payment status if not provided
        if payment_status is None:
            invoice_data = Invoice.get_invoice_by_number(invoice_number)
            if invoice_data:
                payment_status = invoice_data['payment_status']
            else:
                payment_status = ""
        
        # Create and show payment dialog
        dialog = PaymentDialog(invoice_id, invoice_number, total_amount, current_paid, payment_status, self)
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
        else:
            # Dialog was cancelled or closed
            pass
    
    def print_invoice(self, invoice_number):
        """Print the selected invoice"""
        try:
            # Get invoice data
            invoice_data = Invoice.get_invoice_by_number(invoice_number)
            if invoice_data:
                # Get items for this invoice
                items_data = Invoice.get_items_by_invoice(invoice_number)
                
                # Print the invoice
                print_invoice_util(invoice_data, items_data)
                QMessageBox.information(self, "Success", "Invoice sent to printer")
            else:
                QMessageBox.warning(self, "Error", "Invoice not found")
        except Exception as e:
            QMessageBox.critical(self, "Printing Error", f"Error printing invoice: {e}")