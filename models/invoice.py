import sqlite3
import datetime
from database import create_connection

class Invoice:
    PAYMENT_STATUS = {
        'PAID': 'Paid',
        'PARTIALLY_PAID': 'Partially Paid',
        'DELAYED': 'Delayed'
    }
    
    @staticmethod
    def add_invoice(invoice_number, supplier_name, total_amount, payment_status, paid_amount=0, due_date=None, notes=None):
        """Add a new invoice to the database"""
        conn = create_connection()
        if conn is None:
            return None
        
        try:
            cursor = conn.cursor()
            issue_date = datetime.datetime.now().strftime('%Y-%m-%d')
            
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
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_all_invoices():
        """Get all invoices from the database"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices ORDER BY issue_date DESC")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_invoices_by_supplier(supplier_name):
        """Get all invoices for a specific supplier"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE supplier_name = ? ORDER BY issue_date DESC", (supplier_name,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def update_payment_status(invoice_id, payment_status, paid_amount=None):
        """Update the payment status of an invoice"""
        conn = create_connection()
        if conn is None:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Validate payment status
            if payment_status not in Invoice.PAYMENT_STATUS.values():
                return False
            
            if paid_amount is not None:
                sql = "UPDATE invoices SET payment_status = ?, paid_amount = ? WHERE id = ?"
                cursor.execute(sql, (payment_status, paid_amount, invoice_id))
            else:
                sql = "UPDATE invoices SET payment_status = ? WHERE id = ?"
                cursor.execute(sql, (payment_status, invoice_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_all_suppliers():
        """Get a list of all suppliers with invoices"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT supplier_name FROM invoices ORDER BY supplier_name")
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if conn:
                conn.close()