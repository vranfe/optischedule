from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, 
    QTableWidgetItem, QMessageBox, QHBoxLayout, QProgressBar, QHeaderView,
    QFileDialog, QFrame, QComboBox
)
from PySide6.QtCore import Qt
import csv
from app.database.database import get_db, SessionLocal
from app.database.models import ScheduleAssignment, DayOfWeek, TimeSlot, Group, Teacher, Room
from app.ui.workers.solver_worker import SolverWorker

class ScheduleView(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;")
        header = QHBoxLayout(header_card)
        
        title_layout = QVBoxLayout()
        title = QLabel("Motor de Optimización y Matriz Institucional de Horarios")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #1e3a8a;")
        subtitle = QLabel("Programación Matemática con Restricciones Duras y Blandas (Google OR-Tools CP-SAT)")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)
        
        # Action Buttons & Filter
        btn_layout = QHBoxLayout()
        
        # Semester Filter Combo
        self.semester_combo = QComboBox()
        self.semester_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background-color: #f8fafc;
                color: #0f172a;
                font-weight: 600;
                font-size: 12px;
                min-width: 170px;
            }
            QComboBox:hover {
                border-color: #3b82f6;
            }
        """)
        self.semester_combo.addItem("📚 Todos los Semestres", None)
        self.semester_combo.addItem("1️⃣ Semestre 1", 1)
        self.semester_combo.addItem("2️⃣ Semestre 2", 2)
        self.semester_combo.addItem("3️⃣ Semestre 3", 3)
        self.semester_combo.addItem("4️⃣ Semestre 4", 4)
        self.semester_combo.currentIndexChanged.connect(lambda: self.load_schedule())
        btn_layout.addWidget(self.semester_combo)

        self.export_btn = QPushButton("📥 Exportar Horario (CSV)")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; 
                color: white; 
                font-weight: bold; 
                padding: 10px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.export_btn.clicked.connect(self.export_csv)
        btn_layout.addWidget(self.export_btn)

        self.generate_btn = QPushButton("⚡ GENERAR HORARIO ÓPTIMO")
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a34a; 
                color: white; 
                font-weight: bold; 
                padding: 10px 18px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #15803d;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
            }
        """)
        self.generate_btn.clicked.connect(self.start_generation)
        btn_layout.addWidget(self.generate_btn)
        
        header.addLayout(btn_layout)
        self.layout.addWidget(header_card)
        
        # Progress & Status Bar
        self.progress_container = QVBoxLayout()
        self.status_lbl = QLabel("Listo para generar.")
        self.status_lbl.setStyleSheet("font-size: 12px; color: #475569; font-weight: 600;")
        
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.pbar.setTextVisible(True)
        self.progress_container.addWidget(self.status_lbl)
        self.progress_container.addWidget(self.pbar)
        self.layout.addLayout(self.progress_container)

        # Table to show full institutional schedule
        self.table = QTableWidget()
        self.days = [d.value for d in DayOfWeek]
        self.table.setColumnCount(len(self.days))
        self.table.setHorizontalHeaderLabels(self.days)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #cbd5e1;
                background-color: #ffffff;
                color: #0f172a;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 8px;
                font-weight: bold;
            }
        """)
        self.layout.addWidget(self.table)
        
        self.load_schedule()

    def start_generation(self):
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("⏳ Optimizando en segundo plano...")
        self.pbar.setValue(0)
        self.status_lbl.setText("Iniciando hilo de optimización...")

        self.worker = SolverWorker(time_limit_seconds=15.0)
        self.worker.progress_signal.connect(self.on_worker_progress)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.error_signal.connect(self.on_worker_error)
        self.worker.start()

    def on_worker_progress(self, percent, msg):
        self.pbar.setValue(percent)
        self.status_lbl.setText(f"⚙️ {msg}")

    def on_worker_finished(self, result):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("⚡ GENERAR HORARIO ÓPTIMO")

        if result["status"] == "SUCCESS":
            db = SessionLocal()
            try:
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
                
                from app.optimization.evaluator import Evaluator
                eval_res = Evaluator(db).evaluate()
            finally:
                db.close()
            
            msg_full = (
                f"{result['msg']}\n\n"
                f"📊 Métricas de Calidad de la Solución Recomendada:\n"
                f"• Calidad Global Ponderada: {eval_res['global_score']}%\n"
                f"• Satisfacción de Preferencias: {eval_res['preference_score']}%\n"
                f"• Minimización de Huecos: {eval_res['gap_score']}%\n"
                f"• Balance de Carga Docente: {eval_res['teacher_load_score']}%\n"
                f"• Utilización de Aulas: {eval_res['room_utilization_score']}%\n"
                f"• Distribución Semanal: {eval_res['distribution_score']}%"
            )
            
            self.status_lbl.setText(f"✅ {result['msg']} | Calidad: {eval_res['global_score']}% ({eval_res['status']})")
            QMessageBox.information(self, "Optimización Completada", msg_full)
            self.load_schedule()
        else:
            self.status_lbl.setText("❌ No se encontró solución factible.")
            QMessageBox.warning(self, "Aviso de Restricciones", result["msg"])

    def on_worker_error(self, error_msg):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("⚡ GENERAR HORARIO ÓPTIMO")
        self.status_lbl.setText(f"❌ Error: {error_msg}")
        QMessageBox.critical(self, "Error", f"Ocurrió un error en el cálculo: {error_msg}")
        
    def load_schedule(self):
        db = SessionLocal()
        try:
            assignments = db.query(ScheduleAssignment).all()
            slots = db.query(TimeSlot).all()
            # Eager load relationships before closing session
            for asg in assignments:
                _ = asg.group.subject.name if asg.group and asg.group.subject else None
                _ = asg.teacher.name if asg.teacher else None
                _ = asg.room.name if asg.room else None
                _ = asg.time_slot.shift if asg.time_slot else None
        finally:
            db.close()
        
        if not slots:
            return
            
        slot_map = {s.id: f"{s.shift.value}\n{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}" for s in slots}
        sorted_slot_ids = sorted(slot_map.keys(), key=lambda sid: slot_map[sid])
        
        self.table.setRowCount(len(sorted_slot_ids))
        self.table.setVerticalHeaderLabels([slot_map[sid] for sid in sorted_slot_ids])
        
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                self.table.setItem(r, c, QTableWidgetItem(""))
        
        day_indices = {d: i for i, d in enumerate(self.days)}
        slot_indices = {sid: i for i, sid in enumerate(sorted_slot_ids)}
        
        # Colorful palette for distinct semesters
        colors = {
            1: "#dbeafe", # light blue
            2: "#d1fae5", # light green
            3: "#fef3c7", # light yellow
            4: "#ede9fe"  # light purple
        }

        # Filter by selected semester if any
        selected_sem = self.semester_combo.currentData() if hasattr(self, 'semester_combo') else None
        if selected_sem is not None:
            assignments = [
                a for a in assignments 
                if a.group and a.group.subject and a.group.subject.semester_id == selected_sem
            ]

        for asg in assignments:
            if asg.time_slot_id in slot_indices and asg.day.value in day_indices:
                r_idx = slot_indices[asg.time_slot_id]
                c_idx = day_indices[asg.day.value]
                
                sem_num = asg.group.subject.semester_id if asg.group and asg.group.subject else 1
                bg_color = colors.get(sem_num, "#f1f5f9")

                text = f"📘 {asg.group.subject.name} ({asg.group.name})\n👨‍🏫 {asg.teacher.name}\n📍 {asg.room.name}"
                
                current_item = self.table.item(r_idx, c_idx)
                if current_item and current_item.text():
                    current_item.setText(current_item.text() + f"\n\n─────────────\n\n{text}")
                else:
                    new_item = QTableWidgetItem(text)
                    new_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(r_idx, c_idx, new_item)
        
        self.table.resizeRowsToContents()

    def export_csv(self):
        db = SessionLocal()
        try:
            assignments = db.query(ScheduleAssignment).all()
            for asg in assignments:
                _ = asg.time_slot
                _ = asg.group.subject if asg.group else None
                _ = asg.teacher
                _ = asg.room
        finally:
            db.close()

        if not assignments:
            QMessageBox.warning(self, "Exportación", "No hay ningún horario generado para exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar Horario", "Horario_OptiSchedule_UMB.csv", "Archivos CSV (*.csv)")
        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["ID", "Día", "Jornada", "Hora Inicio", "Hora Fin", "Asignatura", "Semestre", "Grupo", "Docente", "Tipo Contrato", "Aula", "Tipo Aula"])
                
                for asg in assignments:
                    slot = asg.time_slot
                    writer.writerow([
                        asg.id,
                        asg.day.value,
                        slot.shift.value if slot else "",
                        slot.start_time.strftime('%H:%M') if slot else "",
                        slot.end_time.strftime('%H:%M') if slot else "",
                        asg.group.subject.name if asg.group and asg.group.subject else "",
                        asg.group.subject.semester_id if asg.group and asg.group.subject else "",
                        asg.group.name if asg.group else "",
                        asg.teacher.name if asg.teacher else "",
                        asg.teacher.teacher_type.value if asg.teacher else "",
                        asg.room.name if asg.room else "",
                        asg.room.room_type if asg.room else ""
                    ])
            QMessageBox.information(self, "Exportación Exitosa", f"El horario se ha exportado correctamente a:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"No se pudo guardar el archivo:\n{e}")


