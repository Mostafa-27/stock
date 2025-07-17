import sqlite3
from database import create_connection

class Settings:
    @staticmethod
    def get_setting(setting_name, default_value=None):
        """
        Get a setting value from the database
        Returns: The setting value or default_value if not found
        """
        conn = create_connection()
        if conn is None:
            return default_value
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT setting_value, setting_type FROM settings WHERE setting_name = ?", 
                (setting_name,)
            )
            result = cursor.fetchone()
            
            if result:
                value, type_name = result
                # Convert value based on type
                if type_name == 'boolean':
                    return value.lower() == 'true'
                elif type_name == 'integer':
                    return int(value) if value else 0
                elif type_name == 'float':
                    return float(value) if value else 0.0
                else:  # text or file_path
                    return value
            else:
                return default_value
        except sqlite3.Error as e:
            print(f"Database error while getting setting: {e}")
            return default_value
        finally:
            conn.close()
    
    @staticmethod
    def update_setting(setting_name, setting_value, setting_type='text'):
        """
        Update a setting in the database
        Returns: True if successful, False otherwise
        """
        conn = create_connection()
        if conn is None:
            return False
        
        # Convert value to string for storage
        if isinstance(setting_value, bool):
            str_value = 'true' if setting_value else 'false'
        else:
            str_value = str(setting_value)
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (setting_name, setting_value, setting_type) VALUES (?, ?, ?)",
                (setting_name, str_value, setting_type)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error while updating setting: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_all_settings():
        """
        Get all settings from the database
        Returns: Dictionary of settings or empty dict on error
        """
        conn = create_connection()
        if conn is None:
            return {}
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT setting_name, setting_value, setting_type FROM settings")
            settings = {}
            for row in cursor.fetchall():
                name, value, type_name = row
                # Convert value based on type
                if type_name == 'boolean':
                    settings[name] = value.lower() == 'true'
                elif type_name == 'integer':
                    settings[name] = int(value) if value else 0
                elif type_name == 'float':
                    settings[name] = float(value) if value else 0.0
                else:  # text or file_path
                    settings[name] = value
            return settings
        except sqlite3.Error as e:
            print(f"Database error while getting all settings: {e}")
            return {}
        finally:
            conn.close()