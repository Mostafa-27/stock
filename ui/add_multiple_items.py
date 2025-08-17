from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                              QSpinBox, QDoubleSpinBox, QPushButton, QLabel,
                              QMessageBox, QDateEdit, QComboBox, QHBoxLayout,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QGroupBox, QGridLayout, QTextEdit, QScrollArea)
from PySide6.QtCore import Qt, QDate, Signal
import pyodbc
from datetime import datetime

from models.item import Item
from models.invoice import Invoice
from models.supplier import Supplier
from database import get_db_connection

class AddMultipleItemsWidget(QWidget):
    # Signal to notify when items are added successfully
    items_added = Signal(str)  # Signal with invoice number
    
    def __init__(self):
        super().__init__()
        self.items_list = []  # List to store items before saving
        
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
        
        # Invoice Information Group
        invoice_group = QGroupBox("معلومات الفاتورة")
        invoice_layout = QFormLayout(invoice_group)
        
        self.invoice_number = QLineEdit()
        self.supplier_combo = QComboBox()
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
        
        # Notes field
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        
        invoice_layout.addRow("رقم الفاتورة *:", self.invoice_number)
        invoice_layout.addRow("المورد *:", self.supplier_combo)
        invoice_layout.addRow("التاريخ:", self.date)
        invoice_layout.addRow("حالة الدفع:", self.payment_status)
        invoice_layout.addRow("المبلغ المدفوع:", self.paid_amount)
        invoice_layout.addRow("ملاحظات:", self.notes)
        
        # Item Entry Group
        item_group = QGroupBox("إضافة منتجات")
        item_layout = QFormLayout(item_group)
        
        self.item_name = QLineEdit()
        self.quantity = QSpinBox()
        self.quantity.setMinimum(1)
        self.quantity.setMaximum(10000)
        
        # Quantity type dropdown
        self.quantity_type = QComboBox()
        self.quantity_type.addItems(['وحدة', 'كيلو', 'لتر', 'جرام', 'متر', 'صندوق', 'قطعة', 'طن'])
        self.quantity_type.setEditable(False)  # Only allow predefined types
        
        self.price = QDoubleSpinBox()
        self.price.setMinimum(0.01)
        self.price.setMaximum(1000000.00)
        self.price.setDecimals(2)
        
        # Add item button
        self.add_item_button = QPushButton("إضافة منتج للقائمة")
        
        item_layout.addRow("اسم المنتج *:", self.item_name)
        item_layout.addRow("الكمية *:", self.quantity)
        item_layout.addRow("نوع الكمية:", self.quantity_type)
        item_layout.addRow("السعر لكل وحدة *:", self.price)
        item_layout.addRow("", self.add_item_button)
        
        # Items List Table
        list_group = QGroupBox("المنتجات في الفاتورة")
        list_layout = QVBoxLayout(list_group)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(['اسم المنتج', 'الكمية', 'النوع', 'السعر/الوحدة', 'الإجمالي'])
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
        
        # Total Display
        total_layout = QHBoxLayout()
        self.total_label = QLabel("إجمالي المبلغ: 0.00 ج.م")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        total_layout.addStretch()
        total_layout.addWidget(self.total_label)
        
        # Main Action Buttons
        button_layout = QHBoxLayout()
        self.save_invoice_button = QPushButton("حفظ الفاتورة")
        self.clear_form_button = QPushButton("مسح النموذج")
        
        self.save_invoice_button.setStyleSheet("font-weight: bold; padding: 10px;")
        
        button_layout.addWidget(self.save_invoice_button)
        button_layout.addWidget(self.clear_form_button)
        
        # Add all groups to main layout
        layout.addWidget(invoice_group)
        layout.addWidget(item_group)
        layout.addWidget(list_group)
        layout.addLayout(total_layout)
        layout.addLayout(button_layout)
        
        # Add stretch to push content to the top
        layout.addStretch()
        
        # Connect signals
        self.add_item_button.clicked.connect(self.add_item_to_list)
        self.remove_item_button.clicked.connect(self.remove_selected_item)
        self.clear_all_button.clicked.connect(self.clear_items_list)
        self.save_invoice_button.clicked.connect(self.save_invoice)
        self.clear_form_button.clicked.connect(self.clear_form)
        self.payment_status.currentTextChanged.connect(self.on_payment_status_changed)
        
        # Load suppliers
        self.load_suppliers()
    
    def load_suppliers(self):
        """Load suppliers from the suppliers table"""
        try:
            supplier_names = Supplier.get_supplier_names()
            self.supplier_combo.clear()
            self.supplier_combo.addItem("-- اختر المورد --")
            self.supplier_combo.addItems(supplier_names)
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل الموردين: {e}")
    
    def on_payment_status_changed(self, status):
        """Show paid amount field only for partially paid status"""
        self.paid_amount.setVisible(status == Invoice.PAYMENT_STATUS['PARTIALLY_PAID'])
    
    def add_item_to_list(self):
        """Add an item to the items list"""
        # Validate item fields
        if not self.item_name.text().strip():
            QMessageBox.warning(self, "خطأ في التحقق", "اسم المنتج مطلوب")
            return
        
        item_name = self.item_name.text().strip()
        quantity = self.quantity.value()
        quantity_type = self.quantity_type.currentText()
        price = self.price.value()
        total = quantity * price
        
        # Add item to list
        item_data = {
            'item_name': item_name,
            'quantity': quantity,
            'quantity_type': quantity_type,
            'price_per_unit': price,
            'total': total
        }
        
        self.items_list.append(item_data)
        self.update_items_table()
        self.clear_item_fields()
        self.update_total()
    
    def remove_selected_item(self):
        """Remove selected item from the list"""
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            self.items_list.pop(current_row)
            self.update_items_table()
            self.update_total()
        else:
            QMessageBox.information(self, "معلومات", "يرجى اختيار منتج لحذفه")
    
    def clear_items_list(self):
        """Clear all items from the list"""
        self.items_list.clear()
        self.update_items_table()
        self.update_total()
    
    def update_items_table(self):
        """Update the items table display"""
        self.items_table.setRowCount(len(self.items_list))
        
        for row, item in enumerate(self.items_list):
            self.items_table.setItem(row, 0, QTableWidgetItem(item['item_name']))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(item['quantity'])))
            self.items_table.setItem(row, 2, QTableWidgetItem(item['quantity_type']))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{item['price_per_unit']:.2f} ج.م"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{item['total']:.2f} ج.م"))
    
    def update_total(self):
        """Update the total amount display"""
        total = sum(item['total'] for item in self.items_list)
        self.total_label.setText(f"إجمالي المبلغ: {total:.2f} ج.م")
    
    def clear_item_fields(self):
        """Clear the item entry fields"""
        self.item_name.clear()
        self.quantity.setValue(1)
        self.quantity_type.setCurrentIndex(0)
        self.price.setValue(0.01)
    
    def save_invoice(self):
        """Save the invoice with all items"""
        # Validate invoice fields
        if not self.invoice_number.text().strip():
            QMessageBox.warning(self, "خطأ في التحقق", "رقم الفاتورة مطلوب")
            return
        
        if self.supplier_combo.currentText() == "-- اختر المورد --":
            QMessageBox.warning(self, "خطأ في التحقق", "يرجى اختيار مورد")
            return
        
        if not self.items_list:
            QMessageBox.warning(self, "خطأ في التحقق", "يرجى إضافة منتج واحد على الأقل")
            return
        
        # Get form values
        invoice_number = self.invoice_number.text().strip()
        supplier_name = self.supplier_combo.currentText()
        payment_status = self.payment_status.currentText()
        notes = self.notes.toPlainText()
        
        # Calculate total amount
        total_amount = sum(item['total'] for item in self.items_list)
        
        # Get paid amount if partially paid
        paid_amount = 0
        if payment_status == Invoice.PAYMENT_STATUS['PARTIALLY_PAID']:
            paid_amount = self.paid_amount.value()
            if paid_amount >= total_amount:
                QMessageBox.warning(self, "خطأ في التحقق", "المبلغ المدفوع يجب أن يكون أقل من إجمالي المبلغ للحالة مدفوع جزئيا")
                return
        elif payment_status == Invoice.PAYMENT_STATUS['PAID']:
            paid_amount = total_amount
        
        try:
            # Check if invoice already exists
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,))
            existing_invoice = cursor.fetchone()
            
            if existing_invoice:
                QMessageBox.warning(self, "خطأ في التحقق", f"رقم الفاتورة '{invoice_number}' موجود بالفعل")
                conn.close()
                return
            conn.close()
            
            # Create invoice first
            invoice_id = Invoice.add_invoice(
                invoice_number=invoice_number,
                supplier_name=supplier_name,
                total_amount=total_amount,
                payment_status=payment_status,
                paid_amount=paid_amount,
                notes=notes
            )
            
            if not invoice_id:
                QMessageBox.critical(self, "خطأ", "فشل في إنشاء الفاتورة")
                return
            
            # Add all items using a different approach
            items_added = 0
            failed_items = []
            
            for item in self.items_list:
                try:
                    # Add item directly to the database without creating/updating invoice
                    # since we already created the invoice
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    date_added = datetime.now().strftime('%Y-%m-%d')
                    
                    # Insert item
                    sql = '''INSERT INTO items
                            (item_name, quantity, quantity_type, price_per_unit, invoice_number, supplier_name, date_added)
                            VALUES (?, ?, ?, ?, ?, ?, ?)'''
                    
                    cursor.execute(sql, (
                        item['item_name'], 
                        item['quantity'], 
                        item['quantity_type'], 
                        item['price_per_unit'], 
                        invoice_number, 
                        supplier_name, 
                        date_added
                    ))
                    
                    conn.commit()
                    items_added += 1
                    
                except Exception as e:
                    print(f"Failed to add item {item['item_name']}: {e}")
                    failed_items.append(item['item_name'])
                finally:
                    if 'conn' in locals():
                        conn.close()
            
            if items_added == len(self.items_list):
                QMessageBox.information(self, "نجح", f"تم حفظ الفاتورة بنجاح مع {items_added} منتج")
                # Emit signal with invoice number for printing
                self.items_added.emit(invoice_number)
                self.clear_form()
            elif items_added > 0:
                failed_list = ", ".join(failed_items)
                QMessageBox.warning(self, "نجح جزئي", 
                                  f"تم حفظ الفاتورة مع {items_added} منتج.\nالمنتجات الفاشلة: {failed_list}")
            else:
                QMessageBox.critical(self, "خطأ", "فشل في إضافة أي منتجات للفاتورة")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ الفاتورة: {e}")
    
    def clear_form(self):
        """Clear the entire form"""
        self.invoice_number.clear()
        self.supplier_combo.setCurrentIndex(0)
        self.date.setDate(QDate.currentDate())
        self.payment_status.setCurrentText(Invoice.PAYMENT_STATUS['DELAYED'])
        self.paid_amount.setValue(0.00)
        self.paid_amount.setVisible(False)
        self.notes.clear()
        
        self.clear_item_fields()
        self.clear_items_list()
