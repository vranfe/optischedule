from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, 
    QTableWidget, QTableWidgetItem, QCheckBox, QPushButton, 
    QComboBox, QMessageBox, QHeaderView, QSlider
)
from PySide6.QtCore import Qt
from app.database.database import get_db
from app.database.models import (
    Teacher, Subject, TimeSlot, DayOfWeek, TeacherAvailability, 
    TeacherSubjectPreference, ShiftType, Student, StudentPreference
)
from app.auth.session import session

class PreferencesView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        title_layout = QVBoxLayout()
        title = QLabel("Gestión de Disponibilidad y Preferencias")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e3a8a;")
        subtitle = QLabel("Registro de franjas horarias disponibles y asignaturas de preferencia para el algoritmo")
        subtitle.setStyleSheet("font-size: 13px; color: #6b7280;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)

        # Teacher selector if admin
        self.teacher_selector = QComboBox()
        self.teacher_selector.setMinimumWidth(200)
        self.teacher_selector.currentIndexChanged.connect(self.load_teacher_data)
        header.addWidget(self.teacher_selector)

        save_btn = QPushButton("💾 Guardar Preferencias")
        save_btn.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold; padding: 10px 18px; border-radius: 6px;")
        save_btn.clicked.connect(self.save_data)
        header.addWidget(save_btn)

        layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: Availability Matrix
        self.avail_tab = QWidget()
        avail_layout = QVBoxLayout(self.avail_tab)
        avail_info = QLabel("Marque las casillas en los días y horarios en los que el docente se encuentra disponible para dictar clase:")
        avail_info.setStyleSheet("font-size: 13px; color: #374151; margin-bottom: 5px;")
        avail_layout.addWidget(avail_info)

        self.avail_table = QTableWidget()
        self.days = [d.value for d in DayOfWeek]
        self.avail_table.setColumnCount(len(self.days))
        self.avail_table.setHorizontalHeaderLabels(self.days)
        self.avail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        avail_layout.addWidget(self.avail_table)

        self.tabs.addTab(self.avail_tab, "🗓️ Disponibilidad Semanal")

        # Tab 2: Subject Preferences
        self.pref_tab = QWidget()
        pref_layout = QVBoxLayout(self.pref_tab)
        pref_info = QLabel("Seleccione el nivel de preferencia/afinidad (1 = Baja, 5 = Muy Alta) para cada asignatura:")
        pref_info.setStyleSheet("font-size: 13px; color: #374151; margin-bottom: 5px;")
        pref_layout.addWidget(pref_info)

        self.pref_table = QTableWidget()
        self.pref_table.setColumnCount(4)
        self.pref_table.setHorizontalHeaderLabels(["ID", "Asignatura", "Semestre", "Nivel de Afinidad (1 - 5)"])
        self.pref_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        pref_layout.addWidget(self.pref_table)

        self.tabs.addTab(self.pref_tab, "📚 Afinidad de Asignaturas")

        layout.addWidget(self.tabs)

        self.load_teachers()

    def load_teachers(self):
        db = next(get_db())
        teachers = db.query(Teacher).all()
        
        self.teacher_selector.clear()
        if session.teacher_id:
            # Locked to logged teacher
            curr = db.query(Teacher).filter_by(id=session.teacher_id).first()
            if curr:
                self.teacher_selector.addItem(f"{curr.name} ({curr.teacher_type.value})", curr.id)
                self.teacher_selector.setEnabled(False)
        else:
            for t in teachers:
                self.teacher_selector.addItem(f"{t.name} ({t.teacher_type.value})", t.id)
            self.teacher_selector.setEnabled(True)

        self.load_teacher_data()

    def load_teacher_data(self):
        if self.teacher_selector.count() == 0:
            return

        teacher_id = self.teacher_selector.currentData()
        if not teacher_id:
            return

        db = next(get_db())
        slots = db.query(TimeSlot).all()
        slot_map = {s.id: f"{s.shift.value}: {s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}" for s in slots}
        self.sorted_slot_ids = sorted(slot_map.keys(), key=lambda sid: slot_map[sid])

        # Setup availability table
        self.avail_table.setRowCount(len(self.sorted_slot_ids))
        self.avail_table.setVerticalHeaderLabels([slot_map[sid] for sid in self.sorted_slot_ids])

        # Get existing availabilities
        avails = db.query(TeacherAvailability).filter_by(teacher_id=teacher_id).all()
        avail_set = {(a.day.value, a.time_slot_id) for a in avails}

        self.checkbox_map = {}
        for r_idx, sid in enumerate(self.sorted_slot_ids):
            for c_idx, day_val in enumerate(self.days):
                cb = QCheckBox()
                cb.setChecked((day_val, sid) in avail_set)
                
                cell_widget = QWidget()
                cell_layout = QHBoxLayout(cell_widget)
                cell_layout.addWidget(cb)
                cell_layout.setAlignment(Qt.AlignCenter)
                cell_layout.setContentsMargins(0, 0, 0, 0)
                
                self.avail_table.setCellWidget(r_idx, c_idx, cell_widget)
                self.checkbox_map[(day_val, sid)] = cb

        # Setup subject preferences table
        subjects = db.query(Subject).all()
        self.pref_table.setRowCount(len(subjects))

        existing_prefs = {p.subject_id: p.preference_score for p in db.query(TeacherSubjectPreference).filter_by(teacher_id=teacher_id).all()}

        self.pref_combos = {}
        for row_idx, subj in enumerate(subjects):
            self.pref_table.setItem(row_idx, 0, QTableWidgetItem(str(subj.id)))
            self.pref_table.setItem(row_idx, 1, QTableWidgetItem(subj.name))
            self.pref_table.setItem(row_idx, 2, QTableWidgetItem(f"Semestre {subj.semester_id}"))

            combo = QComboBox()
            combo.addItem("⭐ 1 - Muy Baja", 1)
            combo.addItem("⭐⭐ 2 - Baja", 2)
            combo.addItem("⭐⭐⭐ 3 - Media", 3)
            combo.addItem("⭐⭐⭐⭐ 4 - Alta", 4)
            combo.addItem("⭐⭐⭐⭐⭐ 5 - Muy Alta", 5)
            
            score = existing_prefs.get(subj.id, 3)
            combo.setCurrentIndex(score - 1)

            self.pref_table.setCellWidget(row_idx, 3, combo)
            self.pref_combos[subj.id] = combo

    def save_data(self):
        teacher_id = self.teacher_selector.currentData()
        if not teacher_id:
            return

        db = next(get_db())

        # 1. Update Availabilities
        db.query(TeacherAvailability).filter_by(teacher_id=teacher_id).delete()
        for (day_val, sid), cb in self.checkbox_map.items():
            if cb.isChecked():
                day_enum = next(d for d in DayOfWeek if d.value == day_val)
                avail = TeacherAvailability(teacher_id=teacher_id, day=day_enum, time_slot_id=sid)
                db.add(avail)

        # 2. Update Subject Preferences
        db.query(TeacherSubjectPreference).filter_by(teacher_id=teacher_id).delete()
        for subj_id, combo in self.pref_combos.items():
            score = combo.currentData()
            pref = TeacherSubjectPreference(teacher_id=teacher_id, subject_id=subj_id, preference_score=score)
            db.add(pref)

        db.commit()
        QMessageBox.information(self, "Guardado", "Disponibilidad y preferencias del docente actualizadas exitosamente.")
