from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, 
    QTableWidget, QTableWidgetItem, QCheckBox, QPushButton, 
    QComboBox, QMessageBox, QHeaderView, QFrame, QScrollArea, QLineEdit
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
from app.database.database import SessionLocal
from app.database.models import (
    Teacher, Subject, TimeSlot, DayOfWeek, TeacherAvailability, 
    TeacherSubjectPreference, ShiftType, TeacherType
)
from app.auth.session import session

class PreferencesView(QWidget):
    def __init__(self):
        super().__init__()
        self.checkbox_map = {}
        self.pref_combos = {}
        self.days = [d.value for d in DayOfWeek]
        self.sorted_slots = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff; 
                border: 1px solid #e2e8f0; 
                border-radius: 12px; 
                padding: 14px 18px;
            }
        """)
        header = QHBoxLayout(header_card)

        title_layout = QVBoxLayout()
        title = QLabel("Disponibilidad Horaria y Afinidad Docente")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1e3a8a;")
        subtitle = QLabel("Configuración de franjas horarias habilitadas y preferencias de asignaturas para el motor de optimización")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        # Teacher selector if admin
        self.teacher_selector = QComboBox()
        self.teacher_selector.setMinimumWidth(240)
        self.teacher_selector.currentIndexChanged.connect(self.load_teacher_data)
        controls_layout.addWidget(self.teacher_selector)

        save_btn = QPushButton("💾 Guardar Preferencias")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981; 
                color: white; 
                font-weight: 800; 
                padding: 10px 20px; 
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        save_btn.clicked.connect(self.save_data)
        controls_layout.addWidget(save_btn)

        header.addLayout(controls_layout)
        layout.addWidget(header_card)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: Availability Matrix
        self.avail_tab = QWidget()
        self.setup_avail_tab()
        self.tabs.addTab(self.avail_tab, "🗓️ Disponibilidad Semanal")

        # Tab 2: Subject Preferences
        self.pref_tab = QWidget()
        self.setup_pref_tab()
        self.tabs.addTab(self.pref_tab, "📚 Afinidad de Asignaturas")

        layout.addWidget(self.tabs)
        self.load_teachers()

    def setup_avail_tab(self):
        avail_layout = QVBoxLayout(self.avail_tab)
        avail_layout.setSpacing(12)

        # Full-Time Institutional Notice Card
        self.ft_notice_card = QFrame()
        self.ft_notice_card.setStyleSheet("""
            QFrame {
                background-color: #eff6ff;
                border: 1.5px solid #3b82f6;
                border-left: 6px solid #2563eb;
                border-radius: 8px;
                padding: 10px 16px;
            }
        """)
        ft_n_layout = QVBoxLayout(self.ft_notice_card)
        ft_n_layout.setSpacing(2)
        ft_n_title = QLabel("🏛️ Régimen Docente: Dedicación de Tiempo Completo (42 hrs)")
        ft_n_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #1e3a8a;")
        ft_n_sub = QLabel("Por estatuto profesoral y contrato de exclusividad de la Universidad Manuela Beltrán, la disponibilidad horaria es 100% institucional y la asigna la Dirección de Programa. Tu ponderación principal se configura en la pestaña de <b>Afinidad de Asignaturas</b>.")
        ft_n_sub.setStyleSheet("font-size: 11px; color: #334155; line-height: 1.4;")
        ft_n_sub.setWordWrap(True)
        ft_n_layout.addWidget(ft_n_title)
        ft_n_layout.addWidget(ft_n_sub)
        self.ft_notice_card.setVisible(False)
        avail_layout.addWidget(self.ft_notice_card)

        # Quick actions bar
        self.bar_card = QFrame()
        self.bar_card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px;")
        bar_layout = QHBoxLayout(self.bar_card)
        bar_layout.setSpacing(8)

        info_lbl = QLabel("<b>Acciones Rápidas de Selección:</b>")
        info_lbl.setStyleSheet("color: #334155; font-size: 12px;")
        bar_layout.addWidget(info_lbl)

        btn_all = QPushButton("✓ Marcar Todo")
        btn_all.setCursor(Qt.PointingHandCursor)
        btn_all.setStyleSheet("background-color: #e0e7ff; color: #3730a3; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
        btn_all.clicked.connect(lambda: self.set_all_checkboxes(True))
        bar_layout.addWidget(btn_all)

        btn_none = QPushButton("✕ Desmarcar Todo")
        btn_none.setCursor(Qt.PointingHandCursor)
        btn_none.setStyleSheet("background-color: #fee2e2; color: #991b1b; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
        btn_none.clicked.connect(lambda: self.set_all_checkboxes(False))
        bar_layout.addWidget(btn_none)

        btn_morning = QPushButton("☀️ Solo Mañanas (8-12)")
        btn_morning.setCursor(Qt.PointingHandCursor)
        btn_morning.setStyleSheet("background-color: #e0f2fe; color: #0369a1; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
        btn_morning.clicked.connect(lambda: self.set_shift_checkboxes(ShiftType.MORNING))
        bar_layout.addWidget(btn_morning)

        btn_afternoon = QPushButton("⛅ Solo Tardes (13-17)")
        btn_afternoon.setCursor(Qt.PointingHandCursor)
        btn_afternoon.setStyleSheet("background-color: #d1fae5; color: #065f46; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
        btn_afternoon.clicked.connect(lambda: self.set_shift_checkboxes(ShiftType.AFTERNOON))
        bar_layout.addWidget(btn_afternoon)

        btn_night = QPushButton("🌙 Solo Noches (18-22)")
        btn_night.setCursor(Qt.PointingHandCursor)
        btn_night.setStyleSheet("background-color: #ede9fe; color: #5b21b6; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
        btn_night.clicked.connect(lambda: self.set_shift_checkboxes(ShiftType.NIGHT))
        bar_layout.addWidget(btn_night)

        bar_layout.addStretch()
        avail_layout.addWidget(self.bar_card)

        # Availability Table
        self.avail_table = QTableWidget()
        self.avail_table.setColumnCount(len(self.days))
        self.avail_table.setHorizontalHeaderLabels(self.days)
        self.avail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # High-contrast horizontal and vertical headers
        self.avail_table.verticalHeader().setMinimumWidth(220)
        self.avail_table.verticalHeader().setDefaultSectionSize(48)
        self.avail_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #0f172a;
                gridline-color: #e2e8f0;
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 8px;
                font-weight: 800;
                font-size: 12px;
                border: none;
                border-right: 1px solid #334155;
                border-bottom: 1px solid #334155;
            }
        """)
        avail_layout.addWidget(self.avail_table)

    def setup_pref_tab(self):
        pref_layout = QVBoxLayout(self.pref_tab)
        pref_layout.setSpacing(12)

        pref_info_card = QFrame()
        pref_info_card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 14px;")
        p_l = QHBoxLayout(pref_info_card)
        
        self.pref_hint_lbl = QLabel("Asigna el nivel de preferencia de dictado para las asignaturas de tu enfoque disciplinar (1 = Baja, 5 = Muy Alta):")
        self.pref_hint_lbl.setStyleSheet("color: #334155; font-size: 13px; font-weight: 600;")
        p_l.addWidget(self.pref_hint_lbl)
        p_l.addStretch()

        self.pref_search = QLineEdit()
        self.pref_search.setPlaceholderText("🔍 Filtrar materia...")
        self.pref_search.setFixedWidth(200)
        self.pref_search.textChanged.connect(self.filter_subject_prefs)
        p_l.addWidget(self.pref_search)

        pref_layout.addWidget(pref_info_card)

        self.pref_table = QTableWidget()
        self.pref_table.setColumnCount(6)
        self.pref_table.setHorizontalHeaderLabels(["ID", "Asignatura", "Área de Conocimiento", "Semestre", "Horas Semanales", "Afinidad Docente"])
        self.pref_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.pref_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.pref_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.pref_table.verticalHeader().setDefaultSectionSize(42)
        pref_layout.addWidget(self.pref_table)

    def load_teachers(self):
        db = SessionLocal()
        try:
            teachers = db.query(Teacher).all()
            self.teacher_selector.clear()
            if session.teacher_id:
                curr = db.query(Teacher).filter_by(id=session.teacher_id).first()
                if curr:
                    area_label = getattr(curr, "knowledge_area", "General")
                    self.teacher_selector.addItem(f"👤 {curr.name} ({curr.teacher_type.value}) • 🏷️ {area_label}", curr.id)
                    self.teacher_selector.setEnabled(False)
            else:
                for t in teachers:
                    area_label = getattr(t, "knowledge_area", "General")
                    self.teacher_selector.addItem(f"👤 {t.name} ({t.teacher_type.value}) • 🏷️ {area_label}", t.id)
                self.teacher_selector.setEnabled(True)
        finally:
            db.close()

        self.load_teacher_data()

    def load_teacher_data(self):
        if self.teacher_selector.count() == 0:
            return

        teacher_id = self.teacher_selector.currentData()
        if not teacher_id:
            return

        db = SessionLocal()
        try:
            teacher = db.query(Teacher).filter_by(id=teacher_id).first()
            is_full_time = (teacher and teacher.teacher_type == TeacherType.FULL_TIME)
            teacher_area = getattr(teacher, "knowledge_area", None) if teacher else None

            self.ft_notice_card.setVisible(is_full_time)
            self.bar_card.setEnabled(not is_full_time)

            slots = db.query(TimeSlot).all()
            SHIFT_ORDER = {
                ShiftType.MORNING: 0,
                ShiftType.AFTERNOON: 1,
                ShiftType.NIGHT: 2,
                "MAÑANA": 0,
                "TARDE": 1,
                "NOCHE": 2
            }
            self.sorted_slots = sorted(slots, key=lambda s: (SHIFT_ORDER.get(s.shift, 99), s.start_time))
            
            # Formatted labels for vertical header
            slot_headers = [
                f"{s.shift.value}\n{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}"
                for s in self.sorted_slots
            ]

            # Setup availability table
            self.avail_table.setRowCount(len(self.sorted_slots))
            self.avail_table.setVerticalHeaderLabels(slot_headers)

            # Get existing availabilities
            avails = db.query(TeacherAvailability).filter_by(teacher_id=teacher_id).all()
            avail_set = {(a.day.value, a.time_slot_id) for a in avails}

            self.checkbox_map = {}
            for r_idx, slot in enumerate(self.sorted_slots):
                for c_idx, day_val in enumerate(self.days):
                    cb = QCheckBox()
                    if is_full_time:
                        cb.setChecked(True)
                        cb.setEnabled(False)
                        cb.setToolTip("Docente de Tiempo Completo: 100% de disponibilidad institucional garantizada.")
                    else:
                        cb.setChecked((day_val, slot.id) in avail_set)
                        cb.setEnabled(True)
                        cb.setCursor(Qt.PointingHandCursor)
                    
                    cell_widget = QWidget()
                    cell_layout = QHBoxLayout(cell_widget)
                    cell_layout.addWidget(cb)
                    cell_layout.setAlignment(Qt.AlignCenter)
                    cell_layout.setContentsMargins(0, 0, 0, 0)
                    
                    self.avail_table.setCellWidget(r_idx, c_idx, cell_widget)
                    self.checkbox_map[(day_val, slot.id)] = cb

            # Setup subject preferences table (filtered strictly by teacher's knowledge area)
            if teacher_area:
                subjects = db.query(Subject).filter_by(knowledge_area=teacher_area).all()
                self.pref_hint_lbl.setText(f"Mostrando únicamente asignaturas de tu enfoque disciplinar: 🎯 <b>{teacher_area}</b>")
            else:
                subjects = db.query(Subject).all()
                self.pref_hint_lbl.setText("Asigna el nivel de preferencia de dictado para las asignaturas (1 = Baja, 5 = Muy Alta):")

            self.pref_table.setRowCount(len(subjects))

            existing_prefs = {
                p.subject_id: p.preference_score 
                for p in db.query(TeacherSubjectPreference).filter_by(teacher_id=teacher_id).all()
            }

            self.pref_combos = {}
            for row_idx, subj in enumerate(subjects):
                id_item = QTableWidgetItem(str(subj.id))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.pref_table.setItem(row_idx, 0, id_item)

                name_item = QTableWidgetItem(f"📘 {subj.name}")
                name_item.setFont(self.pref_table.font())
                self.pref_table.setItem(row_idx, 1, name_item)

                # Knowledge Area Column
                subj_area = getattr(subj, "knowledge_area", "General")
                is_area_match = (teacher_area and subj_area == teacher_area)
                area_text = f"🎯 {subj_area}" if is_area_match else subj_area
                area_item = QTableWidgetItem(area_text)
                area_item.setTextAlignment(Qt.AlignCenter)
                if is_area_match:
                    area_item.setBackground(QColor("#ecfdf5"))
                    area_item.setForeground(QColor("#065f46"))
                    font = area_item.font()
                    font.setBold(True)
                    area_item.setFont(font)
                self.pref_table.setItem(row_idx, 2, area_item)

                sem_item = QTableWidgetItem(f"Semestre {subj.semester_id}")
                sem_item.setTextAlignment(Qt.AlignCenter)
                self.pref_table.setItem(row_idx, 3, sem_item)

                hrs_item = QTableWidgetItem(f"{subj.hours_per_week} hrs/sem")
                hrs_item.setTextAlignment(Qt.AlignCenter)
                self.pref_table.setItem(row_idx, 4, hrs_item)

                combo = QComboBox()
                combo.setStyleSheet("font-weight: 700; color: #0f172a; padding: 4px 10px;")
                combo.addItem("⭐ 1 - Muy Baja", 1)
                combo.addItem("⭐⭐ 2 - Baja", 2)
                combo.addItem("⭐⭐⭐ 3 - Media (Normal)", 3)
                combo.addItem("⭐⭐⭐⭐ 4 - Alta", 4)
                combo.addItem("⭐⭐⭐⭐⭐ 5 - Muy Alta", 5)
                
                score = existing_prefs.get(subj.id, (5 if is_area_match else 1))
                combo.setCurrentIndex(max(0, min(4, score - 1)))

                self.pref_table.setCellWidget(row_idx, 5, combo)
                self.pref_combos[subj.id] = (combo, subj.name)
        finally:
            db.close()

    def set_all_checkboxes(self, checked):
        for cb in self.checkbox_map.values():
            cb.setChecked(checked)

    def set_shift_checkboxes(self, target_shift):
        for (day_val, sid), cb in self.checkbox_map.items():
            matching_slot = next((s for s in self.sorted_slots if s.id == sid), None)
            if matching_slot and matching_slot.shift == target_shift:
                cb.setChecked(True)
            else:
                cb.setChecked(False)

    def filter_subject_prefs(self, text):
        query = text.strip().lower()
        for r in range(self.pref_table.rowCount()):
            name_item = self.pref_table.item(r, 1)
            if not query or (name_item and query in name_item.text().lower()):
                self.pref_table.setRowHidden(r, False)
            else:
                self.pref_table.setRowHidden(r, True)

    def save_data(self):
        teacher_id = self.teacher_selector.currentData()
        if not teacher_id:
            return

        db = SessionLocal()
        try:
            # 1. Update Availabilities
            db.query(TeacherAvailability).filter_by(teacher_id=teacher_id).delete()
            for (day_val, sid), cb in self.checkbox_map.items():
                if cb.isChecked():
                    day_enum = next(d for d in DayOfWeek if d.value == day_val)
                    avail = TeacherAvailability(teacher_id=teacher_id, day=day_enum, time_slot_id=sid)
                    db.add(avail)

            # 2. Update Subject Preferences
            subj_ids_to_update = list(self.pref_combos.keys())
            if subj_ids_to_update:
                db.query(TeacherSubjectPreference).filter(
                    TeacherSubjectPreference.teacher_id == teacher_id,
                    TeacherSubjectPreference.subject_id.in_(subj_ids_to_update)
                ).delete(synchronize_session=False)

            for subj_id, (combo, _) in self.pref_combos.items():
                score = combo.currentData()
                pref = TeacherSubjectPreference(teacher_id=teacher_id, subject_id=subj_id, preference_score=score)
                db.add(pref)

            db.commit()
            QMessageBox.information(
                self, "Preferencias Guardadas", 
                "La disponibilidad horaria semanal y afinidades de asignaturas se han guardado exitosamente."
            )
        finally:
            db.close()
