from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QMessageBox, QHBoxLayout, QFrame)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QIcon, QPixmap, QFont, QPalette, QBrush, QColor, QMouseEvent

from models.user import User

class LoginWidget(QWidget):
    # Signal emitted when login is successful
    login_successful = Signal(dict)  # Passes user data
    
    def __init__(self):
        super().__init__()
        self.drag_position = QPoint()
        self.init_ui()
    
    def init_ui(self):
        # Set window properties
        self.setWindowTitle("LOGIN")
        self.setFixedSize(1200, 700)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create custom title bar with window controls
        title_bar = QFrame()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.8);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        
        # Title label
        title_label = QLabel("PIZZA MELANO - LOGIN")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Window control buttons
        self.minimize_btn = QPushButton("−")
        self.maximize_btn = QPushButton("□")
        self.close_btn = QPushButton("×")
        
        for btn in [self.minimize_btn, self.maximize_btn, self.close_btn]:
            btn.setFixedSize(30, 30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: none;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)
        
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
        """)
        
        # Connect button signals
        self.minimize_btn.clicked.connect(self.showMinimized)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(self.minimize_btn)
        title_layout.addWidget(self.maximize_btn)
        title_layout.addWidget(self.close_btn)
        
        main_layout.addWidget(title_bar)
        
        # Create background with overlay
        background_frame = QFrame()
        background_frame.setStyleSheet("""
            QFrame {
                background-image: url('loginbackground.jpg');
                background-repeat: no-repeat;
                background-position: center;
                background-size: cover;
            }
        """)
        
        # Create dark overlay
        overlay_frame = QFrame()
        overlay_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.9);
            }
        """)
        
        # Stack the overlay on top of background
        background_layout = QVBoxLayout(background_frame)
        background_layout.setContentsMargins(0, 0, 0, 0)
        background_layout.addWidget(overlay_frame)
        
        # Create centered login container with modern styling
        login_container = QFrame()
        login_container.setFixedSize(500, 600)
        login_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.98);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.8);
            }
        """)
        
        # Create container layout
        container_layout = QVBoxLayout(login_container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)
        
        # Add logo image
        logo_label = QLabel()
        logo_pixmap = QPixmap("logo.png")
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
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 15px 20px;
                font-size: 16px;
                color: #2c3e50;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                background-color: white;
                border: 2px solid #663399;
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
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 15px 20px;
                font-size: 16px;
                color: #2c3e50;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                background-color: white;
                border: 2px solid #663399;
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
                transform: translateY(-2px);
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
        
        # Center the login container on overlay
        overlay_layout = QVBoxLayout(overlay_frame)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.addStretch()
        overlay_layout.addWidget(login_container, 0, Qt.AlignCenter)
        overlay_layout.addStretch()
        
        main_layout.addWidget(background_frame)
        
        # Set default values for testing
        self.username_input.setText("cafe")
        self.password_input.setText("admin")
        
        # Set layout
        self.setLayout(main_layout)
    
    def toggle_maximize(self):
        """Toggle between maximized and normal window state"""
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for window dragging"""
        if event.buttons() == Qt.LeftButton and not self.isMaximized():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        
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