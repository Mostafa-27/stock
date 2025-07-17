import sqlite3
from database import create_connection

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
        conn = create_connection()
        if conn is None:
            return (User.DB_ERROR, None)
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, is_admin FROM users WHERE username = ? AND password = ?", 
                (username, password)
            )
            user = cursor.fetchone()
            
            if user:
                # Return user data as a dictionary
                user_data = {
                    'id': user[0],
                    'username': user[1],
                    'is_admin': bool(user[2])
                }
                return (User.LOGIN_SUCCESS, user_data)
            else:
                return (User.INVALID_CREDENTIALS, None)
        except sqlite3.Error as e:
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
        conn = create_connection()
        if conn is None:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (new_password, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
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
        conn = create_connection()
        if conn is None:
            return []
        
        try:
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
        except sqlite3.Error as e:
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
        conn = create_connection()
        if conn is None:
            return (False, "Database connection error")
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                (username, password, 1 if is_admin else 0)
            )
            conn.commit()
            return (True, "")
        except sqlite3.IntegrityError:
            return (False, "Username already exists")
        except sqlite3.Error as e:
            return (False, f"Database error: {e}")
        finally:
            conn.close()