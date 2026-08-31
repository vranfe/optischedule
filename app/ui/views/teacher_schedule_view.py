from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from app.database.database import get_db
from app.database.models import Teacher, ScheduleAssignment, TimeSlot, DayOfWeek
from app.auth.session import session

class TeacherScheduleView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        self.title_lbl = QLabel("Mi Horario de Clases Asignadas")
        self.title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e3a8a;")
        header.addWidget(self.title_lbl)

        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
        refresh_btn.clicked.connect(self.load_schedule)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Teacher Info Card
        self.info_card = QFrame()
        self.info_card.setStyleSheet("background-color: #eff6ff; border-left: 5px solid #3b82f6; border-radius: 6px; padding: 12px;")
        info_layout = QHBoxLayout(self.info_card)
        self.docente_info_lbl = QLabel("Docente: - | Tipo: - | Total Horas Asignadas: 0 hrs")
        self.docente_info_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e40af;")
        info_layout.addWidget(self.docente_info_lbl)
        layout.addWidget(self.info_card)

        # Timetable
        self.table = QTableWidget()
        self.days = [d.value for d in DayOfWeek]
        self.table.setColumnCount(len(self.days))
        self.table.setHorizontalHeaderLabels(self.days)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d1d5db;
                background-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #f3f4f6;
                padding: 6px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)

        self.load_schedule()

    def load_schedule(self):
        db = next(get_db())
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

        total_hours = len(teacher.assignments) * 2
        self.docente_info_lbl.setText(f"Docente: {teacher.name} | Contrato: {teacher.teacher_type.value} | Total Horas Asignadas: {total_hours} hrs")

        slots = db.query(TimeSlot).all()
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

        for asg in teacher.assignments:
            if asg.time_slot_id in slot_indices and asg.day.value in day_indices:
                r_idx = slot_indices[asg.time_slot_id]
                c_idx = day_indices[asg.day.value]

                text = f"📖 {asg.group.subject.name}\n👥 Grupo: {asg.group.name}\n📍 Aula: {asg.room.name} ({asg.room.room_type})"
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(Qt.cyan)
                self.table.setItem(r_idx, c_idx, item)

        self.table.resizeRowsToContents()
