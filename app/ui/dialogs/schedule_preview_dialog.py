from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QFrame, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
import csv
from app.database.database import get_db, SessionLocal
from app.database.models import TimeSlot, DayOfWeek

class SchedulePreviewDialog(QDialog):
    """
    Modal dialog to preview full weekly schedule alternatives with 
    rich pastel visual cards and instant CSV export.
    """
    def __init__(self, title_text, groups_data=None, assignments_data=None, metrics=None, parent=None, on_confirm_callback=None):
        super().__init__(parent)
        self.title_text = title_text
        self.groups_data = groups_data or [] # For student optimizer format [(subj_id, group_id, group_info), ...]
        self.assignments_data = assignments_data or [] # For institutional format [{'group_id': ..., 'day': ..., ...}]
        self.metrics = metrics or {}
        self.on_confirm_callback = on_confirm_callback
        self.days = [d.value for d in DayOfWeek]
        
        self.setWindowTitle(f"OptiSchedule UMB - Vista Previa: {self.title_text}")
        self.resize(1000, 680)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #f8fafc);
                border: 1.5px solid #e2e8f0;
                border-radius: 12px;
                padding: 14px 18px;
            }
        """)
        h_layout = QHBoxLayout(header_card)

        info_col = QVBoxLayout()
        title_lbl = QLabel(self.title_text)
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #1e3a8a;")
        
        subtitle_text = "Distribución semanal de clases, docentes asignados y aulas correspondientes."
        sub_lbl = QLabel(subtitle_text)
        sub_lbl.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 500;")
        
        info_col.addWidget(title_lbl)
        info_col.addWidget(sub_lbl)
        h_layout.addLayout(info_col)

        # Global Score Badge
        global_score = self.metrics.get("global_score", None)
        if global_score is not None:
            score_frame = QFrame()
            score_frame.setStyleSheet("""
                background-color: #ecfdf5;
                border: 1.5px solid #10b981;
                border-radius: 10px;
                padding: 6px 14px;
            """)
            s_layout = QVBoxLayout(score_frame)
            s_layout.setContentsMargins(4, 4, 4, 4)
            s_layout.setAlignment(Qt.AlignCenter)
            
            s_title = QLabel("CALIDAD GLOBAL")
            s_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #065f46;")
            s_title.setAlignment(Qt.AlignCenter)
            
            s_val = QLabel(f"{global_score}%")
            s_val.setStyleSheet("font-size: 20px; font-weight: 800; color: #047857;")
            s_val.setAlignment(Qt.AlignCenter)
            
            s_layout.addWidget(s_title)
            s_layout.addWidget(s_val)
            h_layout.addWidget(score_frame)

        layout.addWidget(header_card)

        # Metrics Pills Bar
        if self.metrics:
            pills_layout = QHBoxLayout()
            pills_layout.setSpacing(10)

            if "shift_score" in self.metrics:
                pills_layout.addWidget(self._create_pill("Jornada Coincidente", f"{self.metrics['shift_score']}%", "#0284c7", "#f0f9ff"))
            if "compactness_score" in self.metrics:
                pills_layout.addWidget(self._create_pill("Sin Huecos / Ventanas", f"{self.metrics['compactness_score']}%", "#8b5cf6", "#f5f3ff"))
            if "free_days" in self.metrics:
                pills_layout.addWidget(self._create_pill("Días Libres", f"{self.metrics['free_days']} días", "#10b981", "#ecfdf5"))
            if "subjects_included" in self.metrics:
                pills_layout.addWidget(self._create_pill("Materias Asignadas", f"{self.metrics['subjects_included']}/{self.metrics.get('total_requested', '-')}", "#f59e0b", "#fffbeb"))
            
            pills_layout.addStretch()
            layout.addLayout(pills_layout)

        # Timetable Grid
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.days))
        self.table.setHorizontalHeaderLabels(self.days)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #0f172a;
                gridline-color: #e2e8f0;
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 9px;
                font-weight: 700;
                font-size: 12px;
                border: none;
                border-right: 1px solid #334155;
            }
        """)
        layout.addWidget(self.table)

        # Action Buttons Footer
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        export_btn = QPushButton("📥 Exportar Esta Alternativa (CSV)")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: 700;
                padding: 10px 18px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        export_btn.clicked.connect(self.export_csv)
        footer_layout.addWidget(export_btn)

        footer_layout.addStretch()

        if self.on_confirm_callback:
            confirm_btn = QPushButton("✅ Inscribir / Seleccionar Este Horario")
            confirm_btn.setCursor(Qt.PointingHandCursor)
            confirm_btn.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: #ffffff;
                    font-weight: 800;
                    padding: 10px 22px;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """)
            confirm_btn.clicked.connect(self._handle_confirm)
            footer_layout.addWidget(confirm_btn)

        close_btn = QPushButton("Cerrar")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #475569;
                border: 1.5px solid #cbd5e1;
                font-weight: 700;
                padding: 10px 18px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #0f172a;
            }
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)

        layout.addLayout(footer_layout)

        self.populate_grid()

    def _create_pill(self, label, value, text_color, bg_color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            background-color: {bg_color};
            border: 1px solid {text_color}40;
            border-radius: 7px;
            padding: 4px 10px;
        """)
        l = QHBoxLayout(frame)
        l.setContentsMargins(6, 3, 6, 3)
        l.setSpacing(6)
        
        lbl = QLabel(f"{label}:")
        lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {text_color};")
        val = QLabel(f"<b>{value}</b>")
        val.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {text_color};")
        l.addWidget(lbl)
        l.addWidget(val)
        return frame

    def populate_grid(self):
        db = SessionLocal()
        try:
            slots = db.query(TimeSlot).all()
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

        # If student optimizer groups format
        if self.groups_data:
            for item in self.groups_data:
                g_info = item[2] if isinstance(item, (list, tuple)) and len(item) == 3 else item
                if isinstance(g_info, dict) and "slots" in g_info:
                    for s in g_info["slots"]:
                        if s["time_slot_id"] in slot_indices and s["day"] in day_indices:
                            r_idx = slot_indices[s["time_slot_id"]]
                            c_idx = day_indices[s["day"]]

                            text = (
                                f"📘 {g_info.get('subject_name', '')}\n"
                                f"👥 {g_info.get('group_name', '')}\n"
                                f"👨‍🏫 {g_info.get('teacher_name', '')}\n"
                                f"📍 {g_info.get('room_name', '')}"
                            )
                            cell_item = QTableWidgetItem(text)
                            cell_item.setTextAlignment(Qt.AlignCenter)
                            self.table.setItem(r_idx, c_idx, cell_item)

        # If institutional assignments format
        elif self.assignments_data:
            for asg in self.assignments_data:
                time_slot_id = asg.get("time_slot_id")
                day_val = asg.get("day")
                if hasattr(day_val, "value"):
                    day_val = day_val.value

                if time_slot_id in slot_indices and day_val in day_indices:
                    r_idx = slot_indices[time_slot_id]
                    c_idx = day_indices[day_val]

                    text = (
                        f"📘 {asg.get('subject_name', '')} ({asg.get('group_name', '')})\n"
                        f"👨‍🏫 {asg.get('teacher_name', '')}\n"
                        f"📍 {asg.get('room_name', '')}"
                    )
                    curr = self.table.item(r_idx, c_idx)
                    if curr and curr.text():
                        curr.setText(curr.text() + f"\n\n─────────────\n\n{text}")
                    else:
                        cell_item = QTableWidgetItem(text)
                        cell_item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(r_idx, c_idx, cell_item)

        self.table.resizeRowsToContents()

    def _handle_confirm(self):
        if self.on_confirm_callback:
            self.on_confirm_callback()
        self.accept()

    def export_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar Horario", f"{self.title_text}.csv", "Archivos CSV (*.csv)")
        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Fila / Horario", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                for r in range(self.table.rowCount()):
                    row_data = [self.table.verticalHeaderItem(r).text().replace("\n", " ")]
                    for c in range(self.table.columnCount()):
                        item = self.table.item(r, c)
                        text = item.text().replace("\n", " | ") if item else ""
                        row_data.append(text)
                    writer.writerow(row_data)
            QMessageBox.information(self, "Exportación Exitosa", f"Horario exportado con éxito a:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar", f"No se pudo exportar el horario:\n{e}")
