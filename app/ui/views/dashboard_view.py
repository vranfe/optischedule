from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QPushButton, QGridLayout
)
from PySide6.QtCore import Qt
from app.database.database import get_db
from app.database.models import Student, Teacher, Subject, Room, Group, ScheduleAssignment

class DashboardView(QWidget):
    def __init__(self, nav_callback=None):
        super().__init__()
        self.nav_callback = nav_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title_layout = QVBoxLayout()
        title = QLabel("Panel de Control - Universidad Manuela Beltrán")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e3a8a;")
        subtitle = QLabel("Monitoreo global de recursos académicos y estado del motor de optimización")
        subtitle.setStyleSheet("font-size: 13px; color: #6b7280;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)

        refresh_btn = QPushButton("🔄 Refrescar Métricas")
        refresh_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
        refresh_btn.clicked.connect(self.load_stats)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # KPI Grid
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(15)

        self.kpi_students = self.create_stat_card("Estudiantes Registrados", "0", "#3b82f6")
        self.kpi_teachers = self.create_stat_card("Docentes Contratados", "0", "#10b981")
        self.kpi_subjects = self.create_stat_card("Asignaturas Malla", "0", "#8b5cf6")
        self.kpi_rooms = self.create_stat_card("Aulas y Laboratorios", "0", "#f59e0b")
        self.kpi_groups = self.create_stat_card("Grupos Abiertos", "0", "#06b6d4")
        self.kpi_assignments = self.create_stat_card("Clases Programadas", "0", "#ec4899")

        kpi_grid.addWidget(self.kpi_students, 0, 0)
        kpi_grid.addWidget(self.kpi_teachers, 0, 1)
        kpi_grid.addWidget(self.kpi_subjects, 0, 2)
        kpi_grid.addWidget(self.kpi_rooms, 1, 0)
        kpi_grid.addWidget(self.kpi_groups, 1, 1)
        kpi_grid.addWidget(self.kpi_assignments, 1, 2)

        layout.addLayout(kpi_grid)

        # Quick Actions Card
        actions_card = QFrame()
        actions_card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px;")
        actions_layout = QVBoxLayout(actions_card)
        
        act_title = QLabel("Acciones Rápidas del Administrador")
        act_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1e293b; margin-bottom: 10px;")
        actions_layout.addWidget(act_title)

        btns_layout = QHBoxLayout()
        
        btn_gen = QPushButton("⚡ Generar Nuevo Horario")
        btn_gen.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        if self.nav_callback:
            btn_gen.clicked.connect(lambda: self.nav_callback("Horario Institucional"))
        btns_layout.addWidget(btn_gen)

        btn_workload = QPushButton("📊 Revisar Sobrecarga Docente")
        btn_workload.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        if self.nav_callback:
            btn_workload.clicked.connect(lambda: self.nav_callback("Sobrecarga Docente"))
        btns_layout.addWidget(btn_workload)

        btn_rules = QPushButton("⚙️ Ajustar Reglas y Restricciones")
        btn_rules.setStyleSheet("background-color: #4f46e5; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        if self.nav_callback:
            btn_rules.clicked.connect(lambda: self.nav_callback("Reglas y Restricciones"))
        btns_layout.addWidget(btn_rules)

        actions_layout.addLayout(btns_layout)
        layout.addWidget(actions_card)

        layout.addStretch()
        self.load_stats()

    def create_stat_card(self, title, default_val, color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border-top: 4px solid {color};
                border-radius: 8px;
                padding: 15px;
                border-left: 1px solid #e2e8f0;
                border-right: 1px solid #e2e8f0;
                border-bottom: 1px solid #e2e8f0;
            }}
        """)
        l = QVBoxLayout(frame)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 12px; color: #64748b; font-weight: bold;")
        v_lbl = QLabel(default_val)
        v_lbl.setStyleSheet(f"font-size: 26px; font-weight: bold; color: #0f172a;")
        l.addWidget(t_lbl)
        l.addWidget(v_lbl)
        frame.val_label = v_lbl
        return frame

    def load_stats(self):
        db = next(get_db())
        try:
            self.kpi_students.val_label.setText(str(db.query(Student).count()))
            self.kpi_teachers.val_label.setText(str(db.query(Teacher).count()))
            self.kpi_subjects.val_label.setText(str(db.query(Subject).count()))
            self.kpi_rooms.val_label.setText(str(db.query(Room).count()))
            self.kpi_groups.val_label.setText(str(db.query(Group).count()))
            self.kpi_assignments.val_label.setText(str(db.query(ScheduleAssignment).count()))
        finally:
            db.close()
