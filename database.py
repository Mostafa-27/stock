import os
import sqlite3
import time
from sqlite3 import Error

DATABASE_FILE = "stock_management.db"

def is_database_locked():
    """Check if the database is locked and try to fix it"""
    # Check if database file exists
    if not os.path.exists(DATABASE_FILE):
        return False
    
    # Try to open and close the database to check if it's locked
    for attempt in range(3):  # Try 3 times
        try:
            conn = sqlite3.connect(DATABASE_FILE, timeout=5)
            conn.execute("PRAGMA busy_timeout = 5000")  # Set busy timeout to 5 seconds
            conn.execute("SELECT 1")  # Simple query to test connection
            conn.close()
            return False  # Database is not locked
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print(f"Database is locked, attempt {attempt+1}/3 to fix...")
                time.sleep(1)  # Wait a bit before retrying
            else:
                print(f"Database error: {e}")
                return False
    
    # If we get here, the database is still locked after retries
    print("Database is locked and could not be fixed automatically.")
    print("Please close any other applications that might be using the database.")
    return True

def create_connection():
    """Create a database connection to the SQLite database"""
    # Check if database is locked and try to fix it
    if is_database_locked():
        return None
    
    conn = None
    try:
        # Set a longer timeout and busy_timeout to handle concurrent access
        conn = sqlite3.connect(DATABASE_FILE, timeout=10)
        conn.execute("PRAGMA busy_timeout = 10000")  # 10 seconds
        return conn
    except Error as e:
        print(f"Database error: {e}")
    
    return conn

def create_tables(conn):
    """Create the necessary tables if they don't exist"""
    # Create items table
    items_table = """CREATE TABLE IF NOT EXISTS items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_name TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        price_per_unit REAL NOT NULL,
                        invoice_number TEXT NOT NULL,
                        supplier_name TEXT,
                        date_added TEXT NOT NULL
                    );"""
    
    # Create extractions table
    extractions_table = """CREATE TABLE IF NOT EXISTS extractions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            item_id INTEGER NOT NULL,
                            branch_name TEXT NOT NULL,
                            quantity_extracted INTEGER NOT NULL,
                            date_extracted TEXT NOT NULL,
                            FOREIGN KEY (item_id) REFERENCES items (id)
                        );"""
    
    # Create invoices table
    invoices_table = """CREATE TABLE IF NOT EXISTS invoices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        invoice_number TEXT NOT NULL UNIQUE,
                        supplier_name TEXT NOT NULL,
                        total_amount REAL NOT NULL,
                        payment_status TEXT NOT NULL,
                        paid_amount REAL DEFAULT 0,
                        issue_date TEXT NOT NULL,
                        due_date TEXT,
                        notes TEXT
                    );"""
    
    # Create users table
    users_table = """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0
                );"""
    
    # Create settings table
    settings_table = """CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        setting_name TEXT NOT NULL UNIQUE,
                        setting_value TEXT,
                        setting_type TEXT
                    );"""
    
    try:
        cursor = conn.cursor()
        cursor.execute(items_table)
        cursor.execute(extractions_table)
        cursor.execute(invoices_table)
        cursor.execute(users_table)
        cursor.execute(settings_table)
        
        # Check if admin user exists, if not create default admin user
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", 
                          ('admin', 'admin', 1))
        
        # Initialize default settings if they don't exist
        default_settings = [
            ('default_printer', '', 'text'),
            ('company_logo', '', 'file_path'),
            ('auto_print', 'true', 'boolean')
        ]
        
        for setting in default_settings:
            cursor.execute("INSERT OR IGNORE INTO settings (setting_name, setting_value, setting_type) VALUES (?, ?, ?)",
                          setting)
        
        conn.commit()
    except Error as e:
        print(e)