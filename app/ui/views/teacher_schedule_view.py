from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QFrame,
    QFileDialog, QMessageBox, QSlider, QApplication, QScrollArea
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, QEvent
import csv
from app.database.database import SessionLocal
from app.database.models import Teacher, ScheduleAssignment, TimeSlot, DayOfWeek, ShiftType
from app.auth.session import session
from app.ui.excel_exporter import export_schedule_dialog
from app.ui.dialogs.schedule_preview_dialog import SchedulePreviewDialog

class TeacherScheduleView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 24, 30)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;")
        header = QHBoxLayout(header_card)

        title_layout = QVBoxLayout()
        self.title_lbl = QLabel("Mi Horario y Asignaciones Académicas")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #1e3a8a;")
        sub_lbl = QLabel("Detalle semanal de carga horaria, asignaturas, grupos y aulas asignadas")
        sub_lbl.setStyleSheet("font-size: 12px; color: #64748b;")
        title_layout.addWidget(self.title_lbl)
        title_layout.addWidget(sub_lbl)
        header.addLayout(title_layout)

        btns_layout = QHBoxLayout()
        export_btn = QPushButton("📥 Exportar Mi Horario (Excel / CSV)")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; 
                color: white; 
                font-weight: bold; 
                padding: 10px 14px; 
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        export_btn.clicked.connect(self.export_csv)
        btns_layout.addWidget(export_btn)

        modal_btn = QPushButton("🔍 Ver en Pantalla Completa")
        modal_btn.setCursor(Qt.PointingHandCursor)
        modal_btn.setStyleSheet("""
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
        modal_btn.clicked.connect(self.open_modal_schedule)
        btns_layout.addWidget(modal_btn)

        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb; 
                color: white; 
                font-weight: bold; 
                padding: 10px 16px; 
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        refresh_btn.clicked.connect(self.load_schedule)
        btns_layout.addWidget(refresh_btn)

        header.addLayout(btns_layout)
        layout.addWidget(header_card)

        # Teacher Info Card
        self.info_card = QFrame()
        self.info_card.setStyleSheet("""
            QFrame {
                background-color: #f0fdf4; 
                border-left: 5px solid #16a34a; 
                border-radius: 6px; 
                padding: 10px 14px;
            }
        """)
        info_layout = QHBoxLayout(self.info_card)
        self.docente_info_lbl = QLabel("Docente: - | Tipo: - | Total Horas Asignadas: 0 hrs")
        self.docente_info_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #166534;")
        info_layout.addWidget(self.docente_info_lbl)
        layout.addWidget(self.info_card)

        # Controls bar with Slider
        controls_card = QFrame()
        controls_card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 14px;")
        c_layout = QHBoxLayout(controls_card)
        c_layout.setSpacing(12)

        dot_morning = QLabel(" ☀️ Mañana ")
        dot_morning.setStyleSheet("background-color: #e0f2fe; color: #0284c7; font-size: 11px; font-weight: bold; border-radius: 5px; padding: 2px 8px; border: 1px solid #0284c740;")
        dot_afternoon = QLabel(" ⛅ Tarde ")
        dot_afternoon.setStyleSheet("background-color: #d1fae5; color: #059669; font-size: 11px; font-weight: bold; border-radius: 5px; padding: 2px 8px; border: 1px solid #05966940;")
        dot_night = QLabel(" 🌙 Noche ")
        dot_night.setStyleSheet("background-color: #ede9fe; color: #7c3aed; font-size: 11px; font-weight: bold; border-radius: 5px; padding: 2px 8px; border: 1px solid #7c3aed40;")
        
        c_layout.addWidget(dot_morning)
        c_layout.addWidget(dot_afternoon)
        c_layout.addWidget(dot_night)
        c_layout.addStretch()
        layout.addWidget(controls_card)

        # Table + Lateral Slider Container
        # Timetable
        self.table = QTableWidget()
        self.days = [d.value for d in DayOfWeek]
        self.table.setColumnCount(len(self.days))
        self.table.setHorizontalHeaderLabels(self.days)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setMinimumWidth(180)
        self.table.verticalHeader().setDefaultSectionSize(55)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setMinimumHeight(470)
        self.table.setStyleSheet("""
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
        self.table.installEventFilter(self)
        layout.addWidget(self.table)

        # Breakdown table: Desglose de grupos y aulas
        breakdown_card = QFrame()
        breakdown_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px;")
        b_layout = QVBoxLayout(breakdown_card)
        b_layout.setContentsMargins(8, 8, 8, 8)
        
        b_title = QLabel("📋 Resumen de Grupos y Carga Semanal Asignada")
        b_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e293b; margin-bottom: 4px;")
        b_layout.addWidget(b_title)

        self.breakdown_table = QTableWidget()
        self.breakdown_table.setColumnCount(5)
        self.breakdown_table.setHorizontalHeaderLabels(["Asignatura", "Grupo", "Aula Asignada", "Horas Semanales", "Franja(s) Horaria(s)"])
        self.breakdown_table.horizontalHeader().setVisible(True)
        self.breakdown_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.breakdown_table.setMinimumHeight(180)
        self.breakdown_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #cbd5e1;
                background-color: #ffffff;
                color: #0f172a;
                font-size: 12px;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
            }
            QHeaderView {
                background-color: #1e293b;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 6px 10px;
                font-weight: 800;
                font-size: 11px;
                border: none;
                border-right: 1px solid #334155;
            }
        """)
        self.breakdown_table.installEventFilter(self)
        b_layout.addWidget(self.breakdown_table)
        layout.addWidget(breakdown_card)
        layout.addSpacing(20)
        self.load_schedule()

    def eventFilter(self, obj, event):
        if obj in (getattr(self, "table", None), getattr(self, "breakdown_table", None)) and event.type() == QEvent.Type.Wheel:
            parent_w = self.parent()
            while parent_w and not isinstance(parent_w, QScrollArea):
                parent_w = parent_w.parent()
            if parent_w:
                QApplication.sendEvent(parent_w.viewport(), event)
                return True
        return super().eventFilter(obj, event)

    def load_schedule(self):
        db = SessionLocal()
        try:
            teacher_id = session.teacher_id

            if not teacher_id:
                # Fallback for admin previewing
                first_t = db.query(Teacher).first()
                teacher_id = first_t.id if first_t else None

            if not teacher_id:
                return

            teacher = db.query(Teacher).filter_by(id=teacher_id).first()
            if not teacher:
                return

            # Eager load assignments and relationships
            assignments = list(teacher.assignments)
            for asg in assignments:
                _ = asg.group.subject.name if asg.group and asg.group.subject else None
                _ = asg.room.name if asg.room else None
                _ = asg.time_slot.shift if asg.time_slot else None

            slots = db.query(TimeSlot).all()
        finally:
            db.close()

        total_hours = len(assignments) * 2
        self.docente_info_lbl.setText(
            f"👤 Docente: {teacher.name} | 📜 Contrato: {teacher.teacher_type.value} | ⏱️ Total Horas Asignadas: {total_hours} hrs/semana"
        )

        SHIFT_ORDER = {
            ShiftType.MORNING: 0,
            ShiftType.AFTERNOON: 1,
            ShiftType.NIGHT: 2,
            "MAÑANA": 0,
            "TARDE": 1,
            "NOCHE": 2
        }
        sorted_slots = sorted(slots, key=lambda s: (SHIFT_ORDER.get(s.shift, 99), s.start_time))
        slot_map = {s.id: f"{s.shift.value}\n{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}" for s in sorted_slots}
        sorted_slot_ids = [s.id for s in sorted_slots]

        self.table.setRowCount(len(sorted_slot_ids))
        self.table.setVerticalHeaderLabels([slot_map[sid] for sid in sorted_slot_ids])

        # Clear cells
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                self.table.setItem(r, c, QTableWidgetItem(""))

        day_indices = {d: i for i, d in enumerate(self.days)}
        slot_indices = {sid: i for i, sid in enumerate(sorted_slot_ids)}

        # Populate schedule grid with elegant styling
        for asg in assignments:
            if asg.time_slot_id in slot_indices and asg.day.value in day_indices:
                r_idx = slot_indices[asg.time_slot_id]
                c_idx = day_indices[asg.day.value]

                text = f"📖 {asg.group.subject.name}\n👥 Grupo: {asg.group.name}\n📍 Aula: {asg.room.name} ({asg.room.room_type})"
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                # Soft blue background with dark blue text
                item.setBackground(QColor("#dbeafe"))
                item.setForeground(QColor("#1e3a8a"))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                self.table.setItem(r_idx, c_idx, item)

        self.table.resizeRowsToContents()

        # Populate breakdown summary table
        groups_seen = {}
        for asg in assignments:
            g_id = asg.group_id
            slot_str = f"{asg.day.value} ({asg.time_slot.start_time.strftime('%H:%M')}-{asg.time_slot.end_time.strftime('%H:%M')})"
            if g_id not in groups_seen:
                groups_seen[g_id] = {
                    "subject": asg.group.subject.name if asg.group and asg.group.subject else "-",
                    "group": asg.group.name if asg.group else "-",
                    "room": f"{asg.room.name} ({asg.room.room_type})" if asg.room else "-",
                    "slots_count": 1,
                    "times": [slot_str]
                }
            else:
                groups_seen[g_id]["slots_count"] += 1
                groups_seen[g_id]["times"].append(slot_str)

        self.breakdown_table.setRowCount(len(groups_seen))
        for row_idx, g_info in enumerate(groups_seen.values()):
            self.breakdown_table.setItem(row_idx, 0, QTableWidgetItem(g_info["subject"]))
            self.breakdown_table.setItem(row_idx, 1, QTableWidgetItem(g_info["group"]))
            self.breakdown_table.setItem(row_idx, 2, QTableWidgetItem(g_info["room"]))
            self.breakdown_table.setItem(row_idx, 3, QTableWidgetItem(f"{g_info['slots_count'] * 2} hrs"))
            self.breakdown_table.setItem(row_idx, 4, QTableWidgetItem(", ".join(g_info["times"])))


    def _on_lateral_slider_changed(self, value):
        self.table.verticalScrollBar().setValue(value)

    def _sync_lateral_slider_range(self, min_val, max_val):
        self.lateral_slider.setRange(min_val, max_val)

    def _sync_lateral_slider_value(self, value):
        self.lateral_slider.blockSignals(True)
        self.lateral_slider.setValue(value)
        self.lateral_slider.blockSignals(False)

    def export_csv(self):
        db = SessionLocal()
        try:
            teacher_id = session.teacher_id
            if not teacher_id:
                first_t = db.query(Teacher).first()
                teacher_id = first_t.id if first_t else None

            if not teacher_id:
                QMessageBox.warning(self, "Aviso", "No se encontró el docente actual.")
                return

            teacher = db.query(Teacher).filter_by(id=teacher_id).first()
            if not teacher or not teacher.assignments:
                QMessageBox.warning(self, "Exportación", "No tienes clases asignadas en el horario institucional.")
                return

            teacher_name = teacher.name if teacher else "Docente"
            raw_assignments = list(teacher.assignments)
            assignments = []
            for asg in raw_assignments:
                slot = asg.time_slot
                group = asg.group
                subj = group.subject if group else None
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
                    "teacher_name": teacher_name,
                    "teacher_type": teacher.teacher_type.value if hasattr(teacher.teacher_type, "value") else str(teacher.teacher_type),
                    "room_name": room.name if room else "",
                    "room_type": room.room_type if room else ""
                })

            clean_name = teacher_name.replace(" ", "_")
            export_schedule_dialog(
                self,
                f"Horario_{clean_name}.xlsx",
                self.table,
                assignments,
                title=f"Horario Semanal Docente - {teacher_name}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"No se pudo guardar el archivo:\n{e}")
        finally:
            db.close()

    def open_modal_schedule(self):
        db = SessionLocal()
        try:
            teacher_id = session.teacher_id
            if not teacher_id:
                first_t = db.query(Teacher).first()
                teacher_id = first_t.id if first_t else None

            if not teacher_id:
                QMessageBox.warning(self, "Aviso", "No se encontró el docente actual.")
                return

            teacher = db.query(Teacher).filter_by(id=teacher_id).first()
            if not teacher or not teacher.assignments:
                QMessageBox.warning(self, "Visualización", "No tienes clases asignadas en el horario institucional.")
                return

            assignments = []
            for asg in teacher.assignments:
                slot = asg.time_slot
                group = asg.group
                subj = group.subject if group else None
                room = asg.room
                day_val = asg.day.value if hasattr(asg.day, "value") else str(asg.day)
                assignments.append({
                    "id": asg.id,
                    "time_slot_id": asg.time_slot_id,
                    "group_id": asg.group_id,
                    "teacher_id": asg.teacher_id,
                    "room_id": asg.room_id,
                    "day": day_val,
                    "shift": slot.shift.value if slot and hasattr(slot.shift, "value") else (str(slot.shift) if slot else ""),
                    "start_time": slot.start_time.strftime('%H:%M') if slot and slot.start_time else "",
                    "end_time": slot.end_time.strftime('%H:%M') if slot and slot.end_time else "",
                    "subject_name": subj.name if subj else "",
                    "group_name": group.name if group else "",
                    "teacher_name": teacher.name,
                    "room_name": f"{room.name} ({room.room_type})" if room else ""
                })

            total_hours = len(assignments) * 2
            dialog = SchedulePreviewDialog(
                title_text=f"Horario Docente: {teacher.name} ({teacher.teacher_type.value} - {total_hours} hrs/sem)",
                assignments_data=assignments,
                metrics={"global_score": 100},
                parent=self
            )
            dialog.exec()
        finally:
            db.close()

