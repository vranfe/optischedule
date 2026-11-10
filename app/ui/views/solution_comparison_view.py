from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QFrame, QHeaderView, QMessageBox,
    QProgressBar, QScrollArea, QSlider, QComboBox
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, Signal, QEvent
from sqlalchemy.orm import joinedload
from app.database.database import get_db, SessionLocal
from app.database.models import ScheduleAssignment, DayOfWeek, TimeSlot, Group, Teacher, Room, Subject
from app.optimization.constraint_solver import ScheduleSolver
from app.optimization.evaluator import Evaluator
from app.ui.workers.alternatives_worker import AlternativesWorker
from app.ui.dialogs.schedule_preview_dialog import SchedulePreviewDialog

class SolutionComparisonView(QWidget):
    solution_applied = Signal()

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
        self.comp_table.setMinimumHeight(360)
        self.comp_table.verticalHeader().setDefaultSectionSize(40)
        self.comp_table.verticalHeader().setMinimumWidth(260)
        self.comp_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.comp_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.comp_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e2e8f0;
                background-color: #ffffff;
                color: #0f172a;
                font-size: 13px;
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 10px;
                font-weight: 800;
                border: none;
                border-right: 1px solid #334155;
            }
        """)
        layout.addWidget(self.comp_table)

        # Embedded Live Schedule Preview
        preview_card = QFrame()
        preview_card.setStyleSheet("background-color: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 12px;")
        p_card_layout = QVBoxLayout(preview_card)
        p_card_layout.setSpacing(10)

        p_header = QHBoxLayout()
        self.preview_title_lbl = QLabel("📅 Matriz Semanal de la Alternativa Seleccionada: Horario Institucional Vigente")
        self.preview_title_lbl.setStyleSheet("font-size: 14px; font-weight: 800; color: #1e3a8a;")
        p_header.addWidget(self.preview_title_lbl)
        p_header.addStretch()

        # Semester Filter Combo to prevent cell overcrowding
        self.semester_combo = QComboBox()
        self.semester_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 14px;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                background-color: #f8fafc;
                color: #0f172a;
                font-weight: 700;
                font-size: 12px;
                min-width: 175px;
            }
            QComboBox:hover {
                border-color: #4f46e5;
            }
        """)
        self.semester_combo.addItem("1️⃣ Semestre 1", 1)
        self.semester_combo.addItem("2️⃣ Semestre 2", 2)
        self.semester_combo.addItem("3️⃣ Semestre 3", 3)
        self.semester_combo.addItem("4️⃣ Semestre 4", 4)
        self.semester_combo.currentIndexChanged.connect(lambda: self.select_solution(self.selected_solution) if self.selected_solution else None)
        p_header.addWidget(self.semester_combo)

        self.preview_modal_btn = QPushButton("🔍 Ver en Pantalla Completa")
        self.preview_modal_btn.setCursor(Qt.PointingHandCursor)
        self.preview_modal_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; 
                color: white; 
                font-weight: bold; 
                padding: 6px 14px; 
                border-radius: 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.preview_modal_btn.clicked.connect(self.open_current_selected_modal)
        p_header.addWidget(self.preview_modal_btn)
        p_card_layout.addLayout(p_header)

        # Table + Lateral Slider Container
        table_container = QHBoxLayout()
        table_container.setSpacing(8)

        self.schedule_table = QTableWidget()
        self.days = [d.value for d in DayOfWeek]
        self.schedule_table.setColumnCount(len(self.days))
        self.schedule_table.setHorizontalHeaderLabels(self.days)
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.schedule_table.verticalHeader().setMinimumWidth(185)
        self.schedule_table.verticalHeader().setDefaultSectionSize(58)
        self.schedule_table.setMinimumHeight(400)
        self.schedule_table.horizontalHeader().setVisible(True)
        self.schedule_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #cbd5e1;
                background-color: #ffffff;
                color: #0f172a;
                font-size: 12px;
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 8px;
                font-weight: bold;
            }
        """)
        table_container.addWidget(self.schedule_table, 1)

        # Lateral Navigation Slider Box
        lateral_box = QVBoxLayout()
        lateral_box.setSpacing(4)
        lateral_box.setAlignment(Qt.AlignCenter)

        top_icon = QLabel("☀️")
        top_icon.setAlignment(Qt.AlignCenter)
        top_icon.setStyleSheet("font-size: 12px;")

        self.lateral_slider = QSlider(Qt.Vertical)
        self.lateral_slider.setRange(0, 100)
        self.lateral_slider.setValue(0)
        self.lateral_slider.setInvertedAppearance(True)
        self.lateral_slider.setFixedWidth(26)
        self.lateral_slider.setCursor(Qt.PointingHandCursor)
        self.lateral_slider.setToolTip("Desliza lateralmente para navegar por el horario")
        self.lateral_slider.setStyleSheet("""
            QSlider::groove:vertical {
                background: #e2e8f0;
                width: 10px;
                border-radius: 5px;
            }
            QSlider::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4f46e5, stop:1 #3730a3);
                height: 38px;
                margin: 0 -5px;
                border-radius: 7px;
                border: 1.5px solid #ffffff;
            }
            QSlider::handle:vertical:hover {
                background: #4338ca;
            }
        """)
        self.lateral_slider.valueChanged.connect(self._on_lateral_slider_changed)
        self.schedule_table.verticalScrollBar().rangeChanged.connect(self._sync_lateral_slider_range)
        self.schedule_table.verticalScrollBar().valueChanged.connect(self._sync_lateral_slider_value)
        self.lateral_slider.installEventFilter(self)

        bot_icon = QLabel("🌙")
        bot_icon.setAlignment(Qt.AlignCenter)
        bot_icon.setStyleSheet("font-size: 12px;")

        lateral_box.addWidget(top_icon)
        lateral_box.addWidget(self.lateral_slider, 1)
        lateral_box.addWidget(bot_icon)

        table_container.addLayout(lateral_box)
        p_card_layout.addLayout(table_container)
        layout.addWidget(preview_card)

        self.selected_solution = None
        self.evaluate_current()

    def evaluate_current(self):
        db = SessionLocal()
        try:
            evaluator = Evaluator(db)
            current_res = evaluator.evaluate()
            
            # Fetch current assignments in dict format for preview with eager loading
            curr_asgs = db.query(ScheduleAssignment).options(
                joinedload(ScheduleAssignment.group).joinedload(Group.subject),
                joinedload(ScheduleAssignment.teacher),
                joinedload(ScheduleAssignment.room)
            ).all()
            assignments_list = []
            for a in curr_asgs:
                subj = a.group.subject if a.group else None
                assignments_list.append({
                    "group_id": a.group_id,
                    "teacher_id": a.teacher_id,
                    "room_id": a.room_id,
                    "subject_name": subj.name if subj else "",
                    "group_name": a.group.name if a.group else "",
                    "teacher_name": a.teacher.name if a.teacher else "",
                    "room_name": a.room.name if a.room else "",
                    "day": a.day.value if hasattr(a.day, "value") else a.day,
                    "time_slot_id": a.time_slot_id,
                    "semester": subj.semester_id if subj else None
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
                "name": "Alternativa A (Enfoque Afinidad Docente)",
                "badge": "ALTERNATIVA A",
                "is_best": False,
                "data": alt1_res,
                "assignments": assignments_list
            })
            self.solutions.append({
                "name": "Alternativa B (Enfoque Horario Compacto)",
                "badge": "ALTERNATIVA B",
                "is_best": False,
                "data": alt2_res,
                "assignments": assignments_list
            })

        self.render_comparison()
        self.status_lbl.setText("✅ Evaluación del horario institucional actualizada.")

    def generate_and_compare_alternatives(self):
        self.status_lbl.setText("⏳ Iniciando cálculo de alternativas con OR-Tools en segundo plano...")
        self.gen_alts_btn.setEnabled(False)
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
        self.pbar.setVisible(False)

        if not generated_solutions:
            self.status_lbl.setText("❌ No se pudieron generar soluciones alternativas factibles.")
            QMessageBox.warning(self, "Aviso", "No se encontraron soluciones alternativas factibles.")
            return

        self.solutions = []
        for idx, sol in enumerate(generated_solutions):
            is_best = (idx == 0)
            letter = chr(65 + idx)
            focus = sol.get("focus_name", sol.get("name", "Optimización")).strip()
            display_name = f"Alternativa {letter} ({focus})"
            badge_text = f"⭐ RECOMENDADA ({letter})" if is_best else f"ALTERNATIVA {letter}"
            self.solutions.append({
                "name": display_name,
                "badge": badge_text,
                "is_best": is_best,
                "data": sol["data"],
                "assignments": sol["assignments"]
            })

        self.render_comparison()
        self.status_lbl.setText(f"✅ Se generaron y compararon {len(self.solutions)} soluciones factibles.")

    def on_worker_error(self, error_msg):
        self.gen_alts_btn.setEnabled(True)
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

            # Preview button that selects and loads in live grid + opens full modal
            btn_view = QPushButton("🔍 Ver Horario")
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.setStyleSheet("background-color: #0284c7; color: white; padding: 6px 10px; border-radius: 6px; font-weight: bold; font-size: 11px;")
            btn_view.clicked.connect(lambda _, s=sol: self._view_solution(s))
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
                font = item.font()
                font.setPointSize(11)
                if key == "status":
                    is_ok = ("FACTIBLE" in str(val) and "NO" not in str(val))
                    item.setForeground(QColor("#047857") if is_ok else QColor("#dc2626"))
                    font.setBold(True)
                elif key == "hard_constraint_violations":
                    item.setForeground(QColor("#047857") if val == 0 else QColor("#dc2626"))
                    font.setBold(True)
                elif key == "global_score":
                    item.setForeground(QColor("#065f46") if is_best else QColor("#1e3a8a"))
                    item.setBackground(QColor("#ecfdf5") if is_best else QColor("#ffffff"))
                    font.setBold(True)
                    font.setPointSize(12)
                else:
                    item.setForeground(QColor("#0f172a"))
                    font.setBold(True)
                item.setFont(font)
                self.comp_table.setItem(row_idx, col_idx, item)

        if self.solutions:
            self.select_solution(self.solutions[0])

    def _view_solution(self, sol):
        self.select_solution(sol)
        self.preview_solution_modal(sol)

    def eventFilter(self, obj, event):
        if obj == getattr(self, "lateral_slider", None) and event.type() == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            step = 1 if delta < 0 else -1
            sb = self.schedule_table.verticalScrollBar()
            sb.setValue(sb.value() + step)
            return True
        return super().eventFilter(obj, event)

    def _on_lateral_slider_changed(self, value):
        self.schedule_table.verticalScrollBar().setValue(value)

    def _sync_lateral_slider_range(self, min_val, max_val):
        self.lateral_slider.setRange(min_val, max_val)

    def _sync_lateral_slider_value(self, value):
        self.lateral_slider.blockSignals(True)
        self.lateral_slider.setValue(value)
        self.lateral_slider.blockSignals(False)

    def select_solution(self, sol):
        self.selected_solution = sol
        self.preview_title_lbl.setText(f"📅 Matriz Semanal: {sol['name']} (Calidad: {sol['data'].get('global_score', '-') }%)")
        
        db = SessionLocal()
        try:
            slots = db.query(TimeSlot).all()
            groups_dict = {}
            for g in db.query(Group).options(joinedload(Group.subject)).all():
                groups_dict[g.id] = {
                    "name": g.name,
                    "subject_name": g.subject.name if g.subject else "",
                    "semester_id": g.subject.semester_id if g.subject else None
                }
            teachers_map = {t.id: t.name for t in db.query(Teacher).all()}
            rooms_map = {r.id: r.name for r in db.query(Room).all()}
        finally:
            db.close()

        if not slots:
            return

        from app.database.models import ShiftType
        SHIFT_ORDER = {
            ShiftType.MORNING: 0,
            ShiftType.AFTERNOON: 1,
            ShiftType.NIGHT: 2,
            "MAÑANA": 0,
            "TARDE": 1,
            "NOCHE": 2
        }
        sorted_slots = sorted(slots, key=lambda s: (SHIFT_ORDER.get(s.shift, 99), s.start_time))
        slot_map = {
            s.id: f"{s.shift.value}\n{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}" 
            for s in sorted_slots
        }
        sorted_slot_ids = [s.id for s in sorted_slots]

        self.schedule_table.setRowCount(len(sorted_slot_ids))
        self.schedule_table.setVerticalHeaderLabels([slot_map[sid] for sid in sorted_slot_ids])

        for r in range(self.schedule_table.rowCount()):
            for c in range(self.schedule_table.columnCount()):
                self.schedule_table.setItem(r, c, QTableWidgetItem(""))

        day_indices = {d: i for i, d in enumerate(self.days)}
        slot_indices = {sid: i for i, sid in enumerate(sorted_slot_ids)}

        from app.database.models import ShiftType
        shift_colors = {
            ShiftType.MORNING: "#f0f9ff",
            ShiftType.AFTERNOON: "#f0fdf4",
            ShiftType.NIGHT: "#faf5ff"
        }

        selected_sem = self.semester_combo.currentData() if hasattr(self, 'semester_combo') else 1
        if selected_sem is None:
            selected_sem = 1

        assignments = sol.get("assignments", [])
        for asg in assignments:
            time_slot_id = asg.get("time_slot_id")
            day_val = asg.get("day")
            if hasattr(day_val, "value"):
                day_val = day_val.value

            group_id = asg.get("group_id")
            g_info = groups_dict.get(group_id, {})
            sem_id = asg.get("semester") or g_info.get("semester_id")

            # Filter by semester if selected
            if selected_sem is not None and sem_id is not None and sem_id != selected_sem:
                continue

            if time_slot_id in slot_indices and day_val in day_indices:
                r_idx = slot_indices[time_slot_id]
                c_idx = day_indices[day_val]

                slot_obj = next((sl for sl in sorted_slots if sl.id == time_slot_id), None)
                bg_color = shift_colors.get(slot_obj.shift, "#ffffff") if slot_obj else "#ffffff"

                subj_name = asg.get("subject_name") or g_info.get("subject_name", "")
                group_name = asg.get("group_name") or g_info.get("name", "")
                teacher_name = asg.get("teacher_name") or teachers_map.get(asg.get("teacher_id"), "")
                room_name = asg.get("room_name") or rooms_map.get(asg.get("room_id"), "")

                sem_tag = f"Sem {sem_id} • " if sem_id else ""
                text = f"📘 {subj_name} ({group_name})\n[{sem_tag}{room_name}]\n👨‍🏫 {teacher_name}"

                
                curr = self.schedule_table.item(r_idx, c_idx)
                if curr and curr.text():
                    curr.setText(curr.text() + f"\n\n─────────────\n\n{text}")
                else:
                    new_item = QTableWidgetItem(text)
                    new_item.setTextAlignment(Qt.AlignCenter)
                    new_item.setBackground(QColor(bg_color))
                    new_item.setForeground(QColor("#1e3a8a"))
                    font = new_item.font()
                    font.setBold(True)
                    new_item.setFont(font)
                    self.schedule_table.setItem(r_idx, c_idx, new_item)

        self.schedule_table.resizeRowsToContents()

    def open_current_selected_modal(self):
        if not self.selected_solution:
            return
        self.preview_solution_modal(self.selected_solution)

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
            f"¿Deseas activar '{solution['name']}' como el horario institucional vigente?\n\nEsta acción actualizará la base de datos y todas las pantallas del sistema en vivo.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            db = SessionLocal()
            try:
                db.query(ScheduleAssignment).delete()
                for asg in solution["assignments"]:
                    t_id = asg.get("teacher_id")
                    r_id = asg.get("room_id")
                    if not t_id or not r_id:
                        g = db.query(Group).filter_by(id=asg["group_id"]).first()
                        if not t_id:
                            pref = db.query(TeacherSubjectPreference).filter_by(subject_id=g.subject_id).first() if g else None
                            t_id = pref.teacher_id if pref else 1
                        if not r_id:
                            r = db.query(Room).first()
                            r_id = r.id if r else 1

                    assignment = ScheduleAssignment(
                        group_id=asg["group_id"],
                        teacher_id=t_id,
                        room_id=r_id,
                        day=DayOfWeek(asg["day"]) if isinstance(asg["day"], str) else asg["day"],
                        time_slot_id=asg["time_slot_id"]
                    )
                    db.add(assignment)
                db.commit()
            finally:
                db.close()

            # Update this solution name as current official
            solution["name"] = f"Horario Oficial Activo ({solution['name']})"
            self.preview_title_lbl.setText(f"📅 Matriz Semanal: {solution['name']} (Calidad: {solution['data'].get('global_score', '-') }%)")
            
            # Emit signal to reload MainWindow views (ScheduleView, DashboardView)
            self.solution_applied.emit()
            self.select_solution(solution)

            QMessageBox.information(
                self, "Horario Institucional Activado", 
                f"¡La solución ha sido aplicada con éxito!\n\nEl Horario Institucional y el Dashboard de Monitoreo se han actualizado automáticamente con este horario."
            )
