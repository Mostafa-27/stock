import pyodbc
from datetime import datetime
from database import get_db_connection
from models.item import Item

class Extraction:
    def __init__(self, id=None, item_id=None, branch_id=None, branch_name="", quantity_extracted=0, extracted_by="", date_extracted=None):
        self.id = id
        self.item_id = item_id
        self.branch_id = branch_id
        self.branch_name = branch_name
        self.quantity_extracted = quantity_extracted
        self.extracted_by = extracted_by
        self.date_extracted = date_extracted if date_extracted else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def extract_item(item_id, branch_id, quantity_extracted, extracted_by=""):
        """Extract an item to a branch"""
        try:
            print(f"Starting extraction: item_id={item_id}, branch_id={branch_id}, quantity={quantity_extracted}, extracted_by={extracted_by}")
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
            
            # Record the extraction with both branch_id, branch_name, and extracted_by
            date_extracted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Inserting extraction record: item_id={item_id}, branch_id={branch_id}, branch_name={branch_name}, quantity={quantity_extracted}, extracted_by={extracted_by}, date={date_extracted}")
            cur.execute(
                "INSERT INTO extractions (item_id, branch_id, branch_name, quantity_extracted, extracted_by, date_extracted) VALUES (?, ?, ?, ?, ?, ?)",
                (item_id, branch_id, branch_name, quantity_extracted, extracted_by, date_extracted)
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
                SELECT e.id, e.item_id, i.item_name, e.branch_id, e.branch_name, e.quantity_extracted, e.extracted_by, e.date_extracted 
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
                    'extracted_by': row[6] if len(row) > 6 else '',
                    'date_extracted': row[7] if len(row) > 7 else row[6]
                }
                extractions.append(extraction)
        except pyodbc.Error as e:
            print(f"Database error: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
        
        return extractions

    @staticmethod
    def extract_multiple_items(items_list, branch_id, extracted_by=""):
        """Extract multiple items to a branch in a single transaction
        items_list: List of dictionaries with 'item_id' and 'quantity' keys
        """
        try:
            print(f"Starting multiple extraction: {len(items_list)} items, branch_id={branch_id}, extracted_by={extracted_by}")
            conn = get_db_connection()
            cur = conn.cursor()
            print("Database connection established")
            
            # Get branch name for backward compatibility
            cur.execute("SELECT branch_name FROM branches WHERE id = ?", (branch_id,))
            branch_row = cur.fetchone()
            if not branch_row:
                conn.rollback()
                print("Branch not found, rolling back")
                return False, "Branch not found"
            
            branch_name = branch_row[0]
            print(f"Branch name: {branch_name}")
            
            # Validate all items first
            for item_data in items_list:
                item_id = item_data['item_id']
                quantity_extracted = item_data['quantity']
                
                # Get the current item
                cur.execute("SELECT quantity, item_name FROM items WHERE id = ?", (item_id,))
                row = cur.fetchone()
                
                if not row:
                    conn.rollback()
                    return False, f"Item with ID {item_id} not found"
                
                current_quantity, item_name = row
                
                # Check if there's enough stock
                if current_quantity < quantity_extracted:
                    conn.rollback()
                    return False, f"Not enough stock for {item_name}. Available: {current_quantity}, Requested: {quantity_extracted}"
            
            # If all validations pass, perform the extractions
            date_extracted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            extraction_results = []
            
            for item_data in items_list:
                item_id = item_data['item_id']
                quantity_extracted = item_data['quantity']
                
                # Get current quantity again
                cur.execute("SELECT quantity FROM items WHERE id = ?", (item_id,))
                current_quantity = cur.fetchone()[0]
                
                # Update the item quantity
                new_quantity = current_quantity - quantity_extracted
                print(f"Updating item {item_id} quantity from {current_quantity} to {new_quantity}")
                cur.execute("UPDATE items SET quantity = ? WHERE id = ?", (new_quantity, item_id))
                
                # Record the extraction
                print(f"Inserting extraction record: item_id={item_id}, quantity={quantity_extracted}")
                cur.execute(
                    "INSERT INTO extractions (item_id, branch_id, branch_name, quantity_extracted, extracted_by, date_extracted) VALUES (?, ?, ?, ?, ?, ?)",
                    (item_id, branch_id, branch_name, quantity_extracted, extracted_by, date_extracted)
                )
                
                extraction_results.append({
                    'item_id': item_id,
                    'quantity': quantity_extracted,
                    'new_stock': new_quantity
                })
            
            # Commit the transaction
            print("Committing transaction")
            conn.commit()
            print("Transaction committed successfully")
            return True, f"Successfully extracted {len(items_list)} items"
            
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