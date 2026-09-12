from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, 
    QButtonGroup, QPushButton, QMessageBox, QGroupBox, QFrame
)
from PySide6.QtCore import Qt
from app.database.database import SessionLocal
from app.database.models import Student, StudentPreference, ShiftType
from app.auth.session import session

class StudentPreferencesView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 16px 20px;
            }
        """)
        h_layout = QVBoxLayout(header_card)
        h_layout.setSpacing(4)

        title = QLabel("Preferencia de Jornada Académica")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #1e3a8a;")
        
        subtitle = QLabel("Indica tu jornada horaria de preferencia para que el algoritmo optimice tu horario personal.")
        subtitle.setStyleSheet("font-size: 13px; color: #64748b;")
        
        h_layout.addWidget(title)
        h_layout.addWidget(subtitle)
        layout.addWidget(header_card)

        # Preference Options Card
        opts_card = QFrame()
        opts_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        opts_layout = QVBoxLayout(opts_card)
        opts_layout.setSpacing(14)

        group_lbl = QLabel("<b>Selecciona tu Jornada Principal de Estudio:</b>")
        group_lbl.setStyleSheet("font-size: 15px; color: #1e293b;")
        opts_layout.addWidget(group_lbl)

        self.btn_group = QButtonGroup(self)

        # Option 1: Morning
        opt1_frame = self._create_option_frame("☀️ Jornada Mañana", "08:00 a 12:00", "#e0f2fe", "#0284c7")
        self.rb_morning = QRadioButton("☀️ Mañana (08:00 - 12:00)")
        self.rb_morning.setStyleSheet("font-size: 14px; font-weight: 700; color: #0f172a;")
        opt1_frame.layout().addWidget(self.rb_morning)
        self.btn_group.addButton(self.rb_morning, 1)
        opts_layout.addWidget(opt1_frame)

        # Option 2: Afternoon
        opt2_frame = self._create_option_frame("⛅ Jornada Tarde", "13:00 a 17:00", "#d1fae5", "#059669")
        self.rb_afternoon = QRadioButton("⛅ Tarde (13:00 - 17:00)")
        self.rb_afternoon.setStyleSheet("font-size: 14px; font-weight: 700; color: #0f172a;")
        opt2_frame.layout().addWidget(self.rb_afternoon)
        self.btn_group.addButton(self.rb_afternoon, 2)
        opts_layout.addWidget(opt2_frame)

        # Option 3: Night
        opt3_frame = self._create_option_frame("🌙 Jornada Noche", "18:00 a 22:00", "#ede9fe", "#7c3aed")
        self.rb_night = QRadioButton("🌙 Noche (18:00 - 22:00)")
        self.rb_night.setStyleSheet("font-size: 14px; font-weight: 700; color: #0f172a;")
        opt3_frame.layout().addWidget(self.rb_night)
        self.btn_group.addButton(self.rb_night, 3)
        opts_layout.addWidget(opt3_frame)

        # Save Button
        save_btn = QPushButton("💾 GUARDAR MI PREFERENCIA DE JORNADA")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: #ffffff;
                font-size: 14px;
                font-weight: 800;
                padding: 12px;
                border-radius: 8px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
        """)
        save_btn.clicked.connect(self.save_preference)
        opts_layout.addWidget(save_btn)

        layout.addWidget(opts_card)
        layout.addStretch()

        self.load_preference()

    def _create_option_frame(self, title, hours, bg_color, border_color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1.5px solid {border_color};
                border-radius: 10px;
                padding: 10px 14px;
            }}
            QFrame:hover {{
                background-color: #ffffff;
                border-color: #4f46e5;
            }}
        """)
        l = QHBoxLayout(frame)
        l.setContentsMargins(10, 8, 10, 8)
        return frame

    def load_preference(self):
        db = SessionLocal()
        try:
            student_id = session.student_id
            if not student_id:
                s = db.query(Student).first()
                student_id = s.id if s else None

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
            else:
                self.rb_morning.setChecked(True)
        finally:
            db.close()

    def save_preference(self):
        db = SessionLocal()
        try:
            student_id = session.student_id
            if not student_id:
                s = db.query(Student).first()
                student_id = s.id if s else 1

            selected_id = self.btn_group.checkedId()
            if selected_id == 1:
                shift = ShiftType.MORNING
            elif selected_id == 2:
                shift = ShiftType.AFTERNOON
            elif selected_id == 3:
                shift = ShiftType.NIGHT
            else:
                QMessageBox.warning(self, "Atención", "Por favor selecciona una jornada.")
                return

            pref = db.query(StudentPreference).filter_by(student_id=student_id, priority=1).first()
            if not pref:
                pref = StudentPreference(student_id=student_id, shift=shift, priority=1)
                db.add(pref)
            else:
                pref.shift = shift

            db.commit()
            QMessageBox.information(
                self, "Preferencia Registrada", 
                "Tu preferencia de jornada horaria ha sido guardada exitosamente."
            )
        finally:
            db.close()
