import pyodbc
import hashlib
from database import get_db_connection

class User:
    # User status constants
    LOGIN_SUCCESS = 0
    INVALID_CREDENTIALS = 1
    DB_ERROR = 2
    
    @staticmethod
    def login(username, password):
        """
        Authenticate a user with the given username and password
        Returns: (status_code, user_data or None)
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Check which columns exist in the users table
            cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'users' AND COLUMN_NAME IN ('is_admin', 'role')")
            columns = [row[0] for row in cursor.fetchall()]
            
            if 'is_admin' in columns:
                cursor.execute(
                    "SELECT id, username, is_admin FROM users WHERE username = ? AND password = ?", 
                    (username, password)
                )
                user = cursor.fetchone()
                if user:
                    user_data = {
                        'id': user[0],
                        'username': user[1],
                        'is_admin': user[2]
                    }
            elif 'role' in columns:
                cursor.execute(
                    "SELECT id, username, role FROM users WHERE username = ? AND password = ?", 
                    (username, password)
                )
                user = cursor.fetchone()
                if user:
                    user_data = {
                        'id': user[0],
                        'username': user[1],
                        'is_admin': user[2] == 'admin'  # Convert role to boolean
                    }
            else:
                cursor.execute(
                    "SELECT id, username FROM users WHERE username = ? AND password = ?", 
                    (username, password)
                )
                user = cursor.fetchone()
                if user:
                    user_data = {
                        'id': user[0],
                        'username': user[1],
                        'is_admin': False  # Default to non-admin
                    }
            
            if user:
                return (User.LOGIN_SUCCESS, user_data)
            else:
                return (User.INVALID_CREDENTIALS, None)
        except pyodbc.Error as e:
            print(f"Database error during login: {e}")
            return (User.DB_ERROR, None)
        finally:
            conn.close()
    
    @staticmethod
    def change_password(user_id, new_password):
        """
        Change the password for a user
        Returns: True if successful, False otherwise
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (new_password, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except pyodbc.Error as e:
            print(f"Database error during password change: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_all_users():
        """
        Get all users from the database
        Returns: List of user dictionaries or empty list on error
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, is_admin FROM users")
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'is_admin': bool(row[2])
                })
            return users
        except pyodbc.Error as e:
            print(f"Database error while getting users: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def add_user(username, password, is_admin=False):
        """
        Add a new user to the database
        Returns: (success, error_message)
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check which columns exist in the users table
            cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'users' AND COLUMN_NAME IN ('is_admin', 'role')")
            columns = [row[0] for row in cursor.fetchall()]
            
            if 'is_admin' in columns:
                cursor.execute(
                    "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                    (username, password, 1 if is_admin else 0)
                )
            elif 'role' in columns:
                # Use role column instead, also need to provide required fields
                role = 'admin' if is_admin else 'user'
                cursor.execute(
                    "INSERT INTO users (name, phone, email, username, password, role) VALUES (?, ?, ?, ?, ?, ?)",
                    (username, '000-000-0000', f'{username}@restaurant.com', username, password, role)
                )
            else:
                # Fallback - just username and password
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, password)
                )
            
            conn.commit()
            return (True, "")
        except pyodbc.Error as e:
            if "UNIQUE constraint" in str(e) or "duplicate" in str(e).lower():
                return (False, "Username already exists")
            return (False, f"Database error: {e}")
        finally:
            conn.close()