from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QGridLayout, QScrollArea,
                               QTextEdit, QLineEdit, QTableWidget, QTableWidgetItem,
                               QHeaderView, QSpinBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class PizzaMainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Left side - Table selection
        left_frame = QFrame()
        left_frame.setFixedWidth(300)
        left_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #663399;
                border-radius: 10px;
            }
        """)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        # Table number label
        table_label = QLabel("رقم الطولة :")
        table_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #663399;
                text-align: right;
            }
        """)
        table_label.setAlignment(Qt.AlignRight)
        left_layout.addWidget(table_label)
        
        # Table selection buttons
        tables_frame = QFrame()
        tables_layout = QGridLayout(tables_frame)
        tables_layout.setSpacing(10)
        
        # Create table buttons (1-6 for example)
        for i in range(1, 7):
            table_btn = QPushButton(str(i))
            table_btn.setFixedSize(80, 80)
            table_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f1c40f;
                    color: #333;
                    border: none;
                    border-radius: 10px;
                    font-size: 24px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f39c12;
                }
                QPushButton:pressed {
                    background-color: #e67e22;
                }
            """)
            row = (i - 1) // 2
            col = (i - 1) % 2
            tables_layout.addWidget(table_btn, row, col)
        
        left_layout.addWidget(tables_frame)
        left_layout.addStretch()
        
        # Transfer table button
        transfer_btn = QPushButton("نقل الطولة")
        transfer_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1c40f;
                color: #333;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f39c12;
            }
        """)
        left_layout.addWidget(transfer_btn)
        
        # Right side - Order details and invoice
        right_frame = QFrame()
        right_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #663399;
                border-radius: 10px;
            }
        """)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(15, 15, 15, 15)
        
        # Invoice header
        invoice_header = QLabel("August-00004")
        invoice_header.setStyleSheet("""
            QLabel {
                background-color: #663399;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                text-align: center;
            }
        """)
        invoice_header.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(invoice_header)
        
        # Order table
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(3)
        self.order_table.setHorizontalHeaderLabels(["الكمية", "السعر", "اسم الصنف"])
        self.order_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #ddd;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                padding: 8px;
                font-weight: bold;
                text-align: center;
            }
            QTableWidget::item {
                padding: 8px;
                text-align: center;
            }
        """)
        
        # Set column widths
        header = self.order_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.order_table.setColumnWidth(0, 80)
        self.order_table.setColumnWidth(1, 100)
        
        right_layout.addWidget(self.order_table)
        
        # Total section
        total_frame = QFrame()
        total_layout = QVBoxLayout(total_frame)
        
        # Total input
        total_input_layout = QHBoxLayout()
        total_label = QLabel("الإجمالي:")
        total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.total_input = QLineEdit()
        self.total_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        total_input_layout.addWidget(total_label)
        total_input_layout.addWidget(self.total_input)
        total_layout.addLayout(total_input_layout)
        
        # Order type buttons
        order_type_layout = QHBoxLayout()
        
        delivery_btn = QPushButton("طولة")
        delivery_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1c40f;
                color: #333;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
        """)
        
        takeaway_btn = QPushButton("تيك اواي")
        takeaway_btn.setStyleSheet("""
            QPushButton {
                background-color: #663399;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
        """)
        
        order_type_layout.addWidget(delivery_btn)
        order_type_layout.addWidget(takeaway_btn)
        total_layout.addLayout(order_type_layout)
        
        # Discount and tax section
        calc_layout = QHBoxLayout()
        
        # Subtotal
        subtotal_layout = QVBoxLayout()
        subtotal_label = QLabel("الفرعي:")
        self.subtotal_input = QLineEdit()
        subtotal_layout.addWidget(subtotal_label)
        subtotal_layout.addWidget(self.subtotal_input)
        
        # Discount
        discount_layout = QVBoxLayout()
        discount_label = QLabel("خصم:")
        discount_input_layout = QHBoxLayout()
        self.discount_input = QLineEdit()
        discount_percent_btn = QPushButton("%")
        discount_dollar_btn = QPushButton("£")
        discount_input_layout.addWidget(self.discount_input)
        discount_input_layout.addWidget(discount_percent_btn)
        discount_input_layout.addWidget(discount_dollar_btn)
        discount_layout.addWidget(discount_label)
        discount_layout.addLayout(discount_input_layout)
        
        # Tax
        tax_layout = QVBoxLayout()
        tax_label = QLabel("ضريبة: 12%")
        tax_label2 = QLabel("توصيل:")
        self.delivery_input = QLineEdit()
        tax_layout.addWidget(tax_label)
        tax_layout.addWidget(tax_label2)
        tax_layout.addWidget(self.delivery_input)
        
        calc_layout.addLayout(subtotal_layout)
        calc_layout.addLayout(discount_layout)
        calc_layout.addLayout(tax_layout)
        total_layout.addLayout(calc_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        save_btn = QPushButton("حفظ")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        delete_btn = QPushButton("حذف")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        action_layout.addWidget(save_btn)
        action_layout.addWidget(delete_btn)
        total_layout.addLayout(action_layout)
        
        right_layout.addWidget(total_frame)
        
        # Add frames to main layout
        main_layout.addWidget(left_frame)
        main_layout.addWidget(right_frame, 1)
        
        self.setLayout(main_layout)
        
        # Add some sample data
        self.add_sample_data()
    
    def add_sample_data(self):
        """Add sample order data to the table"""
        sample_items = [
            ("2", "25.00", "Pizza Margherita"),
            ("1", "15.00", "Caesar Salad"),
            ("3", "8.00", "Soft Drinks")
        ]
        
        self.order_table.setRowCount(len(sample_items))
        
        for row, (qty, price, name) in enumerate(sample_items):
            self.order_table.setItem(row, 0, QTableWidgetItem(qty))
            self.order_table.setItem(row, 1, QTableWidgetItem(price))
            self.order_table.setItem(row, 2, QTableWidgetItem(name))
        
        # Set totals
        self.subtotal_input.setText("74.00")
        self.total_input.setText("82.88")
        self.delivery_input.setText("0.00")