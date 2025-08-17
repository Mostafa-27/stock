from PySide6.QtWidgets import (QFrame, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                              QComboBox, QPushButton, QLabel, QHeaderView, QMessageBox,
                              QDoubleSpinBox, QDialog, QFormLayout, QDialogButtonBox, QScrollArea,
                              QTextEdit, QGroupBox, QGridLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from models.invoice import Invoice
from utils.printer_utils import print_invoice as print_invoice_util

class PaymentDialog(QDialog):
    def __init__(self, invoice_id, invoice_number, total_amount, current_paid=0, current_status="", parent=None):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.total_amount = total_amount
        self.current_paid = current_paid
        self.current_status = current_status
        
        self.setWindowTitle(f"تحديث الدفع - فاتورة رقم #{invoice_number}")
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
            paid_label = QLabel("هذه الفاتورة مدفوعة بالكامل ولا يمكن تعديلها.")
            paid_label.setObjectName("paidLabel")
            layout.addWidget(paid_label)
            
            # Add close button
            close_button = QPushButton("إغلاق")
            close_button.clicked.connect(self.reject)
            layout.addWidget(close_button)
            return
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Display total amount
        self.total_label = QLabel(f"{total_amount:.2f} ج.م")
        self.total_label.setObjectName("totalLabel")
        form_layout.addRow("إجمالي المبلغ:", self.total_label)
        
        # Display current paid amount
        current_paid_label = QLabel(f"{current_paid:.2f} ج.م")
        form_layout.addRow("المبلغ المدفوع حاليا:", current_paid_label)
        
        # Display remaining amount
        remaining_label = QLabel(f"{(total_amount - current_paid):.2f} ج.م")
        form_layout.addRow("المبلغ المتبقي:", remaining_label)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addLayout(form_layout)
        layout.addWidget(separator)
        
        # Payment status selection
        status_label = QLabel("اختر حالة الدفع:")
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
        amount_label = QLabel("أدخل دفعة إضافية:")
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
        self.total_payment_label = QLabel(f"{current_paid:.2f} ج.م")
        form_layout.addRow("إجمالي المدفوع بعد المعاملة:", self.total_payment_label)
        
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
        self.save_button = QPushButton("حفظ")
        self.save_button.clicked.connect(self.validate_and_accept)
        cancel_button = QPushButton("إلغاء")
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
            self.total_payment_label.setText(f"{self.total_amount:.2f} ج.م")
            self.warning_label.setText("")
        elif status == Invoice.PAYMENT_STATUS['DELAYED']:
            # For delayed status, no additional payment
            self.paid_amount.setValue(0)
            self.paid_amount.setEnabled(False)
            self.total_payment_label.setText(f"{self.current_paid:.2f} ج.م")
            self.warning_label.setText("")
        else:  # Partially paid
            self.paid_amount.setEnabled(True)
            # Update the validation based on the current additional amount
            self.validate_amount(self.paid_amount.value())
    
    def update_total_payment_label(self, additional_amount):
        # Update the total payment label based on current paid + additional amount
        total_payment = float(self.current_paid) + additional_amount
        self.total_payment_label.setText(f"{total_payment:.2f} ج.م")
        
    def validate_amount(self, additional_amount):
        total_payment = float(self.current_paid) + additional_amount
        
        if self.status_combo.currentText() == Invoice.PAYMENT_STATUS['PARTIALLY_PAID']:
            if total_payment <= 0:
                self.warning_label.setText("يجب أن يكون إجمالي المبلغ المدفوع أكبر من الصفر للحالة مدفوع جزئيا.")
                self.save_button.setEnabled(False)
            elif total_payment >= self.total_amount:
                self.warning_label.setText("للحالة مدفوع جزئيا، يجب أن يكون إجمالي المبلغ أقل من إجمالي الفاتورة. استخدم حالة 'مدفوع' بدلا من ذلك.")
                self.save_button.setEnabled(False)
            else:
                self.warning_label.setText("")
                self.save_button.setEnabled(True)
    
    def validate_and_accept(self):
        # Final validation before accepting
        status = self.status_combo.currentText()
        additional_amount = self.paid_amount.value()
        total_payment = float(self.current_paid) + additional_amount
        
        if status == Invoice.PAYMENT_STATUS['PARTIALLY_PAID']:
            if total_payment <= 0:
                self.warning_label.setText("يجب أن يكون إجمالي المبلغ المدفوع أكبر من الصفر للحالة مدفوع جزئيا.")
                return
            elif total_payment >= self.total_amount:
                self.warning_label.setText("للحالة مدفوع جزئيا، يجب أن يكون إجمالي المبلغ أقل من إجمالي الفاتورة. استخدم حالة 'مدفوع' بدلا من ذلك.")
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
            total_payment = float(self.current_paid) + additional_amount
        
        return {
            'status': status,
            'paid_amount': total_payment
        }

class InvoiceDetailsDialog(QDialog):
    def __init__(self, invoice_number, parent=None):
        super().__init__(parent)
        self.invoice_number = invoice_number
        
        self.setWindowTitle(f"تفاصيل الفاتورة رقم #{invoice_number}")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background-color: #f8f9fa;
            }
            QLabel {
                font-size: 12px;
                color: #495057;
            }
            QLabel[class="header"] {
                font-size: 16px;
                font-weight: bold;
                color: #212529;
            }
            QLabel[class="value"] {
                font-size: 12px;
                font-weight: bold;
                color: #0056b3;
            }
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                gridline-color: #dee2e6;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton[class="print"] {
                background-color: #28a745;
            }
            QPushButton[class="print"]:hover {
                background-color: #1e7e34;
            }
            QPushButton[class="close"] {
                background-color: #6c757d;
            }
            QPushButton[class="close"]:hover {
                background-color: #545b62;
            }
        """)
        
        self.setup_ui()
        self.load_invoice_details()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # Invoice header group
        self.invoice_header_group = QGroupBox("معلومات الفاتورة الأساسية")
        self.setup_invoice_header()
        content_layout.addWidget(self.invoice_header_group)
        
        # Payment details group
        self.payment_group = QGroupBox("تفاصيل الدفع")
        self.setup_payment_details()
        content_layout.addWidget(self.payment_group)
        
        # Items table group
        self.items_group = QGroupBox("عناصر الفاتورة")
        self.setup_items_table()
        content_layout.addWidget(self.items_group)
        
        # Notes group (if any)
        # self.notes_group = QGroupBox("الملاحظات")
        # self.setup_notes_section()
        # content_layout.addWidget(self.notes_group)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Print button
        print_button = QPushButton("🖨️ طباعة الفاتورة")
        print_button.setProperty("class", "print")
        print_button.clicked.connect(self.print_invoice)
        
        # Close button
        close_button = QPushButton("إغلاق")
        close_button.setProperty("class", "close")
        close_button.clicked.connect(self.close)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(print_button)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
    
    def setup_invoice_header(self):
        layout = QGridLayout(self.invoice_header_group)
        layout.setSpacing(10)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        
        # Invoice number
        layout.addWidget(QLabel("رقم الفاتورة:"), 0, 0)
        self.invoice_num_label = QLabel()
        self.invoice_num_label.setProperty("class", "value")
        layout.addWidget(self.invoice_num_label, 0, 1)
        
        # Supplier name
        layout.addWidget(QLabel("اسم المورد:"), 0, 2)
        self.supplier_label = QLabel()
        self.supplier_label.setProperty("class", "value")
        layout.addWidget(self.supplier_label, 0, 3)
        
        # Issue date
        layout.addWidget(QLabel("تاريخ الإصدار:"), 1, 0)
        self.issue_date_label = QLabel()
        self.issue_date_label.setProperty("class", "value")
        layout.addWidget(self.issue_date_label, 1, 1)
        
      
    
    def setup_payment_details(self):
        layout = QGridLayout(self.payment_group)
        layout.setSpacing(10)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        
        # Total amount
        layout.addWidget(QLabel("إجمالي المبلغ:"), 0, 0)
        self.total_amount_label = QLabel()
        self.total_amount_label.setProperty("class", "value")
        layout.addWidget(self.total_amount_label, 0, 1)
        
        # Paid amount
        layout.addWidget(QLabel("المبلغ المدفوع:"), 0, 2)
        self.paid_amount_label = QLabel()
        self.paid_amount_label.setProperty("class", "value")
        layout.addWidget(self.paid_amount_label, 0, 3)
        
        # Remaining amount
        layout.addWidget(QLabel("المبلغ المتبقي:"), 1, 0)
        self.remaining_amount_label = QLabel()
        self.remaining_amount_label.setProperty("class", "value")
        layout.addWidget(self.remaining_amount_label, 1, 1)
        
        # Payment status
        layout.addWidget(QLabel("حالة الدفع:"), 1, 2)
        self.payment_status_label = QLabel()
        self.payment_status_label.setProperty("class", "value")
        layout.addWidget(self.payment_status_label, 1, 3)
    
    def setup_items_table(self):
        layout = QVBoxLayout(self.items_group)
        
        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            "اسم المنتج", "الكمية", "نوع الكمية", "سعر الوحدة", "الإجمالي"
        ])
        
        # Set table properties
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.items_table)
        
        # Summary labels
        summary_layout = QHBoxLayout()
        summary_layout.addStretch()
        
        self.items_count_label = QLabel("عدد العناصر: 0")
        self.items_count_label.setProperty("class", "value")
        summary_layout.addWidget(self.items_count_label)
        
        layout.addLayout(summary_layout)
    
    
    
    def load_invoice_details(self):
        # Get invoice data
        invoice_data = Invoice.get_invoice_by_number(self.invoice_number)
        if not invoice_data:
            QMessageBox.warning(self, "خطأ", "لا يمكن العثور على الفاتورة")
            self.close()
            return
        
        # Load invoice header
        self.invoice_num_label.setText(invoice_data['invoice_number'])
        self.supplier_label.setText(invoice_data['supplier_name'])
        self.issue_date_label.setText(str(invoice_data['issue_date']))
         
        # Load payment details
        total_amount = invoice_data['total_amount']
        paid_amount = invoice_data['paid_amount']
        remaining = total_amount - paid_amount
        
        self.total_amount_label.setText(f"{total_amount:.2f} ج.م")
        self.paid_amount_label.setText(f"{paid_amount:.2f} ج.م")
        self.remaining_amount_label.setText(f"{remaining:.2f} ج.م")
        
        # Set payment status with color
        payment_status = invoice_data['payment_status']
        self.payment_status_label.setText(payment_status)
        
        if payment_status == Invoice.PAYMENT_STATUS['PAID']:
            self.payment_status_label.setStyleSheet("color: #28a745; font-weight: bold;")
        elif payment_status == Invoice.PAYMENT_STATUS['DELAYED']:
            self.payment_status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        else:  # Partially paid
            self.payment_status_label.setStyleSheet("color: #ffc107; font-weight: bold;")
        
        # Load items
        items_data = Invoice.get_items_by_invoice(self.invoice_number)
        self.load_items_table(items_data)
        
        
    
    def load_items_table(self, items_data):
        self.items_table.setRowCount(len(items_data))
        
        total_items = 0
        for row, item in enumerate(items_data):
            # Item name
            self.items_table.setItem(row, 0, QTableWidgetItem(item['item_name']))
            
            # Quantity
            quantity = item['quantity']
            self.items_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
            total_items += quantity
            
            # Quantity type
            quantity_type = item.get('quantity_type', 'unit')
            self.items_table.setItem(row, 2, QTableWidgetItem(quantity_type))
            
            # Price per unit
            price_per_unit = item['price_per_unit']
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{price_per_unit:.2f} ج.م"))
            
            # Total for this item
            total_item_price = quantity * price_per_unit
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{total_item_price:.2f} ج.م"))
            
            # Center align all items
            for col in range(5):
                item_widget = self.items_table.item(row, col)
                if item_widget:
                    item_widget.setTextAlignment(Qt.AlignCenter)
        
        # Update items count
        self.items_count_label.setText(f"عدد العناصر: {len(items_data)} منتج - إجمالي الكمية: {total_items}")
    
    def print_invoice(self):
        """Print the invoice"""
        try:
            # Get invoice data
            invoice_data = Invoice.get_invoice_by_number(self.invoice_number)
            if invoice_data:
                # Get items for this invoice
                items_data = Invoice.get_items_by_invoice(self.invoice_number)
                
                # Print the invoice
                print_invoice_util(invoice_data, items_data)
                QMessageBox.information(self, "نجح", "تم إرسال الفاتورة إلى الطابعة")
            else:
                QMessageBox.warning(self, "خطأ", "الفاتورة غير موجودة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الطباعة", f"خطأ في طباعة الفاتورة: {e}")

class InvoiceViewWidget(QWidget):
    # Signal to notify when an invoice payment is updated
    invoice_updated = Signal(str)  # invoice_number
    
    def __init__(self):
        super().__init__()
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create supplier selection
        supplier_layout = QHBoxLayout()
        supplier_label = QLabel("اختر المورد:")
        self.supplier_combo = QComboBox()
        self.refresh_button = QPushButton("تحديث")
        
        supplier_layout.addWidget(supplier_label)
        supplier_layout.addWidget(self.supplier_combo)
        supplier_layout.addWidget(self.refresh_button)
        supplier_layout.addStretch()
        
        # Create table for invoices
        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(7)
        self.invoice_table.setHorizontalHeaderLabels([
            "رقم الفاتورة", "إجمالي المبلغ", "المبلغ المدفوع", "المتبقي", 
            "الحالة", "تاريخ الإصدار", "الإجراءات"
        ])
        
        # Set table properties
        header = self.invoice_table.horizontalHeader()
        # Set most columns to stretch except the actions column
        for i in range(6):  # Columns 0-5
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        # Set actions column (index 6) to fixed width
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.invoice_table.setColumnWidth(6, 300)  # Set actions column to 250px width
        
        self.invoice_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.invoice_table.setAlternatingRowColors(True)
        
        # Set default row height to make rows taller
        self.invoice_table.verticalHeader().setDefaultSectionSize(40)
        
        # Add widgets to layout
        layout.addLayout(supplier_layout)
        layout.addWidget(self.invoice_table)
        
        # Connect signals
        self.supplier_combo.currentTextChanged.connect(self.load_invoices)
        self.refresh_button.clicked.connect(self.refresh_suppliers)
        self.invoice_table.cellDoubleClicked.connect(self.show_invoice_details)
        
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
            self.invoice_table.setHorizontalHeaderLabels(["الحالة"])
            message_item = QTableWidgetItem("لا توجد فواتير. أضف منتجات مع معلومات المورد أولا.")
            self.invoice_table.setItem(0, 0, message_item)
            # Restore original headers after displaying the message
            self.invoice_table.setColumnCount(7)
            self.invoice_table.setHorizontalHeaderLabels([
                "رقم الفاتورة", "إجمالي المبلغ", "المبلغ المدفوع", "المتبقي", 
                "الحالة", "تاريخ الإصدار", "الإجراءات"
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
            self.invoice_table.setItem(row_position, 1, QTableWidgetItem(f"{total_amount:.2f} ج.م"))
            self.invoice_table.setItem(row_position, 2, QTableWidgetItem(f"{paid_amount:.2f} ج.م"))
            self.invoice_table.setItem(row_position, 3, QTableWidgetItem(f"{remaining:.2f} ج.م"))
            
            # Status with color coding
            status_item = QTableWidgetItem(payment_status)
            if payment_status == Invoice.PAYMENT_STATUS['PAID']:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif payment_status == Invoice.PAYMENT_STATUS['DELAYED']:
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            else:  # Partially paid
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow
            
            self.invoice_table.setItem(row_position, 4, status_item)
            self.invoice_table.setItem(row_position, 5, QTableWidgetItem(str(issue_date)))
            
            # Create a widget to hold all buttons
            buttons_widget = QWidget()
            buttons_layout = QHBoxLayout(buttons_widget)
            buttons_layout.setContentsMargins(2, 2, 2, 2)
            buttons_layout.setSpacing(5)
            
            # Add view details button
            details_button = QPushButton("👁️ عرض")
            details_button.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    padding: 6px;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """)
            details_button.clicked.connect(lambda checked=False, num=invoice_number: self.show_invoice_details_by_number(num))
            
            # Add update payment button with styling based on payment status
            update_button = QPushButton("💰 دفع")
            
            # Style the update button based on payment status
            if payment_status == Invoice.PAYMENT_STATUS['PAID']:
                update_button.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60;
                        color: white;
                        border: none;
                        padding: 6px;
                        border-radius: 4px;
                        font-size: 11px;
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
                        font-size: 11px;
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
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #d35400;
                    }
                """)
            
            update_button.clicked.connect(lambda checked=False, id=invoice_id, num=invoice_number, 
                                         total=total_amount, paid=paid_amount, status=payment_status: 
                                         self.update_payment(id, num, total, paid, status))
            
            # Add print button with styling
            print_button = QPushButton("🖨️ طباعة")
            print_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 6px;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            print_button.clicked.connect(lambda checked=False, num=invoice_number: self.print_invoice(num))
            
            buttons_layout.addWidget(details_button)
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
                QMessageBox.information(self, "نجح", "تم تحديث الدفع بنجاح")
                # Emit signal with invoice number for printing
                self.invoice_updated.emit(invoice_number)
                self.load_invoices(self.supplier_combo.currentText())
            else:
                QMessageBox.critical(self, "خطأ", "فشل في تحديث الدفع")
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
                QMessageBox.information(self, "نجح", "تم إرسال الفاتورة إلى الطابعة")
            else:
                QMessageBox.warning(self, "خطأ", "الفاتورة غير موجودة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الطباعة", f"خطأ في طباعة الفاتورة: {e}")
    
    def show_invoice_details(self, row, column):
        """Show invoice details when a row is double-clicked"""
        if row < self.invoice_table.rowCount():
            # Get invoice number from the first column
            invoice_number_item = self.invoice_table.item(row, 0)
            if invoice_number_item:
                invoice_number = invoice_number_item.text()
                self.show_invoice_details_by_number(invoice_number)
    
    def show_invoice_details_by_number(self, invoice_number):
        """Show detailed invoice dialog for the given invoice number"""
        try:
            details_dialog = InvoiceDetailsDialog(invoice_number, self)
            details_dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في عرض تفاصيل الفاتورة: {e}")