import pyodbc
from datetime import datetime
from database import get_db_connection
from models.item import Item

class Extraction:
    def __init__(self, id=None, item_id=None, branch_id=None, branch_name="", quantity_extracted=0, date_extracted=None):
        self.id = id
        self.item_id = item_id
        self.branch_id = branch_id
        self.branch_name = branch_name
        self.quantity_extracted = quantity_extracted
        self.date_extracted = date_extracted if date_extracted else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def extract_item(item_id, branch_id, quantity_extracted):
        """Extract an item to a branch"""
        try:
            print(f"Starting extraction: item_id={item_id}, branch_id={branch_id}, quantity={quantity_extracted}")
            conn = get_db_connection()
            cur = conn.cursor()
            print("Database connection established")
            
            # Get the current item
            cur.execute("SELECT quantity FROM items WHERE id = ?", (item_id,))
            row = cur.fetchone()
            print(f"Item query result: {row}")
                
            if not row:
                conn.rollback()
                print("Item not found, rolling back")
                return False, "Item not found"
            
            current_quantity = row[0]
            print(f"Current quantity: {current_quantity}")
            
            # Check if there's enough stock
            if current_quantity < quantity_extracted:
                conn.rollback()
                return False, f"Not enough stock. Available: {current_quantity}"
            
            # Get branch name for backward compatibility
            cur.execute("SELECT branch_name FROM branches WHERE id = ?", (branch_id,))
            branch_row = cur.fetchone()
            print(f"Branch query result: {branch_row}")
            if not branch_row:
                conn.rollback()
                print("Branch not found, rolling back")
                return False, "Branch not found"
            
            branch_name = branch_row[0]
            print(f"Branch name: {branch_name}")
            
            # Update the item quantity
            new_quantity = current_quantity - quantity_extracted
            print(f"Updating item quantity from {current_quantity} to {new_quantity}")
            cur.execute("UPDATE items SET quantity = ? WHERE id = ?", (new_quantity, item_id))
            print("Item quantity updated")
            
            # Record the extraction with both branch_id and branch_name
            date_extracted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Inserting extraction record: item_id={item_id}, branch_id={branch_id}, branch_name={branch_name}, quantity={quantity_extracted}, date={date_extracted}")
            cur.execute(
                "INSERT INTO extractions (item_id, branch_id, branch_name, quantity_extracted, date_extracted) VALUES (?, ?, ?, ?, ?)",
                (item_id, branch_id, branch_name, quantity_extracted, date_extracted)
            )
            print("Extraction record inserted")
            
            # Commit the transaction
            print("Committing transaction")
            conn.commit()
            print("Transaction committed successfully")
            return True, "Item extracted successfully"
            
        except pyodbc.Error as e:
            if 'conn' in locals():
                try:
                    conn.rollback()
                except:
                    pass
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
                SELECT e.id, e.item_id, i.item_name, e.branch_id, e.branch_name, e.quantity_extracted, e.date_extracted 
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
                    'branch_id': row[3],
                    'branch_name': row[4],
                    'quantity_extracted': row[5],
                    'date_extracted': row[6]
                }
                extractions.append(extraction)
        except pyodbc.Error as e:
            print(f"Database error: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        
        return extractions