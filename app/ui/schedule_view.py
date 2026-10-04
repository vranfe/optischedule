from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, 
    QTableWidgetItem, QMessageBox, QHBoxLayout, QProgressBar, QHeaderView,
    QFileDialog, QFrame, QComboBox, QSlider
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
import csv
from app.database.database import SessionLocal
from app.database.models import ScheduleAssignment, DayOfWeek, TimeSlot, Group, Teacher, Room, ShiftType
from app.ui.workers.solver_worker import SolverWorker
from app.ui.excel_exporter import export_schedule_dialog

class ScheduleView(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.base_row_height = 50
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 18px;")
        header = QHBoxLayout(header_card)
        
        title_layout = QVBoxLayout()
        title = QLabel("Motor de Optimización y Matriz Institucional de Horarios")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1e3a8a;")
        subtitle = QLabel("Programación Matemática con Restricciones Duras y Blandas (Google OR-Tools CP-SAT)")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)
        
        # Action Buttons & Filter
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        # Semester Filter Combo
        self.semester_combo = QComboBox()
        self.semester_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 14px;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                background-color: #f8fafc;
                color: #0f172a;
                font-weight: 700;
                font-size: 12px;
                min-width: 180px;
            }
            QComboBox:hover {
                border-color: #4f46e5;
            }
        """)
        self.semester_combo.addItem("1️⃣ Semestre 1", 1)
        self.semester_combo.addItem("2️⃣ Semestre 2", 2)
        self.semester_combo.addItem("3️⃣ Semestre 3", 3)
        self.semester_combo.addItem("4️⃣ Semestre 4", 4)
        self.semester_combo.currentIndexChanged.connect(lambda: self.load_schedule())
        btn_layout.addWidget(self.semester_combo)

        self.export_btn = QPushButton("📥 Exportar (Excel / CSV)")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; 
                color: white; 
                font-weight: bold; 
                padding: 9px 16px;
                border-radius: 8px;
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
                background-color: #10b981; 
                color: white; 
                font-weight: 800; 
                padding: 9px 18px;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
            }
        """)
        self.generate_btn.clicked.connect(self.start_generation)
        btn_layout.addWidget(self.generate_btn)
        
        header.addLayout(btn_layout)
        self.layout.addWidget(header_card)
        
        # Legend & Cell Height Slider Bar
        legend_card = QFrame()
        legend_card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 14px;")
        l_layout = QHBoxLayout(legend_card)
        l_layout.setSpacing(12)

        l_layout.addWidget(self._create_legend_dot("☀️ Mañana (8-12)", "#0284c7", "#e0f2fe"))
        l_layout.addWidget(self._create_legend_dot("⛅ Tarde (13-17)", "#059669", "#d1fae5"))
        l_layout.addWidget(self._create_legend_dot("🌙 Noche (18-22)", "#7c3aed", "#ede9fe"))
        l_layout.addStretch()
        self.layout.addWidget(legend_card)

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

        # Schedule table + Lateral Navigation Slider container
        table_container = QHBoxLayout()
        table_container.setSpacing(8)

        # Table to show full institutional schedule
        self.table = QTableWidget()
        self.days = [d.value for d in DayOfWeek]
        self.table.setColumnCount(len(self.days))
        self.table.setHorizontalHeaderLabels(self.days)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setMinimumWidth(180)
        self.table.verticalHeader().setDefaultSectionSize(self.base_row_height)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #cbd5e1;
                background-color: #ffffff;
                color: #0f172a;
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 8px;
                font-weight: 800;
                font-size: 12px;
                border: none;
                border-right: 1px solid #334155;
            }
        """)
        table_container.addWidget(self.table, 1)

        # Lateral Navigation Slider Box
        lateral_box = QVBoxLayout()
        lateral_box.setSpacing(4)
        lateral_box.setAlignment(Qt.AlignCenter)

        top_icon = QLabel("☀️")
        top_icon.setAlignment(Qt.AlignCenter)
        top_icon.setStyleSheet("font-size: 13px;")

        self.lateral_slider = QSlider(Qt.Vertical)
        self.lateral_slider.setRange(0, 100)
        self.lateral_slider.setValue(0)
        self.lateral_slider.setInvertedAppearance(True)
        self.lateral_slider.setFixedWidth(26)
        self.lateral_slider.setCursor(Qt.PointingHandCursor)
        self.lateral_slider.setToolTip("Desliza lateralmente para navegar por las franjas horarias")
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
        self.table.verticalScrollBar().rangeChanged.connect(self._sync_lateral_slider_range)
        self.table.verticalScrollBar().valueChanged.connect(self._sync_lateral_slider_value)

        bot_icon = QLabel("🌙")
        bot_icon.setAlignment(Qt.AlignCenter)
        bot_icon.setStyleSheet("font-size: 13px;")

        mid_icon = QLabel("⛅")
        mid_icon.setAlignment(Qt.AlignCenter)
        mid_icon.setStyleSheet("font-size: 11px;")

        lateral_box.addWidget(top_icon)
        lateral_box.addWidget(mid_icon)
        lateral_box.addWidget(self.lateral_slider, 1)
        lateral_box.addWidget(bot_icon)

        table_container.addLayout(lateral_box)
        self.layout.addLayout(table_container)
        
        self.load_schedule()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_schedule()

    def _on_lateral_slider_changed(self, value):
        self.table.verticalScrollBar().setValue(value)

    def _sync_lateral_slider_range(self, min_val, max_val):
        self.lateral_slider.setRange(min_val, max_val)

    def _sync_lateral_slider_value(self, value):
        self.lateral_slider.blockSignals(True)
        self.lateral_slider.setValue(value)
        self.lateral_slider.blockSignals(False)

    def _create_legend_dot(self, text, color, bg):
        lbl = QLabel(f" {text} ")
        lbl.setStyleSheet(f"background-color: {bg}; color: {color}; font-size: 11px; font-weight: bold; border-radius: 5px; padding: 2px 8px; border: 1px solid {color}40;")
        return lbl

    def start_generation(self):
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("⏳ Optimizando con CP-SAT...")
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
                f"📊 Métricas de Calidad:\n"
                f"• Calidad Global: {eval_res['global_score']}%\n"
                f"• Satisfacción de Preferencias: {eval_res['preference_score']}%\n"
                f"• Minimización de Huecos: {eval_res['gap_score']}%\n"
                f"• Balance de Carga: {eval_res['teacher_load_score']}%\n"
                f"• Utilización de Aulas: {eval_res['room_utilization_score']}%\n"
                f"• Distribución Semanal: {eval_res['distribution_score']}%"
            )
            
            self.status_lbl.setText(f"✅ {result['msg']} | Calidad: {eval_res['global_score']}% ({eval_res['status']})")
            QMessageBox.information(self, "Optimización Exitosa", msg_full)
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
            for asg in assignments:
                _ = asg.group.subject.name if asg.group and asg.group.subject else None
                _ = asg.teacher.name if asg.teacher else None
                _ = asg.room.name if asg.room else None
                _ = asg.time_slot.shift if asg.time_slot else None
        finally:
            db.close()
        
        if not slots:
            return
            
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
        
        self.table.setRowCount(len(sorted_slot_ids))
        self.table.setVerticalHeaderLabels([slot_map[sid] for sid in sorted_slot_ids])
        
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                self.table.setItem(r, c, QTableWidgetItem(""))
        
        day_indices = {d: i for i, d in enumerate(self.days)}
        slot_indices = {sid: i for i, sid in enumerate(sorted_slot_ids)}
        
        # Shift colors
        shift_colors = {
            ShiftType.MORNING: "#f0f9ff",
            ShiftType.AFTERNOON: "#f0fdf4",
            ShiftType.NIGHT: "#faf5ff"
        }

        selected_sem = self.semester_combo.currentData() if hasattr(self, 'semester_combo') else 1
        if selected_sem is None:
            selected_sem = 1
        assignments = [
            a for a in assignments 
            if a.group and a.group.subject and a.group.subject.semester_id == selected_sem
        ]

        for asg in assignments:
            if asg.time_slot_id in slot_indices and asg.day.value in day_indices:
                r_idx = slot_indices[asg.time_slot_id]
                c_idx = day_indices[asg.day.value]
                
                slot_obj = next((sl for sl in sorted_slots if sl.id == asg.time_slot_id), None)
                bg_color = shift_colors.get(slot_obj.shift, "#ffffff") if slot_obj else "#ffffff"

                text = f"📘 {asg.group.subject.name} ({asg.group.name})\n👨‍🏫 {asg.teacher.name}\n📍 {asg.room.name}"
                
                current_item = self.table.item(r_idx, c_idx)
                if current_item and current_item.text():
                    current_item.setText(current_item.text() + f"\n\n─────────────\n\n{text}")
                else:
                    new_item = QTableWidgetItem(text)
                    new_item.setTextAlignment(Qt.AlignCenter)
                    new_item.setBackground(QColor(bg_color))
                    new_item.setForeground(QColor("#1e3a8a"))
                    font = new_item.font()
                    font.setBold(True)
                    new_item.setFont(font)
                    self.table.setItem(r_idx, c_idx, new_item)
        
        self.table.resizeRowsToContents()

    def export_csv(self):
        db = SessionLocal()
        try:
            raw_assignments = db.query(ScheduleAssignment).all()
            assignments = []
            for asg in raw_assignments:
                slot = asg.time_slot
                group = asg.group
                subj = group.subject if group else None
                teacher = asg.teacher
                room = asg.room
                day_val = asg.day.value if hasattr(asg.day, "value") else str(asg.day)
                assignments.append({
                    "id": asg.id,
                    "day": day_val,
                    "shift": slot.shift.value if slot and hasattr(slot.shift, "value") else (str(slot.shift) if slot else ""),
                    "start_time": slot.start_time.strftime('%H:%M') if slot and slot.start_time else "",
                    "end_time": slot.end_time.strftime('%H:%M') if slot and slot.end_time else "",
                    "subject_name": subj.name if subj else "",
                    "semester": f"Semestre {subj.semester_id}" if subj else "",
                    "group_name": group.name if group else "",
                    "teacher_name": teacher.name if teacher else "",
                    "teacher_type": teacher.teacher_type.value if teacher and hasattr(teacher.teacher_type, "value") else "",
                    "room_name": room.name if room else "",
                    "room_type": room.room_type if room else ""
                })
        finally:
            db.close()

        if not assignments:
            QMessageBox.warning(self, "Exportación", "No hay ningún horario generado para exportar.")
            return

        export_schedule_dialog(
            self,
            "Horario_Institucional_UMB.xlsx",
            self.table,
            assignments,
            title="Matriz Institucional de Horarios UMB"
        )

