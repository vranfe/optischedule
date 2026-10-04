from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QPushButton, QProgressBar, QHeaderView, QFrame,
    QComboBox, QMessageBox
)
from PySide6.QtCore import Qt
from app.database.database import get_db, SessionLocal
from app.database.models import Teacher, ScheduleAssignment, Config, TeacherType
from app.auth.session import session
from app.ui.workers.solver_worker import SolverWorker

class WorkloadView(QWidget):
    def __init__(self):
        super().__init__()
        self.raw_teacher_data = []
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 18px;")
        header = QHBoxLayout(header_card)

        title_layout = QVBoxLayout()
        title = QLabel("Gestión, Nivelación y Monitoreo de Carga Docente")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #1e3a8a;")
        subtitle = QLabel("Control y optimización de Sobrecarga (>100%), Carga Óptima (80-100%) y Subcarga (<80%) según contrato institucional")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 500;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)

        btn_layout = QHBoxLayout()
        
        # Balance Load Button (Admin only)
        if not session.teacher_id:
            self.balance_btn = QPushButton("⚡ Optimizar Balance (Reducir Subcarga)")
            self.balance_btn.setCursor(Qt.PointingHandCursor)
            self.balance_btn.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
            self.balance_btn.clicked.connect(self.run_load_balance_optimization)
            btn_layout.addWidget(self.balance_btn)

        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
        refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(refresh_btn)

        header.addLayout(btn_layout)
        layout.addWidget(header_card)

        # Summary KPIs
        self.kpi_layout = QHBoxLayout()
        self.total_teachers_lbl = self.create_kpi_card("Total Docentes", "0", "#3b82f6", "Plantilla docente")
        self.optimal_lbl = self.create_kpi_card("Carga Óptima (80-100%)", "0", "#10b981", "Eficiencia de nómina")
        self.underload_lbl = self.create_kpi_card("Subcarga (<80%)", "0", "#f59e0b", "Horas ociosas a optimizar")
        self.overload_lbl = self.create_kpi_card("Sobrecarga (>100%)", "0", "#ef4444", "Riesgo de exceso laboral")

        layout.addLayout(self.kpi_layout)

        # Controls row: Filter by load state (Admin only)
        self.filter_container = QWidget(self)
        filter_row = QHBoxLayout(self.filter_container)
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.addWidget(QLabel("<b>Filtrar por Estado de Carga:</b>"))
        
        self.filter_combo = QComboBox(self.filter_container)
        self.filter_combo.addItems([
            "📋 Todos los Docentes", 
            "⚡ Solo Docentes con Subcarga (<80%)", 
            "✅ Solo Carga Óptima (80-100%)", 
            "⚠️ Solo Sobrecarga (>100%)"
        ])
        self.filter_combo.currentIndexChanged.connect(self.apply_filter)
        self.filter_combo.setFixedWidth(280)
        filter_row.addWidget(self.filter_combo)
        filter_row.addStretch()
        layout.addWidget(self.filter_container)

        # Progress & Status Bar
        self.progress_container = QVBoxLayout()
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("font-size: 12px; color: #475569; font-weight: 600;")
        self.status_lbl.setVisible(False)
        
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.pbar.setTextVisible(True)
        self.pbar.setVisible(False)
        self.progress_container.addWidget(self.status_lbl)
        self.progress_container.addWidget(self.pbar)
        layout.addLayout(self.progress_container)

        # Table
        self.table = QTableWidget()
        self.headers = ["ID", "Docente", "Tipo Contrato", "Horas Asignadas", "Tope Horas", "Ocupación (%)", "Estado de Carga Laboral", "Acción Recomendada"]
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.horizontalHeader().setVisible(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #cbd5e1;
                background-color: #ffffff;
                color: #0f172a;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
            }
            QHeaderView {
                background-color: #1e293b;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 8px 12px;
                font-weight: 800;
                font-size: 12px;
                border: none;
                border-right: 1px solid #334155;
                border-bottom: 2px solid #4f46e5;
            }
        """)
        layout.addWidget(self.table)

        self.load_data()

    def create_kpi_card(self, title, default_val, color, hint):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border-left: 6px solid {color};
                border-radius: 8px;
                padding: 10px 14px;
                border-top: 1px solid #e2e8f0;
                border-right: 1px solid #e2e8f0;
                border-bottom: 1px solid #e2e8f0;
            }}
        """)
        l = QVBoxLayout(frame)
        l.setSpacing(2)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 800;")
        v_lbl = QLabel(default_val)
        v_lbl.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {color};")
        h_lbl = QLabel(hint)
        h_lbl.setStyleSheet("font-size: 10px; color: #94a3b8;")
        l.addWidget(t_lbl)
        l.addWidget(v_lbl)
        l.addWidget(h_lbl)
        self.kpi_layout.addWidget(frame)
        return (t_lbl, v_lbl, h_lbl)

    def load_data(self):
        db = next(get_db())
        teachers = db.query(Teacher).all()
        config = db.query(Config).first()

        full_time_max = config.full_time_hours if config else 42
        part_time_max = config.part_time_hours if config else 21
        catedra_max = config.catedra_hours if config else 23

        is_teacher_role = bool(session.teacher_id)
        self.filter_container.setVisible(not is_teacher_role)

        if is_teacher_role:
            teachers = [t for t in teachers if t.id == session.teacher_id]

        self.raw_teacher_data = []
        overload_count = 0
        optimal_count = 0
        underload_count = 0

        for teacher in teachers:
            assigned_count = len(teacher.assignments)
            assigned_hours = assigned_count * 2

            if teacher.teacher_type == TeacherType.FULL_TIME:
                max_hours = full_time_max
            elif teacher.teacher_type == TeacherType.PART_TIME:
                max_hours = part_time_max
            else:
                max_hours = catedra_max

            pct = int((assigned_hours / max_hours) * 100) if max_hours > 0 else 0

            if assigned_hours > max_hours:
                state_type = "OVERLOAD"
                state_text = f"⚠️ SOBRECARGA (+{assigned_hours - max_hours}h)"
                action_text = "Reducir grupos asignados"
                overload_count += 1
            elif pct >= 80:
                state_type = "OPTIMAL"
                state_text = "✅ CARGA ÓPTIMA"
                action_text = "Carga balanceada correctamente"
                optimal_count += 1
            else:
                state_type = "UNDERLOAD"
                state_text = f"⚡ SUBCARGA ({max_hours - assigned_hours}h libres)"
                action_text = "Asignar más grupos / Rebalancear"
                underload_count += 1

            self.raw_teacher_data.append({
                "id": teacher.id,
                "name": teacher.name,
                "type": teacher.teacher_type.value if hasattr(teacher.teacher_type, "value") else str(teacher.teacher_type),
                "assigned": assigned_hours,
                "max": max_hours,
                "pct": pct,
                "state_type": state_type,
                "state_text": state_text,
                "action_text": action_text
            })

        if is_teacher_role and self.raw_teacher_data:
            d = self.raw_teacher_data[0]
            self.total_teachers_lbl[0].setText("Horas Asignadas")
            self.total_teachers_lbl[1].setText(f"{d['assigned']} hrs")
            self.total_teachers_lbl[2].setText("Total semanal asignado")

            self.optimal_lbl[0].setText("Tope Contractual")
            self.optimal_lbl[1].setText(f"{d['max']} hrs")
            self.optimal_lbl[2].setText(f"Modalidad: {d['type']}")

            self.underload_lbl[0].setText("% Cumplimiento")
            self.underload_lbl[1].setText(f"{d['pct']}%")
            self.underload_lbl[2].setText("Ocupación de carga")

            self.overload_lbl[0].setText("Estado de Carga")
            self.overload_lbl[1].setText(d['state_type'])
            self.overload_lbl[2].setText(d['state_text'])
        else:
            self.total_teachers_lbl[0].setText("Total Docentes")
            self.total_teachers_lbl[1].setText(str(len(teachers)))
            self.total_teachers_lbl[2].setText("Plantilla docente")

            self.optimal_lbl[0].setText("Carga Óptima (80-100%)")
            self.optimal_lbl[1].setText(str(optimal_count))
            self.optimal_lbl[2].setText("Eficiencia de nómina")

            self.underload_lbl[0].setText("Subcarga (<80%)")
            self.underload_lbl[1].setText(str(underload_count))
            self.underload_lbl[2].setText("Horas ociosas a optimizar")

            self.overload_lbl[0].setText("Sobrecarga (>100%)")
            self.overload_lbl[1].setText(str(overload_count))
            self.overload_lbl[2].setText("Riesgo de exceso laboral")

        self.apply_filter()

    def apply_filter(self):
        filter_idx = self.filter_combo.currentIndex()
        if filter_idx == 1:
            filtered = [t for t in self.raw_teacher_data if t["state_type"] == "UNDERLOAD"]
        elif filter_idx == 2:
            filtered = [t for t in self.raw_teacher_data if t["state_type"] == "OPTIMAL"]
        elif filter_idx == 3:
            filtered = [t for t in self.raw_teacher_data if t["state_type"] == "OVERLOAD"]
        else:
            filtered = self.raw_teacher_data

        self.table.setRowCount(len(filtered))

        for row_idx, data in enumerate(filtered):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(data["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(data["name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(data["type"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{data['assigned']} hrs"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{data['max']} hrs"))

            # Progress bar
            pbar = QProgressBar()
            pbar.setValue(min(100, data["pct"]))
            pbar.setAlignment(Qt.AlignCenter)
            if data["state_type"] == "OVERLOAD":
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #ef4444; }")
            elif data["state_type"] == "OPTIMAL":
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #10b981; }")
            else:
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #f59e0b; }")
            self.table.setCellWidget(row_idx, 5, pbar)

            state_item = QTableWidgetItem(data["state_text"])
            state_item.setTextAlignment(Qt.AlignCenter)
            state_item.setFont(self.table.font())
            self.table.setItem(row_idx, 6, state_item)

            action_item = QTableWidgetItem(data["action_text"])
            self.table.setItem(row_idx, 7, action_item)

    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()

    def on_worker_progress(self, percent, msg):
        self.pbar.setValue(percent)
        self.status_lbl.setText(f"⚙️ {msg}")

    def run_load_balance_optimization(self):
        self.balance_btn.setEnabled(False)
        self.balance_btn.setText("⏳ Optimizando carga...")
        self.status_lbl.setVisible(True)
        self.pbar.setVisible(True)
        self.pbar.setValue(0)
        self.status_lbl.setText("Iniciando balance de carga con CP-SAT...")

        self.worker = SolverWorker(time_limit_seconds=15.0, profile="load_balance")
        self.worker.progress_signal.connect(self.on_worker_progress)
        self.worker.finished_signal.connect(self.on_balance_finished)
        self.worker.error_signal.connect(self.on_balance_error)
        self.worker.start()

    def on_balance_finished(self, result):
        self.balance_btn.setEnabled(True)
        self.balance_btn.setText("⚡ Optimizar Balance (Reducir Subcarga)")
        self.pbar.setValue(100)
        self.status_lbl.setText("✅ Optimización completada exitosamente.")

        if result.get("status") == "SUCCESS":
            db = SessionLocal()
            try:
                from app.database.models import DayOfWeek
                db.query(ScheduleAssignment).delete()
                for asg in result["assignments"]:
                    assignment = ScheduleAssignment(
                        group_id=asg["group_id"],
                        teacher_id=asg["teacher_id"],
                        room_id=asg["room_id"],
                        day=DayOfWeek(asg["day"]) if isinstance(asg["day"], str) else asg["day"],
                        time_slot_id=asg["time_slot_id"]
                    )
                    db.add(assignment)
                db.commit()
            finally:
                db.close()

            total_asg = len(result.get("assignments", []))
            solver_st = result.get("solver_status", "OPTIMAL")
            QMessageBox.information(
                self, 
                "✅ Balance de Carga Exitoso", 
                f"El motor OR-Tools CP-SAT completó la reoptimización con estado: {solver_st}.\n\n"
                f"• Clases asignadas rebalanceadas: {total_asg} bloques semanales.\n"
                f"• Se maximizó la ocupación de docentes de Tiempo Completo y Medio Tiempo para reducir la subcarga.\n"
                f"• Los indicadores KPI y las alertas laborales han sido recalculados."
            )
            self.load_data()
        else:
            QMessageBox.warning(self, "Aviso", result.get("msg", "No se encontró solución factible."))

    def on_balance_error(self, err):
        self.balance_btn.setEnabled(True)
        self.balance_btn.setText("⚡ Optimizar Balance (Reducir Subcarga)")
        self.status_lbl.setText(f"❌ Error: {err}")
        QMessageBox.critical(self, "Error", f"Error en la optimización: {err}")
