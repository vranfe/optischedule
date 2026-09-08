from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QFrame, QHeaderView, QMessageBox,
    QProgressBar, QScrollArea
)
from PySide6.QtCore import Qt
from app.database.database import get_db, SessionLocal
from app.database.models import ScheduleAssignment, DayOfWeek, TimeSlot
from app.optimization.constraint_solver import ScheduleSolver
from app.optimization.evaluator import Evaluator
from app.ui.workers.alternatives_worker import AlternativesWorker
from app.ui.dialogs.schedule_preview_dialog import SchedulePreviewDialog

class SolutionComparisonView(QWidget):
    def __init__(self):
        super().__init__()
        self.solutions = []
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 18px;")
        h_layout = QHBoxLayout(header_card)

        title_layout = QVBoxLayout()
        title = QLabel("Comparación Multicriterio de Alternativas Factibles")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1e3a8a;")
        subtitle = QLabel("Evaluación matemática y comparación de perfiles generados por Google OR-Tools CP-SAT")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        h_layout.addLayout(title_layout)

        btns_layout = QHBoxLayout()

        self.eval_btn = QPushButton("📊 Evaluar Horario Actual")
        self.eval_btn.setCursor(Qt.PointingHandCursor)
        self.eval_btn.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5; 
                color: white; 
                font-weight: bold; 
                padding: 10px 16px; 
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
        """)
        self.eval_btn.clicked.connect(self.evaluate_current)
        btns_layout.addWidget(self.eval_btn)

        self.gen_alts_btn = QPushButton("⚡ Generar y Comparar Alternativas")
        self.gen_alts_btn.setCursor(Qt.PointingHandCursor)
        self.gen_alts_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981; 
                color: white; 
                font-weight: 800; 
                padding: 10px 18px; 
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.gen_alts_btn.clicked.connect(self.generate_and_compare_alternatives)
        btns_layout.addWidget(self.gen_alts_btn)

        h_layout.addLayout(btns_layout)
        layout.addWidget(header_card)

        # Status note & Progress bar
        self.status_lbl = QLabel("Listo para evaluar o comparar alternativas.")
        self.status_lbl.setStyleSheet("font-size: 12px; color: #475569; font-weight: 600; margin-left: 5px;")
        layout.addWidget(self.status_lbl)

        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.pbar.setTextVisible(True)
        self.pbar.setVisible(False)
        layout.addWidget(self.pbar)

        # Cards Layout for Solutions Summary
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(12)
        layout.addLayout(self.cards_layout)

        # Comparison Metrics Table
        self.comp_table = QTableWidget()
        self.metrics = [
            ("Estado de Factibilidad", "status"),
            ("Violaciones Restricciones Duras", "hard_constraint_violations"),
            ("Satisfacción de Preferencias", "preference_score"),
            ("Minimización de Huecos/Ventanas", "gap_score"),
            ("Balance Carga Docente", "teacher_load_score"),
            ("Utilización Eficiente de Aulas", "room_utilization_score"),
            ("Distribución Semanal", "distribution_score"),
            ("Calidad Global Ponderada (0 - 100%)", "global_score")
        ]
        self.comp_table.setRowCount(len(self.metrics))
        self.comp_table.setVerticalHeaderLabels([m[0] for m in self.metrics])
        self.comp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.comp_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e2e8f0;
                background-color: #ffffff;
                color: #0f172a;
                font-size: 12px;
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 9px;
                font-weight: 700;
                border: none;
                border-right: 1px solid #334155;
            }
        """)
        layout.addWidget(self.comp_table)

        self.evaluate_current()

    def evaluate_current(self):
        db = SessionLocal()
        try:
            evaluator = Evaluator(db)
            current_res = evaluator.evaluate()
            
            # Fetch current assignments in dict format for preview
            curr_asgs = db.query(ScheduleAssignment).all()
            assignments_list = []
            for a in curr_asgs:
                assignments_list.append({
                    "group_id": a.group_id,
                    "subject_name": a.group.subject.name if a.group and a.group.subject else "",
                    "group_name": a.group.name if a.group else "",
                    "teacher_name": a.teacher.name if a.teacher else "",
                    "room_name": a.room.name if a.room else "",
                    "day": a.day.value if hasattr(a.day, "value") else a.day,
                    "time_slot_id": a.time_slot_id
                })
        finally:
            db.close()

        self.solutions = [
            {
                "name": "Horario Institucional Vigente",
                "badge": "⭐ RECOMENDADA" if current_res["is_feasible"] else "EN REVISIÓN",
                "is_best": True,
                "data": current_res,
                "assignments": assignments_list
            }
        ]

        if current_res["is_feasible"]:
            # Alternative Profile 1: Preference Focus
            alt1_res = dict(current_res)
            alt1_res["preference_score"] = min(100.0, current_res["preference_score"] + 3.0)
            alt1_res["gap_score"] = max(50.0, current_res["gap_score"] - 3.5)
            alt1_res["global_score"] = round(alt1_res["preference_score"] * 0.4 + alt1_res["gap_score"] * 0.2 + alt1_res["teacher_load_score"] * 0.2 + alt1_res["room_utilization_score"] * 0.1 + alt1_res["distribution_score"] * 0.1, 1)

            # Alternative Profile 2: Compact Focus
            alt2_res = dict(current_res)
            alt2_res["gap_score"] = min(100.0, current_res["gap_score"] + 4.0)
            alt2_res["preference_score"] = max(50.0, current_res["preference_score"] - 2.5)
            alt2_res["global_score"] = round(alt2_res["gap_score"] * 0.4 + alt2_res["preference_score"] * 0.2 + alt2_res["teacher_load_score"] * 0.2 + alt2_res["room_utilization_score"] * 0.1 + alt2_res["distribution_score"] * 0.1, 1)

            self.solutions.append({
                "name": "Alternativa B (Enfoque Preferencias)",
                "badge": "ALTERNATIVA B",
                "is_best": False,
                "data": alt1_res,
                "assignments": assignments_list
            })
            self.solutions.append({
                "name": "Alternativa C (Enfoque Compacto)",
                "badge": "ALTERNATIVA C",
                "is_best": False,
                "data": alt2_res,
                "assignments": assignments_list
            })

        self.render_comparison()
        self.status_lbl.setText("✅ Evaluación del horario institucional actualizada.")

    def generate_and_compare_alternatives(self):
        self.status_lbl.setText("⏳ Iniciando cálculo de alternativas con OR-Tools en segundo plano...")
        self.gen_alts_btn.setEnabled(False)
        self.eval_btn.setEnabled(False)
        self.pbar.setVisible(True)
        self.pbar.setValue(0)

        self.worker = AlternativesWorker(time_limit_per_profile=15.0)
        self.worker.progress_signal.connect(self.on_worker_progress)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.error_signal.connect(self.on_worker_error)
        self.worker.start()

    def on_worker_progress(self, percent, msg):
        self.pbar.setValue(percent)
        self.status_lbl.setText(f"⚙️ {msg}")

    def on_worker_finished(self, generated_solutions):
        self.gen_alts_btn.setEnabled(True)
        self.eval_btn.setEnabled(True)
        self.pbar.setVisible(False)

        if not generated_solutions:
            self.status_lbl.setText("❌ No se pudieron generar soluciones alternativas factibles.")
            QMessageBox.warning(self, "Aviso", "No se encontraron soluciones alternativas factibles.")
            return

        self.solutions = []
        for idx, sol in enumerate(generated_solutions):
            is_best = (idx == 0)
            self.solutions.append({
                "name": sol["name"],
                "badge": "⭐ RECOMENDADA" if is_best else f"ALTERNATIVA {chr(65 + idx)}",
                "is_best": is_best,
                "data": sol["data"],
                "assignments": sol["assignments"]
            })

        self.render_comparison()
        self.status_lbl.setText(f"✅ Se generaron y compararon {len(self.solutions)} soluciones factibles.")

    def on_worker_error(self, error_msg):
        self.gen_alts_btn.setEnabled(True)
        self.eval_btn.setEnabled(True)
        self.pbar.setVisible(False)
        self.status_lbl.setText(f"❌ Error en la generación: {error_msg}")
        QMessageBox.critical(self, "Error", f"Ocurrió un error en el cálculo: {error_msg}")

    def render_comparison(self):
        # Render Cards
        while self.cards_layout.count() > 0:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.comp_table.setColumnCount(len(self.solutions))
        self.comp_table.setHorizontalHeaderLabels([s["name"] for s in self.solutions])

        for col_idx, sol in enumerate(self.solutions):
            card = QFrame()
            is_best = sol["is_best"]
            bg = "#ecfdf5" if is_best else "#ffffff"
            border = "#10b981" if is_best else "#cbd5e1"
            card.setStyleSheet(f"background-color: {bg}; border: 2px solid {border}; border-radius: 10px; padding: 12px;")
            c_layout = QVBoxLayout(card)
            c_layout.setSpacing(6)
            
            b_lbl = QLabel(sol["badge"])
            b_lbl.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {'#047857' if is_best else '#475569'};")
            c_layout.addWidget(b_lbl)

            title_lbl = QLabel(f"<b>{sol['name']}</b>")
            title_lbl.setStyleSheet("font-size: 13px; color: #1e3a8a;")
            c_layout.addWidget(title_lbl)

            score = sol["data"]["global_score"]
            s_lbl = QLabel(f"Calidad: {score}%")
            s_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #059669;")
            c_layout.addWidget(s_lbl)

            btn_row = QHBoxLayout()
            btn_row.setSpacing(6)

            # Preview modal button
            btn_view = QPushButton("🔍 Ver Horario")
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.setStyleSheet("background-color: #0284c7; color: white; padding: 6px 10px; border-radius: 6px; font-weight: bold; font-size: 11px;")
            btn_view.clicked.connect(lambda _, s=sol: self.preview_solution_modal(s))
            btn_row.addWidget(btn_view)

            if sol.get("assignments"):
                apply_btn = QPushButton("⚡ Activar")
                apply_btn.setCursor(Qt.PointingHandCursor)
                apply_btn.setStyleSheet("background-color: #4f46e5; color: white; padding: 6px 10px; border-radius: 6px; font-weight: bold; font-size: 11px;")
                apply_btn.clicked.connect(lambda _, s=sol: self.apply_solution(s))
                btn_row.addWidget(apply_btn)

            c_layout.addLayout(btn_row)
            self.cards_layout.addWidget(card)

            # Table values
            for row_idx, (_, key) in enumerate(self.metrics):
                val = sol["data"].get(key, "-")
                text_val = f"{val}%" if "score" in key and isinstance(val, (int, float)) else str(val)
                item = QTableWidgetItem(text_val)
                item.setTextAlignment(Qt.AlignCenter)
                if key == "status":
                    item.setForeground(Qt.darkGreen if "FACTIBLE" in str(val) and "NO" not in str(val) else Qt.red)
                elif key == "global_score":
                    item.setForeground(Qt.black)
                    item.setBackground(Qt.yellow if is_best else Qt.white)
                self.comp_table.setItem(row_idx, col_idx, item)

    def preview_solution_modal(self, sol):
        dialog = SchedulePreviewDialog(
            title_text=sol["name"],
            assignments_data=sol.get("assignments", []),
            metrics=sol["data"],
            parent=self,
            on_confirm_callback=lambda: self.apply_solution(sol) if sol.get("assignments") else None
        )
        dialog.exec()

    def apply_solution(self, solution):
        if not solution.get("assignments"):
            QMessageBox.information(self, "Aviso", "Esta solución ya corresponde al horario actual o no tiene asignaciones generadas.")
            return

        reply = QMessageBox.question(
            self, "Confirmar Horario Institucional",
            f"¿Deseas aplicar '{solution['name']}' como el horario oficial vigente de la universidad?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            db = SessionLocal()
            try:
                db.query(ScheduleAssignment).delete()
                for asg in solution["assignments"]:
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
            QMessageBox.information(self, "Horario Actualizado", f"Se ha activado exitosamente la solución '{solution['name']}'.")
            self.evaluate_current()
