import pyodbc
from datetime import datetime
from database import get_db_connection
from models.invoice import Invoice

class Item:
    def __init__(self, id=None, item_name="", quantity=0, price_per_unit=0.0, 
                 invoice_number="", supplier_name="", date_added=None):
        self.id = id
        self.item_name = item_name
        self.quantity = quantity
        self.price_per_unit = price_per_unit
        self.invoice_number = invoice_number
        self.supplier_name = supplier_name
        self.date_added = date_added if date_added else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def add_item(item_name, quantity, price_per_unit, invoice_number, supplier_name=None, payment_status=None):
        """Add a new item to the database and create/update invoice"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")
            date_added = datetime.now().strftime('%Y-%m-%d')
            
            # Insert item
            sql = '''INSERT INTO items
                    (item_name, quantity, price_per_unit, invoice_number, supplier_name, date_added)
                    VALUES (?, ?, ?, ?, ?, ?); SELECT SCOPE_IDENTITY() AS item_id'''
            
            cursor.execute(sql, (item_name, quantity, price_per_unit, invoice_number, supplier_name, date_added))
            item_id = cursor.fetchone()[0]
            
            # Check if invoice exists
            cursor.execute("SELECT id, total_amount FROM invoices WHERE invoice_number = ?", (invoice_number,))
            invoice = cursor.fetchone()
            
            total_amount = quantity * price_per_unit
            
            # Set default payment status if not provided
            if payment_status is None:
                payment_status = Invoice.PAYMENT_STATUS['DELAYED']
            
            if invoice:
                # Update existing invoice
                invoice_id, current_total = invoice
                new_total = current_total + total_amount
                cursor.execute("UPDATE invoices SET total_amount = ? WHERE id = ?", (new_total, invoice_id))
            else:
                # Create new invoice within the same transaction
                # Instead of calling Invoice.add_invoice which opens a new connection,
                # we'll insert the invoice directly here
                issue_date = datetime.now().strftime('%Y-%m-%d')
                
                # Validate payment status
                if payment_status not in Invoice.PAYMENT_STATUS.values():
                    payment_status = Invoice.PAYMENT_STATUS['DELAYED']
                
                # Insert invoice
                invoice_sql = '''INSERT INTO invoices
                        (invoice_number, supplier_name, total_amount, payment_status, paid_amount, issue_date)
                        VALUES (?, ?, ?, ?, ?, ?)'''
                
                cursor.execute(invoice_sql, (
                    invoice_number, 
                    supplier_name or "Unknown", 
                    total_amount, 
                    payment_status, 
                    0, # Default paid_amount
                    issue_date
                ))
                
                invoice_id = cursor.lastrowid
            
            conn.commit()
            return item_id
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_all_items():
        """Get all items from the database"""
        items = []
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM items")
            rows = cur.fetchall()
            
            for row in rows:
                item = Item(
                    id=row[0],
                    item_name=row[1],
                    quantity=int(row[2]) if row[2] is not None and str(row[2]).isdigit() else 0,
                    price_per_unit=float(row[3]) if row[3] is not None else 0.0,
                    invoice_number=row[4],
                    supplier_name=row[5],
                    date_added=row[6]
                )
                items.append(item)
        except pyodbc.Error as e:
            print(f"Database error: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        
        return items

    @staticmethod
    def get_item_by_id(item_id):
        """Get an item by its ID"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM items WHERE id = ?", (item_id,))
            row = cur.fetchone()
            
            if row:
                item = Item(
                    id=row[0],
                    item_name=row[1],
                    quantity=int(row[2]) if row[2] is not None and str(row[2]).isdigit() else 0,
                    price_per_unit=float(row[3]) if row[3] is not None else 0.0,
                    invoice_number=row[4],
                    supplier_name=row[5],
                    date_added=row[6]
                )
                return item
        except pyodbc.Error as e:
            print(f"Database error: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        
        return None

    @staticmethod
    def update_quantity(item_id, new_quantity):
        """Update the quantity of an item"""
        try:
            conn = get_db_connection()
            sql = '''UPDATE items SET quantity = ? WHERE id = ?'''
            cur = conn.cursor()
            cur.execute(sql, (new_quantity, item_id))
            conn.commit()
            return cur.rowcount > 0
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def search_items(search_term):
        """Search for items by name"""
        items = []
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM items WHERE item_name LIKE ?", (f'%{search_term}%',))
            rows = cur.fetchall()
            
            for row in rows:
                item = Item(
                    id=row[0],
                    item_name=row[1],
                    quantity=int(row[2]) if row[2] is not None and str(row[2]).isdigit() else 0,
                    price_per_unit=float(row[3]) if row[3] is not None else 0.0,
                    invoice_number=row[4],
                    supplier_name=row[5],
                    date_added=row[6]
                )
                items.append(item)
        except pyodbc.Error as e:
            print(f"Database error: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        
        return items

    @staticmethod
    def filter_by_invoice(invoice_number):
        """Filter items by invoice number"""
        items = []
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM items WHERE invoice_number LIKE ?", (f'%{invoice_number}%',))
            rows = cur.fetchall()
            
            for row in rows:
                item = Item(
                    id=row[0],
                    item_name=row[1],
                    quantity=int(row[2]) if row[2] is not None and str(row[2]).isdigit() else 0,
                    price_per_unit=float(row[3]) if row[3] is not None else 0.0,
                    invoice_number=row[4],
                    supplier_name=row[5],
                    date_added=row[6]
                )
                items.append(item)
        except pyodbc.Error as e:
            print(f"Database error: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        
        return items