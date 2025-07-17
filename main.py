import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer

from ui.main_window import MainWindow
from ui.login import LoginWidget
from database import create_connection, create_tables, is_database_locked

def main():
    # Create the application
    app = QApplication(sys.argv)
    app.setApplicationName("Stock Management System")
    
    # Create a splash screen
    splash_pix = QPixmap(400, 200)
    splash_pix.fill(Qt.white)
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.showMessage("Loading Stock Management System...", 
                      Qt.AlignCenter | Qt.AlignBottom, Qt.black)
    splash.show()
    app.processEvents()
    
    # Check if database is locked
    if is_database_locked():
        splash.close()
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
        splash.close()
        # Show error message and exit
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Database Error")
        error_dialog.setText("Cannot create the database connection.")
        error_dialog.setInformativeText("Please check if the database file is accessible and not corrupted.")
        error_dialog.exec()
        return
    
    # Create login widget
    login_widget = LoginWidget()
    
    # Function to handle successful login
    main_window = None

    def on_login_successful(user_data):
        nonlocal main_window
        # Close login widget
        login_widget.close()
        
        # Create and show the main window with user data
        main_window = MainWindow(user_data)
        main_window.show()
    
    # Connect login signal
    login_widget.login_successful.connect(on_login_successful)
    
    # Close splash and show login after a short delay
    QTimer.singleShot(1000, lambda: {
        splash.close(),
        login_widget.show()
    })
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()