from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QPushButton, QProgressBar, QHeaderView, QFrame
)
from PySide6.QtCore import Qt
from app.database.database import get_db
from app.database.models import Teacher, ScheduleAssignment, Config, TeacherType
from app.auth.session import session

class WorkloadView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        title_layout = QVBoxLayout()
        title = QLabel("Gestión y Monitoreo de Sobrecarga Docente")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e3a8a;")
        subtitle = QLabel("Control de horas asignadas vs. topes contractuales (Tiempo Completo, Medio Tiempo, Cátedra)")
        subtitle.setStyleSheet("font-size: 13px; color: #6b7280;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)

        refresh_btn = QPushButton("🔄 Actualizar Datos")
        refresh_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
        refresh_btn.clicked.connect(self.load_data)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Summary KPIs
        self.kpi_layout = QHBoxLayout()
        self.total_teachers_lbl = self.create_kpi_card("Total Docentes", "0", "#3b82f6")
        self.overload_lbl = self.create_kpi_card("Docentes con Sobrecarga", "0", "#ef4444")
        self.optimal_lbl = self.create_kpi_card("Docentes con Carga Óptima", "0", "#10b981")
        self.underload_lbl = self.create_kpi_card("Docentes con Subcarga", "0", "#f59e0b")

        layout.addLayout(self.kpi_layout)

        # Table
        self.table = QTableWidget()
        self.headers = ["ID", "Docente", "Tipo Contrato", "Horas Asignadas", "Tope Horas", "Ocupación (%)", "Estado Carga Laboral"]
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e5e7eb;
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #f3f4f6;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #e5e7eb;
            }
        """)
        layout.addWidget(self.table)

        self.load_data()

    def create_kpi_card(self, title, default_val, color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border-left: 5px solid {color};
                border-radius: 6px;
                padding: 10px;
                border-top: 1px solid #e5e7eb;
                border-right: 1px solid #e5e7eb;
                border-bottom: 1px solid #e5e7eb;
            }}
        """)
        l = QVBoxLayout(frame)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 11px; color: #6b7280; font-weight: bold;")
        v_lbl = QLabel(default_val)
        v_lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
        l.addWidget(t_lbl)
        l.addWidget(v_lbl)
        self.kpi_layout.addWidget(frame)
        return v_lbl

    def load_data(self):
        db = next(get_db())
        teachers = db.query(Teacher).all()
        config = db.query(Config).first()

        full_time_max = config.full_time_hours if config else 40
        part_time_max = config.part_time_hours if config else 20
        catedra_max = config.catedra_hours if config else 16

        # Filter if logged in as teacher
        if session.teacher_id:
            teachers = [t for t in teachers if t.id == session.teacher_id]

        total_count = len(teachers)
        overload_count = 0
        optimal_count = 0
        underload_count = 0

        self.table.setRowCount(len(teachers))

        for row_idx, teacher in enumerate(teachers):
            # Calculate assigned hours (each assignment = 2 hours)
            assigned_count = len(teacher.assignments)
            assigned_hours = assigned_count * 2

            if teacher.teacher_type == TeacherType.FULL_TIME:
                max_hours = full_time_max
            elif teacher.teacher_type == TeacherType.PART_TIME:
                max_hours = part_time_max
            else:
                max_hours = catedra_max

            pct = int((assigned_hours / max_hours) * 100) if max_hours > 0 else 0

            # State & coloring
            if assigned_hours > max_hours:
                state_text = f"⚠️ SOBRECARGA (+{assigned_hours - max_hours}h)"
                state_color = "#ef4444"
                overload_count += 1
            elif pct >= 80:
                state_text = "✅ ÓPTIMO"
                state_color = "#10b981"
                optimal_count += 1
            else:
                state_text = f"⚡ SUBCARGA ({max_hours - assigned_hours}h disp.)"
                state_color = "#f59e0b"
                underload_count += 1

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(teacher.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(teacher.name))
            self.table.setItem(row_idx, 2, QTableWidgetItem(teacher.teacher_type.value))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{assigned_hours} hrs"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{max_hours} hrs"))

            # Progress Bar for occupation
            pbar = QProgressBar()
            pbar.setValue(min(100, pct))
            pbar.setAlignment(Qt.AlignCenter)
            pbar.setFormat(f"{pct}%")
            if assigned_hours > max_hours:
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #ef4444; }")
            elif pct >= 80:
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #10b981; }")
            else:
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #f59e0b; }")
            self.table.setCellWidget(row_idx, 5, pbar)

            state_item = QTableWidgetItem(state_text)
            state_item.setForeground(Qt.white)
            state_item.setBackground(Qt.red if "SOBRECARGA" in state_text else (Qt.darkGreen if "ÓPTIMO" in state_text else Qt.darkYellow))
            self.table.setItem(row_idx, 6, state_item)

        self.total_teachers_lbl.setText(str(total_count))
        self.overload_lbl.setText(str(overload_count))
        self.optimal_lbl.setText(str(optimal_count))
        self.underload_lbl.setText(str(underload_count))
