import pyodbc
from datetime import datetime
from database import get_db_connection

class Supplier:
    @staticmethod
    def add_supplier(supplier_name, contact_person=None, phone=None, email=None, 
                    address=None, payment_terms=None, notes=None):
        """Add a new supplier to the database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = '''INSERT INTO suppliers
                    (supplier_name, contact_person, phone, email, address, payment_terms, notes)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            
            cursor.execute(sql, (supplier_name, contact_person, phone, email, 
                                address, payment_terms, notes))
            
            # Get the inserted ID
            inserted_id = cursor.fetchone()[0]
            conn.commit()
            return inserted_id
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def get_all_suppliers():
        """Get all active suppliers from the database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers WHERE is_active = 1 ORDER BY supplier_name")
            suppliers = []
            for row in cursor.fetchall():
                suppliers.append({
                    'id': row[0],
                    'supplier_name': row[1],
                    'contact_person': row[2],
                    'phone': row[3],
                    'email': row[4],
                    'address': row[5],
                    'payment_terms': row[6],
                    'notes': row[7],
                    'date_added': row[8],
                    'is_active': row[9]
                })
            return suppliers
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def get_supplier_by_id(supplier_id):
        """Get a supplier by ID"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'supplier_name': row[1],
                    'contact_person': row[2],
                    'phone': row[3],
                    'email': row[4],
                    'address': row[5],
                    'payment_terms': row[6],
                    'notes': row[7],
                    'date_added': row[8],
                    'is_active': row[9]
                }
            return None
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def update_supplier(supplier_id, supplier_name, contact_person=None, phone=None, 
                       email=None, address=None, payment_terms=None, notes=None):
        """Update an existing supplier"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = '''UPDATE suppliers SET 
                    supplier_name = ?, contact_person = ?, phone = ?, email = ?,
                    address = ?, payment_terms = ?, notes = ?
                    WHERE id = ?'''
            
            cursor.execute(sql, (supplier_name, contact_person, phone, email,
                                address, payment_terms, notes, supplier_id))
            conn.commit()
            return cursor.rowcount > 0
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def delete_supplier(supplier_id):
        """Soft delete a supplier (set is_active to 0)"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("UPDATE suppliers SET is_active = 0 WHERE id = ?", (supplier_id,))
            conn.commit()
            return cursor.rowcount > 0
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def get_supplier_names():
        """Get list of supplier names for dropdowns"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT supplier_name FROM suppliers WHERE is_active = 1 ORDER BY supplier_name")
            return [row[0] for row in cursor.fetchall()]
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()