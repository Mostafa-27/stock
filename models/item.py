import pyodbc
from datetime import datetime
from database import get_db_connection
from models.invoice import Invoice

class Item:
    def __init__(self, id=None, item_name="", quantity=0, quantity_type="unit", price_per_unit=0.0, 
                 invoice_number="", supplier_name="", date_added=None):
        self.id = id
        self.item_name = item_name
        self.quantity = quantity
        self.quantity_type = quantity_type
        self.price_per_unit = price_per_unit
        self.invoice_number = invoice_number
        self.supplier_name = supplier_name
        self.date_added = date_added if date_added else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def add_item(item_name, quantity, quantity_type, price_per_unit, invoice_number, supplier_name=None, payment_status=None):
        """Add a new item to the database and create/update invoice"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            date_added = datetime.now().strftime('%Y-%m-%d')
            
            # Insert item
            sql = '''INSERT INTO items
                    (item_name, quantity, quantity_type, price_per_unit, invoice_number, supplier_name, date_added)
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            
            print(f"Executing SQL: {sql}")
            cursor.execute(sql, (item_name, quantity, quantity_type, price_per_unit, invoice_number, supplier_name, date_added))
            
            # Get the last inserted ID
            cursor.execute("SELECT SCOPE_IDENTITY()")
            result = cursor.fetchone()
            if result and result[0] is not None:
                item_id = int(result[0])
                print(f"Inserted item ID: {item_id}")
            else:
                # Fallback: get the max ID from items table
                cursor.execute("SELECT MAX(id) FROM items WHERE item_name = ? AND invoice_number = ?", 
                             (item_name, invoice_number))
                result = cursor.fetchone()
                item_id = int(result[0]) if result and result[0] is not None else 1
                print(f"Fallback item ID: {item_id}")

            
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
                
                # Get the last inserted invoice ID
                cursor.execute("SELECT SCOPE_IDENTITY()")
                result = cursor.fetchone()
                if result and result[0] is not None:
                    invoice_id = int(result[0])
                else:
                    # Fallback: get the max ID from invoices table
                    cursor.execute("SELECT MAX(id) FROM invoices WHERE invoice_number = ?", (invoice_number,))
                    result = cursor.fetchone()
                    invoice_id = int(result[0]) if result and result[0] is not None else 1
            
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
                # Handle both old and new table structure
                if len(row) >= 8:  # New structure with quantity_type
                    item = Item(
                        id=row[0],
                        item_name=row[1],
                        quantity=int(row[2]) if row[2] is not None and str(row[2]).isdigit() else 0,
                        quantity_type=row[3] if row[3] else "unit",
                        price_per_unit=float(row[4]) if row[4] is not None else 0.0,
                        invoice_number=row[5],
                        supplier_name=row[6],
                        date_added=row[7]
                    )
                else:  # Old structure without quantity_type
                    item = Item(
                        id=row[0],
                        item_name=row[1],
                        quantity=int(row[2]) if row[2] is not None and str(row[2]).isdigit() else 0,
                        quantity_type="unit",
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
                # Handle both old and new table structure
                if len(row) >= 8:  # New structure with quantity_type
                    item = Item(
                        id=row[0],
                        item_name=row[1],
                        quantity=int(row[2]) if row[2] is not None and str(row[2]).isdigit() else 0,
                        quantity_type=row[3] if row[3] else "unit",
                        price_per_unit=float(row[4]) if row[4] is not None else 0.0,
                        invoice_number=row[5],
                        supplier_name=row[6],
                        date_added=row[7]
                    )
                else:  # Old structure without quantity_type
                    item = Item(
                        id=row[0],
                        item_name=row[1],
                        quantity=int(row[2]) if row[2] is not None and str(row[2]).isdigit() else 0,
                        quantity_type="unit",
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
                # Handle both old and new table structure
                if len(row) >= 8:  # New structure with quantity_type
                    item = Item(
                        id=row[0],
                        item_name=row[1],
                        quantity=int(row[2]) if row[2] is not None and str(row[2]).isdigit() else 0,
                        quantity_type=row[3] if row[3] else "unit",
                        price_per_unit=float(row[4]) if row[4] is not None else 0.0,
                        invoice_number=row[5],
                        supplier_name=row[6],
                        date_added=row[7]
                    )
                else:  # Old structure without quantity_type
                    item = Item(
                        id=row[0],
                        item_name=row[1],
                        quantity=int(row[2]) if row[2] is not None and str(row[2]).isdigit() else 0,
                        quantity_type="unit",
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
                # Handle both old and new table structure
                if len(row) >= 8:  # New structure with quantity_type
                    item = Item(
                        id=row[0],
                        item_name=row[1],
                        quantity=int(row[2]) if row[2] is not None and str(row[2]).isdigit() else 0,
                        quantity_type=row[3] if row[3] else "unit",
                        price_per_unit=float(row[4]) if row[4] is not None else 0.0,
                        invoice_number=row[5],
                        supplier_name=row[6],
                        date_added=row[7]
                    )
                else:  # Old structure without quantity_type
                    item = Item(
                        id=row[0],
                        item_name=row[1],
                        quantity=int(row[2]) if row[2] is not None and str(row[2]).isdigit() else 0,
                        quantity_type="unit",
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