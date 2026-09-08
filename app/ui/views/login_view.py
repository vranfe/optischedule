from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from app.auth.auth_service import AuthService
from app.ui.dialogs.credentials_dialog import CredentialsDialog

class LoginView(QWidget):
    login_successful = Signal(object)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Centered Login Card
        card = QFrame()
        card.setFixedWidth(440)
        card.setStyleSheet("""
            QFrame#login_card {
                background-color: #ffffff;
                border-radius: 16px;
                border: 1.5px solid #e2e8f0;
            }
        """)
        card.setObjectName("login_card")
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(36, 36, 36, 36)

        # Header Institutional Emblem / Banner
        header_banner = QFrame()
        header_banner.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e3a8a, stop:0.6 #2563eb, stop:1 #b91c1c);
            border-radius: 12px;
            padding: 16px;
        """)
        h_layout = QVBoxLayout(header_banner)
        h_layout.setSpacing(4)
        h_layout.setAlignment(Qt.AlignCenter)
        
        logo_icon = QLabel("🎓")
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_icon.setStyleSheet("font-size: 28px; background: transparent;")
        
        title = QLabel("OptiSchedule UMB")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff; background: transparent; letter-spacing: -0.5px;")
        
        sub = QLabel("Universidad Manuela Beltrán")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 12px; font-weight: 600; color: #e0e7ff; background: transparent;")
        
        h_layout.addWidget(logo_icon)
        h_layout.addWidget(title)
        h_layout.addWidget(sub)
        card_layout.addWidget(header_banner)

        # Title Form Section
        welcome_box = QVBoxLayout()
        welcome_box.setSpacing(2)
        welcome_title = QLabel("Portal de Acceso Institucional")
        welcome_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0f172a;")
        welcome_sub = QLabel("Ingresa con tus credenciales de usuario")
        welcome_sub.setStyleSheet("font-size: 12px; color: #64748b;")
        welcome_box.addWidget(welcome_title)
        welcome_box.addWidget(welcome_sub)
        card_layout.addLayout(welcome_box)

        # Form Inputs
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)

        # Username Input
        user_lbl = QLabel("Nombre de Usuario")
        user_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #334155;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ej: admin, docente1, estudiante1")
        self.username_input.setStyleSheet("""
            QLineEdit {
                color: #0f172a; 
                background-color: #f8fafc; 
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                font-size: 13px; 
                padding: 10px 12px;
            }
            QLineEdit:focus {
                border-color: #4f46e5;
                background-color: #ffffff;
            }
        """)
        form_layout.addWidget(user_lbl)
        form_layout.addWidget(self.username_input)

        # Password Input with Toggle
        pass_lbl = QLabel("Contraseña")
        pass_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #334155;")
        
        pass_container = QHBoxLayout()
        pass_container.setSpacing(6)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Tu contraseña institucional")
        self.password_input.setStyleSheet("""
            QLineEdit {
                color: #0f172a; 
                background-color: #f8fafc; 
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                font-size: 13px; 
                padding: 10px 12px;
            }
            QLineEdit:focus {
                border-color: #4f46e5;
                background-color: #ffffff;
            }
        """)
        self.password_input.returnPressed.connect(self.handle_login)

        self.toggle_pass_btn = QPushButton("👁️")
        self.toggle_pass_btn.setFixedSize(38, 38)
        self.toggle_pass_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_pass_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                font-size: 14px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.toggle_pass_btn.clicked.connect(self.toggle_password_visibility)

        pass_container.addWidget(self.password_input)
        pass_container.addWidget(self.toggle_pass_btn)

        form_layout.addWidget(pass_lbl)
        form_layout.addLayout(pass_container)
        card_layout.addLayout(form_layout)

        # Login Submit Button
        self.login_btn = QPushButton("🚀 INICIAR SESIÓN")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e3a8a;
                color: #ffffff;
                font-weight: 800;
                font-size: 14px;
                padding: 12px;
                border-radius: 8px;
                margin-top: 6px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        card_layout.addWidget(self.login_btn)

        # Subtle Credentials Helper Modal Trigger
        help_layout = QHBoxLayout()
        help_layout.setAlignment(Qt.AlignCenter)

        helper_btn = QPushButton("🔑 Ver Cuentas y Credenciales de Prueba")
        helper_btn.setCursor(Qt.PointingHandCursor)
        helper_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #4f46e5;
                font-size: 12px;
                font-weight: 600;
                border: none;
                padding: 4px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #3730a3;
            }
        """)
        helper_btn.clicked.connect(self.open_credentials_dialog)
        help_layout.addWidget(helper_btn)
        card_layout.addLayout(help_layout)

        main_layout.addWidget(card)

    def toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_pass_btn.setText("🔒")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_pass_btn.setText("👁️")

    def open_credentials_dialog(self):
        dialog = CredentialsDialog(self)
        dialog.account_selected.connect(self.fill_credentials)
        dialog.exec()

    def fill_credentials(self, username, password):
        self.username_input.setText(username)
        self.password_input.setText(password)
        self.handle_login()

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Campos Requeridos", "Por favor ingresa usuario y contraseña.")
            return

        success, user = AuthService.authenticate(username, password)
        if success:
            self.username_input.clear()
            self.password_input.clear()
            self.login_successful.emit(user)
        else:
            QMessageBox.critical(
                self, "Error de Autenticación", 
                f"No se pudo iniciar sesión con el usuario '{username}'.\n\nVerifica las credenciales o consulta la lista de cuentas de prueba."
            )

    def clear_fields(self):
        self.username_input.clear()
        self.password_input.clear()
        self.username_input.setFocus()
