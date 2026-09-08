from PySide6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget, QStackedWidget, 
    QListWidget, QHBoxLayout, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from app.auth.session import session
from app.auth.auth_service import AuthService
from app.database.database import SessionLocal
from app.database.models import UserRole, Student, Teacher, Subject, Room, Group, TeacherType
from app.ui.views.login_view import LoginView
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.workload_view import WorkloadView
from app.ui.views.rules_view import RulesView
from app.ui.views.preferences_view import PreferencesView
from app.ui.views.solution_comparison_view import SolutionComparisonView
from app.ui.views.teacher_schedule_view import TeacherScheduleView
from app.ui.views.student_schedule_view import StudentScheduleView
from app.ui.views.student_preferences_view import StudentPreferencesView
from app.ui.schedule_view import ScheduleView
from app.ui.results_view import ResultsView
from app.ui.generic_table_view import GenericTableView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OptiSchedule UMB - Sistema de Optimización y Asignación de Horarios")
        self.resize(1280, 840)
        self.setStyleSheet("font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', -apple-system, sans-serif;")
        
        self.root_stack = QStackedWidget()
        self.setCentralWidget(self.root_stack)

        # Page 0: Login View
        self.login_view = LoginView()
        self.login_view.login_successful.connect(self.on_login_success)
        self.root_stack.addWidget(self.login_view)

        # Page 1: Main Application Container
        self.app_container = QWidget()
        self.app_layout = QHBoxLayout(self.app_container)
        self.app_layout.setContentsMargins(0, 0, 0, 0)
        self.app_layout.setSpacing(0)

        # Sidebar Panel
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border-right: 1px solid #1e293b;
            }
            QLabel {
                color: #f8fafc;
            }
            QListWidget {
                background-color: transparent;
                border: none;
                color: #94a3b8;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 14px;
                border-radius: 8px;
                margin: 2px 6px;
                font-weight: 600;
            }
            QListWidget::item:selected {
                background-color: #4f46e5;
                color: #ffffff;
                font-weight: 800;
            }
            QListWidget::item:hover:!selected {
                background-color: #1e293b;
                color: #f8fafc;
            }
        """)
        
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(12, 18, 12, 18)
        self.sidebar_layout.setSpacing(12)

        # App Brand in Sidebar
        brand_box = QVBoxLayout()
        brand_box.setSpacing(2)
        
        brand_label = QLabel("OptiSchedule")
        brand_label.setStyleSheet("font-size: 20px; font-weight: 800; color: #818cf8; letter-spacing: -0.4px;")
        
        brand_sub = QLabel("Universidad Manuela Beltrán")
        brand_sub.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; margin-bottom: 6px;")
        
        brand_box.addWidget(brand_label)
        brand_box.addWidget(brand_sub)
        self.sidebar_layout.addLayout(brand_box)

        # User profile box
        self.profile_box = QFrame()
        self.profile_box.setStyleSheet("""
            QFrame {
                background-color: #1e293b; 
                border: 1px solid #334155; 
                border-radius: 10px; 
                padding: 10px 12px;
            }
        """)
        profile_layout = QVBoxLayout(self.profile_box)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(3)
        
        self.user_lbl = QLabel("Usuario: -")
        self.user_lbl.setStyleSheet("font-size: 13px; font-weight: 800; color: #ffffff;")
        
        self.role_lbl = QLabel("Rol: -")
        self.role_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #38bdf8;")
        
        self.detail_lbl = QLabel("")
        self.detail_lbl.setStyleSheet("font-size: 10px; color: #a5b4fc;")
        self.detail_lbl.setVisible(False)

        profile_layout.addWidget(self.user_lbl)
        profile_layout.addWidget(self.role_lbl)
        profile_layout.addWidget(self.detail_lbl)
        self.sidebar_layout.addWidget(self.profile_box)

        # Navigation menu
        self.menu_list = QListWidget()
        self.sidebar_layout.addWidget(self.menu_list)

        # Logout button (Visible & Stylized across all roles)
        self.logout_btn = QPushButton("🚪 Cerrar Sesión")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #f43f5e;
                color: #ffffff;
                font-weight: 800;
                font-size: 13px;
                padding: 10px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e11d48;
            }
            QPushButton:pressed {
                background-color: #be123c;
            }
        """)
        self.logout_btn.clicked.connect(self.logout)
        self.sidebar_layout.addWidget(self.logout_btn)

        # Main content area
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #f8fafc; padding: 15px;")

        self.app_layout.addWidget(self.sidebar)
        self.app_layout.addWidget(self.content_stack)

        self.root_stack.addWidget(self.app_container)

        self.menu_list.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        
        # Start at login screen
        self.root_stack.setCurrentIndex(0)

    def on_login_success(self, user):
        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        self.user_lbl.setText(f"👤 {user.username}")
        self.role_lbl.setText(f"🛡️ {role_str}")

        # Extra context info
        if user.role == UserRole.STUDENT and user.student:
            is_reg = getattr(user.student, "is_regular", True)
            reg_text = "Nivelado" if is_reg else "No Nivelado"
            self.detail_lbl.setText(f"Sem {user.student.semester_id} • {reg_text}")
            self.detail_lbl.setVisible(True)
        elif user.role == UserRole.TEACHER and user.teacher:
            t_type = user.teacher.teacher_type.value if user.teacher.teacher_type else "Docente"
            self.detail_lbl.setText(f"{t_type}")
            self.detail_lbl.setVisible(True)
        else:
            self.detail_lbl.setVisible(False)

        self.setup_role_navigation(user.role)
        self.root_stack.setCurrentIndex(1)

    def navigate_to(self, menu_title):
        for i in range(self.menu_list.count()):
            if menu_title.lower() in self.menu_list.item(i).text().lower():
                self.menu_list.setCurrentRow(i)
                break

    def _clear_content(self):
        """Safely remove and delete all previous content widgets."""
        while self.content_stack.count() > 0:
            widget = self.content_stack.widget(0)
            self.content_stack.removeWidget(widget)
            if widget is not None:
                widget.deleteLater()

    def setup_role_navigation(self, role):
        # Block signals to avoid cascade event with row -1 during rebuild
        self.menu_list.blockSignals(True)
        try:
            self.menu_list.clear()
            self._clear_content()

            if role == UserRole.ADMIN:
                # Views for Universidad / Admin
                views = [
                    ("📊 Dashboard General", DashboardView(nav_callback=self.navigate_to)),
                    ("⚡ Horario Institucional", ScheduleView()),
                    ("⚖️ Comparar Soluciones", SolutionComparisonView()),
                    ("📈 Carga y Subcarga Docente", WorkloadView()),
                    ("⚙️ Reglas y Calendario", RulesView()),
                    ("📝 Preferencias Docentes", PreferencesView()),
                    ("🎯 Evaluación y Métricas", ResultsView()),
                    ("🎓 Estudiantes (CRUD)", GenericTableView(
                        "Estudiantes", ["ID", "Nombre", "Semestre", "Nivelado", "Inscrito", "Acuerdo Pago"],
                        Student, ["id", "name", "semester_id", "is_regular", "is_enrolled", "has_payment_agreement"]
                    )),
                    ("👨‍🏫 Docentes (CRUD)", GenericTableView(
                        "Docentes", ["ID", "Nombre", "Tipo Contrato"],
                        Teacher, ["id", "name", "teacher_type"],
                        enum_mappings={"teacher_type": TeacherType}
                    )),
                    ("📚 Asignaturas (CRUD)", GenericTableView(
                        "Asignaturas", ["ID", "Nombre", "Horas Semanales", "Semestre"],
                        Subject, ["id", "name", "hours_per_week", "semester_id"]
                    )),
                    ("👥 Grupos (CRUD)", GenericTableView(
                        "Grupos", ["ID", "Nombre", "ID Asignatura", "Estudiantes Estimados"],
                        Group, ["id", "name", "subject_id", "expected_students"]
                    )),
                    ("📍 Aulas (CRUD)", GenericTableView(
                        "Aulas", ["ID", "Nombre", "Capacidad", "Tipo Aula"],
                        Room, ["id", "name", "capacity", "room_type"]
                    ))
                ]

            elif role == UserRole.TEACHER:
                # Views for Docente
                views = [
                    ("📅 Mi Horario Asignado", TeacherScheduleView()),
                    ("📝 Disponibilidad y Afinidad", PreferencesView()),
                    ("📈 Mi Carga Laboral", WorkloadView())
                ]

            elif role == UserRole.STUDENT:
                # Views for Estudiante
                views = [
                    ("📅 Mi Horario Semestral", StudentScheduleView()),
                    ("☀️ Preferencia de Jornada", StudentPreferencesView())
                ]

            else:
                views = []

            for title, widget in views:
                self.menu_list.addItem(title)
                self.content_stack.addWidget(widget)

            if views:
                self.menu_list.setCurrentRow(0)
                self.content_stack.setCurrentIndex(0)
        finally:
            self.menu_list.blockSignals(False)

    def logout(self):
        AuthService.logout()
        self.menu_list.blockSignals(True)
        try:
            self.menu_list.clear()
            self._clear_content()
        finally:
            self.menu_list.blockSignals(False)
        self.user_lbl.setText("Usuario: -")
        self.role_lbl.setText("Rol: -")
        self.detail_lbl.setText("")
        self.detail_lbl.setVisible(False)
        self.login_view.clear_fields()
        self.root_stack.setCurrentIndex(0)
