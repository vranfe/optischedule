from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QFrame, QGroupBox,
    QCheckBox, QRadioButton, QButtonGroup, QSlider, QTabWidget,
    QMessageBox, QScrollArea, QFileDialog
)
from PySide6.QtCore import Qt
import csv
from app.database.database import get_db
from app.database.models import (
    Student, ScheduleAssignment, TimeSlot, DayOfWeek, Subject, ShiftType, 
    StudentEnrollment, StudentPreference
)
from app.optimization.student_optimizer import StudentScheduleOptimizer
from app.auth.session import session

class StudentScheduleView(QWidget):
    def __init__(self):
        super().__init__()
        self.optimizer_options = []
        self.current_preview_option = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header Info Card
        self.info_card = QFrame()
        self.info_card.setStyleSheet("background-color: #ffffff; border-left: 5px solid #2563eb; border-radius: 8px; padding: 12px; border: 1px solid #e2e8f0;")
        info_layout = QHBoxLayout(self.info_card)
        
        self.student_info_lbl = QLabel("🎓 Estudiante: - | Semestre: - | Estado: -")
        self.student_info_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e3a8a;")
        info_layout.addWidget(self.student_info_lbl)

        refresh_btn = QPushButton("🔄 Actualizar Datos")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        refresh_btn.clicked.connect(self.load_data)
        info_layout.addWidget(refresh_btn)

        layout.addWidget(self.info_card)

        # Tabs
        self.tabs = QTabWidget()

        # TAB 1: Optimizer & Planner
        self.planner_tab = QWidget()
        self.setup_planner_tab()
        self.tabs.addTab(self.planner_tab, "⚡ Planificador Personal y Comparador de Horarios")

        # TAB 2: Official Enrolled Timetable
        self.timetable_tab = QWidget()
        self.setup_timetable_tab()
        self.tabs.addTab(self.timetable_tab, "📅 Mi Horario Oficial Inscrito")

        layout.addWidget(self.tabs)
        self.load_data()

    def setup_planner_tab(self):
        p_layout = QVBoxLayout(self.planner_tab)
        p_layout.setSpacing(10)

        # Split controls into two columns (Subjects & Preferences)
        top_row = QHBoxLayout()

        # Step 1: Subjects selection
        subj_group = QGroupBox("1. Selecciona las Asignaturas a Cursar")
        subj_group.setStyleSheet("QGroupBox { font-weight: bold; color: #1e3a8a; }")
        self.subj_layout = QVBoxLayout(subj_group)
        
        self.subj_scroll = QScrollArea()
        self.subj_scroll.setWidgetResizable(True)
        self.subj_container = QWidget()
        self.subj_checkboxes_layout = QVBoxLayout(self.subj_container)
        self.subj_scroll.setWidget(self.subj_container)
        self.subj_scroll.setFixedHeight(160)
        self.subj_layout.addWidget(self.subj_scroll)
        top_row.addWidget(subj_group)

        # Step 2: Student Preferences & Weights
        pref_group = QGroupBox("2. Tus Criterios y Preferencias de Calidad")
        pref_group.setStyleSheet("QGroupBox { font-weight: bold; color: #1e3a8a; }")
        pref_layout = QVBoxLayout(pref_group)

        # Shift Radios
        shift_row = QHBoxLayout()
        shift_row.addWidget(QLabel("<b>Jornada Preferida:</b>"))
        self.shift_btn_group = QButtonGroup(self)
        self.rb_any = QRadioButton("Cualquiera")
        self.rb_morning = QRadioButton("☀️ Mañana")
        self.rb_afternoon = QRadioButton("⛅ Tarde")
        self.rb_night = QRadioButton("🌙 Noche")
        self.rb_morning.setChecked(True)

        self.shift_btn_group.addButton(self.rb_any, 0)
        self.shift_btn_group.addButton(self.rb_morning, 1)
        self.shift_btn_group.addButton(self.rb_afternoon, 2)
        self.shift_btn_group.addButton(self.rb_night, 3)

        shift_row.addWidget(self.rb_any)
        shift_row.addWidget(self.rb_morning)
        shift_row.addWidget(self.rb_afternoon)
        shift_row.addWidget(self.rb_night)
        pref_layout.addLayout(shift_row)

        # Sliders for priorities
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("Prioridad Jornada:"))
        self.shift_weight_slider = QSlider(Qt.Horizontal)
        self.shift_weight_slider.setRange(1, 10)
        self.shift_weight_slider.setValue(6)
        slider_row.addWidget(self.shift_weight_slider)

        slider_row.addWidget(QLabel("Minimizar Huecos:"))
        self.gap_weight_slider = QSlider(Qt.Horizontal)
        self.gap_weight_slider.setRange(1, 10)
        self.gap_weight_slider.setValue(3)
        slider_row.addWidget(self.gap_weight_slider)

        slider_row.addWidget(QLabel("Días Libres:"))
        self.free_weight_slider = QSlider(Qt.Horizontal)
        self.free_weight_slider.setRange(1, 10)
        self.free_weight_slider.setValue(2)
        slider_row.addWidget(self.free_weight_slider)
        pref_layout.addLayout(slider_row)

        # Optimize Button
        self.opt_btn = QPushButton("🚀 OPTIMIZAR MI HORARIO PERSONAL")
        self.opt_btn.setCursor(Qt.PointingHandCursor)
        self.opt_btn.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold; padding: 10px; border-radius: 6px; font-size: 13px;")
        self.opt_btn.clicked.connect(self.run_student_optimization)
        pref_layout.addWidget(self.opt_btn)

        top_row.addWidget(pref_group)
        p_layout.addLayout(top_row)

        # Step 3: Alternatives Comparison Cards & Preview Table
        comp_group = QGroupBox("3. Comparación de Alternativas Factibles Encontradas")
        comp_group.setStyleSheet("QGroupBox { font-weight: bold; color: #1e3a8a; }")
        comp_layout = QVBoxLayout(comp_group)

        self.options_cards_layout = QHBoxLayout()
        comp_layout.addLayout(self.options_cards_layout)

        # Live Schedule Preview Table
        self.preview_table = QTableWidget()
        self.days = [d.value for d in DayOfWeek]
        self.preview_table.setColumnCount(len(self.days))
        self.preview_table.setHorizontalHeaderLabels(self.days)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.preview_table.setFixedHeight(220)
        comp_layout.addWidget(self.preview_table)

        # Save Selected Schedule Button
        self.save_schedule_btn = QPushButton("✅ CONFIRMAR E INSCRIBIR ESTA ALTERNATIVA")
        self.save_schedule_btn.setEnabled(False)
        self.save_schedule_btn.setCursor(Qt.PointingHandCursor)
        self.save_schedule_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 10px; border-radius: 6px; font-size: 13px;")
        self.save_schedule_btn.clicked.connect(self.confirm_enrollment)
        comp_layout.addWidget(self.save_schedule_btn)

        p_layout.addWidget(comp_group)

    def setup_timetable_tab(self):
        t_layout = QVBoxLayout(self.timetable_tab)
        t_layout.setSpacing(10)

        t_header = QHBoxLayout()
        t_title = QLabel("Mi Horario Oficial Registrado")
        t_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e3a8a;")
        t_header.addWidget(t_title)

        export_btn = QPushButton("📥 Exportar Mi Horario (CSV)")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 8px 14px; border-radius: 6px;")
        export_btn.clicked.connect(self.export_my_schedule)
        t_header.addWidget(export_btn)
        t_layout.addLayout(t_header)

        self.official_table = QTableWidget()
        self.official_table.setColumnCount(len(self.days))
        self.official_table.setHorizontalHeaderLabels(self.days)
        self.official_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t_layout.addWidget(self.official_table)

    def load_data(self):
        db = next(get_db())
        student_id = session.student_id
        if not student_id:
            s = db.query(Student).first()
            student_id = s.id if s else None

        if not student_id:
            return

        student = db.query(Student).filter_by(id=student_id).first()
        if not student:
            return

        pago_str = "Al Día" if not student.has_payment_agreement else "Con Acuerdo de Pago"
        self.student_info_lbl.setText(
            f"🎓 Estudiante: {student.name} | Semestre: {student.semester_id} | Inscrito: {'Sí' if student.is_enrolled else 'No'} | Estado Financiero: {pago_str}"
        )

        # Load saved shift preference
        saved_pref = db.query(StudentPreference).filter_by(student_id=student_id, priority=1).first()
        if saved_pref:
            if saved_pref.shift == ShiftType.MORNING:
                self.rb_morning.setChecked(True)
            elif saved_pref.shift == ShiftType.AFTERNOON:
                self.rb_afternoon.setChecked(True)
            elif saved_pref.shift == ShiftType.NIGHT:
                self.rb_night.setChecked(True)

        # Populate Subjects for checkbox selection
        while self.subj_checkboxes_layout.count() > 0:
            item = self.subj_checkboxes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Fetch subjects: prioritize student's semester (checked) and then other semesters (unchecked)
        sem_subjects = db.query(Subject).filter_by(semester_id=student.semester_id).all()
        other_subjects = db.query(Subject).filter(Subject.semester_id != student.semester_id).all()
        
        self.subject_checkboxes = {}
        for subj in sem_subjects:
            cb = QCheckBox(f"📘 {subj.name} (Semestre {subj.semester_id} - {subj.hours_per_week}h/sem)")
            cb.setChecked(True) # Checked by default for own semester
            cb.setStyleSheet("font-weight: bold; color: #1e3a8a;")
            self.subj_checkboxes_layout.addWidget(cb)
            self.subject_checkboxes[subj.id] = cb

        for subj in other_subjects:
            cb = QCheckBox(f"📙 {subj.name} (Semestre {subj.semester_id} - {subj.hours_per_week}h/sem)")
            cb.setChecked(False) # Unchecked by default
            cb.setStyleSheet("color: #475569;")
            self.subj_checkboxes_layout.addWidget(cb)
            self.subject_checkboxes[subj.id] = cb

        self.load_official_schedule()

    def run_student_optimization(self):
        db = next(get_db())
        student_id = session.student_id or 1
        
        selected_ids = [s_id for s_id, cb in self.subject_checkboxes.items() if cb.isChecked()]
        if not selected_ids:
            QMessageBox.warning(self, "Atención", "Debes seleccionar al menos una asignatura para optimizar tu horario.")
            return

        # Resolve preferred shift
        shift_id = self.shift_btn_group.checkedId()
        preferred_shift = None
        if shift_id == 1: preferred_shift = ShiftType.MORNING
        elif shift_id == 2: preferred_shift = ShiftType.AFTERNOON
        elif shift_id == 3: preferred_shift = ShiftType.NIGHT

        # Normalize weights
        w_shift = self.shift_weight_slider.value()
        w_gap = self.gap_weight_slider.value()
        w_free = self.free_weight_slider.value()
        total_w = w_shift + w_gap + w_free
        w_shift /= total_w
        w_gap /= total_w
        w_free /= total_w

        optimizer = StudentScheduleOptimizer(db, student_id)
        result = optimizer.optimize_student_schedule(
            selected_subject_ids=selected_ids,
            preferred_shift=preferred_shift,
            shift_weight=w_shift,
            gap_weight=w_gap,
            free_day_weight=w_free
        )

        if result["status"] != "SUCCESS":
            QMessageBox.warning(self, "Sin Combinación Factible", result["msg"])
            return

        self.optimizer_options = result["options"]
        self.render_alternative_cards()
        if self.optimizer_options:
            self.preview_option(0)

    def render_alternative_cards(self):
        # Clear cards
        while self.options_cards_layout.count() > 0:
            item = self.options_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for idx, opt in enumerate(self.optimizer_options):
            card = QFrame()
            is_best = (idx == 0)
            border_color = "#16a34a" if is_best else "#cbd5e1"
            bg_color = "#f0fdf4" if is_best else "#ffffff"

            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 8px;
                    padding: 10px;
                }}
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setSpacing(4)

            badge = "⭐ RECOMENDADA" if is_best else f"ALTERNATIVA {idx + 1}"
            b_lbl = QLabel(badge)
            b_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {'#15803d' if is_best else '#475569'};")
            c_layout.addWidget(b_lbl)

            score_lbl = QLabel(f"<b>Calidad Global: {opt['global_score']}%</b>")
            score_lbl.setStyleSheet("font-size: 14px; color: #1e3a8a;")
            c_layout.addWidget(score_lbl)

            details_lbl = QLabel(f"• Jornada: {opt['shift_score']}%\n• Compactación: {opt['compactness_score']}%\n• Días Libres: {opt['free_days']}")
            details_lbl.setStyleSheet("font-size: 11px; color: #334155;")
            c_layout.addWidget(details_lbl)

            btn = QPushButton("👁️ Previsualizar")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("background-color: #2563eb; color: white; padding: 6px; border-radius: 4px; font-weight: bold;")
            btn.clicked.connect(lambda _, i=idx: self.preview_option(i))
            c_layout.addWidget(btn)

            self.options_cards_layout.addWidget(card)

    def preview_option(self, option_index):
        if option_index >= len(self.optimizer_options):
            return

        self.current_preview_option = self.optimizer_options[option_index]
        self.save_schedule_btn.setEnabled(True)
        self.save_schedule_btn.setText(f"✅ CONFIRMAR E INSCRIBIR ALTERNATIVA #{option_index + 1} (Score: {self.current_preview_option['global_score']}%)")

        db = next(get_db())
        slots = db.query(TimeSlot).all()
        slot_map = {s.id: f"{s.shift.value}\n{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}" for s in slots}
        sorted_slot_ids = sorted(slot_map.keys(), key=lambda sid: slot_map[sid])

        self.preview_table.setRowCount(len(sorted_slot_ids))
        self.preview_table.setVerticalHeaderLabels([slot_map[sid] for sid in sorted_slot_ids])

        for r in range(self.preview_table.rowCount()):
            for c in range(self.preview_table.columnCount()):
                self.preview_table.setItem(r, c, QTableWidgetItem(""))

        day_indices = {d: i for i, d in enumerate(self.days)}
        slot_indices = {sid: i for i, sid in enumerate(sorted_slot_ids)}

        for _, _, g_info in self.current_preview_option["groups"]:
            for s in g_info["slots"]:
                if s["time_slot_id"] in slot_indices and s["day"] in day_indices:
                    r_idx = slot_indices[s["time_slot_id"]]
                    c_idx = day_indices[s["day"]]

                    text = f"📘 {g_info['subject_name']}\n👥 {g_info['group_name']}\n👨‍🏫 {g_info['teacher_name']}\n📍 {g_info['room_name']}"
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setBackground(Qt.cyan)
                    self.preview_table.setItem(r_idx, c_idx, item)

        self.preview_table.resizeRowsToContents()

    def confirm_enrollment(self):
        if not self.current_preview_option:
            return

        db = next(get_db())
        student_id = session.student_id or 1
        group_ids = [g_id for _, g_id, _ in self.current_preview_option["groups"]]

        optimizer = StudentScheduleOptimizer(db, student_id)
        optimizer.save_selected_schedule(group_ids)

        QMessageBox.information(self, "Inscripción Exitosa", "¡Tu horario personalizado ha sido confirmado e inscrito exitosamente!")
        self.load_official_schedule()
        self.tabs.setCurrentIndex(1)

    def load_official_schedule(self):
        db = next(get_db())
        student_id = session.student_id or 1
        enrollments = db.query(StudentEnrollment).filter_by(student_id=student_id).all()

        slots = db.query(TimeSlot).all()
        slot_map = {s.id: f"{s.shift.value}\n{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}" for s in slots}
        sorted_slot_ids = sorted(slot_map.keys(), key=lambda sid: slot_map[sid])

        self.official_table.setRowCount(len(sorted_slot_ids))
        self.official_table.setVerticalHeaderLabels([slot_map[sid] for sid in sorted_slot_ids])

        for r in range(self.official_table.rowCount()):
            for c in range(self.official_table.columnCount()):
                self.official_table.setItem(r, c, QTableWidgetItem(""))

        day_indices = {d: i for i, d in enumerate(self.days)}
        slot_indices = {sid: i for i, sid in enumerate(sorted_slot_ids)}

        if enrollments:
            enrolled_group_ids = {e.group_id for e in enrollments}
            assignments = db.query(ScheduleAssignment).filter(ScheduleAssignment.group_id.in_(enrolled_group_ids)).all()
        else:
            # Fallback to semester default
            student = db.query(Student).filter_by(id=student_id).first()
            sem_id = student.semester_id if student else 1
            semester_subjs = db.query(Subject).filter_by(semester_id=sem_id).all()
            subj_ids = {s.id for s in semester_subjs}
            all_asg = db.query(ScheduleAssignment).all()
            assignments = [a for a in all_asg if a.group and a.group.subject_id in subj_ids]

        for asg in assignments:
            if asg.time_slot_id in slot_indices and asg.day.value in day_indices:
                r_idx = slot_indices[asg.time_slot_id]
                c_idx = day_indices[asg.day.value]

                text = f"📘 {asg.group.subject.name}\n👥 Grupo: {asg.group.name}\n👨‍🏫 {asg.teacher.name}\n📍 {asg.room.name}"
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(Qt.cyan if enrollments else Qt.yellow)
                self.official_table.setItem(r_idx, c_idx, item)

        self.official_table.resizeRowsToContents()

    def export_my_schedule(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar Mi Horario", "Mi_Horario_UMB.csv", "Archivos CSV (*.csv)")
        if not file_path:
            return

        try:
            db = next(get_db())
            student_id = session.student_id or 1
            enrollments = db.query(StudentEnrollment).filter_by(student_id=student_id).all()
            enrolled_group_ids = {e.group_id for e in enrollments}
            assignments = db.query(ScheduleAssignment).filter(ScheduleAssignment.group_id.in_(enrolled_group_ids)).all()

            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Día", "Jornada", "Hora Inicio", "Hora Fin", "Asignatura", "Grupo", "Docente", "Aula"])
                for asg in assignments:
                    slot = asg.time_slot
                    writer.writerow([
                        asg.day.value,
                        slot.shift.value if slot else "",
                        slot.start_time.strftime('%H:%M') if slot else "",
                        slot.end_time.strftime('%H:%M') if slot else "",
                        asg.group.subject.name,
                        asg.group.name,
                        asg.teacher.name,
                        asg.room.name
                    ])
            QMessageBox.information(self, "Exportación", f"Tu horario ha sido exportado exitosamente a:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {e}")
