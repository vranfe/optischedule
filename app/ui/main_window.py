from PySide6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget, QStackedWidget, 
    QListWidget, QHBoxLayout, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from app.auth.session import session
from app.auth.auth_service import AuthService
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
        self.resize(1200, 800)
        self.setStyleSheet("font-family: 'Segoe UI', Arial, sans-serif;")
        
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

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-right: 1px solid #334155;
            }
            QLabel {
                color: #f8fafc;
            }
            QListWidget {
                background-color: transparent;
                border: none;
                color: #cbd5e1;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 15px;
                border-radius: 6px;
                margin: 2px 8px;
            }
            QListWidget::item:selected {
                background-color: #3b82f6;
                color: #ffffff;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background-color: #334155;
                color: #ffffff;
            }
        """)
        
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 15, 10, 15)

        # App Brand in Sidebar
        brand_label = QLabel("OptiSchedule")
        brand_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #60a5fa;")
        brand_sub = QLabel("UMB - Semillero")
        brand_sub.setStyleSheet("font-size: 11px; color: #94a3b8; margin-bottom: 10px;")
        self.sidebar_layout.addWidget(brand_label)
        self.sidebar_layout.addWidget(brand_sub)

        # User profile box
        self.profile_box = QFrame()
        self.profile_box.setStyleSheet("background-color: #0f172a; border-radius: 6px; padding: 10px; margin-bottom: 10px;")
        profile_layout = QVBoxLayout(self.profile_box)
        profile_layout.setContentsMargins(5, 5, 5, 5)
        
        self.user_lbl = QLabel("Usuario: -")
        self.user_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #f1f5f9;")
        self.role_lbl = QLabel("Rol: -")
        self.role_lbl.setStyleSheet("font-size: 11px; color: #38bdf8;")
        profile_layout.addWidget(self.user_lbl)
        profile_layout.addWidget(self.role_lbl)
        self.sidebar_layout.addWidget(self.profile_box)

        # Navigation menu
        self.menu_list = QListWidget()
        self.sidebar_layout.addWidget(self.menu_list)

        # Logout button
        self.logout_btn = QPushButton("🚪 Cerrar Sesión")
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
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

        self.setup_role_navigation(user.role)
        self.root_stack.setCurrentIndex(1)

    def navigate_to(self, menu_title):
        for i in range(self.menu_list.count()):
            if menu_title.lower() in self.menu_list.item(i).text().lower():
                self.menu_list.setCurrentRow(i)
                break

    def setup_role_navigation(self, role):
        # Clear existing views and menu items
        self.menu_list.clear()
        while self.content_stack.count() > 0:
            widget = self.content_stack.widget(0)
            self.content_stack.removeWidget(widget)

        if role == UserRole.ADMIN:
            # Views for Universidad / Admin
            views = [
                ("📊 Dashboard General", DashboardView(nav_callback=self.navigate_to)),
                ("⚡ Generar Horario", ScheduleView()),
                ("📅 Horario Institucional", ScheduleView()),
                ("⚖️ Comparar Soluciones", SolutionComparisonView()),
                ("📈 Sobrecarga Docente", WorkloadView()),
                ("⚙️ Reglas y Restricciones", RulesView()),
                ("📝 Preferencias Docentes", PreferencesView()),
                ("🎯 Evaluación y Métricas", ResultsView()),
                ("🎓 Estudiantes (CRUD)", GenericTableView(
                    "Estudiantes", ["ID", "Nombre", "Semestre", "Inscrito", "Acuerdo Pago"],
                    Student, ["id", "name", "semester_id", "is_enrolled", "has_payment_agreement"]
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

    def logout(self):
        AuthService.logout()
        self.root_stack.setCurrentIndex(0)


