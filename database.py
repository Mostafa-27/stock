import os
import pyodbc
import time

# SQL Server connection configuration
DATABASE = "stock"
SERVER = r".\SQLEXPRESS"
# SERVER = r"DESKTOP-AR99KHQ"

def get_db_connection():
    """Helper to get a new DB connection."""
    conn_str = (
        r"DRIVER={SQL Server};"
        fr"SERVER={SERVER};"
        fr"DATABASE={DATABASE};"
        r"Trusted_Connection=yes;"
        r"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    try:
        # Connect to master database to check if our database exists
        master_conn_str = (
            r"DRIVER={SQL Server};"
            fr"SERVER={SERVER};"
            r"DATABASE=master;"
            r"Trusted_Connection=yes;"
            r"TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(master_conn_str)
        conn.autocommit = True  # Enable autocommit for CREATE DATABASE
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT database_id FROM sys.databases WHERE name = ?", (DATABASE,))
        if cursor.fetchone() is None:
            # Database doesn't exist, create it
            cursor.execute(f"CREATE DATABASE [{DATABASE}]")
            print(f"Database '{DATABASE}' created successfully.")
        else:
            print(f"Database '{DATABASE}' already exists.")
        
        cursor.close()
        conn.close()
        
    except pyodbc.Error as e:
        print(f"Error creating database: {e}")
        raise

def is_database_locked():
    """Check if the database connection is available"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return False  # Database is accessible
    except pyodbc.Error as e:
        print(f"Database connection error: {e}")
        return True

def create_connection():
    """Create a database connection to SQL Server"""
    try:
        # Ensure database exists before connecting
        create_database_if_not_exists()
        return get_db_connection()
    except pyodbc.Error as e:
        print(f"Database error: {e}")
        return None

def migrate_extractions_table(cursor):
    """Migrate extractions table to use branch_id instead of branch_name"""
    try:
        # Check if branch_id column exists
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'extractions' AND COLUMN_NAME = 'branch_id'
        """)
        
        if cursor.fetchone()[0] == 0:
            # Add branch_id column
            cursor.execute("ALTER TABLE extractions ADD branch_id INT")
            
            # Update existing records to set branch_id based on branch_name
            cursor.execute("""
                UPDATE e SET e.branch_id = b.id
                FROM extractions e
                INNER JOIN branches b ON e.branch_name = b.branch_name
                WHERE e.branch_id IS NULL
            """)
            
            # Make branch_id NOT NULL after updating existing records
            cursor.execute("ALTER TABLE extractions ALTER COLUMN branch_id INT NOT NULL")
            
            # Add foreign key constraint
            cursor.execute("""
                ALTER TABLE extractions 
                ADD CONSTRAINT FK_extractions_branch_id 
                FOREIGN KEY (branch_id) REFERENCES branches (id)
            """)
            
            print("Extractions table migrated to use branch_id")
            
    except Exception as e:
        print(f"Migration error: {e}")

def migrate_items_quantity_type(cursor):
    """Add quantity_type column to items table"""
    try:
        # Check if quantity_type column exists
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'items' AND COLUMN_NAME = 'quantity_type'
        """)
        
        if cursor.fetchone()[0] == 0:
            # Add quantity_type column with default value 'unit'
            cursor.execute("ALTER TABLE items ADD quantity_type NVARCHAR(50) DEFAULT 'unit'")
            
            # Update existing records to have 'unit' as default
            cursor.execute("UPDATE items SET quantity_type = 'unit' WHERE quantity_type IS NULL")
            
            print("Items table migrated to include quantity_type column")
            
    except Exception as e:
        print(f"Migration error: {e}")

def create_tables():
    """Create the necessary tables if they don't exist"""
    # Ensure database exists before creating tables
    create_database_if_not_exists()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create items table
        items_table = """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='items' AND xtype='U')
                         BEGIN
                         CREATE TABLE items (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            item_name NVARCHAR(255) NOT NULL,
                            quantity INT NOT NULL,
                            quantity_type NVARCHAR(50) DEFAULT 'unit',
                            price_per_unit DECIMAL(10,2) NOT NULL,
                            invoice_number NVARCHAR(100) NOT NULL,
                            supplier_name NVARCHAR(255),
                            date_added DATETIME NOT NULL
                        )
                        END"""
        
        # Create extractions table
        extractions_table = """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='extractions' AND xtype='U')
                               BEGIN
                               CREATE TABLE extractions (
                                id INT IDENTITY(1,1) PRIMARY KEY,
                                item_id INT NOT NULL,
                                branch_id INT NOT NULL,
                                branch_name NVARCHAR(255),
                                quantity_extracted INT NOT NULL,
                                date_extracted DATETIME NOT NULL,
                                FOREIGN KEY (item_id) REFERENCES items (id),
                                FOREIGN KEY (branch_id) REFERENCES branches (id)
                            )
                            END"""
    
        # Create invoices table
        invoices_table = """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='invoices' AND xtype='U')
                            BEGIN
                            CREATE TABLE invoices (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            invoice_number NVARCHAR(100) NOT NULL UNIQUE,
                            supplier_name NVARCHAR(255) NOT NULL,
                            total_amount DECIMAL(10,2) NOT NULL,
                            payment_status NVARCHAR(50) NOT NULL,
                            paid_amount DECIMAL(10,2) DEFAULT 0,
                            issue_date DATETIME NOT NULL,
                            due_date DATETIME,
                            notes NTEXT
                        )
                        END"""
        
        # Create users table
        users_table = """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
                         BEGIN
                         CREATE TABLE users (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        name NVARCHAR(255) NOT NULL,
                        phone NVARCHAR(50) NOT NULL,
                        email NVARCHAR(255) NOT NULL,
                        username NVARCHAR(100),
                        password NVARCHAR(255),
                        role NVARCHAR(50) NOT NULL,
                        job_title NVARCHAR(255),
                        salary NVARCHAR(50)
                    )
                    END"""
    
        # Create settings table
        settings_table = """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='settings' AND xtype='U')
                            BEGIN
                            CREATE TABLE settings (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            setting_name NVARCHAR(100) NOT NULL UNIQUE,
                            setting_value NTEXT,
                            setting_type NVARCHAR(50)
                        )
                        END"""
        
        # Create suppliers table
        suppliers_table = """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='suppliers' AND xtype='U')
                             BEGIN
                             CREATE TABLE suppliers (
                             id INT IDENTITY(1,1) PRIMARY KEY,
                             supplier_name NVARCHAR(255) NOT NULL UNIQUE,
                             contact_person NVARCHAR(255),
                             phone NVARCHAR(50),
                             email NVARCHAR(255),
                             address NTEXT,
                             payment_terms NVARCHAR(100),
                             notes NTEXT,
                             date_added DATETIME NOT NULL DEFAULT GETDATE(),
                             is_active BIT DEFAULT 1
                         )
                         END"""
        
        # Create branches table
        branches_table = """IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='branches' AND xtype='U')
                            BEGIN
                            CREATE TABLE branches (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            branch_name NVARCHAR(255) NOT NULL UNIQUE,
                            branch_code NVARCHAR(50),
                            manager_name NVARCHAR(255),
                            phone NVARCHAR(50),
                            address NTEXT,
                            opening_date DATETIME,
                            notes NTEXT,
                            date_added DATETIME NOT NULL DEFAULT GETDATE(),
                            is_active BIT DEFAULT 1
                        )
                        END"""
        
        # Execute table creation statements in correct order (dependencies first)
        cursor.execute(suppliers_table)
        cursor.execute(branches_table)
        cursor.execute(items_table)
        cursor.execute(extractions_table)
        cursor.execute(invoices_table)
        cursor.execute(users_table)
        cursor.execute(settings_table)
        
        # Migrate existing extractions table to use branch_id
        migrate_extractions_table(cursor)
        
        # Migrate items table to include quantity_type
        migrate_items_quantity_type(cursor)
        
        # No need to add is_admin column since table now uses role column
        
        # Check if admin user exists, if not create default admin user
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ('admin',))
        if cursor.fetchone()[0] == 0:
            # Create admin user with all required fields
            cursor.execute("INSERT INTO users (name, phone, email, username, password, role) VALUES (?, ?, ?, ?, ?, ?)", 
                          ('Administrator', '000-000-0000', 'admin@restaurant.com', 'admin', 'admin', 'admin'))
        
        # Initialize default settings if they don't exist
        default_settings = [
            ('default_printer', '', 'text'),
            ('company_logo', '', 'file_path'),
            ('auto_print', 'true', 'boolean')
        ]
        
        for setting in default_settings:
            # Use MERGE for SQL Server equivalent of INSERT OR IGNORE
            merge_sql = """
            MERGE settings AS target
            USING (SELECT ? AS setting_name, ? AS setting_value, ? AS setting_type) AS source
            ON target.setting_name = source.setting_name
            WHEN NOT MATCHED THEN
                INSERT (setting_name, setting_value, setting_type)
                VALUES (source.setting_name, source.setting_value, source.setting_type);
            """
            cursor.execute(merge_sql, (setting[0], setting[1], setting[2]))
        
        conn.commit()
        
    except pyodbc.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()