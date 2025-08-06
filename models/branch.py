import pyodbc
from datetime import datetime
from database import get_db_connection

class Branch:
    @staticmethod
    def add_branch(branch_name, branch_code=None, manager_name=None, phone=None, 
                  address=None, opening_date=None, notes=None):
        """Add a new branch to the database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = '''INSERT INTO branches
                    (branch_name, branch_code, manager_name, phone, address, opening_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            
            cursor.execute(sql, (branch_name, branch_code, manager_name, phone, 
                                address, opening_date, notes))
            conn.commit()
            return cursor.lastrowid
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def get_all_branches():
        """Get all active branches from the database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM branches WHERE is_active = 1 ORDER BY branch_name")
            branches = []
            for row in cursor.fetchall():
                branches.append({
                    'id': row[0],
                    'branch_name': row[1],
                    'branch_code': row[2],
                    'manager_name': row[3],
                    'phone': row[4],
                    'address': row[5],
                    'opening_date': row[6],
                    'notes': row[7],
                    'date_added': row[8],
                    'is_active': row[9]
                })
            return branches
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def get_branch_by_id(branch_id):
        """Get a branch by ID"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM branches WHERE id = ?", (branch_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'branch_name': row[1],
                    'branch_code': row[2],
                    'manager_name': row[3],
                    'phone': row[4],
                    'address': row[5],
                    'opening_date': row[6],
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
    def update_branch(branch_id, branch_name, branch_code=None, manager_name=None, 
                     phone=None, address=None, opening_date=None, notes=None):
        """Update an existing branch"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = '''UPDATE branches SET 
                    branch_name = ?, branch_code = ?, manager_name = ?, phone = ?,
                    address = ?, opening_date = ?, notes = ?
                    WHERE id = ?'''
            
            cursor.execute(sql, (branch_name, branch_code, manager_name, phone,
                                address, opening_date, notes, branch_id))
            conn.commit()
            return cursor.rowcount > 0
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def delete_branch(branch_id):
        """Soft delete a branch (set is_active to 0)"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("UPDATE branches SET is_active = 0 WHERE id = ?", (branch_id,))
            conn.commit()
            return cursor.rowcount > 0
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def get_branch_names():
        """Get list of branch names for dropdowns"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT branch_name FROM branches WHERE is_active = 1 ORDER BY branch_name")
            return [row[0] for row in cursor.fetchall()]
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()