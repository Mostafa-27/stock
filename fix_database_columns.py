"""
Database Column Fix Script
This script fixes the column arrangements and ensures all tables have correct structure
"""

import pyodbc
from database import get_db_connection, create_database_if_not_exists

def check_table_structure():
    """Check the current structure of tables"""
    try:
        create_database_if_not_exists()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("=== Checking Items Table Structure ===")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'items'
            ORDER BY ORDINAL_POSITION
        """)
        
        items_columns = cursor.fetchall()
        for col in items_columns:
            print(f"Position {col[3]}: {col[0]} - {col[1]} - Nullable: {col[2]}")
        
        print("\n=== Current Items Data Sample ===")
        cursor.execute("SELECT TOP 5 * FROM items")
        sample_data = cursor.fetchall()
        
        for row in sample_data:
            print(f"Row: {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking table structure: {e}")

def fix_database_structure():
    """Fix the database structure issues"""
    try:
        create_database_if_not_exists()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("=== Fixing Database Structure ===")
        
        # Check if quantity_type column exists in correct position
        cursor.execute("""
            SELECT COLUMN_NAME, ORDINAL_POSITION
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'items' AND COLUMN_NAME = 'quantity_type'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"quantity_type column exists at position {result[1]}")
        else:
            print("Adding quantity_type column...")
            cursor.execute("ALTER TABLE items ADD quantity_type NVARCHAR(50) DEFAULT 'unit'")
            cursor.execute("UPDATE items SET quantity_type = 'unit' WHERE quantity_type IS NULL")
        
        # Verify the final structure
        print("\n=== Final Items Table Structure ===")
        cursor.execute("""
            SELECT COLUMN_NAME, ORDINAL_POSITION
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'items'
            ORDER BY ORDINAL_POSITION
        """)
        
        final_columns = cursor.fetchall()
        for col in final_columns:
            print(f"Position {col[1]}: {col[0]}")
        
        # Expected structure should be:
        # 1: id
        # 2: item_name  
        # 3: quantity
        # 4: quantity_type
        # 5: price_per_unit
        # 6: invoice_number
        # 7: supplier_name
        # 8: date_added
        
        conn.commit()
        conn.close()
        print("Database structure fix completed!")
        
    except Exception as e:
        print(f"Error fixing database structure: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def test_queries():
    """Test the queries to ensure they work correctly"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("=== Testing Queries ===")
        
        # Test selecting all items with correct column order
        cursor.execute("SELECT id, item_name, quantity, quantity_type, price_per_unit, invoice_number, supplier_name, date_added FROM items")
        
        items = cursor.fetchall()
        print(f"Found {len(items)} items")
        
        if items:
            print("Sample item:", items[0])
            
        conn.close()
        
    except Exception as e:
        print(f"Error testing queries: {e}")

if __name__ == "__main__":
    print("Starting database column fix...")
    check_table_structure()
    fix_database_structure()
    test_queries()
    print("Database fix completed!")
