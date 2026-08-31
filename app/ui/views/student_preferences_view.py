from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, 
    QButtonGroup, QPushButton, QMessageBox, QGroupBox
)
from app.database.database import get_db
from app.database.models import Student, StudentPreference, ShiftType
from app.auth.session import session

class StudentPreferencesView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Preferencia de Jornada Académica")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e3a8a;")
        subtitle = QLabel("Indique su preferencia de horario para la asignación de materias del semestre")
        subtitle.setStyleSheet("font-size: 13px; color: #6b7280; margin-bottom: 15px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        group = QGroupBox("Seleccione su Jornada Principal")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; color: #1e3a8a; }")
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(15)

        self.btn_group = QButtonGroup(self)
        self.rb_morning = QRadioButton("☀️ Jornada Mañana (08:00 - 12:00)")
        self.rb_afternoon = QRadioButton("⛅ Jornada Tarde (13:00 - 17:00)")
        self.rb_night = QRadioButton("🌙 Jornada Noche (18:00 - 22:00)")

        self.btn_group.addButton(self.rb_morning, 1)
        self.btn_group.addButton(self.rb_afternoon, 2)
        self.btn_group.addButton(self.rb_night, 3)

        g_layout.addWidget(self.rb_morning)
        g_layout.addWidget(self.rb_afternoon)
        g_layout.addWidget(self.rb_night)

        layout.addWidget(group)

        save_btn = QPushButton("💾 Guardar Mi Preferencia")
        save_btn.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        save_btn.clicked.connect(self.save_preference)
        layout.addWidget(save_btn)

        layout.addStretch()
        self.load_preference()

    def load_preference(self):
        db = next(get_db())
        student_id = session.student_id
        if not student_id:
            return

        pref = db.query(StudentPreference).filter_by(student_id=student_id, priority=1).first()
        if pref:
            if pref.shift == ShiftType.MORNING:
                self.rb_morning.setChecked(True)
            elif pref.shift == ShiftType.AFTERNOON:
                self.rb_afternoon.setChecked(True)
            elif pref.shift == ShiftType.NIGHT:
                self.rb_night.setChecked(True)

    def save_preference(self):
        db = next(get_db())
        student_id = session.student_id
        if not student_id:
            return

        selected_id = self.btn_group.checkedId()
        if selected_id == 1:
            shift = ShiftType.MORNING
        elif selected_id == 2:
            shift = ShiftType.AFTERNOON
        elif selected_id == 3:
            shift = ShiftType.NIGHT
        else:
            QMessageBox.warning(self, "Atención", "Por favor seleccione una jornada.")
            return

        # Update or create
        pref = db.query(StudentPreference).filter_by(student_id=student_id, priority=1).first()
        if not pref:
            pref = StudentPreference(student_id=student_id, shift=shift, priority=1)
            db.add(pref)
        else:
            pref.shift = shift

        db.commit()
        QMessageBox.information(self, "Guardado", "Su preferencia de jornada ha sido registrada exitosamente.")
