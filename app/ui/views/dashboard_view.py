from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QPushButton, QGridLayout
)
from PySide6.QtCore import Qt
from app.database.database import SessionLocal
from app.database.models import Student, Teacher, Subject, Room, Group, ScheduleAssignment, Config

class DashboardView(QWidget):
    def __init__(self, nav_callback=None):
        super().__init__()
        self.nav_callback = nav_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 14px 18px;
            }
        """)
        header = QHBoxLayout(header_card)

        title_layout = QVBoxLayout()
        title = QLabel("Panel de Control - Universidad Manuela Beltrán")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1e3a8a;")
        subtitle = QLabel("Monitoreo institucional de recursos, matrículas, carga docente y optimización CP-SAT")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)

        refresh_btn = QPushButton("🔄 Refrescar Métricas")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                font-weight: 700;
                padding: 9px 18px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
        """)
        refresh_btn.clicked.connect(self.load_stats)
        header.addWidget(refresh_btn)

        layout.addWidget(header_card)

        # KPI Grid
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(14)

        self.kpi_students = self.create_stat_card("Estudiantes Registrados", "0", "#6366f1", "#eef2ff", "🎓")
        self.kpi_teachers = self.create_stat_card("Docentes Contratados", "0", "#10b981", "#ecfdf5", "👨‍🏫")
        self.kpi_subjects = self.create_stat_card("Asignaturas Malla", "0", "#8b5cf6", "#f5f3ff", "📚")
        self.kpi_rooms = self.create_stat_card("Aulas y Laboratorios", "0", "#f59e0b", "#fffbeb", "📍")
        self.kpi_groups = self.create_stat_card("Grupos de Clase", "0", "#06b6d4", "#ecfeff", "👥")
        self.kpi_assignments = self.create_stat_card("Clases Programadas", "0", "#ec4899", "#fdf2f8", "⚡")

        kpi_grid.addWidget(self.kpi_students, 0, 0)
        kpi_grid.addWidget(self.kpi_teachers, 0, 1)
        kpi_grid.addWidget(self.kpi_subjects, 0, 2)
        kpi_grid.addWidget(self.kpi_rooms, 1, 0)
        kpi_grid.addWidget(self.kpi_groups, 1, 1)
        kpi_grid.addWidget(self.kpi_assignments, 1, 2)

        layout.addLayout(kpi_grid)

        # Quick Actions Card
        actions_card = QFrame()
        actions_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px;")
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setSpacing(12)
        
        act_title = QLabel("Acciones Rápidas de Planificación Académica")
        act_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #1e293b;")
        actions_layout.addWidget(act_title)

        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(12)
        
        btn_gen = QPushButton("⚡ Generar Horario Institucional")
        btn_gen.setCursor(Qt.PointingHandCursor)
        btn_gen.setStyleSheet("background-color: #10b981; color: white; font-weight: 800; padding: 12px; border-radius: 8px;")
        if self.nav_callback:
            btn_gen.clicked.connect(lambda: self.nav_callback("Horario Institucional"))
        btns_layout.addWidget(btn_gen)

        btn_alts = QPushButton("⚖️ Comparar Alternativas Multicriterio")
        btn_alts.setCursor(Qt.PointingHandCursor)
        btn_alts.setStyleSheet("background-color: #4f46e5; color: white; font-weight: 800; padding: 12px; border-radius: 8px;")
        if self.nav_callback:
            btn_alts.clicked.connect(lambda: self.nav_callback("Comparar Soluciones"))
        btns_layout.addWidget(btn_alts)

        btn_workload = QPushButton("📊 Monitorear Carga Docente")
        btn_workload.setCursor(Qt.PointingHandCursor)
        btn_workload.setStyleSheet("background-color: #0284c7; color: white; font-weight: 800; padding: 12px; border-radius: 8px;")
        if self.nav_callback:
            btn_workload.clicked.connect(lambda: self.nav_callback("Carga y Subcarga Docente"))
        btns_layout.addWidget(btn_workload)

        btn_rules = QPushButton("📅 Calendario y Reglas")
        btn_rules.setCursor(Qt.PointingHandCursor)
        btn_rules.setStyleSheet("background-color: #f59e0b; color: white; font-weight: 800; padding: 12px; border-radius: 8px;")
        if self.nav_callback:
            btn_rules.clicked.connect(lambda: self.nav_callback("Reglas y Calendario"))
        btns_layout.addWidget(btn_rules)

        actions_layout.addLayout(btns_layout)
        layout.addWidget(actions_card)

        layout.addStretch()
        self.load_stats()

    def create_stat_card(self, title, default_val, text_color, bg_color, icon=""):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 12px;
                padding: 16px;
            }}
            QFrame:hover {{
                border-color: {text_color};
            }}
        """)
        l = QVBoxLayout(frame)
        l.setSpacing(6)

        top_row = QHBoxLayout()
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 700;")
        top_row.addWidget(t_lbl)
        top_row.addStretch()

        icon_frame = QFrame()
        icon_frame.setStyleSheet(f"background-color: {bg_color}; border-radius: 8px; padding: 4px;")
        i_l = QHBoxLayout(icon_frame)
        i_l.setContentsMargins(4, 2, 4, 2)
        i_lbl = QLabel(icon)
        i_lbl.setStyleSheet(f"font-size: 16px; background: transparent;")
        i_l.addWidget(i_lbl)
        top_row.addWidget(icon_frame)
        l.addLayout(top_row)

        v_lbl = QLabel(default_val)
        v_lbl.setStyleSheet(f"font-size: 26px; font-weight: 800; color: #0f172a;")
        l.addWidget(v_lbl)
        frame.val_label = v_lbl
        return frame

    def load_stats(self):
        db = SessionLocal()
        try:
            total_students = db.query(Student).count()
            regular_students = db.query(Student).filter_by(is_regular=True).count()
            self.kpi_students.val_label.setText(f"{total_students} ({regular_students} Nivelados)")
            self.kpi_teachers.val_label.setText(str(db.query(Teacher).count()))
            self.kpi_subjects.val_label.setText(str(db.query(Subject).count()))
            self.kpi_rooms.val_label.setText(str(db.query(Room).count()))
            self.kpi_groups.val_label.setText(str(db.query(Group).count()))
            self.kpi_assignments.val_label.setText(str(db.query(ScheduleAssignment).count()))
        finally:
            db.close()
