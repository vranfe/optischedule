from PySide6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget, QStackedWidget, 
    QListWidget, QHBoxLayout, QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from app.auth.session import session
from app.auth.auth_service import AuthService
from app.database.database import SessionLocal
from app.database.models import UserRole, Student, Teacher, Subject, Room, Group, TeacherType, Config, KnowledgeArea
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
from app.ui.generic_table_view import GenericTableView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OptiSchedule UMB - Sistema de Optimización y Asignación de Horarios")
        self.resize(1320, 860)
        self.setStyleSheet("font-family: 'Plus Jakarta Sans', 'Inter', 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;")
        
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

        # -------------------------------------------------------------
        # Sidebar Panel
        # -------------------------------------------------------------
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet("""
            QFrame#sidebar_frame {
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
                padding: 11px 14px;
                border-radius: 10px;
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
        self.sidebar.setObjectName("sidebar_frame")
        
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(14, 20, 14, 20)
        self.sidebar_layout.setSpacing(12)

        # App Brand in Sidebar
        brand_box = QVBoxLayout()
        brand_box.setSpacing(3)
        
        brand_label = QLabel("OptiSchedule UMB")
        brand_label.setStyleSheet("font-size: 20px; font-weight: 800; color: #818cf8; letter-spacing: -0.5px;")
        
        brand_sub = QLabel("Universidad Manuela Beltrán")
        brand_sub.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; margin-bottom: 4px;")
        
        brand_box.addWidget(brand_label)
        brand_box.addWidget(brand_sub)
        self.sidebar_layout.addLayout(brand_box)

        # User profile box in Sidebar
        self.profile_box = QFrame()
        self.profile_box.setStyleSheet("""
            QFrame {
                background-color: #1e293b; 
                border: 1px solid #334155; 
                border-radius: 12px; 
                padding: 12px 14px;
            }
        """)
        profile_layout = QVBoxLayout(self.profile_box)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        profile_layout.setSpacing(4)
        
        self.user_lbl = QLabel("Usuario: -")
        self.user_lbl.setStyleSheet("font-size: 13px; font-weight: 800; color: #ffffff;")
        
        self.role_lbl = QLabel("Rol: -")
        self.role_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #38bdf8;")
        
        self.detail_lbl = QLabel("")
        self.detail_lbl.setStyleSheet("font-size: 10px; color: #a5b4fc; font-weight: 600;")
        self.detail_lbl.setVisible(False)

        profile_layout.addWidget(self.user_lbl)
        profile_layout.addWidget(self.role_lbl)
        profile_layout.addWidget(self.detail_lbl)
        self.sidebar_layout.addWidget(self.profile_box)

        # Navigation menu
        self.menu_list = QListWidget()
        self.sidebar_layout.addWidget(self.menu_list, 1)

        # -------------------------------------------------------------
        # Main Area: Top Navbar + Content Stack (Animated)
        # -------------------------------------------------------------
        self.main_content_container = QWidget()
        self.main_content_layout = QVBoxLayout(self.main_content_container)
        self.main_content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_content_layout.setSpacing(0)

        # Top Navbar (Persistent Header)
        self.top_navbar = QFrame()
        self.top_navbar.setFixedHeight(62)
        self.top_navbar.setStyleSheet("""
            QFrame#top_navbar {
                background-color: #ffffff;
                border-bottom: 1.5px solid #e2e8f0;
                padding: 0px 20px;
            }
        """)
        self.top_navbar.setObjectName("top_navbar")
        nav_layout = QHBoxLayout(self.top_navbar)
        nav_layout.setContentsMargins(20, 0, 20, 0)

        # Left: Current section & Institutional tag
        self.section_lbl = QLabel("🏫 Portal de Gestión de Horarios")
        self.section_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #1e3a8a;")
        nav_layout.addWidget(self.section_lbl)

        nav_layout.addStretch()

        # Middle: Institutional Academic Date Pill
        self.date_badge = QLabel("📅 Calendario Institucional: 2026-2")
        self.date_badge.setStyleSheet("""
            background-color: #ecfdf5; 
            color: #065f46; 
            font-size: 12px; 
            font-weight: 700; 
            padding: 6px 14px; 
            border-radius: 8px; 
            border: 1px solid #a7f3d0;
        """)
        nav_layout.addWidget(self.date_badge)

        # Right: User profile chip + Direct Top Logout button
        self.user_chip = QLabel("👤 Sesión Activa")
        self.user_chip.setStyleSheet("""
            background-color: #f1f5f9; 
            color: #334155; 
            font-size: 12px; 
            font-weight: 700; 
            padding: 6px 12px; 
            border-radius: 8px; 
            border: 1px solid #e2e8f0; 
            margin-left: 10px;
        """)
        nav_layout.addWidget(self.user_chip)

        self.top_logout_btn = QPushButton("🚪 Cerrar Sesión")
        self.top_logout_btn.setCursor(Qt.PointingHandCursor)
        self.top_logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #fff1f2;
                color: #be123c;
                font-weight: 800;
                font-size: 12px;
                padding: 7px 14px;
                border-radius: 8px;
                border: 1.5px solid #fecdd3;
                margin-left: 8px;
            }
            QPushButton:hover {
                background-color: #ffe4e6;
                color: #9f1239;
            }
        """)
        self.top_logout_btn.clicked.connect(self.logout)
        nav_layout.addWidget(self.top_logout_btn)

        self.main_content_layout.addWidget(self.top_navbar)

        # Main Content Stack
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #f8fafc; padding: 0px;")
        self.main_content_layout.addWidget(self.content_stack)

        self.app_layout.addWidget(self.sidebar)
        self.app_layout.addWidget(self.main_content_container)

        self.root_stack.addWidget(self.app_container)

        self.menu_list.currentRowChanged.connect(self.on_menu_selection_changed)
        
        # Start at login screen
        self.root_stack.setCurrentIndex(0)

    def on_menu_selection_changed(self, row):
        if row < 0 or row >= self.menu_list.count():
            return
        item_text = self.menu_list.item(row).text()
        if "cerrar sesión" in item_text.lower():
            self.logout()
            return
        
        self.section_lbl.setText(f"🏫 {item_text}")
        self.content_stack.setCurrentIndex(row)

    def on_login_success(self, user):
        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        self.user_lbl.setText(f"👤 {user.username}")
        self.role_lbl.setText(f"🛡️ {role_str}")
        self.user_chip.setText(f"👤 {user.username} ({role_str})")

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

        # Refresh institutional date pill
        db = SessionLocal()
        try:
            cfg = db.query(Config).first()
            sys_date = getattr(cfg, "system_current_date", "2026-09-08") if cfg else "2026-09-08"
            self.date_badge.setText(f"📅 Fecha Institucional: {sys_date} | Período 2026-2")
        finally:
            db.close()

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
        self.menu_list.blockSignals(True)
        try:
            self.menu_list.clear()
            self._clear_content()

            if role == UserRole.ADMIN:
                dashboard_view = DashboardView(nav_callback=self.navigate_to)
                schedule_view = ScheduleView(nav_callback=self.navigate_to)
                comparison_view = SolutionComparisonView()

                # Live signal connection: applying a solution updates schedule and dashboard in real time
                comparison_view.solution_applied.connect(schedule_view.load_schedule)
                comparison_view.solution_applied.connect(dashboard_view.load_stats)

                views = [
                    ("📊 Dashboard General", dashboard_view),
                    ("⚡ Horario Institucional", schedule_view),
                    ("⚖️ Comparar Soluciones", comparison_view),
                    ("📈 Carga y Subcarga Docente", WorkloadView()),
                    ("⚙️ Reglas y Calendario", RulesView()),
                    ("📝 Preferencias Docentes", PreferencesView()),
                    ("🎓 Estudiantes (CRUD)", GenericTableView(
                        "Estudiantes", 
                        ["ID Estudiante", "Nombre Completo", "Semestre", "Nivelación", "Estado Matrícula", "Acuerdo de Pago"],
                        Student, ["id", "name", "semester_id", "is_regular", "is_enrolled", "has_payment_agreement"]
                    )),
                    ("👨‍🏫 Docentes (CRUD)", GenericTableView(
                        "Docentes", 
                        ["ID Docente", "Nombre Docente", "Modalidad Contractual", "Área de Conocimiento"],
                        Teacher, ["id", "name", "teacher_type", "knowledge_area"],
                        enum_mappings={"teacher_type": TeacherType, "knowledge_area": KnowledgeArea}
                    )),
                    ("📚 Asignaturas (CRUD)", GenericTableView(
                        "Asignaturas", 
                        ["ID Asignatura", "Nombre de la Materia", "Créditos", "Horas Semanales", "Semestre Malla", "Área Académica"],
                        Subject, ["id", "name", "credits", "hours_per_week", "semester_id", "knowledge_area"],
                        enum_mappings={"knowledge_area": KnowledgeArea}
                    )),
                    ("👥 Grupos (CRUD)", GenericTableView(
                        "Grupos", 
                        ["ID", "Código de Grupo", "Asignatura", "ID Materia", "Capacidad Aula", "Inscritos Reales", "Disponibilidad"],
                        Group, 
                        ["id", "name", "subject_name", "subject_id", "max_capacity", "enrolled_count", "availability_status"],
                        read_only_keys=["id", "subject_name", "max_capacity", "enrolled_count", "availability_status"]
                    )),
                    ("📍 Aulas (CRUD)", GenericTableView(
                        "Aulas", 
                        ["ID Aula", "Nombre / Número", "Capacidad Máxima", "Tipo de Espacio"],
                        Room, ["id", "name", "capacity", "room_type"]
                    ))
                ]

            elif role == UserRole.TEACHER:
                views = [
                    ("📅 Mi Horario Asignado", TeacherScheduleView()),
                    ("📝 Disponibilidad y Afinidad", PreferencesView()),
                    ("📈 Mi Carga Laboral", WorkloadView())
                ]

            elif role == UserRole.STUDENT:
                views = [
                    ("📅 Mi Horario Semestral", StudentScheduleView()),
                    ("☀️ Preferencia de Jornada", StudentPreferencesView())
                ]

            else:
                views = []

            for title, widget in views:
                self.menu_list.addItem(title)
                if isinstance(widget, (RulesView, PreferencesView, StudentPreferencesView, TeacherScheduleView, SolutionComparisonView, ScheduleView)):
                    scroll = QScrollArea()
                    scroll.setWidgetResizable(True)
                    scroll.setFrameShape(QFrame.NoFrame)
                    scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
                    scroll.setWidget(widget)
                    self.content_stack.addWidget(scroll)
                else:
                    self.content_stack.addWidget(widget)

            if views:
                self.menu_list.setCurrentRow(0)
                self.content_stack.setCurrentIndex(0)
                self.section_lbl.setText(f"🏫 {views[0][0]}")
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
