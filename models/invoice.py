import pyodbc
from datetime import datetime
from database import get_db_connection

class Invoice:
    PAYMENT_STATUS = {
        'PAID': 'Paid',
        'PARTIALLY_PAID': 'Partially Paid',
        'DELAYED': 'Delayed'
    }
    
    @staticmethod
    def add_invoice(invoice_number, supplier_name, total_amount, payment_status, paid_amount=0, due_date=None, notes=None):
        """Add a new invoice to the database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            issue_date = datetime.now().strftime('%Y-%m-%d')
            
            # Validate payment status
            if payment_status not in Invoice.PAYMENT_STATUS.values():
                payment_status = Invoice.PAYMENT_STATUS['DELAYED']
            
            # Insert invoice
            sql = '''INSERT INTO invoices
                    (invoice_number, supplier_name, total_amount, payment_status, paid_amount, issue_date, due_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
            
            cursor.execute(sql, (invoice_number, supplier_name, total_amount, payment_status, 
                                paid_amount, issue_date, due_date, notes))
            conn.commit()
            return cursor.lastrowid
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def get_all_invoices():
        """Get all invoices from the database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices ORDER BY issue_date DESC")
            invoices = []
            for row in cursor.fetchall():
                invoices.append({
                    'id': row[0],
                    'invoice_number': row[1],
                    'supplier_name': row[2],
                    'total_amount': row[3],
                    'payment_status': row[4],
                    'paid_amount': row[5],
                    'issue_date': row[6],
                    'due_date': row[7],
                    'notes': row[8]
                })
            return invoices
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def get_invoice_by_number(invoice_number):
        """Get an invoice by its invoice number"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM invoices WHERE invoice_number = ?",
                (invoice_number,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'invoice_number': row[1],
                    'supplier_name': row[2],
                    'total_amount': row[3],
                    'payment_status': row[4],
                    'paid_amount': row[5],
                    'issue_date': row[6],
                    'due_date': row[7],
                    'notes': row[8]
                }
            return None
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def get_items_by_invoice(invoice_number):
        """Get all items for a specific invoice"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM items WHERE invoice_number = ?",
                (invoice_number,)
            )
            items = []
            for row in cursor.fetchall():
                items.append({
                    'id': row[0],
                    'item_name': row[1],
                    'quantity': row[2],
                    'price_per_unit': row[3],
                    'invoice_number': row[4],
                    'supplier_name': row[5],
                    'date_added': row[6]
                })
            return items
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def get_invoices_by_supplier(supplier_name):
        """Get all invoices for a specific supplier"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE supplier_name = ? ORDER BY issue_date DESC", (supplier_name,))
            invoices = []
            for row in cursor.fetchall():
                invoices.append({
                    'id': row[0],
                    'invoice_number': row[1],
                    'supplier_name': row[2],
                    'total_amount': row[3],
                    'payment_status': row[4],
                    'paid_amount': row[5],
                    'issue_date': row[6],
                    'due_date': row[7],
                    'notes': row[8]
                })
            return invoices
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def update_payment_status(invoice_id, payment_status, paid_amount=None):
        """Update the payment status of an invoice"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Validate payment status
            if payment_status not in Invoice.PAYMENT_STATUS.values():
                return False
            
            if paid_amount is not None:
                # Get current invoice data to check existing paid amount and total amount
                cursor.execute("SELECT paid_amount, total_amount FROM invoices WHERE id = ?", (invoice_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                current_paid, total_amount = row
                
                # If new paid amount is less than current, keep the current amount
                # This prevents decreasing the already paid amount
                if paid_amount < current_paid:
                    paid_amount = current_paid
                
                # Ensure paid amount doesn't exceed total amount
                if paid_amount > total_amount:
                    paid_amount = total_amount
                
                sql = "UPDATE invoices SET payment_status = ?, paid_amount = ? WHERE id = ?"
                cursor.execute(sql, (payment_status, paid_amount, invoice_id))
            else:
                sql = "UPDATE invoices SET payment_status = ? WHERE id = ?"
                cursor.execute(sql, (payment_status, invoice_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def get_all_suppliers():
        """Get a list of all suppliers with invoices"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT supplier_name FROM invoices ORDER BY supplier_name")
            return [row[0] for row in cursor.fetchall()]
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()