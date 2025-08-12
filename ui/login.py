from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QMessageBox, QHBoxLayout, QFrame, QGraphicsBlurEffect)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QIcon, QPixmap, QFont, QPalette, QBrush, QColor, QMouseEvent, QPainter

from models.user import User
from utils.resource_utils import get_image_path

class LoginWidget(QWidget):
    # Signal emitted when login is successful
    login_successful = Signal(dict)  # Passes user data
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # Set window properties
        self.setWindowTitle("PIZZA MELANO - LOGIN")
        self.setMinimumSize(800, 600)  # Set minimum size instead of fixed size
        self.resize(1200, 700)  # Set initial size
        # Remove frameless window flag to use standard window frame
        
        # Create a background label for the blurred image
        self.background_label = QLabel(self)
        self.background_label.setScaledContents(True)
        
        # Set background image with blur effect
        background_image_path = get_image_path('loginbackground.jpg')
        pixmap = QPixmap(background_image_path)
        
        if not pixmap.isNull():
            # Create blur effect
            blur_effect = QGraphicsBlurEffect()
            blur_effect.setBlurRadius(100)  # Adjust blur radius as needed
            self.background_label.setGraphicsEffect(blur_effect)
            self.background_label.setPixmap(pixmap)
        
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create white overlay for better contrast and readability with blur effect
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.5);
            }
        """)
        
        # Create centered login container with modern styling
        login_container = QFrame()
        login_container.setObjectName("login_container")
        login_container.setFixedSize(500, 600)
        login_container.setAutoFillBackground(True)
        login_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.55);
                background-image: none;
                border-radius: 20px;
                border: 2px solid rgba(200, 200, 200, 0.8);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
        """)
        
        # Create container layout
        container_layout = QVBoxLayout(login_container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)
         
        
        # Add logo image
        logo_label = QLabel()
        logo_path = get_image_path("logo.png")
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            # Scale the logo to fit nicely in the login form
            scaled_pixmap = logo_pixmap.scaled(360, 100, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            # Fallback text if image not found
            logo_label.setText("PIZZA\nMELANO")
            logo_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-size: 18px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
        
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedHeight(120)
        container_layout.addWidget(logo_label)
        
        # LOGIN title
        title_label = QLabel("LOGIN")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 36px;
                font-weight: bold;
                background: transparent;
                margin: 15px 0;
                letter-spacing: 2px;
            }
        """)
        container_layout.addWidget(title_label)
        
        # Username field with modern styling
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 1.0);
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 15px 20px;
                font-size: 16px;
                color: #000000;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: normal;
            }
            QLineEdit:focus {
                background-color: rgba(255, 255, 255, 1.0);
                border: 2px solid #663399;
                color: #000000;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #6c757d;
            }
        """)
        container_layout.addWidget(self.username_input)
        
        # Password field with modern styling
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 1.0);
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 15px 20px;
                font-size: 16px;
                color: #000000;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: normal;
            }
            QLineEdit:focus {
                background-color: rgba(255, 255, 255, 1.0);
                border: 2px solid #663399;
                color: #000000;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #6c757d;
            }
        """)
        container_layout.addWidget(self.password_input)
        
        # Login button with modern gradient styling
        self.login_button = QPushButton("تسجيل الدخول")
        self.login_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #663399, stop:1 #8e44ad);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #552288, stop:1 #7d3c98);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #441177, stop:1 #6c3483);
            }
        """)
        self.login_button.clicked.connect(self.attempt_login)
        container_layout.addWidget(self.login_button)
        
        # Footer text
        footer_label = QLabel("Tech Gear Solution")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("""
            QLabel {
                color: #3498db;
                font-size: 12px;
                background: transparent;
                margin-top: 20px;
            }
        """)
        container_layout.addWidget(footer_label)
        
        # Center the login container on content frame
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addStretch()
        content_layout.addWidget(login_container, 0, Qt.AlignCenter)
        content_layout.addStretch()
        
        main_layout.addWidget(content_frame)
        
        # Set default values for testing
        self.username_input.setText("cafe")
        self.password_input.setText("admin")
        
        # Set layout
        self.setLayout(main_layout)
        
        # Connect enter key to login button
        self.username_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)
    
    def resizeEvent(self, event):
        """Handle window resize to maintain background scaling"""
        super().resizeEvent(event)
        if hasattr(self, 'background_label'):
            self.background_label.resize(self.size())
    
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