from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QMessageBox, QHBoxLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap

from models.user import User

class LoginWidget(QWidget):
    # Signal emitted when login is successful
    login_successful = Signal(dict)  # Passes user data
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Add logo or title
        title_label = QLabel("Stock Management System")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        main_layout.addWidget(title_label)
        
        # Create form layout
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        
        # Username field
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        
        # Password field
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;"
        )
        self.login_button.clicked.connect(self.attempt_login)
        
        # Add form to main layout with some margins
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        form_widget.setFixedWidth(300)
        main_layout.addWidget(form_widget)
        main_layout.addWidget(self.login_button)
        
        # Set default values for testing (remove in production)
        self.username_input.setText("admin")
        self.password_input.setText("admin")
        
        # Set layout
        self.setLayout(main_layout)
        
        # Connect enter key to login button
        self.username_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)
    
    def attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
            return
        
        # Attempt to login
        status, user_data = User.login(username, password)
        
        if status == User.LOGIN_SUCCESS:
            # Emit signal with user data
            self.login_successful.emit(user_data)
        elif status == User.INVALID_CREDENTIALS:
            QMessageBox.warning(self, "Login Error", "Invalid username or password.")
        else:  # DB_ERROR
            QMessageBox.critical(self, "Database Error", "Could not connect to the database.")