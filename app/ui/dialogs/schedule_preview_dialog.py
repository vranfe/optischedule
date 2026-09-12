from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QFrame, QFileDialog, 
    QMessageBox, QSlider, QScrollArea
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
import csv
from app.database.database import SessionLocal
from app.database.models import TimeSlot, DayOfWeek, ShiftType

class SchedulePreviewDialog(QDialog):
    """
    Modal dialog to preview full weekly schedule alternatives with 
    zoom slider, distinct shift color bands, and instant CSV export.
    """
    def __init__(self, title_text, groups_data=None, assignments_data=None, metrics=None, parent=None, on_confirm_callback=None):
        super().__init__(parent)
        self.title_text = title_text
        self.groups_data = groups_data or [] # For student optimizer format [(subj_id, group_id, group_info), ...]
        self.assignments_data = assignments_data or [] # For institutional format [{'group_id': ..., 'day': ..., ...}]
        self.metrics = metrics or {}
        self.on_confirm_callback = on_confirm_callback
        self.days = [d.value for d in DayOfWeek]
        self.base_row_height = 54
        
        self.setWindowTitle(f"OptiSchedule UMB - Vista Previa: {self.title_text}")
        self.resize(1080, 720)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 12px;
                padding: 12px 18px;
            }
        """)
        h_layout = QHBoxLayout(header_card)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        title_lbl = QLabel(self.title_text)
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #1e3a8a;")
        
        subtitle_text = "Matriz semanal completa con diferenciación por jornadas horarias (Mañana, Tarde, Noche)."
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

        # Controls & Metrics Bar (Pills + Zoom Slider + Shift Legend)
        controls_bar = QFrame()
        controls_bar.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 12px;")
        c_layout = QHBoxLayout(controls_bar)
        c_layout.setSpacing(12)

        # Shift Legend Pills
        c_layout.addWidget(self._create_legend_dot("☀️ Mañana (8-12)", "#0284c7", "#e0f2fe"))
        c_layout.addWidget(self._create_legend_dot("⛅ Tarde (13-17)", "#059669", "#d1fae5"))
        c_layout.addWidget(self._create_legend_dot("🌙 Noche (18-22)", "#7c3aed", "#ede9fe"))

        c_layout.addStretch()

        # Zoom Slider
        zoom_label = QLabel("🔍 <b>Escala de Celdas:</b>")
        zoom_label.setStyleSheet("color: #334155; font-size: 12px;")
        c_layout.addWidget(zoom_label)

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(80, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(140)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        c_layout.addWidget(self.zoom_slider)

        self.zoom_val_lbl = QLabel("100%")
        self.zoom_val_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #4f46e5; min-width: 35px;")
        c_layout.addWidget(self.zoom_val_lbl)

        layout.addWidget(controls_bar)

        # Timetable Grid
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.days))
        self.table.setHorizontalHeaderLabels(self.days)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setMinimumWidth(200)
        self.table.verticalHeader().setDefaultSectionSize(self.base_row_height)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #0f172a;
                gridline-color: #cbd5e1;
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
        layout.addWidget(self.table)

        # Action Buttons Footer
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        export_btn = QPushButton("📥 Exportar Horario a CSV")
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
                color: #334155;
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

    def _create_legend_dot(self, text, color, bg):
        lbl = QLabel(f" {text} ")
        lbl.setStyleSheet(f"background-color: {bg}; color: {color}; font-size: 11px; font-weight: bold; border-radius: 5px; padding: 3px 8px; border: 1px solid {color}40;")
        return lbl

    def on_zoom_changed(self, value):
        self.zoom_val_lbl.setText(f"{value}%")
        scale = value / 100.0
        new_height = int(self.base_row_height * scale)
        self.table.verticalHeader().setDefaultSectionSize(new_height)
        
        # Adjust cell font size
        new_font_size = max(9, min(16, int(11 * scale)))
        font = self.table.font()
        font.setPointSize(new_font_size)
        self.table.setFont(font)
        self.table.resizeRowsToContents()

    def populate_grid(self):
        db = SessionLocal()
        try:
            slots = db.query(TimeSlot).all()
        finally:
            db.close()

        if not slots:
            return

        sorted_slots = sorted(slots, key=lambda s: (s.shift.value, s.start_time))
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

        # Shift-based pastel background colors
        shift_colors = {
            ShiftType.MORNING: {"bg": "#f0f9ff", "border": "#0284c7", "text": "#0369a1"},
            ShiftType.AFTERNOON: {"bg": "#f0fdf4", "border": "#10b981", "text": "#047857"},
            ShiftType.NIGHT: {"bg": "#faf5ff", "border": "#8b5cf6", "text": "#5b21b6"}
        }

        # If student optimizer groups format
        if self.groups_data:
            for item in self.groups_data:
                g_info = item[2] if isinstance(item, (list, tuple)) and len(item) == 3 else item
                if isinstance(g_info, dict) and "slots" in g_info:
                    for s in g_info["slots"]:
                        if s["time_slot_id"] in slot_indices and s["day"] in day_indices:
                            r_idx = slot_indices[s["time_slot_id"]]
                            c_idx = day_indices[s["day"]]

                            # Determine slot shift
                            slot_obj = next((sl for sl in sorted_slots if sl.id == s["time_slot_id"]), None)
                            shift_theme = shift_colors.get(slot_obj.shift, {"bg": "#f8fafc", "text": "#0f172a"}) if slot_obj else {"bg": "#f8fafc", "text": "#0f172a"}

                            text = (
                                f"📘 {g_info.get('subject_name', '')}\n"
                                f"👥 Grupo: {g_info.get('group_name', '')}\n"
                                f"👨‍🏫 {g_info.get('teacher_name', '')}\n"
                                f"📍 {g_info.get('room_name', '')}"
                            )
                            cell_item = QTableWidgetItem(text)
                            cell_item.setTextAlignment(Qt.AlignCenter)
                            cell_item.setBackground(QColor(shift_theme["bg"]))
                            cell_item.setForeground(QColor(shift_theme["text"]))
                            font = cell_item.font()
                            font.setBold(True)
                            cell_item.setFont(font)
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

                    slot_obj = next((sl for sl in sorted_slots if sl.id == time_slot_id), None)
                    shift_theme = shift_colors.get(slot_obj.shift, {"bg": "#f8fafc", "text": "#0f172a"}) if slot_obj else {"bg": "#f8fafc", "text": "#0f172a"}

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
                        cell_item.setBackground(QColor(shift_theme["bg"]))
                        cell_item.setForeground(QColor(shift_theme["text"]))
                        font = cell_item.font()
                        font.setBold(True)
                        cell_item.setFont(font)
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
