from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QTableWidget, QTableWidgetItem, QHeaderView, 
                                QComboBox, QLabel, QMessageBox, QFrame, QGroupBox,
                                QDateEdit, QFileDialog, QTabWidget, QScrollArea)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont
from database import get_db_connection
import pyodbc
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime, timedelta

# Try to import bidi for proper Arabic text processing
try:
    from bidi.algorithm import get_display
    BIDI_AVAILABLE = True
except ImportError:
    BIDI_AVAILABLE = False
    print("Warning: python-bidi not available. Arabic text may not display correctly.")

# Try to import arabic-reshaper for proper Arabic text shaping
try:
    import arabic_reshaper
    ARABIC_RESHAPER_AVAILABLE = True
except ImportError:
    ARABIC_RESHAPER_AVAILABLE = False
    print("Warning: arabic-reshaper not available. Arabic text may not display correctly.")

# Register Arabic font for PDF generation
def register_arabic_font():
    """Register Arabic font for ReportLab PDF generation"""
    try:
        # Try to register fonts that support Arabic text
        font_paths = [
            "C:/Windows/Fonts/tahoma.ttf",  # Tahoma supports Arabic well
            "C:/Windows/Fonts/tahomabd.ttf",  # Tahoma Bold supports Arabic well
            "C:/Windows/Fonts/arial.ttf",  # Arial supports basic Arabic
            "C:/Windows/Fonts/arialbd.ttf",  # Arial Bold supports basic Arabic
            "C:/Windows/Fonts/calibri.ttf",  # Calibri supports Arabic
            "C:/Windows/Fonts/segoeui.ttf",  # Segoe UI supports Arabic
            "C:/Windows/Fonts/times.ttf",  # Times New Roman supports Arabic
        ]
        
        registered = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('Arabic', font_path))
                    # Also register bold version if Tahoma
                    if 'tahoma.ttf' in font_path:
                        bold_path = font_path.replace('tahoma.ttf', 'tahomabd.ttf')
                        if os.path.exists(bold_path):
                            pdfmetrics.registerFont(TTFont('Arabic-Bold', bold_path))
                    registered = True
                    print(f"Successfully registered Arabic font: {font_path}")
                    break
                except Exception as e:
                    print(f"Failed to register font {font_path}: {e}")
                    continue
        
        if not registered:
            # If no system fonts found, try DejaVu Sans which has good Arabic support
            print("Warning: No Arabic-supporting fonts found, trying DejaVu Sans...")
            try:
                # DejaVu Sans typically has good Arabic support and is often available
                dejavu_path = "C:/Windows/Fonts/DejaVuSans.ttf"
                if os.path.exists(dejavu_path):
                    pdfmetrics.registerFont(TTFont('Arabic', dejavu_path))
                    registered = True
                else:
                    # Register Arial as fallback (should be available on most systems)
                    pdfmetrics.registerFont(TTFont('Arabic', 'C:/Windows/Fonts/arial.ttf'))
                    registered = True
            except:
                # If even Arial fails, use default system font
                print("Using default system font for Arabic text")
                registered = False
                
        return registered
        
    except Exception as e:
        print(f"Error registering Arabic font: {e}")
        # Register fallback font
        try:
            # Try to use built-in font that supports Unicode
            return False  # Let system handle font selection
        except:
            return False

# Register the font when module is imported
font_registered = register_arabic_font()

def get_font_name():
    """Get the appropriate font name for Arabic text"""
    if font_registered:
        return 'Arabic'
    else:
        # Use built-in fonts that should support Unicode/Arabic better
        return 'Times-Roman'  # Times-Roman has better Unicode support than Helvetica

def format_arabic_text(text):
    """Format Arabic text for proper display in PDF"""
    if not text:
        return ""
    
    text_str = str(text)
    
    # First, reshape Arabic text to connect letters properly
    if ARABIC_RESHAPER_AVAILABLE:
        try:
            reshaped_text = arabic_reshaper.reshape(text_str)
        except Exception as e:
            print(f"Warning: Could not reshape Arabic text: {e}")
            reshaped_text = text_str
    else:
        reshaped_text = text_str
    
    # Then apply bidirectional algorithm for proper text direction
    if BIDI_AVAILABLE:
        try:
            # Use bidi algorithm to properly format Arabic text direction
            return get_display(reshaped_text)
        except Exception as e:
            print(f"Warning: Could not format Arabic text direction: {e}")
            return reshaped_text
    
    return reshaped_text
from models.supplier import Supplier
from models.branch import Branch
from models.invoice import Invoice

class SuppliersWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_branch_data = None
        self.init_ui()
        self.load_suppliers()
        
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("إدارة الموردين والفروع")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 8px;
                text-align: center;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #bdc3c7;
            }
        """)
        
        # Create supplier tab
        self.supplier_tab = self.create_supplier_tab()
        self.tab_widget.addTab(self.supplier_tab, "تقارير الموردين")
        
        # Create branch tab
        self.branch_tab = self.create_branch_tab()
        self.tab_widget.addTab(self.branch_tab, "تقارير الفروع")
        
        main_layout.addWidget(self.tab_widget)
    
    def generate_branch_report_inline(self):
        """Generate branch report inline in the tab"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get branch extraction data with branch details from new branches table
            cursor.execute("""
                SELECT COALESCE(b.branch_name, e.branch_name) as branch_name, 
                       COUNT(e.id) as total_extractions,
                       SUM(e.quantity_extracted) as total_quantity,
                       COUNT(DISTINCT i.item_name) as unique_items,
                       b.branch_code,
                       b.manager_name
                FROM extractions e
                JOIN items i ON e.item_id = i.id
                LEFT JOIN branches b ON e.branch_name = b.branch_name AND b.is_active = 1
                GROUP BY COALESCE(b.branch_name, e.branch_name), b.branch_code, b.manager_name
                ORDER BY total_quantity DESC
            """)
            
            branch_data = cursor.fetchall()
            conn.close()
            
            if not branch_data:
                # Clear table and show empty state
                self.branch_table.setRowCount(0)
                self.branch_report_frame.show()
                self.adjust_branch_table_height()
                
                # Switch to branch tab and show message
                self.tab_widget.setCurrentIndex(1)
                QMessageBox.information(self, "معلومات", "لا توجد بيانات فروع للعرض")
                return
            
            # Store branch data for export
            self.current_branch_data = branch_data
            
            # Clear existing data
            self.branch_table.setRowCount(0)
            
            # Populate the branch table
            self.branch_table.setRowCount(len(branch_data))
            
            for row, data in enumerate(branch_data):
                self.branch_table.setItem(row, 0, QTableWidgetItem(str(data[0]) if data[0] else ""))
                self.branch_table.setItem(row, 1, QTableWidgetItem(str(data[4]) if data[4] else "غير محدد"))
                self.branch_table.setItem(row, 2, QTableWidgetItem(str(data[5]) if data[5] else "غير محدد"))
                self.branch_table.setItem(row, 3, QTableWidgetItem(str(data[1])))
                self.branch_table.setItem(row, 4, QTableWidgetItem(str(data[2])))
                self.branch_table.setItem(row, 5, QTableWidgetItem(str(data[3])))
            
            # Show the branch report frame
            self.branch_report_frame.show()
            
            # Adjust branch table height
            self.adjust_branch_table_height()
            
            # Switch to branch tab
            self.tab_widget.setCurrentIndex(1)
            
        except pyodbc.Error as e:
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"فشل في تحميل تقرير الفروع: {e}")
    
    def create_supplier_tab(self):
        """Create the supplier reports tab"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
        """)
        
        # Create content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Supplier selection section
        supplier_frame = QGroupBox("اختيار المورد")
        supplier_frame.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        supplier_layout = QHBoxLayout(supplier_frame)
        
        # Supplier dropdown
        supplier_label = QLabel("المورد:")
        supplier_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        self.supplier_combo = QComboBox()
        self.supplier_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #7f8c8d;
                margin-right: 5px;
            }
        """)
        self.supplier_combo.currentTextChanged.connect(self.on_supplier_changed)
        
        # Refresh button
        refresh_btn = QPushButton("تحديث")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        refresh_btn.clicked.connect(self.load_suppliers)
        
        supplier_layout.addWidget(supplier_label)
        supplier_layout.addWidget(self.supplier_combo)
        supplier_layout.addWidget(refresh_btn)
        supplier_layout.addStretch()
        
        layout.addWidget(supplier_frame)
        
        # Date filtering section
        filter_frame = QGroupBox("تصفية حسب التاريخ")
        filter_frame.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        
        # From date
        from_date_label = QLabel("من تاريخ:")
        from_date_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))  # Default to 30 days ago
        self.from_date.setCalendarPopup(True)
        self.from_date.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
                min-width: 120px;
            }
            QDateEdit:focus {
                border-color: #3498db;
            }
        """)
        
        # To date
        to_date_label = QLabel("إلى تاريخ:")
        to_date_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
                min-width: 120px;
            }
            QDateEdit:focus {
                border-color: #3498db;
            }
        """)
        
        # Filter button
        filter_btn = QPushButton("تطبيق التصفية")
        filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        filter_btn.clicked.connect(self.apply_date_filter)
        
        # Clear filter button
        clear_filter_btn = QPushButton("إزالة التصفية")
        clear_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """)
        clear_filter_btn.clicked.connect(self.clear_date_filter)
        
        filter_layout.addWidget(from_date_label)
        filter_layout.addWidget(self.from_date)
        filter_layout.addWidget(to_date_label)
        filter_layout.addWidget(self.to_date)
        filter_layout.addWidget(filter_btn)
        filter_layout.addWidget(clear_filter_btn)
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)
        
        # Invoices table
        table_frame = QGroupBox("فواتير المورد")
        table_frame.setMinimumHeight(500)  # Set larger height for the invoices section
        table_frame.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(6)
        self.invoices_table.setHorizontalHeaderLabels([
            "رقم الفاتورة", "المورد", "المبلغ الإجمالي", "حالة الدفع", "المبلغ المدفوع", "تاريخ الإصدار"
        ])
        
        # Set dynamic height based on content
        self.invoices_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.invoices_table.verticalHeader().setDefaultSectionSize(35)  # Row height
        self.invoices_table.setMaximumHeight(600)  # Maximum height to prevent excessive growth
        

        
        # Style the table
        self.invoices_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                gridline-color: #ecf0f1;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        # Configure table
        header = self.invoices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        table_layout.addWidget(self.invoices_table)
        layout.addWidget(table_frame)
        
        # Summary section
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)
        
        self.total_invoices_label = QLabel("إجمالي الفواتير: 0")
        self.total_amount_label = QLabel("إجمالي المبلغ: 0.00")
        self.paid_amount_label = QLabel("المبلغ المدفوع: 0.00")
        self.remaining_amount_label = QLabel("المبلغ المتبقي: 0.00")
        
        for label in [self.total_invoices_label, self.total_amount_label, 
                     self.paid_amount_label, self.remaining_amount_label]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 5px;
                }
            """)
        
        summary_layout.addWidget(self.total_invoices_label)
        summary_layout.addWidget(self.total_amount_label)
        summary_layout.addWidget(self.paid_amount_label)
        summary_layout.addWidget(self.remaining_amount_label)
        
        layout.addWidget(summary_frame)
        
        # Export and Reports section
        actions_frame = QGroupBox("التصدير والتقارير")
        actions_frame.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        actions_layout = QHBoxLayout(actions_frame)
        
        # Export to PDF button
        export_pdf_btn = QPushButton("تصدير الفواتير إلى PDF")
        export_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        export_pdf_btn.clicked.connect(self.export_to_pdf)
        
        # Branch report button
        branch_report_btn = QPushButton("تقرير الفروع")
        branch_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        branch_report_btn.clicked.connect(self.generate_branch_report)
        
        # Export branch report to PDF button
        export_branch_pdf_btn = QPushButton("تصدير تقرير الفروع إلى PDF")
        export_branch_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:pressed {
                background-color: #d35400;
            }
        """)
        export_branch_pdf_btn.clicked.connect(self.export_branch_report_to_pdf)
        
        actions_layout.addWidget(export_pdf_btn)
        actions_layout.addStretch()
        
        layout.addWidget(actions_frame)
        
        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        return tab
    
    def create_branch_tab(self):
        """Create the branch reports tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Branch report generation section
        branch_actions_frame = QGroupBox("تقارير الفروع")
        branch_actions_frame.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        branch_actions_layout = QVBoxLayout(branch_actions_frame)
        
        # Branch selection section
        branch_selection_layout = QHBoxLayout()
        branch_label = QLabel("اختر الفرع:")
        branch_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        
        self.branch_combo = QComboBox()
        self.branch_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                background-color: white;
                min-width: 200px;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #2c3e50;
                margin-right: 10px;
            }
        """)
        
        branch_selection_layout.addWidget(branch_label)
        branch_selection_layout.addWidget(self.branch_combo)
        branch_selection_layout.addStretch()
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Generate branch report button
        branch_report_btn = QPushButton("إنشاء تقرير الأصناف المستخرجة")
        branch_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        branch_report_btn.clicked.connect(self.generate_branch_items_report)
        
        # Export branch report to PDF button
        export_branch_pdf_btn = QPushButton("تصدير تقرير الفروع إلى PDF")
        export_branch_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:pressed {
                background-color: #d35400;
            }
        """)
        export_branch_pdf_btn.clicked.connect(self.export_branch_report_to_pdf)
        
        buttons_layout.addWidget(branch_report_btn)
        buttons_layout.addWidget(export_branch_pdf_btn)
        buttons_layout.addStretch()
        
        branch_actions_layout.addLayout(branch_selection_layout)
        branch_actions_layout.addLayout(buttons_layout)
        
        layout.addWidget(branch_actions_frame)
        
        # Branch report display table
        self.branch_report_frame = QGroupBox("تقرير الأصناف المستخرجة")
        self.branch_report_frame.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        branch_report_layout = QVBoxLayout(self.branch_report_frame)
        
        self.branch_table = QTableWidget()
        self.branch_table.setColumnCount(7)
        self.branch_table.setHorizontalHeaderLabels([
            "رقم الفاتورة", "اسم الصنف", "الوحدة", "الكمية المستخرجة", "تاريخ الاستخراج", "المورد", "ملاحظات"
        ])
        
        # Style the branch table
        self.branch_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                gridline-color: #ecf0f1;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        # Configure branch table
        branch_header = self.branch_table.horizontalHeader()
        branch_header.setSectionResizeMode(QHeaderView.Stretch)
        self.branch_table.setAlternatingRowColors(True)
        self.branch_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Set dynamic height based on content
        self.branch_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        self.branch_table.verticalHeader().setDefaultSectionSize(35)  # Row height
        self.branch_table.setMaximumHeight(600)  # Maximum height to prevent excessive growth
        
        branch_report_layout.addWidget(self.branch_table)
        layout.addWidget(self.branch_report_frame)
        
        # Initially hide the branch report frame
        self.branch_report_frame.hide()
        
        # Load branches into combo box
        self.load_branches_combo()
        
        return tab
    
    def adjust_table_height(self):
        """Dynamically adjust table height based on number of rows"""
        if hasattr(self, 'invoices_table'):
            row_count = self.invoices_table.rowCount()
            if row_count == 0:
                # Minimum height when no data
                self.invoices_table.setMinimumHeight(150)
            else:
                # Calculate height: header + rows + some padding
                header_height = self.invoices_table.horizontalHeader().height()
                row_height = self.invoices_table.verticalHeader().defaultSectionSize()
                total_height = header_height + (row_count * row_height) + 20  # 20px padding
                
                # Set minimum height but respect maximum
                min_height = min(max(total_height, 200), 600)
                self.invoices_table.setMinimumHeight(min_height)
    
    def adjust_branch_table_height(self):
        """Dynamically adjust branch table height based on number of rows"""
        if hasattr(self, 'branch_table'):
            row_count = self.branch_table.rowCount()
            if row_count == 0:
                # Minimum height when no data
                self.branch_table.setMinimumHeight(150)
            else:
                # Calculate height: header + rows + some padding
                header_height = self.branch_table.horizontalHeader().height()
                row_height = self.branch_table.verticalHeader().defaultSectionSize()
                total_height = header_height + (row_count * row_height) + 20  # 20px padding
                
                # Set minimum height but respect maximum
                min_height = min(max(total_height, 200), 600)
                self.branch_table.setMinimumHeight(min_height)
        
    def load_suppliers(self):
        """Load all suppliers from the new suppliers table"""
        try:
            supplier_names = Supplier.get_supplier_names()
            
            self.supplier_combo.clear()
            self.supplier_combo.addItem("-- اختر المورد --")
            
            for supplier_name in supplier_names:
                if supplier_name:  # Check if supplier name is not None
                    self.supplier_combo.addItem(supplier_name)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"فشل في تحميل الموردين: {e}")
    
    def on_supplier_changed(self, supplier_name):
        """Handle supplier selection change"""
        if supplier_name == "-- اختر المورد --" or not supplier_name:
            self.clear_table()
            self.update_summary([], 0, 0, 0)
            return
            
        self.load_supplier_invoices(supplier_name)
    
    def load_supplier_invoices(self, supplier_name, from_date=None, to_date=None):
        """Load invoices for the selected supplier with optional date filtering"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Build query with optional date filtering
            base_query = """
                SELECT invoice_number, supplier_name, total_amount, payment_status, 
                       paid_amount, issue_date
                FROM invoices 
                WHERE supplier_name = ?
            """
            
            params = [supplier_name]
            
            if from_date and to_date:
                base_query += " AND issue_date BETWEEN ? AND ?"
                params.extend([from_date, to_date])
            
            base_query += " ORDER BY issue_date DESC"
            
            cursor.execute(base_query, params)
            invoices = cursor.fetchall()
            
            # Store current invoices for export
            self.current_invoices = invoices
            
            # Populate the table
            self.populate_table(invoices)
            
            # Calculate summary
            total_invoices = len(invoices)
            total_amount = sum(invoice[2] for invoice in invoices)
            paid_amount = sum(invoice[4] for invoice in invoices)
            remaining_amount = total_amount - paid_amount
            
            self.update_summary(invoices, total_amount, paid_amount, remaining_amount)
            self.adjust_table_height()  # Adjust height after loading invoices
            
            conn.close()
            
        except pyodbc.Error as e:
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"فشل في تحميل فواتير المورد: {e}")
    
    def populate_table(self, invoices):
        """Populate the invoices table with data"""
        self.invoices_table.setRowCount(len(invoices))
        
        for row, invoice in enumerate(invoices):
            # Invoice number
            self.invoices_table.setItem(row, 0, QTableWidgetItem(str(invoice[0])))
            
            # Supplier name
            self.invoices_table.setItem(row, 1, QTableWidgetItem(str(invoice[1])))
            
            # Total amount
            self.invoices_table.setItem(row, 2, QTableWidgetItem(f"{invoice[2]:.2f}"))
            
            # Payment status (translate to Arabic)
            payment_status = str(invoice[3])
            if payment_status == "PAID" or payment_status == "Paid":
                payment_status = "مدفوع"
            elif payment_status == "PARTIALLY_PAID" or payment_status == "Partially Paid":
                payment_status = "مدفوع جزئيا"
            elif payment_status == "DELAYED" or payment_status == "Delayed":
                payment_status = "متأخر"
            
            status_item = QTableWidgetItem(payment_status)
            if payment_status == "مدفوع":
                status_item.setBackground(Qt.green)
            elif payment_status == "متأخر":
                status_item.setBackground(Qt.red)
            else:
                status_item.setBackground(Qt.yellow)
            self.invoices_table.setItem(row, 3, status_item)
            
            # Paid amount
            self.invoices_table.setItem(row, 4, QTableWidgetItem(f"{invoice[4]:.2f}"))
            
            # Issue date
            date_str = invoice[5].strftime("%Y-%m-%d") if invoice[5] else ""
            self.invoices_table.setItem(row, 5, QTableWidgetItem(date_str))
    
    def clear_table(self):
        """Clear the invoices table"""
        self.invoices_table.setRowCount(0)
        self.adjust_table_height()  # Adjust height after clearing table
    
    def update_summary(self, invoices, total_amount, paid_amount, remaining_amount):
        """Update the summary labels"""
        self.total_invoices_label.setText(f"إجمالي الفواتير: {len(invoices)}")
        self.total_amount_label.setText(f"إجمالي المبلغ: {total_amount:.2f}")
        self.paid_amount_label.setText(f"المبلغ المدفوع: {paid_amount:.2f}")
        self.remaining_amount_label.setText(f"المبلغ المتبقي: {remaining_amount:.2f}")
    
    def apply_date_filter(self):
        """Apply date filtering to the current supplier's invoices"""
        current_supplier = self.supplier_combo.currentText()
        if current_supplier == "-- اختر المورد --" or not current_supplier:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار مورد أولاً")
            return
        
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        
        if self.from_date.date() > self.to_date.date():
            QMessageBox.warning(self, "تحذير", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
        
        self.load_supplier_invoices(current_supplier, from_date, to_date)
        self.adjust_table_height()  # Adjust height after filtering
    
    def clear_date_filter(self):
        """Clear date filtering and reload all invoices for current supplier"""
        current_supplier = self.supplier_combo.currentText()
        if current_supplier == "-- اختر المورد --" or not current_supplier:
            return
        
        self.load_supplier_invoices(current_supplier)
        self.adjust_table_height()  # Adjust height after clearing filter
    
    def export_to_pdf(self):
        """Export current invoices to PDF"""
        if not hasattr(self, 'current_invoices') or not self.current_invoices:
            QMessageBox.warning(self, "تحذير", "لا توجد فواتير للتصدير")
            return
        
        # Get file path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ تقرير الفواتير", "invoices_report.pdf", "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        try:
            self.create_invoices_pdf(file_path, self.current_invoices)
            QMessageBox.information(self, "نجح", f"تم تصدير التقرير بنجاح إلى:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تصدير التقرير: {e}")
    
    def create_invoices_pdf(self, file_path, invoices):
        """Create PDF report for invoices"""
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Get appropriate font name
        font_name = get_font_name()
        
        # Create custom styles with Arabic font and RTL support
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            fontName=font_name,
            wordWrap='RTL'  # Right-to-left text direction
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            fontName=font_name,
            alignment=2,  # Right alignment for Arabic text
            wordWrap='RTL'  # Right-to-left text direction
        )
        
        current_supplier = self.supplier_combo.currentText()
        title = Paragraph(format_arabic_text(f"تقرير فواتير المورد: {current_supplier}"), title_style)
        story.append(title)
        
        # Date range if filtering is applied
        if hasattr(self, 'from_date') and hasattr(self, 'to_date'):
            date_range = f"من {self.from_date.date().toString('yyyy-MM-dd')} إلى {self.to_date.date().toString('yyyy-MM-dd')}"
            date_para = Paragraph(format_arabic_text(date_range), normal_style)
            story.append(date_para)
            story.append(Spacer(1, 12))
        
        # Create table data
        data = [[format_arabic_text('رقم الفاتورة'), format_arabic_text('المورد'), format_arabic_text('المبلغ الإجمالي'), 
                format_arabic_text('حالة الدفع'), format_arabic_text('المبلغ المدفوع'), format_arabic_text('تاريخ الإصدار')]]
        
        for invoice in invoices:
            date_str = invoice[5].strftime("%Y-%m-%d") if invoice[5] else ""
            # Translate payment status to Arabic
            payment_status = str(invoice[3])
            if payment_status == "PAID" or payment_status == "Paid":
                payment_status = "مدفوع"
            elif payment_status == "PARTIALLY_PAID" or payment_status == "Partially Paid":
                payment_status = "مدفوع جزئيا"
            elif payment_status == "DELAYED" or payment_status == "Delayed":
                payment_status = "متأخر"
            
            data.append([
                str(invoice[0]),
                format_arabic_text(str(invoice[1])),
                f"{invoice[2]:.2f} ج.م",
                format_arabic_text(payment_status),
                f"{invoice[4]:.2f} ج.م",
                date_str
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),  # Right alignment for Arabic text
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical middle alignment
            ('FONTNAME', (0, 0), (-1, 0), font_name),  # Use dynamic font for headers
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), font_name),  # Use dynamic font for data
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 12))
        
        # Summary
        total_amount = sum(invoice[2] for invoice in invoices)
        paid_amount = sum(invoice[4] for invoice in invoices)
        remaining_amount = total_amount - paid_amount
        
        summary_data = [
            [format_arabic_text('إجمالي الفواتير'), str(len(invoices))],
            [format_arabic_text('إجمالي المبلغ'), f"{total_amount:.2f} ج.م"],
            [format_arabic_text('المبلغ المدفوع'), f"{paid_amount:.2f} ج.م"],
            [format_arabic_text('المبلغ المتبقي'), f"{remaining_amount:.2f} ج.م"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),  # Use dynamic font for summary
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        
        # Build PDF
        doc.build(story)
    
    def generate_branch_report(self):
        """Generate branch report (legacy method for compatibility)"""
        self.generate_branch_report_inline()
    
    def show_branch_report_dialog(self, branch_data):
        """Show branch report in a dialog"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem
        
        dialog = QDialog(self)
        dialog.setWindowTitle("تقرير الفروع")
        dialog.setGeometry(200, 200, 800, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Create table
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "اسم الفرع", "كود الفرع", "مدير الفرع", "إجمالي الاستخراجات", "إجمالي الكمية", "عدد الأصناف المختلفة"
        ])
        
        # Populate table
        table.setRowCount(len(branch_data))
        for row, data in enumerate(branch_data):
            table.setItem(row, 0, QTableWidgetItem(str(data[0]) if data[0] else ""))
            table.setItem(row, 1, QTableWidgetItem(str(data[4]) if data[4] else "غير محدد"))
            table.setItem(row, 2, QTableWidgetItem(str(data[5]) if data[5] else "غير محدد"))
            table.setItem(row, 3, QTableWidgetItem(str(data[1])))
            table.setItem(row, 4, QTableWidgetItem(str(data[2])))
            table.setItem(row, 5, QTableWidgetItem(str(data[3])))
        
        # Style table
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        
        layout.addWidget(table)
        dialog.exec()
    
    def export_branch_report_to_pdf(self):
        """Export branch report to PDF"""
        if not hasattr(self, 'current_branch_data') or not self.current_branch_data:
            # Generate branch data if not available
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COALESCE(b.branch_name, e.branch_name) as branch_name, 
                           COUNT(e.id) as total_extractions,
                           SUM(e.quantity_extracted) as total_quantity,
                           COUNT(DISTINCT i.item_name) as unique_items,
                           b.branch_code,
                           b.manager_name
                    FROM extractions e
                    JOIN items i ON e.item_id = i.id
                    LEFT JOIN branches b ON e.branch_name = b.branch_name AND b.is_active = 1
                    GROUP BY COALESCE(b.branch_name, e.branch_name), b.branch_code, b.manager_name
                    ORDER BY total_quantity DESC
                """)
                
                self.current_branch_data = cursor.fetchall()
                conn.close()
                
            except pyodbc.Error as e:
                QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"فشل في تحميل بيانات الفروع: {e}")
                return
        
        if not self.current_branch_data:
            QMessageBox.warning(self, "تحذير", "لا توجد بيانات فروع للتصدير")
            return
        
        # Get file path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ تقرير الفروع", "branch_report.pdf", "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        try:
            self.create_branch_report_pdf(file_path, self.current_branch_data)
            QMessageBox.information(self, "نجح", f"تم تصدير تقرير الفروع بنجاح إلى:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تصدير تقرير الفروع: {e}")
    
    def load_branches_combo(self):
        """Load branches into the combo box"""
        try:
            branches = Branch.get_all_branches()
            
            self.branch_combo.clear()
            self.branch_combo.addItem("-- اختر الفرع --", None)
            
            for branch in branches:
                if branch['branch_name']:  # Check if branch name is not None
                    self.branch_combo.addItem(branch['branch_name'], branch['id'])
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"فشل في تحميل الفروع: {e}")
    
    def generate_branch_items_report(self):
        """Generate branch items extraction report"""
        selected_branch_id = self.branch_combo.currentData()
        selected_branch_name = self.branch_combo.currentText()
        
        if selected_branch_id is None or selected_branch_name == "-- اختر الفرع --":
            QMessageBox.warning(self, "تحذير", "يرجى اختيار فرع أولاً")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get extraction data for the selected branch using branch_id
            cursor.execute("""
                SELECT i.invoice_number, i.item_name, 'قطعة' as unit, e.quantity_extracted, 
                       e.date_extracted, i.supplier_name, 'لا توجد ملاحظات' as notes
                FROM extractions e
                JOIN items i ON e.item_id = i.id
                WHERE e.branch_id = ?
                ORDER BY e.date_extracted DESC
            """, [selected_branch_id])
            
            extraction_data = cursor.fetchall()
            conn.close()
            
            if not extraction_data:
                # Clear table and show empty state
                self.branch_table.setRowCount(0)
                self.branch_report_frame.show()
                self.adjust_branch_table_height()
                QMessageBox.information(self, "معلومات", f"لا توجد بيانات استخراج للفرع: {selected_branch_name}")
                return
            
            # Store extraction data for export
            self.current_extraction_data = extraction_data
            
            # Clear existing data
            self.branch_table.setRowCount(0)
            
            # Populate the branch table
            self.branch_table.setRowCount(len(extraction_data))
            
            for row, data in enumerate(extraction_data):
                self.branch_table.setItem(row, 0, QTableWidgetItem(str(data[0]) if data[0] else ""))
                self.branch_table.setItem(row, 1, QTableWidgetItem(str(data[1]) if data[1] else ""))
                self.branch_table.setItem(row, 2, QTableWidgetItem(str(data[2]) if data[2] else ""))
                self.branch_table.setItem(row, 3, QTableWidgetItem(str(data[3])))
                
                # Format date
                date_str = data[4].strftime("%Y-%m-%d") if data[4] else ""
                self.branch_table.setItem(row, 4, QTableWidgetItem(date_str))
                
                self.branch_table.setItem(row, 5, QTableWidgetItem(str(data[5]) if data[5] else ""))
                self.branch_table.setItem(row, 6, QTableWidgetItem(str(data[6]) if data[6] else ""))
            
            # Show the branch report frame
            self.branch_report_frame.show()
            
            # Adjust branch table height
            self.adjust_branch_table_height()
            
        except pyodbc.Error as e:
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"فشل في تحميل تقرير الفرع: {e}")
    
    def create_branch_report_pdf(self, file_path, branch_data):
        """Create PDF report for branches"""
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Get appropriate font name
        font_name = get_font_name()
        
        # Create custom styles with Arabic font and RTL support
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            fontName=font_name,
            wordWrap='RTL'  # Right-to-left text direction
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            fontName=font_name,
            alignment=2,  # Right alignment for Arabic text
            wordWrap='RTL'  # Right-to-left text direction
        )
        
        title = Paragraph(format_arabic_text("تقرير الفروع"), title_style)
        story.append(title)
        
        # Generation date
        date_para = Paragraph(format_arabic_text(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), normal_style)
        story.append(date_para)
        story.append(Spacer(1, 12))
        
        # Create table data with new branch information
        data = [[format_arabic_text('اسم الفرع'), format_arabic_text('كود الفرع'), format_arabic_text('مدير الفرع'), 
                format_arabic_text('إجمالي الاستخراجات'), format_arabic_text('إجمالي الكمية'), format_arabic_text('عدد الأصناف المختلفة')]]
        
        for branch in branch_data:
            data.append([
                format_arabic_text(str(branch[0])) if branch[0] else "",
                format_arabic_text(str(branch[4])) if branch[4] else format_arabic_text("غير محدد"),
                format_arabic_text(str(branch[5])) if branch[5] else format_arabic_text("غير محدد"),
                str(branch[1]),
                str(branch[2]),
                str(branch[3])
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),  # Use dynamic font for headers
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), font_name),  # Use dynamic font for data
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 12))
        
        # Summary
        total_extractions = sum(branch[1] for branch in branch_data)
        total_quantity = sum(branch[2] for branch in branch_data)
        total_branches = len(branch_data)
        
        summary_data = [
            [format_arabic_text('إجمالي الفروع'), str(total_branches)],
            [format_arabic_text('إجمالي الاستخراجات'), str(total_extractions)],
            [format_arabic_text('إجمالي الكمية المستخرجة'), str(total_quantity)]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),  # Use dynamic font for summary
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        
        # Build PDF
        doc.build(story)