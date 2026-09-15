from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame, QSpacerItem, QSizePolicy,
    QGraphicsDropShadowEffect, QGridLayout
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
from app.auth.auth_service import AuthService
from app.ui.dialogs.credentials_dialog import CredentialsDialog

class LoginView(QWidget):
    login_successful = Signal(object)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f8fafc, stop:0.5 #f1f5f9, stop:1 #e2e8f0);")
        root_grid = QGridLayout(self)
        root_grid.setContentsMargins(24, 24, 24, 24)
        root_grid.setRowStretch(0, 1)
        root_grid.setRowStretch(1, 0)
        root_grid.setRowStretch(2, 1)
        root_grid.setColumnStretch(0, 1)
        root_grid.setColumnStretch(1, 0)
        root_grid.setColumnStretch(2, 1)

        # Centered Formal Login Card
        card = QFrame()
        card.setFixedWidth(460)
        card.setStyleSheet("""
            QFrame#formal_login_card {
                background-color: #ffffff;
                border-radius: 18px;
                border: 1.5px solid #cbd5e1;
            }
        """)
        card.setObjectName("formal_login_card")

        # Soft subtle shadow
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(15, 23, 42, 35))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(18)
        card_layout.setContentsMargins(36, 40, 36, 36)

        # Header Institutional Emblem / Banner
        header_banner = QFrame()
        header_banner.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e3a8a, stop:0.65 #2563eb, stop:1 #4f46e5);
            border-radius: 14px;
            padding: 18px;
        """)
        h_layout = QVBoxLayout(header_banner)
        h_layout.setSpacing(4)
        h_layout.setAlignment(Qt.AlignCenter)

        logo_icon = QLabel("🎓")
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_icon.setStyleSheet("font-size: 32px; background: transparent;")

        title = QLabel("OptiSchedule UMB")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff; background: transparent; letter-spacing: -0.5px;")

        sub = QLabel("UNIVERSIDAD MANUELA BELTRÁN")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 11px; font-weight: 700; color: #e0e7ff; background: transparent; letter-spacing: 1px;")

        h_layout.addWidget(logo_icon)
        h_layout.addWidget(title)
        h_layout.addWidget(sub)
        card_layout.addWidget(header_banner)

        # Formal Portal Title Section
        welcome_box = QVBoxLayout()
        welcome_box.setSpacing(3)
        welcome_title = QLabel("Portal de Acceso Institucional")
        welcome_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #0f172a;")
        welcome_sub = QLabel("Ingresa con tu usuario institucional o código estudiantil")
        welcome_sub.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 500;")
        welcome_box.addWidget(welcome_title)
        welcome_box.addWidget(welcome_sub)
        card_layout.addLayout(welcome_box)

        # Form Inputs
        form_layout = QVBoxLayout()
        form_layout.setSpacing(14)

        # Username Input
        user_lbl = QLabel("Usuario / Código Institucional")
        user_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #334155;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ej: admin, docente1, estudiante1")
        self.username_input.setStyleSheet("""
            QLineEdit {
                color: #0f172a; 
                background-color: #f8fafc; 
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
                font-size: 13px; 
                padding: 11px 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4f46e5;
                background-color: #ffffff;
            }
        """)
        form_layout.addWidget(user_lbl)
        form_layout.addWidget(self.username_input)

        # Password Input with Toggle
        pass_lbl = QLabel("Contraseña Institucional")
        pass_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #334155;")
        
        pass_container = QHBoxLayout()
        pass_container.setSpacing(8)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Tu contraseña de acceso")
        self.password_input.setStyleSheet("""
            QLineEdit {
                color: #0f172a; 
                background-color: #f8fafc; 
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
                font-size: 13px; 
                padding: 11px 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4f46e5;
                background-color: #ffffff;
            }
        """)
        self.password_input.returnPressed.connect(self.handle_login)

        self.toggle_pass_btn = QPushButton("👁️")
        self.toggle_pass_btn.setFixedSize(42, 42)
        self.toggle_pass_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_pass_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
                font-size: 15px;
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
        self.login_btn = QPushButton("🔐 INICIAR SESIÓN INSTITUCIONAL")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e3a8a, stop:1 #4f46e5);
                color: #ffffff;
                font-weight: 800;
                font-size: 13px;
                padding: 13px;
                border-radius: 10px;
                margin-top: 6px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #6366f1);
            }
            QPushButton:pressed {
                background: #1e40af;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        card_layout.addWidget(self.login_btn)

        # Institutional Security Notice
        sec_notice = QLabel("🔒 Conexión Segura SSL • Sistema Centralizado UMB")
        sec_notice.setAlignment(Qt.AlignCenter)
        sec_notice.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: 600; margin-top: 4px;")
        card_layout.addWidget(sec_notice)

        # Center card absolutely horizontally and vertically in center cell (1, 1)
        root_grid.addWidget(card, 1, 1, Qt.AlignCenter)

        # Subtle Evaluation Helper Link (anclado a esquina inferior derecha en celda 2, 2)
        footer_row = QHBoxLayout()
        footer_row.addStretch()
        helper_btn = QPushButton("ℹ️ Directorio de Cuentas (Entorno Evaluativo)")
        helper_btn.setCursor(Qt.PointingHandCursor)
        helper_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748b;
                font-size: 11px;
                font-weight: 600;
                border: none;
                padding: 6px 10px;
            }
            QPushButton:hover {
                color: #4f46e5;
                text-decoration: underline;
            }
        """)
        helper_btn.clicked.connect(self.open_credentials_dialog)
        footer_row.addWidget(helper_btn)
        root_grid.addLayout(footer_row, 2, 2, Qt.AlignBottom | Qt.AlignRight)

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
            QMessageBox.warning(self, "Campos Requeridos", "Por favor ingresa tu usuario y contraseña institucional.")
            return

        success, user = AuthService.authenticate(username, password)
        if success:
            self.username_input.clear()
            self.password_input.clear()
            self.login_successful.emit(user)
        else:
            QMessageBox.critical(
                self, "Error de Autenticación", 
                f"Las credenciales ingresadas para '{username}' no son válidas.\n\nPor favor verifica tu usuario y contraseña."
            )

    def clear_fields(self):
        self.username_input.clear()
        self.password_input.clear()
        self.username_input.setFocus()
