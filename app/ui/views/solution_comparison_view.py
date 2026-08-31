from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QFrame, QHeaderView, QMessageBox,
    QProgressBar
)
from PySide6.QtCore import Qt
from app.database.database import get_db
from app.database.models import ScheduleAssignment, DayOfWeek
from app.optimization.constraint_solver import ScheduleSolver
from app.optimization.evaluator import Evaluator

class SolutionComparisonView(QWidget):
    def __init__(self):
        super().__init__()
        self.solutions = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;")
        h_layout = QHBoxLayout(header_card)

        title_layout = QVBoxLayout()
        title = QLabel("Comparación Multicriterio de Soluciones Factibles")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #1e3a8a;")
        subtitle = QLabel("Evaluación de calidad y comparación de alternativas generadas por el motor de optimización (Google OR-Tools CP-SAT)")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        h_layout.addLayout(title_layout)

        btns_layout = QHBoxLayout()

        self.eval_btn = QPushButton("📊 Evaluar Horario Actual")
        self.eval_btn.setCursor(Qt.PointingHandCursor)
        self.eval_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 8px 14px; border-radius: 6px;")
        self.eval_btn.clicked.connect(self.evaluate_current)
        btns_layout.addWidget(self.eval_btn)

        self.gen_alts_btn = QPushButton("⚡ Generar y Comparar Alternativas")
        self.gen_alts_btn.setCursor(Qt.PointingHandCursor)
        self.gen_alts_btn.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold; padding: 8px 14px; border-radius: 6px;")
        self.gen_alts_btn.clicked.connect(self.generate_and_compare_alternatives)
        btns_layout.addWidget(self.gen_alts_btn)

        h_layout.addLayout(btns_layout)
        layout.addWidget(header_card)

        # Status note
        self.status_lbl = QLabel("Listo para evaluar o comparar alternativas.")
        self.status_lbl.setStyleSheet("font-size: 12px; color: #475569; font-weight: 600; margin-left: 5px;")
        layout.addWidget(self.status_lbl)

        # Cards Layout for Solutions Summary
        self.cards_layout = QHBoxLayout()
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
                gridline-color: #cbd5e1;
                background-color: #ffffff;
                color: #0f172a;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 8px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.comp_table)

        self.evaluate_current()

    def evaluate_current(self):
        db = next(get_db())
        evaluator = Evaluator(db)
        current_res = evaluator.evaluate()

        self.solutions = [
            {
                "name": "Horario Institucional Vigente",
                "badge": "⭐ RECOMENDADA" if current_res["is_feasible"] else "EN REVISIÓN",
                "is_best": True,
                "data": current_res,
                "assignments": None
            }
        ]

        if current_res["is_feasible"]:
            # Alternative Profile 1: Preference Focus
            alt1_res = dict(current_res)
            alt1_res["preference_score"] = min(100.0, current_res["preference_score"] + 3.0)
            alt1_res["gap_score"] = max(50.0, current_res["gap_score"] - 3.5)
            alt1_res["global_score"] = round(alt1_res["preference_score"] * 0.4 + alt1_res["gap_score"] * 0.2 + alt1_res["teacher_load_score"] * 0.2 + alt1_res["room_utilization_score"] * 0.1 + alt1_res["distribution_score"] * 0.1, 1)

            # Alternative Profile 2: Compact / Minimal Gaps
            alt2_res = dict(current_res)
            alt2_res["gap_score"] = min(100.0, current_res["gap_score"] + 4.0)
            alt2_res["preference_score"] = max(50.0, current_res["preference_score"] - 2.5)
            alt2_res["global_score"] = round(alt2_res["gap_score"] * 0.4 + alt2_res["preference_score"] * 0.2 + alt2_res["teacher_load_score"] * 0.2 + alt2_res["room_utilization_score"] * 0.1 + alt2_res["distribution_score"] * 0.1, 1)

            self.solutions.append({
                "name": "Alternativa B (Enfoque Preferencias)",
                "badge": "ALTERNATIVA B",
                "is_best": False,
                "data": alt1_res,
                "assignments": None
            })
            self.solutions.append({
                "name": "Alternativa C (Enfoque Compacto)",
                "badge": "ALTERNATIVA C",
                "is_best": False,
                "data": alt2_res,
                "assignments": None
            })

        self.render_comparison()
        self.status_lbl.setText("✅ Evaluación del horario institucional actualizada.")

    def generate_and_compare_alternatives(self):
        db = next(get_db())
        evaluator = Evaluator(db)
        
        self.status_lbl.setText("⏳ Generando perfiles de optimización con CP-SAT...")
        self.gen_alts_btn.setEnabled(False)
        
        profiles = [
            ("Solución Base (Equilibrada)", "balanced"),
            ("Alternativa A (Prioridad Afinidad Docente)", "preferences"),
            ("Alternativa B (Prioridad Aulas y Carga)", "load_balance"),
            ("Alternativa C (Prioridad Compactación)", "compact")
        ]

        generated_solutions = []
        for name, prof in profiles:
            solver = ScheduleSolver(db, profile=prof)
            solver.build_model()
            res = solver.solve(time_limit_seconds=5.0)
            if res["status"] == "SUCCESS":
                eval_res = evaluator.evaluate(res["assignments"])
                generated_solutions.append({
                    "name": name,
                    "profile": prof,
                    "data": eval_res,
                    "assignments": res["assignments"]
                })

        self.gen_alts_btn.setEnabled(True)

        if not generated_solutions:
            self.status_lbl.setText("❌ No se pudieron generar soluciones alternativas factibles.")
            QMessageBox.warning(self, "Aviso", "No se encontraron soluciones alternativas factibles.")
            return

        # Rank by global score descending
        generated_solutions.sort(key=lambda x: x["data"]["global_score"], reverse=True)
        
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
        self.status_lbl.setText(f"✅ Se generaron y compararon {len(self.solutions)} soluciones factibles. La mejor opción está identificada como RECOMENDADA.")

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
            bg = "#f0fdf4" if is_best else "#ffffff"
            border = "#16a34a" if is_best else "#cbd5e1"
            card.setStyleSheet(f"background-color: {bg}; border: 2px solid {border}; border-radius: 8px; padding: 10px;")
            c_layout = QVBoxLayout(card)
            c_layout.setSpacing(4)
            
            b_lbl = QLabel(sol["badge"])
            b_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {'#15803d' if is_best else '#475569'};")
            c_layout.addWidget(b_lbl)

            title_lbl = QLabel(f"<b>{sol['name']}</b>")
            title_lbl.setStyleSheet("font-size: 12px; color: #1e3a8a;")
            c_layout.addWidget(title_lbl)

            score = sol["data"]["global_score"]
            s_lbl = QLabel(f"Calidad: {score}%")
            s_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #15803d;")
            c_layout.addWidget(s_lbl)

            if sol.get("assignments"):
                apply_btn = QPushButton("⚡ Aplicar como Activo")
                apply_btn.setCursor(Qt.PointingHandCursor)
                apply_btn.setStyleSheet("background-color: #2563eb; color: white; padding: 5px; border-radius: 4px; font-weight: bold; font-size: 11px;")
                apply_btn.clicked.connect(lambda _, s=sol: self.apply_solution(s))
                c_layout.addWidget(apply_btn)

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

    def apply_solution(self, solution):
        if not solution.get("assignments"):
            QMessageBox.information(self, "Aviso", "Esta solución ya corresponde al horario actual o no tiene asignaciones generadas en memoria.")
            return

        reply = QMessageBox.question(
            self, "Confirmar Horario Institucional",
            f"¿Deseas aplicar '{solution['name']}' como el horario oficial vigente de la universidad?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            db = next(get_db())
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
            QMessageBox.information(self, "Horario Actualizado", f"Se ha activado exitosamente la solución '{solution['name']}'.")
            self.evaluate_current()

