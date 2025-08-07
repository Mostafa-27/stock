import os
import tempfile
from datetime import datetime
import win32print
import win32con
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtCore import QSize, Qt

from models.settings import Settings

def get_available_printers():
    """
    Get a list of available printers on the system
    Returns: List of printer names
    """
    printers = []
    try:
        for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
            printers.append(printer[2])  # printer name is at index 2
    except Exception as e:
        print(f"Error getting printers: {e}")
    return printers

def get_default_printer():
    """
    Get the system default printer
    Returns: Default printer name or None if not found
    """
    try:
        return win32print.GetDefaultPrinter()
    except Exception as e:
        print(f"Error getting default printer: {e}")
        return None

def print_invoice(invoice_data, items_data):
    """
    Print an invoice with the given data
    Returns: True if successful, False otherwise
    """
    # Get printer settings
    printer_name = Settings.get_setting('default_printer')
    logo_path = Settings.get_setting('company_logo')
    
    # Create a printer object
    printer = QPrinter(QPrinter.HighResolution)
    
    # Set the printer name if configured
    if printer_name:
        printer.setPrinterName(printer_name)
    
    # Create the receipt content
    receipt_content = generate_receipt_content(invoice_data, items_data, logo_path)
    
    # Print the receipt
    try:
        painter = QPainter()
        if painter.begin(printer):
            # Draw the receipt content
            painter.drawPixmap(0, 0, receipt_content)
            painter.end()
            return True
        else:
            QMessageBox.warning(None, "Printing Error", "Could not start printer.")
            return False
    except Exception as e:
        QMessageBox.warning(None, "Printing Error", f"Error printing receipt: {e}")
        return False

def generate_receipt_content(invoice_data, items_data, logo_path=None, is_history=False):
    """
    Generate a QPixmap containing the receipt content
    Returns: QPixmap with the receipt content
    
    Parameters:
    - invoice_data: Dictionary with invoice details
    - items_data: List of dictionaries with item details
    - logo_path: Path to company logo image
    - is_history: Boolean indicating if this is a history report
    """
    # Create a pixmap to draw on
    printer = QPrinter(QPrinter.HighResolution)
    rect = printer.pageRect(QPrinter.Point)
    pixmap = QPixmap(rect.width(), rect.height())
    pixmap.fill(Qt.white)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Set fonts
    title_font = painter.font()
    title_font.setPointSize(16)
    title_font.setBold(True)
    
    header_font = painter.font()
    header_font.setPointSize(12)
    header_font.setBold(True)
    
    normal_font = painter.font()
    normal_font.setPointSize(10)
    
    # Start position
    x, y = 50, 50
    line_height = 20
    
    # Draw logo if available
    if logo_path and os.path.exists(logo_path):
        logo = QPixmap(logo_path)
        if not logo.isNull():
            logo = logo.scaled(QSize(200, 100), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(x, y, logo)
            y += logo.height() + 20
    
    # Draw header
    painter.setFont(title_font)
    if is_history:
        painter.drawText(x, y, "HISTORY OPERATIONS REPORT")
    else:
        painter.drawText(x, y, "INVOICE")
    y += line_height * 2
    
    # Reset to normal font
    painter.setFont(normal_font)
    
    # Draw document details
    painter.drawText(x, y, f"Reference #: {str(invoice_data['invoice_number'])}")
    y += line_height
    painter.drawText(x, y, f"Date: {str(invoice_data['issue_date'])}")
    y += line_height
    
    if is_history:
        painter.drawText(x, y, f"Report Type: {str(invoice_data['supplier_name'])}")
    else:
        painter.drawText(x, y, f"Supplier: {str(invoice_data['supplier_name'])}")
    y += line_height
    
    # Add notes if available
    if 'notes' in invoice_data and invoice_data['notes']:
        painter.drawText(x, y, f"Notes: {str(invoice_data['notes'])}")
        y += line_height
    
    y += line_height
    
    # Draw items header
    painter.setFont(header_font)
    if is_history:
        painter.drawText(x, y, "Item/Operation")
        painter.drawText(x + 250, y, "Quantity")
        painter.drawText(x + 350, y, "Date")
        painter.drawText(x + 450, y, "User/Details")
    else:
        painter.drawText(x, y, "Item")
        painter.drawText(x + 200, y, "Quantity")
        painter.drawText(x + 300, y, "Price")
        painter.drawText(x + 400, y, "Total")
    y += line_height
    
    # Draw separator line
    painter.drawLine(x, y, x + 550, y)
    y += line_height
    
    # Reset to normal font
    painter.setFont(normal_font)
    
    # Draw items
    for item in items_data:
        if is_history:
            # For history report
            painter.drawText(x, y, item['item_name'])
            painter.drawText(x + 250, y, str(item['quantity']))
            painter.drawText(x + 350, y, str(item['date_added']))
            painter.drawText(x + 450, y, str(item['supplier_name']))  # Using supplier_name field for user/details
        else:
            # For regular invoice
            painter.drawText(x, y, str(item['item_name']))
            painter.drawText(x + 200, y, str(item['quantity']))
            # Convert to float to ensure proper formatting
            price_per_unit = float(item['price_per_unit']) if item['price_per_unit'] is not None else 0.0
            quantity = int(item['quantity']) if item['quantity'] is not None else 0
            painter.drawText(x + 300, y, f"${price_per_unit:.2f}")
            total = quantity * price_per_unit
            painter.drawText(x + 400, y, f"${total:.2f}")
        y += line_height
        
        # Check if we need to start a new page (simple pagination)
        if y > rect.height() - 100:
            # Add page number
            painter.drawText(rect.width() - 100, rect.height() - 20, "Page 1")
            # TODO: Implement proper multi-page support if needed
    
    # Draw separator line
    y += line_height / 2
    painter.drawLine(x, y, x + 550, y)
    y += line_height
    
    # Only show financial details for invoices, not history reports
    if not is_history:
        # Draw total
        painter.drawText(x + 300, y, "Total:")
        # Convert to float to ensure proper formatting
        total_amount = float(invoice_data['total_amount']) if invoice_data['total_amount'] is not None else 0.0
        painter.drawText(x + 400, y, f"${total_amount:.2f}")
        y += line_height
        
        # Draw payment status
        painter.drawText(x + 300, y, "Status:")
        painter.drawText(x + 400, y, str(invoice_data['payment_status']))
        
        if invoice_data['payment_status'] == 'Partially Paid':
            y += line_height
            painter.drawText(x + 300, y, "Paid:")
            # Convert to float to ensure proper formatting
            paid_amount = float(invoice_data['paid_amount']) if invoice_data['paid_amount'] is not None else 0.0
            painter.drawText(x + 400, y, f"${paid_amount:.2f}")
            y += line_height
            remaining = total_amount - paid_amount
            painter.drawText(x + 300, y, "Remaining:")
            painter.drawText(x + 400, y, f"${remaining:.2f}")
    
    # Draw footer
    y += line_height * 3
    if is_history:
        painter.drawText(x, y, "End of History Report")
    else:
        painter.drawText(x, y, "Thank you for your business!")
    y += line_height
    painter.drawText(x, y, f"Printed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    painter.end()
    return pixmap

def show_print_dialog(parent, invoice_data, items_data, is_history=False):
    """
    Show a print dialog and print if accepted
    
    Parameters:
    - parent: Parent widget for the dialog
    - invoice_data: Dictionary with invoice details
    - items_data: List of dictionaries with item details
    - is_history: Boolean indicating if this is a history report
    
    Returns: True if printed, False otherwise
    """
    printer = QPrinter(QPrinter.HighResolution)
    dialog = QPrintDialog(printer, parent)
    
    # Set the document name for the print job
    if is_history:
        printer.setDocName("History Operations Report")
    else:
        printer.setDocName(f"Invoice {str(invoice_data['invoice_number'])}")
    
    if dialog.exec() == QPrintDialog.Accepted:
        # Generate receipt content
        logo_path = Settings.get_setting('company_logo')
        receipt_content = generate_receipt_content(invoice_data, items_data, logo_path, is_history)
        
        # Print the receipt
        try:
            painter = QPainter()
            if painter.begin(printer):
                painter.drawPixmap(0, 0, receipt_content)
                painter.end()
                return True
            else:
                QMessageBox.warning(parent, "Printing Error", "Could not start printer.")
                return False
        except Exception as e:
            QMessageBox.warning(parent, "Printing Error", f"Error printing document: {e}")
            return False
    
    return False