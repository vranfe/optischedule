from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QFrame,
    QFileDialog, QMessageBox
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
import csv
from app.database.database import SessionLocal
from app.database.models import Teacher, ScheduleAssignment, TimeSlot, DayOfWeek
from app.auth.session import session

class TeacherScheduleView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

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
        export_btn = QPushButton("📥 Exportar Mi Horario (CSV)")
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

        slider_lbl = QLabel("🎚️ <b>Ajuste de Visualización / Altura:</b>")
        slider_lbl.setStyleSheet("color: #334155; font-size: 12px;")
        c_layout.addWidget(slider_lbl)

        from PySide6.QtWidgets import QSlider
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(45, 130)
        self.zoom_slider.setValue(55)
        self.zoom_slider.setFixedWidth(140)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        c_layout.addWidget(self.zoom_slider)

        self.zoom_val_lbl = QLabel("55 px")
        self.zoom_val_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #4f46e5; min-width: 40px;")
        c_layout.addWidget(self.zoom_val_lbl)

        layout.addWidget(controls_card)

        # Table + Lateral Slider Container
        table_container = QHBoxLayout()
        table_container.setSpacing(8)

        # Timetable
        self.table = QTableWidget()
        self.days = [d.value for d in DayOfWeek]
        self.table.setColumnCount(len(self.days))
        self.table.setHorizontalHeaderLabels(self.days)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setMinimumWidth(180)
        self.table.verticalHeader().setDefaultSectionSize(55)
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
        table_container.addWidget(self.table, 1)

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
        bot_icon.setStyleSheet("font-size: 12px;")

        lateral_box.addWidget(top_icon)
        lateral_box.addWidget(self.lateral_slider, 1)
        lateral_box.addWidget(bot_icon)

        table_container.addLayout(lateral_box)
        layout.addLayout(table_container)

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
        self.breakdown_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.breakdown_table.setMaximumHeight(150)
        self.breakdown_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e2e8f0;
                background-color: #ffffff;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                color: #334155;
                padding: 6px;
                font-weight: 600;
            }
        """)
        b_layout.addWidget(self.breakdown_table)
        layout.addWidget(breakdown_card)

        self.load_schedule()

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

        slot_map = {s.id: f"{s.shift.value}\n{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}" for s in slots}
        sorted_slot_ids = sorted(slot_map.keys(), key=lambda sid: slot_map[sid])

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

    def on_zoom_changed(self, value):
        self.zoom_val_lbl.setText(f"{value} px")
        self.table.verticalHeader().setDefaultSectionSize(value)
        font_size = max(10, min(14, int(9 + (value - 45) * 0.06)))
        font = self.table.font()
        font.setPointSize(font_size)
        self.table.setFont(font)
        self.table.resizeRowsToContents()

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

            assignments = list(teacher.assignments)
            for asg in assignments:
                _ = asg.time_slot
                _ = asg.group.subject if asg.group else None
                _ = asg.room
            teacher_name = teacher.name
        finally:
            db.close()

        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar Mi Horario", f"Horario_{teacher_name.replace(' ', '_')}.csv", "Archivos CSV (*.csv)")
        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                
                # 1. Weekly 2D Timetable Matrix
                writer.writerow([f"=== HORARIO SEMANAL DOCENTE - {teacher_name.upper()} ==="])
                writer.writerow(["Franja Horaria / Jornada", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                for r in range(self.table.rowCount()):
                    header_item = self.table.verticalHeaderItem(r)
                    row_header = header_item.text().replace("\n", " ") if header_item else f"Franja {r+1}"
                    row_data = [row_header]
                    for c in range(self.table.columnCount()):
                        item = self.table.item(r, c)
                        text = item.text().replace("\n", " | ") if item and item.text() else "---"
                        row_data.append(text)
                    writer.writerow(row_data)
                
                writer.writerow([])
                writer.writerow(["=== DESGLOSE DETALLADO DE CLASES ==="])
                writer.writerow(["Día", "Jornada", "Hora Inicio", "Hora Fin", "Asignatura", "Semestre", "Grupo", "Aula", "Tipo Aula"])
                for asg in assignments:
                    slot = asg.time_slot
                    writer.writerow([
                        asg.day.value,
                        slot.shift.value if slot else "",
                        slot.start_time.strftime('%H:%M') if slot else "",
                        slot.end_time.strftime('%H:%M') if slot else "",
                        asg.group.subject.name if asg.group and asg.group.subject else "",
                        asg.group.subject.semester_id if asg.group and asg.group.subject else "",
                        asg.group.name if asg.group else "",
                        asg.room.name if asg.room else "",
                        asg.room.room_type if asg.room else ""
                    ])
            QMessageBox.information(self, "Exportación Exitosa", f"Tu horario se ha exportado correctamente a:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"No se pudo guardar el archivo:\n{e}")
