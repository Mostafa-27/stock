from PySide6.QtWidgets import (QHeaderView, QMainWindow, QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout, 
                              QPushButton, QHBoxLayout, QStackedWidget,
                              QMessageBox, QToolBar, QDialog, QLabel,
                              QComboBox, QSplitter, QListWidget, QListWidgetItem,
                              QFrame, QApplication, QTabWidget, QAbstractItemView)
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QIcon, QAction, QColor, QPalette, QFont, QPixmap
import datetime
import pyodbc

from utils.resource_utils import get_image_path

from ui.add_multiple_items import AddMultipleItemsWidget
from ui.extract_item import ExtractItemWidget
from ui.stock_view import StockViewWidget
from ui.invoice_view import InvoiceViewWidget
from models.extraction import Extraction
from ui.settings import PrinterSettingsWidget
from ui.pizza_main import PizzaMainWidget
from ui.suppliers import SuppliersWidget
from models.settings import Settings
from utils.printer_utils import print_invoice, show_print_dialog
from models.invoice import Invoice
from database import get_db_connection
from management import ManagementWindow

class MainWindow(QMainWindow):
    def __init__(self, user_data=None):
        super().__init__()
        
        # Store user data
        self.user_data = user_data or {'id': 0, 'username': 'guest', 'is_admin': False}
        
        self.setWindowTitle(f"بيتزا ميلانو - {self.user_data['username']}")
        self.setMinimumSize(1200, 800)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Apply modern styling to the application
        self.apply_modern_style()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create custom title bar
        self.create_title_bar(main_layout)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create header bar
        header_bar = QFrame()
        header_bar.setFixedHeight(100)  # Increased height from 60 to 100
        header_bar.setStyleSheet("""
            QFrame {
                background-color: #663399;
                border-bottom: 3px solid #552288;
            }
        """)
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(30, 15, 30, 15)  # Increased margins
        
        # User info section with logout button
        user_section = QFrame()
        user_section_layout = QVBoxLayout(user_section)
        user_section_layout.setContentsMargins(0, 0, 0, 0)
        user_section_layout.setSpacing(5)
        
        user_info = QLabel(f"مستخدم: {self.user_data['username']}")
        user_info.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # Logout button
        self.logout_btn = QPushButton("تسجيل الخروج")
        self.logout_btn.setFixedSize(100, 25)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.logout_btn.clicked.connect(self.logout)
        
        # user_section_layout.addWidget(user_info)
        user_section_layout.addWidget(self.logout_btn)
        
        # Current date and time
        current_date = QLabel(datetime.datetime.now().strftime("%Y-%m-%d"))
        self.current_time = QLabel(datetime.datetime.now().strftime("%I:%M:%S %p"))
        invoice_label = QLabel(f" {user_info.text()}")  # Displaying user info in invoice label

        for label in [current_date, self.current_time, invoice_label]:
            label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 16px;  /* Increased font size */
                    font-weight: bold;
                    background: transparent;
                }
            """)
        
        # Setup timer for updating current time
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_current_time)
        self.time_timer.start(1000)  # Update every 1000ms (1 second)
        
        header_layout.addWidget(user_section)
        header_layout.addWidget(current_date)
        header_layout.addWidget(self.current_time)
        header_layout.addStretch()
        header_layout.addWidget(invoice_label)
        
        # Pizza Melano logo with actual image on the right
        logo_label = QLabel()
        logo_path = get_image_path("logo.png")
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            # Scale the logo to fit in the header
            scaled_pixmap = logo_pixmap.scaled(120, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            # Fallback text if image not found
            logo_label.setText("بيتزا\nميلانو")
            logo_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-size: 14px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
        
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedSize(120, 70)
        logo_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 2px solid #e74c3c;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        header_layout.addWidget(logo_label)
        
        # Add header to main layout
        main_layout.addWidget(header_bar)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #663399;
                color: white;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #e74c3c;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #552288;
            }
        """)
        
        # Create the different screens
        self.add_item_widget = AddMultipleItemsWidget()
        self.extract_item_widget = ExtractItemWidget()
        self.stock_view_widget = StockViewWidget()
        self.invoice_view_widget = InvoiceViewWidget()
        self.pizza_main_widget = PizzaMainWidget()
        self.suppliers_widget = SuppliersWidget()
        self.settings_widget = PrinterSettingsWidget(self.user_data)
        
        # Create management widget wrapper
        self.management_widget = self.create_management_widget()
        
        # Connect print signals
        self.add_item_widget.items_added.connect(self.handle_item_added)
        self.extract_item_widget.extraction_completed.connect(self.handle_item_extracted)
        self.invoice_view_widget.invoice_updated.connect(self.handle_invoice_updated)
        
        # Add tabs with Arabic text
        # self.tab_widget.addTab(self.pizza_main_widget, "الطولات")  # Tables
        self.tab_widget.addTab(self.invoice_view_widget, "الفواتير")  # Food Menu
        self.tab_widget.addTab(self.stock_view_widget, "المخزون")  # Reports
        self.tab_widget.addTab(self.extract_item_widget, "تصدير منتجات")  # Add Products
        self.tab_widget.addTab(self.suppliers_widget, "الموردين")  # Suppliers
        self.tab_widget.addTab(self.management_widget, "إدارة الموردين والفروع")  # Management
        self.tab_widget.addTab(self.add_item_widget, "إضافة منتجات")  # Settings
        self.tab_widget.addTab(self.settings_widget, "إعدادات الطابعة")  # Printer Settings
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.change_page)
        
        # Show pizza main view by default (الطولات)
        self.tab_widget.setCurrentIndex(0)  # Pizza main is at index 0
    
    def apply_modern_style(self):
        """Apply modern styling to the entire application"""
        # Set application font
        font = QFont("Segoe UI", 10)
        QApplication.setFont(font)
        
        # Set global stylesheet
        self.setStyleSheet("""
            /* General styles */
            QWidget {
                font-family: 'Segoe UI', sans-serif;
            }
            
            /* Button styles */
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
            
            /* Table styles */
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                alternate-background-color: #f9f9f9;
                gridline-color: #ddd;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 6px;
                font-weight: bold;
            }
            
            /* Input field styles */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #3498db;
            }
            
            /* Combobox styles */
            QComboBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            /* Scrollbar styles */
            QScrollBar:vertical {
                border: none;
                background: #f5f5f5;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a8a8a8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f5f5f5;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #c1c1c1;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #a8a8a8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
    
    def create_title_bar(self, main_layout):
        """Create custom title bar with window controls"""
        title_bar = QFrame()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-bottom: 1px solid #34495e;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        title_layout.setSpacing(0)
        
        # Window title
        title_label = QLabel(f"بيتزا ميلانو - {self.user_data['username']}")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Window control buttons
        button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 16px;
                font-weight: bold;
                width: 30px;
                height: 30px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #34495e;
                border-radius: 3px;
            }
        """
        
        # Minimize button
        minimize_btn = QPushButton("−")
        minimize_btn.setStyleSheet(button_style)
        minimize_btn.clicked.connect(self.showMinimized)
        minimize_btn.setToolTip("تصغير")
        
        # Maximize/Restore button
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setStyleSheet(button_style)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.maximize_btn.setToolTip("تكبير")
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 18px;
                font-weight: bold;
                width: 30px;
                height: 30px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
                border-radius: 3px;
            }
        """)
        close_btn.clicked.connect(self.close)
        close_btn.setToolTip("إغلاق")
        
        title_layout.addWidget(minimize_btn)
        title_layout.addWidget(self.maximize_btn)
        title_layout.addWidget(close_btn)
        
        # Make title bar draggable
        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move
        
        main_layout.addWidget(title_bar)
    
    def toggle_maximize(self):
        """Toggle between maximized and normal window state"""
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("□")
            self.maximize_btn.setToolTip("تكبير")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")
            self.maximize_btn.setToolTip("استعادة")
    
    def title_bar_mouse_press(self, event):
        """Handle mouse press on title bar for dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def title_bar_mouse_move(self, event):
        """Handle mouse move on title bar for dragging"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def create_toolbar(self):
        """Create the application toolbar - hidden for Pizza Melano design"""
        # Hide toolbar for frameless design
        pass
    
    def change_page(self, index):
        """Change the current page based on tab selection"""
        # Refresh data as needed
        if index == 1:  # Food Menu (Invoice View)
            self.invoice_view_widget.refresh_suppliers()
        elif index == 2:  # Reports (Stock View)
            self.stock_view_widget.refresh_items()
        elif index == 3:  # Add Products (Extract Items)
            self.extract_item_widget.refresh_items()
        elif index == 4:  # Suppliers
            pass  # No refresh needed for suppliers
        elif index == 5:  # Management (Suppliers and Branches)
            self.load_management_data()
        elif index == 6:  # Add Items
            pass  # No refresh needed for add items
        elif index == 7:  # Printer Settings
            pass  # Printer settings widget handles its own refresh
    
    def create_history_widget(self):
        """Create the history operations widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title label
        title_label = QLabel("عمليات التاريخ")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        # Create table for history
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "التاريخ", "اسم المنتج", "نوع العملية", "الكمية", "التفاصيل"
        ])
        self.history_table.setAlternatingRowColors(True)  # Alternate row colors
        
        # Set table properties
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.verticalHeader().setVisible(False)  # Hide vertical header
        
        layout.addWidget(self.history_table)
        
        # Add buttons in a horizontal layout
        buttons_layout = QHBoxLayout()
        
        # Add refresh button
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.refresh_history)
        
        # Add print button for history operations
        print_btn = QPushButton("🖨️ طباعة التاريخ")
        print_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        print_btn.clicked.connect(self.print_history)
        
        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addWidget(print_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        return widget
        
    def print_history(self):
        """Print the history operations table"""
        try:
            # Get all rows from the history table
            rows = []
            for row in range(self.history_table.rowCount()):
                row_data = {
                    'date': self.history_table.item(row, 0).text(),
                    'item_name': self.history_table.item(row, 1).text(),
                    'operation_type': self.history_table.item(row, 2).text(),
                    'quantity': self.history_table.item(row, 3).text(),
                    'details': self.history_table.item(row, 4).text()
                }
                rows.append(row_data)
            
            if not rows:
                QMessageBox.information(self, "لا توجد بيانات", "لا توجد بيانات تاريخ للطباعة.")
                return
            
            # Create a simplified invoice-like structure for history
            history_data = {
                'invoice_number': f"HIST-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                'supplier_name': "History Operations Report",
                'total_amount': 0,
                'payment_status': 'Report',
                'paid_amount': 0,
                'issue_date': datetime.datetime.now().strftime('%Y-%m-%d'),
                'due_date': None,
                'notes': f"History operations report generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            # Create items data for the report
            items_data = []
            for row in rows:
                items_data.append({
                    'id': 0,
                    'item_name': f"{row['item_name']} ({row['operation_type']})",
                    'quantity': row['quantity'],
                    'price_per_unit': 0,
                    'invoice_number': history_data['invoice_number'],
                    'supplier_name': row['details'],
                    'date_added': row['date']
                })
            
            # Print the history report
            from utils.printer_utils import show_print_dialog
            if show_print_dialog(self, history_data, items_data, is_history=True):
                QMessageBox.information(self, "نجح", "تم إرسال تقرير التاريخ إلى الطابعة")
            else:
                QMessageBox.warning(self, "تم إلغاء الطباعة", "تم إلغاء الطباعة أو فشلت.")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الطباعة", f"خطأ في طباعة تقرير التاريخ: {e}")
    
    def refresh_history(self):
        """Refresh the history operations table"""
        # Clear table
        self.history_table.setRowCount(0)
        
        # Get all extractions
        extractions = Extraction.get_all_extractions()
        
        # Add extractions to table
        for extraction in extractions:
            row_position = self.history_table.rowCount()
            self.history_table.insertRow(row_position)
            
            self.history_table.setItem(row_position, 0, QTableWidgetItem(extraction['date_extracted']))
            self.history_table.setItem(row_position, 1, QTableWidgetItem(extraction['item_name']))
            self.history_table.setItem(row_position, 2, QTableWidgetItem("Extraction"))
            self.history_table.setItem(row_position, 3, QTableWidgetItem(str(extraction['quantity_extracted'])))
            self.history_table.setItem(row_position, 4, QTableWidgetItem(f"To: {extraction['branch_name']}"))
        
        # Get all items (additions)
        from models.item import Item
        items = Item.get_all_items()
        
        # Add items to table
        for item in items:
            row_position = self.history_table.rowCount()
            self.history_table.insertRow(row_position)
            
            self.history_table.setItem(row_position, 0, QTableWidgetItem(item.date_added))
            self.history_table.setItem(row_position, 1, QTableWidgetItem(item.item_name))
            self.history_table.setItem(row_position, 2, QTableWidgetItem("Addition"))
            self.history_table.setItem(row_position, 3, QTableWidgetItem(str(item.quantity)))
            self.history_table.setItem(row_position, 4, QTableWidgetItem(f"Invoice: {item.invoice_number}"))
        
        # Sort by date (newest first)
        self.history_table.sortItems(0, Qt.DescendingOrder)
    
    def handle_item_added(self, invoice_number):
        """Handle auto-printing when an item is added"""
        if Settings.get_setting('auto_print', True):
            try:
                # Get invoice data
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM invoices WHERE invoice_number = ?", 
                    (invoice_number,)
                )
                invoice_row = cursor.fetchone()
                
                if invoice_row:
                    invoice_data = {
                        'id': invoice_row[0],
                        'invoice_number': invoice_row[1],
                        'supplier_name': invoice_row[2],
                        'total_amount': invoice_row[3],
                        'payment_status': invoice_row[4],
                        'paid_amount': invoice_row[5],
                        'issue_date': invoice_row[6],
                        'due_date': invoice_row[7],
                        'notes': invoice_row[8]
                    }
                    
                    # Get items for this invoice
                    cursor.execute(
                        "SELECT * FROM items WHERE invoice_number = ?",
                        (invoice_number,)
                    )
                    items_data = []
                    for item_row in cursor.fetchall():
                        items_data.append({
                            'id': item_row[0],
                            'item_name': item_row[1],
                            'quantity': item_row[2],
                            'quantity_type': item_row[3],
                            'price_per_unit': item_row[4],
                            'invoice_number': item_row[5],
                            'supplier_name': item_row[6],
                            'date_added': item_row[7]
                        })
                    
                    # Print the invoice
                    print_invoice(invoice_data, items_data)
                
                if 'conn' in locals():
                    conn.close()
            except pyodbc.Error as e:
                QMessageBox.warning(self, "Printing Error", f"Error printing invoice: {e}")
    
    def handle_item_extracted(self, items_list, branch_name, extracted_by):
        """Handle auto-printing when items are extracted"""
        if Settings.get_setting('auto_print', True):
            try:
                # Get item data from database
                from models.item import Item
                
                # Create a simplified invoice-like structure for extraction
                extraction_data = {
                    'invoice_number': f"EXT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'supplier_name': f"Extraction to {branch_name}",
                    'total_amount': 0,  # Will calculate below
                    'payment_status': 'Extraction',
                    'paid_amount': 0,
                    'issue_date': datetime.datetime.now().strftime('%Y-%m-%d'),
                    'due_date': None,
                    'notes': f"Items extracted from inventory to {branch_name} by {extracted_by}"
                }
                
                # Create items data and calculate total
                items_data = []
                total_amount = 0
                
                for item_data in items_list:
                    # Get full item details
                    item = Item.get_item_by_id(item_data['item_id'])
                    if item:
                        quantity = item_data['quantity']
                        item_total = item.price_per_unit * quantity
                        total_amount += item_total
                        
                        items_data.append({
                            'id': item.id,
                            'item_name': item.item_name,
                            'quantity': quantity,
                            'price_per_unit': item.price_per_unit,
                            'invoice_number': extraction_data['invoice_number'],
                            'supplier_name': extraction_data['supplier_name'],
                            'date_added': datetime.datetime.now().strftime('%Y-%m-%d')
                        })
                
                extraction_data['total_amount'] = total_amount
                
                # Print the extraction receipt
                print_invoice(extraction_data, items_data)
            except Exception as e:
                QMessageBox.warning(self, "Printing Error", f"Error printing extraction receipt: {e}")
    
    def handle_invoice_updated(self, invoice_number):
        """Handle auto-printing when an invoice is updated"""
        if Settings.get_setting('auto_print', True):
            try:
                # Get invoice data and print
                invoice_data = Invoice.get_invoice_by_number(invoice_number)
                if invoice_data:
                    # Get items for this invoice
                    items_data = Invoice.get_items_by_invoice(invoice_number)
                    
                    # Print the invoice
                    print_invoice(invoice_data, items_data)
            except Exception as e:
                QMessageBox.warning(self, "Printing Error", f"Error printing invoice: {e}")
    
    def show_print_dialog(self):
        """Show dialog to select an invoice to print"""
        # Get all invoices
        invoices = Invoice.get_all_invoices()
        
        if not invoices:
            QMessageBox.information(self, "لا توجد فواتير", "لا توجد فواتير للطباعة.")
            return
        
        # Create a dialog to select an invoice
        dialog = QDialog(self)
        dialog.setWindowTitle("اختر الفاتورة للطباعة")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Create a combo box with invoice numbers
        combo = QComboBox()
        for invoice in invoices:
            combo.addItem(f"{invoice['invoice_number']} - {invoice['supplier_name']}", 
                         invoice['invoice_number'])
        
        layout.addWidget(QLabel("اختر الفاتورة:"))
        layout.addWidget(combo)
        
        # Create buttons
        buttons = QHBoxLayout()
        print_btn = QPushButton("طباعة")
        cancel_btn = QPushButton("إلغاء")
        
        buttons.addWidget(print_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
        
        # Connect buttons
        cancel_btn.clicked.connect(dialog.reject)
        
        def print_selected_invoice():
            invoice_number = combo.currentData()
            if invoice_number:
                # Get invoice data
                invoice_data = Invoice.get_invoice_by_number(invoice_number)
                if invoice_data:
                    # Get items for this invoice
                    items_data = Invoice.get_items_by_invoice(invoice_number)
                    
                    # Show print dialog
                    if show_print_dialog(self, invoice_data, items_data):
                        dialog.accept()
                    else:
                        QMessageBox.warning(self, "Printing Error", "Failed to print invoice.")
        
        print_btn.clicked.connect(print_selected_invoice)
        
        # Show the dialog
        dialog.exec()
    
    def create_management_widget(self):
        """Create the management widget with suppliers and branches tabs"""
        from models.supplier import Supplier
        from models.branch import Branch
        from supplier_dialog import SupplierDialog
        from branch_dialog import BranchDialog
        
        # Main widget
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("إدارة الموردين والفروع")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                background-color: #ecf0f1;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Tab widget for suppliers and branches
        self.management_tab_widget = QTabWidget()
        self.management_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: black;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #5dade2;
                color: white;
            }
        """)
        
        # Create suppliers and branches tabs
        self.suppliers_tab = self.create_suppliers_management_tab()
        self.branches_tab = self.create_branches_management_tab()
        
        self.management_tab_widget.addTab(self.suppliers_tab, "الموردين")
        self.management_tab_widget.addTab(self.branches_tab, "الفروع")
        
        layout.addWidget(self.management_tab_widget)
        widget.setLayout(layout)
        
        # Load initial data
        self.load_management_data()
        
        return widget
    
    def create_suppliers_management_tab(self):
        """Create suppliers management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        self.add_supplier_btn = QPushButton("إضافة مورد جديد")
        self.add_supplier_btn.setStyleSheet(self.get_management_button_style("#27ae60"))
        self.add_supplier_btn.clicked.connect(self.add_supplier)
        
        self.edit_supplier_btn = QPushButton("تعديل المورد")
        self.edit_supplier_btn.setStyleSheet(self.get_management_button_style("#3498db"))
        self.edit_supplier_btn.clicked.connect(self.edit_supplier)
        
        self.delete_supplier_btn = QPushButton("حذف المورد")
        self.delete_supplier_btn.setStyleSheet(self.get_management_button_style("#e74c3c"))
        self.delete_supplier_btn.clicked.connect(self.delete_supplier)
        
        self.refresh_suppliers_btn = QPushButton("تحديث")
        self.refresh_suppliers_btn.setStyleSheet(self.get_management_button_style("#f39c12"))
        self.refresh_suppliers_btn.clicked.connect(self.load_suppliers_data)
        
        buttons_layout.addWidget(self.add_supplier_btn)
        buttons_layout.addWidget(self.edit_supplier_btn)
        buttons_layout.addWidget(self.delete_supplier_btn)
        buttons_layout.addWidget(self.refresh_suppliers_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Suppliers table
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(6)
        self.suppliers_table.setHorizontalHeaderLabels([
            "اسم المورد", "الشخص المسؤول", "الهاتف", "البريد الإلكتروني", "شروط الدفع", "تاريخ الإضافة"
        ])
        
        # Table styling
        self.suppliers_table.setStyleSheet(self.get_management_table_style())
        self.suppliers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.suppliers_table.setAlternatingRowColors(True)
        
        # Auto resize columns
        header = self.suppliers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Double click to edit
        self.suppliers_table.doubleClicked.connect(self.edit_supplier)
        
        layout.addWidget(self.suppliers_table)
        widget.setLayout(layout)
        return widget
    
    def create_branches_management_tab(self):
        """Create branches management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        self.add_branch_btn = QPushButton("إضافة فرع جديد")
        self.add_branch_btn.setStyleSheet(self.get_management_button_style("#27ae60"))
        self.add_branch_btn.clicked.connect(self.add_branch)
        
        self.edit_branch_btn = QPushButton("تعديل الفرع")
        self.edit_branch_btn.setStyleSheet(self.get_management_button_style("#3498db"))
        self.edit_branch_btn.clicked.connect(self.edit_branch)
        
        self.delete_branch_btn = QPushButton("حذف الفرع")
        self.delete_branch_btn.setStyleSheet(self.get_management_button_style("#e74c3c"))
        self.delete_branch_btn.clicked.connect(self.delete_branch)
        
        self.refresh_branches_btn = QPushButton("تحديث")
        self.refresh_branches_btn.setStyleSheet(self.get_management_button_style("#f39c12"))
        self.refresh_branches_btn.clicked.connect(self.load_branches_data)
        
        buttons_layout.addWidget(self.add_branch_btn)
        buttons_layout.addWidget(self.edit_branch_btn)
        buttons_layout.addWidget(self.delete_branch_btn)
        buttons_layout.addWidget(self.refresh_branches_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Branches table
        self.branches_table = QTableWidget()
        self.branches_table.setColumnCount(6)
        self.branches_table.setHorizontalHeaderLabels([
            "اسم الفرع", "كود الفرع", "المدير", "الهاتف", "تاريخ الافتتاح", "تاريخ الإضافة"
        ])
        
        # Table styling
        self.branches_table.setStyleSheet(self.get_management_table_style())
        self.branches_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.branches_table.setAlternatingRowColors(True)
        
        # Auto resize columns
        header = self.branches_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Double click to edit
        self.branches_table.doubleClicked.connect(self.edit_branch)
        
        layout.addWidget(self.branches_table)
        widget.setLayout(layout)
        return widget
    
    def get_management_button_style(self, color):
        """Get button style for management buttons"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
            }}
        """
    
    def get_management_table_style(self):
        """Get table style for management tables"""
        return """
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """
    
    def darken_color(self, color, factor=0.9):
        """Darken a hex color"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def load_management_data(self):
        """Load both suppliers and branches data"""
        self.load_suppliers_data()
        self.load_branches_data()
    
    def load_suppliers_data(self):
        """Load suppliers data into table"""
        from models.supplier import Supplier
        suppliers = Supplier.get_all_suppliers()
        self.suppliers_table.setRowCount(len(suppliers))
        
        for row, supplier in enumerate(suppliers):
            self.suppliers_table.setItem(row, 0, QTableWidgetItem(supplier['supplier_name']))
            self.suppliers_table.setItem(row, 1, QTableWidgetItem(supplier['contact_person'] or ''))
            self.suppliers_table.setItem(row, 2, QTableWidgetItem(supplier['phone'] or ''))
            self.suppliers_table.setItem(row, 3, QTableWidgetItem(supplier['email'] or ''))
            self.suppliers_table.setItem(row, 4, QTableWidgetItem(supplier['payment_terms'] or ''))
            
            date_added = supplier['date_added']
            if date_added:
                date_str = date_added.strftime('%Y-%m-%d') if hasattr(date_added, 'strftime') else str(date_added)
                self.suppliers_table.setItem(row, 5, QTableWidgetItem(date_str))
            else:
                self.suppliers_table.setItem(row, 5, QTableWidgetItem(''))
            
            # Store supplier data in the first item for easy access
            self.suppliers_table.item(row, 0).setData(Qt.UserRole, supplier)
    
    def load_branches_data(self):
        """Load branches data into table"""
        from models.branch import Branch
        branches = Branch.get_all_branches()
        self.branches_table.setRowCount(len(branches))
        
        for row, branch in enumerate(branches):
            self.branches_table.setItem(row, 0, QTableWidgetItem(branch['branch_name']))
            self.branches_table.setItem(row, 1, QTableWidgetItem(branch['branch_code'] or ''))
            self.branches_table.setItem(row, 2, QTableWidgetItem(branch['manager_name'] or ''))
            self.branches_table.setItem(row, 3, QTableWidgetItem(branch['phone'] or ''))
            
            opening_date = branch['opening_date']
            if opening_date:
                date_str = opening_date.strftime('%Y-%m-%d') if hasattr(opening_date, 'strftime') else str(opening_date)
                self.branches_table.setItem(row, 4, QTableWidgetItem(date_str))
            else:
                self.branches_table.setItem(row, 4, QTableWidgetItem(''))
            
            date_added = branch['date_added']
            if date_added:
                date_str = date_added.strftime('%Y-%m-%d') if hasattr(date_added, 'strftime') else str(date_added)
                self.branches_table.setItem(row, 5, QTableWidgetItem(date_str))
            else:
                self.branches_table.setItem(row, 5, QTableWidgetItem(''))
            
            # Store branch data in the first item for easy access
            self.branches_table.item(row, 0).setData(Qt.UserRole, branch)
    
    def add_supplier(self):
        """Add new supplier"""
        from supplier_dialog import SupplierDialog
        dialog = SupplierDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_suppliers_data()
    
    def edit_supplier(self):
        """Edit selected supplier"""
        current_row = self.suppliers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار مورد للتعديل")
            return
        
        supplier_data = self.suppliers_table.item(current_row, 0).data(Qt.UserRole)
        from supplier_dialog import SupplierDialog
        dialog = SupplierDialog(self, supplier_data)
        if dialog.exec() == QDialog.Accepted:
            self.load_suppliers_data()
    
    def delete_supplier(self):
        """Delete selected supplier"""
        current_row = self.suppliers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار مورد للحذف")
            return
        
        supplier_data = self.suppliers_table.item(current_row, 0).data(Qt.UserRole)
        supplier_name = supplier_data['supplier_name']
        
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   f"هل أنت متأكد من حذف المورد '{supplier_name}'؟",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            from models.supplier import Supplier
            if Supplier.delete_supplier(supplier_data['id']):
                QMessageBox.information(self, "نجح", "تم حذف المورد بنجاح")
                self.load_suppliers_data()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف المورد")
    
    def add_branch(self):
        """Add new branch"""
        from branch_dialog import BranchDialog
        dialog = BranchDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_branches_data()
    
    def edit_branch(self):
        """Edit selected branch"""
        current_row = self.branches_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار فرع للتعديل")
            return
        
        branch_data = self.branches_table.item(current_row, 0).data(Qt.UserRole)
        from branch_dialog import BranchDialog
        dialog = BranchDialog(self, branch_data)
        if dialog.exec() == QDialog.Accepted:
            self.load_branches_data()
    
    def delete_branch(self):
        """Delete selected branch"""
        current_row = self.branches_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار فرع للحذف")
            return
        
        branch_data = self.branches_table.item(current_row, 0).data(Qt.UserRole)
        branch_name = branch_data['branch_name']
        
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   f"هل أنت متأكد من حذف الفرع '{branch_name}'؟",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            from models.branch import Branch
            if Branch.delete_branch(branch_data['id']):
                QMessageBox.information(self, "نجح", "تم حذف الفرع بنجاح")
                self.load_branches_data()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف الفرع")
    
    
    def open_management_window(self):
        """This method is no longer needed as management is now integrated in tabs"""
        # This method is kept for compatibility but does nothing
        # Management functionality is now integrated directly in the management tab
        pass
    
    def update_current_time(self):
        """Update the current time display"""
        current_time_str = datetime.datetime.now().strftime("%I:%M:%S %p")
        self.current_time.setText(current_time_str)
    
    def logout(self):
        """Handle logout functionality"""
        reply = QMessageBox.question(self, 'تسجيل الخروج', 
                                   'هل أنت متأكد من تسجيل الخروج؟',
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Close the main window
            self.close()
            
            # Import and show login widget
            from ui.login import LoginWidget
            self.login_widget = LoginWidget()
            self.login_widget.show()