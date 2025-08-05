import pyodbc
from datetime import datetime
from database import get_db_connection
from models.item import Item

class Extraction:
    def __init__(self, id=None, item_id=None, branch_name="", quantity_extracted=0, date_extracted=None):
        self.id = id
        self.item_id = item_id
        self.branch_name = branch_name
        self.quantity_extracted = quantity_extracted
        self.date_extracted = date_extracted if date_extracted else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def extract_item(item_id, branch_name, quantity_extracted):
        """Extract an item to a branch"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # Start a transaction
            cur.execute("BEGIN TRANSACTION")
            
            # Get the current item
            cur.execute("SELECT quantity FROM items WHERE id = ?", (item_id,))
            row = cur.fetchone()
                
            if not row:
                conn.rollback()
                return False, "Item not found"
            
            current_quantity = row[0]
            
            # Check if there's enough stock
            if current_quantity < quantity_extracted:
                conn.rollback()
                return False, f"Not enough stock. Available: {current_quantity}"
            
            # Update the item quantity
            new_quantity = current_quantity - quantity_extracted
            cur.execute("UPDATE items SET quantity = ? WHERE id = ?", (new_quantity, item_id))
            
            # Record the extraction
            date_extracted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "INSERT INTO extractions (item_id, branch_name, quantity_extracted, date_extracted) VALUES (?, ?, ?, ?)",
                (item_id, branch_name, quantity_extracted, date_extracted)
            )
            
            # Commit the transaction
            conn.commit()
            return True, "Item extracted successfully"
            
        except pyodbc.Error as e:
            if 'conn' in locals():
                conn.rollback()
            return False, f"Database error: {e}"
        finally:
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def get_all_extractions():
        """Get all extractions from the database"""
        extractions = []
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT e.id, e.item_id, i.item_name, e.branch_name, e.quantity_extracted, e.date_extracted 
                FROM extractions e
                JOIN items i ON e.item_id = i.id
                ORDER BY e.date_extracted DESC
            """)
            rows = cur.fetchall()
                
            for row in rows:
                extraction = {
                    'id': row[0],
                    'item_id': row[1],
                    'item_name': row[2],
                    'branch_name': row[3],
                    'quantity_extracted': row[4],
                    'date_extracted': row[5]
                }
                extractions.append(extraction)
        except pyodbc.Error as e:
            print(f"Database error: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        
        return extractions