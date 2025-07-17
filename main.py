import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from database import create_connection, create_tables, is_database_locked

def main():
    # Create the application
    app = QApplication(sys.argv)
    app.setApplicationName("Stock Management System")
    
    # Check if database is locked
    if is_database_locked():
        # Show error message and exit
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Database Error")
        error_dialog.setText("The database is locked by another process.")
        error_dialog.setInformativeText("Please close any other instances of the application and try again.")
        error_dialog.exec()
        return
    
    # Initialize database
    conn = create_connection()
    if conn is not None:
        create_tables(conn)
        conn.close()
    else:
        # Show error message and exit
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Database Error")
        error_dialog.setText("Cannot create the database connection.")
        error_dialog.setInformativeText("Please check if the database file is accessible and not corrupted.")
        error_dialog.exec()
        return
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()