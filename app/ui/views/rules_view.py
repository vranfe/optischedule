from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
    QDoubleSpinBox, QCheckBox, QPushButton, QMessageBox, QGroupBox, 
    QFormLayout, QDateEdit, QFrame, QScrollArea
)
from PySide6.QtCore import QDate, Qt
from app.database.database import get_db, SessionLocal
from app.database.models import Config

class RulesView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 14px 18px;
            }
        """)
        header = QHBoxLayout(header_card)

        title_layout = QVBoxLayout()
        title = QLabel("Reglas Institucionales y Calendario Académico")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1e3a8a;")
        subtitle = QLabel("Configuración de fechas de matrícula, topes de contratación docente y ponderaciones del optimizador")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)

        save_btn = QPushButton("💾 Guardar Configuración")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981; 
                color: white; 
                font-weight: 800; 
                padding: 10px 22px; 
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        save_btn.clicked.connect(self.save_config)
        header.addWidget(save_btn)

        main_layout.addWidget(header_card)

        # Group 1: Academic Enrollment Dates & Leveling Calendars
        dates_group = QGroupBox("📅 Calendario Institucional de Inscripción de Materias")
        dates_group.setStyleSheet("QGroupBox { font-weight: 800; font-size: 14px; color: #1e3a8a; }")
        dates_layout = QFormLayout(dates_group)
        dates_layout.setSpacing(12)

        # Date for Regular Students
        reg_dates_layout = QHBoxLayout()
        self.reg_start_edit = QDateEdit()
        self.reg_start_edit.setCalendarPopup(True)
        self.reg_start_edit.setDisplayFormat("yyyy-MM-dd")
        
        self.reg_end_edit = QDateEdit()
        self.reg_end_edit.setCalendarPopup(True)
        self.reg_end_edit.setDisplayFormat("yyyy-MM-dd")
        
        reg_dates_layout.addWidget(QLabel("Desde:"))
        reg_dates_layout.addWidget(self.reg_start_edit)
        reg_dates_layout.addWidget(QLabel("Hasta:"))
        reg_dates_layout.addWidget(self.reg_end_edit)
        dates_layout.addRow("🎓 Estudiantes Nivelados (Al Día):", reg_dates_layout)

        # Date for Irregular Students
        irreg_dates_layout = QHBoxLayout()
        self.irreg_start_edit = QDateEdit()
        self.irreg_start_edit.setCalendarPopup(True)
        self.irreg_start_edit.setDisplayFormat("yyyy-MM-dd")
        
        self.irreg_end_edit = QDateEdit()
        self.irreg_end_edit.setCalendarPopup(True)
        self.irreg_end_edit.setDisplayFormat("yyyy-MM-dd")
        
        irreg_dates_layout.addWidget(QLabel("Desde:"))
        irreg_dates_layout.addWidget(self.irreg_start_edit)
        irreg_dates_layout.addWidget(QLabel("Hasta:"))
        irreg_dates_layout.addWidget(self.irreg_end_edit)
        dates_layout.addRow("⚠️ Estudiantes No Nivelados / Rezagados:", irreg_dates_layout)

        # Current System Date Simulator
        curr_date_layout = QHBoxLayout()
        self.curr_date_edit = QDateEdit()
        self.curr_date_edit.setCalendarPopup(True)
        self.curr_date_edit.setDisplayFormat("yyyy-MM-dd")
        curr_date_layout.addWidget(self.curr_date_edit)
        
        date_hint = QLabel("💡 <i>Simula la fecha actual del sistema para validar ventanas de inscripción en tiempo real.</i>")
        date_hint.setStyleSheet("font-size: 11px; color: #64748b;")
        curr_date_layout.addWidget(date_hint)
        curr_date_layout.addStretch()
        dates_layout.addRow("🕒 Fecha Actual del Sistema:", curr_date_layout)

        main_layout.addWidget(dates_group)

        # Group 2: Hard Constraints (Contractual Limits)
        hard_group = QGroupBox("Restricciones Duras (Límites Contractuales y Operativos)")
        hard_group.setStyleSheet("QGroupBox { font-weight: 800; font-size: 14px; color: #1e3a8a; }")
        hard_layout = QFormLayout(hard_group)
        hard_layout.setSpacing(10)

        self.ft_spin = QSpinBox()
        self.ft_spin.setRange(10, 60)
        self.ft_spin.setSuffix(" hrs/semana")
        hard_layout.addRow("Tope Tiempo Completo (FT):", self.ft_spin)

        self.pt_spin = QSpinBox()
        self.pt_spin.setRange(5, 40)
        self.pt_spin.setSuffix(" hrs/semana")
        hard_layout.addRow("Tope Medio Tiempo (PT):", self.pt_spin)

        self.cat_spin = QSpinBox()
        self.cat_spin.setRange(4, 30)
        self.cat_spin.setSuffix(" hrs/semana")
        hard_layout.addRow("Tope Cátedra:", self.cat_spin)

        self.consec_spin = QSpinBox()
        self.consec_spin.setRange(2, 8)
        self.consec_spin.setSuffix(" hrs seguidas")
        hard_layout.addRow("Máximo de horas continuas por docente:", self.consec_spin)

        self.sat_check = QCheckBox("Habilitar Sábados para clases (hasta las 17:00 / 5:00 p.m.)")
        hard_layout.addRow("Operación Fin de Semana:", self.sat_check)

        main_layout.addWidget(hard_group)

        # Group 3: Soft Constraints (Objective Function Weights)
        soft_group = QGroupBox("Restricciones Blandas (Ponderaciones de Calidad de Horario)")
        soft_group.setStyleSheet("QGroupBox { font-weight: 800; font-size: 14px; color: #1e3a8a; }")
        soft_layout = QFormLayout(soft_group)
        soft_layout.setSpacing(10)

        self.pref_weight = QDoubleSpinBox()
        self.pref_weight.setRange(0.0, 1.0)
        self.pref_weight.setSingleStep(0.05)
        soft_layout.addRow("Peso Preferencias Docentes y Estudiantes:", self.pref_weight)

        self.gap_weight = QDoubleSpinBox()
        self.gap_weight.setRange(0.0, 1.0)
        self.gap_weight.setSingleStep(0.05)
        soft_layout.addRow("Peso Minimización de Huecos (Ventanas):", self.gap_weight)

        self.load_weight = QDoubleSpinBox()
        self.load_weight.setRange(0.0, 1.0)
        self.load_weight.setSingleStep(0.05)
        soft_layout.addRow("Peso Balance de Carga Laboral:", self.load_weight)

        self.room_weight = QDoubleSpinBox()
        self.room_weight.setRange(0.0, 1.0)
        self.room_weight.setSingleStep(0.05)
        soft_layout.addRow("Peso Eficiencia de Uso de Aulas:", self.room_weight)

        self.dist_weight = QDoubleSpinBox()
        self.dist_weight.setRange(0.0, 1.0)
        self.dist_weight.setSingleStep(0.05)
        soft_layout.addRow("Peso Distribución Semanal:", self.dist_weight)

        main_layout.addWidget(soft_group)

        scroll.setWidget(container)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

        self.load_config()

    def load_config(self):
        db = SessionLocal()
        try:
            config = db.query(Config).first()
            if not config:
                return

            # Dates
            reg_start = getattr(config, "enrollment_start_regular", "2026-09-01") or "2026-09-01"
            reg_end = getattr(config, "enrollment_end_regular", "2026-09-15") or "2026-09-15"
            irreg_start = getattr(config, "enrollment_start_irregular", "2026-09-16") or "2026-09-16"
            irreg_end = getattr(config, "enrollment_end_irregular", "2026-09-30") or "2026-09-30"
            curr_date = getattr(config, "system_current_date", "2026-09-08") or "2026-09-08"

            self.reg_start_edit.setDate(QDate.fromString(reg_start, "yyyy-MM-dd"))
            self.reg_end_edit.setDate(QDate.fromString(reg_end, "yyyy-MM-dd"))
            self.irreg_start_edit.setDate(QDate.fromString(irreg_start, "yyyy-MM-dd"))
            self.irreg_end_edit.setDate(QDate.fromString(irreg_end, "yyyy-MM-dd"))
            self.curr_date_edit.setDate(QDate.fromString(curr_date, "yyyy-MM-dd"))

            # Limits & Weights
            self.ft_spin.setValue(config.full_time_hours)
            self.pt_spin.setValue(config.part_time_hours)
            self.cat_spin.setValue(config.catedra_hours)
            self.consec_spin.setValue(config.max_consecutive_hours if hasattr(config, "max_consecutive_hours") else 4)
            self.sat_check.setChecked(config.allow_saturday if hasattr(config, "allow_saturday") else True)

            self.pref_weight.setValue(config.pref_weight)
            self.gap_weight.setValue(config.gap_weight)
            self.load_weight.setValue(config.load_weight)
            self.room_weight.setValue(config.room_weight)
            self.dist_weight.setValue(config.dist_weight if hasattr(config, "dist_weight") else 0.10)
        finally:
            db.close()

    def save_config(self):
        db = SessionLocal()
        try:
            config = db.query(Config).first()
            if not config:
                config = Config()
                db.add(config)

            # Save Dates
            config.enrollment_start_regular = self.reg_start_edit.date().toString("yyyy-MM-dd")
            config.enrollment_end_regular = self.reg_end_edit.date().toString("yyyy-MM-dd")
            config.enrollment_start_irregular = self.irreg_start_edit.date().toString("yyyy-MM-dd")
            config.enrollment_end_irregular = self.irreg_end_edit.date().toString("yyyy-MM-dd")
            config.system_current_date = self.curr_date_edit.date().toString("yyyy-MM-dd")

            # Save Limits & Weights
            config.full_time_hours = self.ft_spin.value()
            config.part_time_hours = self.pt_spin.value()
            config.catedra_hours = self.cat_spin.value()
            config.max_consecutive_hours = self.consec_spin.value()
            config.allow_saturday = self.sat_check.isChecked()

            config.pref_weight = self.pref_weight.value()
            config.gap_weight = self.gap_weight.value()
            config.load_weight = self.load_weight.value()
            config.room_weight = self.room_weight.value()
            config.dist_weight = self.dist_weight.value()

            db.commit()
            QMessageBox.information(self, "Configuración Guardada", "Las reglas, restricciones y fechas del calendario académico se han actualizado exitosamente.")
        finally:
            db.close()
