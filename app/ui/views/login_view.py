from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame, QGroupBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from app.auth.auth_service import AuthService

class LoginView(QWidget):
    login_successful = Signal(object)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Card container
        card = QFrame()
        card.setFixedWidth(460)
        card.setStyleSheet("""
            QFrame#login_card {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #cbd5e1;
            }
        """)
        card.setObjectName("login_card")
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)
        card_layout.setContentsMargins(30, 30, 30, 30)

        # Institutional Header Banner
        header_banner = QFrame()
        header_banner.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e3a8a, stop:1 #b91c1c);
            border-radius: 8px;
            padding: 12px;
        """)
        h_layout = QVBoxLayout(header_banner)
        h_layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("OptiSchedule UMB")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff; background: transparent;")
        
        sub = QLabel("Sistema de Planificación y Asignación de Horarios")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 11px; color: #f1f5f9; background: transparent;")
        
        h_layout.addWidget(title)
        h_layout.addWidget(sub)
        card_layout.addWidget(header_banner)

        # Welcome text
        welcome = QLabel("Inicio de Sesión")
        welcome.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a; margin-top: 5px;")
        card_layout.addWidget(welcome)

        # Form Inputs
        card_layout.addWidget(QLabel("<b>Nombre de Usuario:</b>"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ej: admin, docente1, estudiante1")
        self.username_input.setStyleSheet("color: #0f172a; background-color: #ffffff; font-size: 14px; padding: 10px;")
        card_layout.addWidget(self.username_input)

        card_layout.addWidget(QLabel("<b>Contraseña:</b>"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Ingrese su contraseña (default: 123)")
        self.password_input.setStyleSheet("color: #0f172a; background-color: #ffffff; font-size: 14px; padding: 10px;")
        self.password_input.returnPressed.connect(self.handle_login)
        card_layout.addWidget(self.password_input)

        # Login button
        self.login_btn = QPushButton("🚀 INGRESAR AL SISTEMA")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e3a8a;
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
                padding: 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        card_layout.addWidget(self.login_btn)

        # Demo Quick-Login Group
        demo_group = QGroupBox("⚡ Accesos Rápidos para Sustentación / Semillero")
        demo_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                color: #475569;
                margin-top: 15px;
                padding: 12px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: #f8fafc;
            }
        """)
        demo_layout = QVBoxLayout(demo_group)
        demo_layout.setSpacing(8)

        btn_admin = QPushButton("🏛️ Ingresar como Universidad (Admin)")
        btn_admin.setCursor(Qt.PointingHandCursor)
        btn_admin.setStyleSheet("background-color: #dbeafe; color: #1e40af; border: 1px solid #93c5fd; text-align: left; padding: 8px 12px; font-weight: bold;")
        btn_admin.clicked.connect(lambda: self.quick_login("admin", "123"))
        demo_layout.addWidget(btn_admin)

        btn_teacher = QPushButton("👨‍🏫 Ingresar como Docente (Docente 1)")
        btn_teacher.setCursor(Qt.PointingHandCursor)
        btn_teacher.setStyleSheet("background-color: #d1fae5; color: #065f46; border: 1px solid #6ee7b7; text-align: left; padding: 8px 12px; font-weight: bold;")
        btn_teacher.clicked.connect(lambda: self.quick_login("docente1", "123"))
        demo_layout.addWidget(btn_teacher)

        btn_student = QPushButton("🎓 Ingresar como Estudiante (Estudiante 1)")
        btn_student.setCursor(Qt.PointingHandCursor)
        btn_student.setStyleSheet("background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; text-align: left; padding: 8px 12px; font-weight: bold;")
        btn_student.clicked.connect(lambda: self.quick_login("estudiante1", "123"))
        demo_layout.addWidget(btn_student)

        card_layout.addWidget(demo_group)

        main_layout.addWidget(card)

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
                f"No se pudo iniciar sesión con el usuario '{username}'.\n\nVerifica las credenciales o usa los botones de acceso rápido de demostración."
            )

    def quick_login(self, username, password):
        self.username_input.setText(username)
        self.password_input.setText(password)
        self.handle_login()

    def clear_fields(self):
        self.username_input.clear()
        self.password_input.clear()
        self.username_input.setFocus()
