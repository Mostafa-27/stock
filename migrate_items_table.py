"""
Database Migration Script - Fix Column Order
This script properly migrates the items table to have the correct column order
"""

import pyodbc
from database import get_db_connection, create_database_if_not_exists

def migrate_items_table_column_order():
    """Migrate items table to have correct column order"""
    try:
        create_database_if_not_exists()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("=== Starting Items Table Migration ===")
        
        # Step 1: Create a new table with correct column order
        print("Creating new items table with correct column order...")
        
        create_new_table_sql = """
        CREATE TABLE items_new (
            id INT IDENTITY(1,1) PRIMARY KEY,
            item_name NVARCHAR(255) NOT NULL,
            quantity INT NOT NULL,
            quantity_type NVARCHAR(50) DEFAULT 'unit',
            price_per_unit DECIMAL(10,2) NOT NULL,
            invoice_number NVARCHAR(100) NOT NULL,
            supplier_name NVARCHAR(255),
            date_added DATETIME NOT NULL
        )
        """
        
        cursor.execute(create_new_table_sql)
        
        # Step 2: Copy data from old table to new table with correct column mapping
        print("Copying data to new table...")
        
        # First, get all data from the old table
        cursor.execute("SELECT id, item_name, quantity, price_per_unit, invoice_number, supplier_name, date_added, quantity_type FROM items")
        old_data = cursor.fetchall()
        
        print(f"Found {len(old_data)} rows to migrate")
        
        # Insert data into new table with correct order
        for row in old_data:
            # Map old columns to new correct order:
            # old: id, item_name, quantity, price_per_unit, invoice_number, supplier_name, date_added, quantity_type
            # new: id, item_name, quantity, quantity_type, price_per_unit, invoice_number, supplier_name, date_added
            
            item_id = row[0]
            item_name = row[1]
            quantity = row[2]
            price_per_unit = row[3]
            invoice_number = row[4]
            supplier_name = row[5]
            date_added = row[6]
            quantity_type = row[7] if row[7] else 'unit'
            
            # Insert with correct column order
            cursor.execute("""
                SET IDENTITY_INSERT items_new ON;
                INSERT INTO items_new (id, item_name, quantity, quantity_type, price_per_unit, invoice_number, supplier_name, date_added)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                SET IDENTITY_INSERT items_new OFF;
            """, (item_id, item_name, quantity, quantity_type, price_per_unit, invoice_number, supplier_name, date_added))
        
        # Step 3: Drop old table and rename new table
        print("Replacing old table with new table...")
        
        # First, drop any foreign key constraints that reference the items table
        cursor.execute("""
            SELECT 
                fk.name AS foreign_key_name,
                tp.name AS parent_table
            FROM sys.foreign_keys fk
            INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
            WHERE fk.referenced_object_id = OBJECT_ID('items')
        """)
        
        foreign_keys = cursor.fetchall()
        
        # Drop foreign key constraints temporarily
        for fk in foreign_keys:
            print(f"Dropping foreign key: {fk[0]} from table: {fk[1]}")
            cursor.execute(f"ALTER TABLE {fk[1]} DROP CONSTRAINT {fk[0]}")
        
        # Drop old table
        cursor.execute("DROP TABLE items")
        
        # Rename new table
        cursor.execute("EXEC sp_rename 'items_new', 'items'")
        
        # Recreate foreign key constraints
        for fk in foreign_keys:
            if fk[1] == 'extractions':  # Only recreate for extractions table
                print(f"Recreating foreign key constraint for extractions table")
                cursor.execute("""
                    ALTER TABLE extractions 
                    ADD CONSTRAINT FK_extractions_item_id 
                    FOREIGN KEY (item_id) REFERENCES items (id)
                """)
        
        # Step 4: Verify the migration
        print("Verifying migration...")
        
        cursor.execute("""
            SELECT COLUMN_NAME, ORDINAL_POSITION
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'items'
            ORDER BY ORDINAL_POSITION
        """)
        
        new_columns = cursor.fetchall()
        print("New table structure:")
        for col in new_columns:
            print(f"Position {col[1]}: {col[0]}")
        
        # Test data integrity
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]
        print(f"Items count after migration: {count}")
        
        # Show sample data
        cursor.execute("SELECT TOP 3 id, item_name, quantity, quantity_type, price_per_unit, invoice_number FROM items")
        sample = cursor.fetchall()
        print("Sample data:")
        for row in sample:
            print(f"ID: {row[0]}, Name: {row[1]}, Qty: {row[2]}, Type: {row[3]}, Price: {row[4]}, Invoice: {row[5]}")
        
        conn.commit()
        conn.close()
        
        print("=== Migration Completed Successfully! ===")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    print("Starting items table column order migration...")
    migrate_items_table_column_order()
    print("Migration completed!")
