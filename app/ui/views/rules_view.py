from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
    QDoubleSpinBox, QCheckBox, QPushButton, QMessageBox, 
    QFormLayout, QDateEdit, QFrame, QScrollArea, QGridLayout, QSlider
)
from PySide6.QtCore import QDate, Qt
from app.database.database import get_db, SessionLocal
from app.database.models import Config

class RulesView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(18, 18, 24, 80)

        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 14px;
                padding: 16px 20px;
            }
        """)
        header = QHBoxLayout(header_card)

        title_layout = QVBoxLayout()
        title = QLabel("Reglas Institucionales y Calendario Académico")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1e3a8a; letter-spacing: -0.4px;")
        subtitle = QLabel("Configuración de ventanas de inscripción para nivelados y rezagados, límites de contratación y pesos de optimización")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 500;")
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
                padding: 11px 24px; 
                border-radius: 10px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        save_btn.clicked.connect(self.save_config)
        header.addWidget(save_btn)

        main_layout.addWidget(header_card)

        # -------------------------------------------------------------
        # 1. Calendario Institucional de Inscripción de Materias
        # -------------------------------------------------------------
        cal_card = QFrame()
        cal_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 14px;
                padding: 18px;
            }
        """)
        cal_layout = QVBoxLayout(cal_card)
        cal_layout.setSpacing(14)

        cal_header = QHBoxLayout()
        cal_title = QLabel("📅 Calendario Institucional de Inscripción de Asignaturas")
        cal_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #1e3a8a;")
        cal_header.addWidget(cal_title)
        cal_header.addStretch()
        cal_badge = QLabel("Período Activo: 2026-2")
        cal_badge.setStyleSheet("background-color: #e0e7ff; color: #3730a3; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 6px;")
        cal_header.addWidget(cal_badge)
        cal_layout.addLayout(cal_header)

        # Dates Subcards Grid
        dates_grid = QGridLayout()
        dates_grid.setSpacing(14)

        # Regular Students Subcard (Mint Pastel)
        reg_box = QFrame()
        reg_box.setStyleSheet("""
            QFrame {
                background-color: #f0fdf4;
                border: 1.5px solid #bbf7d0;
                border-radius: 12px;
                padding: 14px;
            }
        """)
        r_layout = QVBoxLayout(reg_box)
        r_layout.setSpacing(10)

        r_head = QHBoxLayout()
        r_title = QLabel("🎓 Estudiantes Nivelados (Regulares)")
        r_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #166534;")
        r_badge = QLabel("Turno 1: Prioritario")
        r_badge.setStyleSheet("background-color: #dcfce7; color: #15803d; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px;")
        r_head.addWidget(r_title)
        r_head.addStretch()
        r_head.addWidget(r_badge)
        r_layout.addLayout(r_head)

        r_desc = QLabel("Alumnos que se encuentran al día con su plan de estudios y sin asignaturas pendientes de semestres anteriores.")
        r_desc.setWordWrap(True)
        r_desc.setStyleSheet("font-size: 11px; color: #15803d;")
        r_layout.addWidget(r_desc)

        r_form = QHBoxLayout()
        r_form.setSpacing(8)

        lbl_r_start = QLabel("Desde:")
        lbl_r_start.setStyleSheet("font-size: 11px; font-weight: 700; color: #166534;")
        self.reg_start_edit = QDateEdit()
        self.reg_start_edit.setCalendarPopup(True)
        self.reg_start_edit.setDisplayFormat("yyyy-MM-dd")

        lbl_r_end = QLabel("Hasta:")
        lbl_r_end.setStyleSheet("font-size: 11px; font-weight: 700; color: #166534;")
        self.reg_end_edit = QDateEdit()
        self.reg_end_edit.setCalendarPopup(True)
        self.reg_end_edit.setDisplayFormat("yyyy-MM-dd")

        r_form.addWidget(lbl_r_start)
        r_form.addWidget(self.reg_start_edit)
        r_form.addWidget(lbl_r_end)
        r_form.addWidget(self.reg_end_edit)
        r_layout.addLayout(r_form)

        dates_grid.addWidget(reg_box, 0, 0)

        # Irregular Students Subcard (Amber Pastel)
        irreg_box = QFrame()
        irreg_box.setStyleSheet("""
            QFrame {
                background-color: #fffbeb;
                border: 1.5px solid #fde68a;
                border-radius: 12px;
                padding: 14px;
            }
        """)
        ir_layout = QVBoxLayout(irreg_box)
        ir_layout.setSpacing(10)

        ir_head = QHBoxLayout()
        ir_title = QLabel("⚠️ Estudiantes No Nivelados (Rezagados)")
        ir_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #92400e;")
        ir_badge = QLabel("Turno 2: Extemporáneo")
        ir_badge.setStyleSheet("background-color: #fef3c7; color: #b45309; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px;")
        ir_head.addWidget(ir_title)
        ir_head.addStretch()
        ir_head.addWidget(ir_badge)
        ir_layout.addLayout(ir_head)

        ir_desc = QLabel("Alumnos con asignaturas pendientes o fuera de ciclo. Se habilita acceso tras finalizar el turno prioritario.")
        ir_desc.setWordWrap(True)
        ir_desc.setStyleSheet("font-size: 11px; color: #92400e;")
        ir_layout.addWidget(ir_desc)

        ir_form = QHBoxLayout()
        ir_form.setSpacing(8)

        lbl_ir_start = QLabel("Desde:")
        lbl_ir_start.setStyleSheet("font-size: 11px; font-weight: 700; color: #92400e;")
        self.irreg_start_edit = QDateEdit()
        self.irreg_start_edit.setCalendarPopup(True)
        self.irreg_start_edit.setDisplayFormat("yyyy-MM-dd")

        lbl_ir_end = QLabel("Hasta:")
        lbl_ir_end.setStyleSheet("font-size: 11px; font-weight: 700; color: #92400e;")
        self.irreg_end_edit = QDateEdit()
        self.irreg_end_edit.setCalendarPopup(True)
        self.irreg_end_edit.setDisplayFormat("yyyy-MM-dd")

        ir_form.addWidget(lbl_ir_start)
        ir_form.addWidget(self.irreg_start_edit)
        ir_form.addWidget(lbl_ir_end)
        ir_form.addWidget(self.irreg_end_edit)
        ir_layout.addLayout(ir_form)

        dates_grid.addWidget(irreg_box, 0, 1)
        cal_layout.addLayout(dates_grid)

        # System Date Simulator Box (Lavender Pastel)
        curr_box = QFrame()
        curr_box.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 12px 16px;
            }
        """)
        curr_layout = QHBoxLayout(curr_box)
        curr_layout.setSpacing(12)

        c_lbl = QLabel("🕒 <b>Fecha Simulada del Sistema:</b>")
        c_lbl.setStyleSheet("font-size: 12px; color: #1e293b;")
        curr_layout.addWidget(c_lbl)

        self.curr_date_edit = QDateEdit()
        self.curr_date_edit.setCalendarPopup(True)
        self.curr_date_edit.setDisplayFormat("yyyy-MM-dd")
        curr_layout.addWidget(self.curr_date_edit)

        btn_today = QPushButton("Establecer Hoy")
        btn_today.setCursor(Qt.PointingHandCursor)
        btn_today.setStyleSheet("background-color: #4f46e5; color: white; padding: 6px 12px; border-radius: 6px; font-size: 11px;")
        btn_today.clicked.connect(lambda: self.curr_date_edit.setDate(QDate.currentDate()))
        curr_layout.addWidget(btn_today)

        hint = QLabel("<i>(Permite simular el paso del tiempo para verificar si un estudiante se encuentra en fecha o fuera de fecha en tiempo real)</i>")
        hint.setStyleSheet("font-size: 11px; color: #64748b;")
        curr_layout.addWidget(hint)
        curr_layout.addStretch()

        cal_layout.addWidget(curr_box)
        main_layout.addWidget(cal_card)

        # -------------------------------------------------------------
        # 2. Restricciones Duras (Límites Contractuales)
        # -------------------------------------------------------------
        hard_card = QFrame()
        hard_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 14px;
                padding: 18px;
            }
        """)
        h_card_layout = QVBoxLayout(hard_card)
        h_card_layout.setSpacing(14)

        hard_title = QLabel("⚡ Restricciones Duras (Límites Contractuales y Operativos)")
        hard_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #1e3a8a;")
        h_card_layout.addWidget(hard_title)

        limits_grid = QGridLayout()
        limits_grid.setSpacing(12)

        self.ft_spin = QSpinBox()
        self.ft_spin.setRange(10, 60)
        self.ft_spin.setSuffix(" hrs/semana")
        limits_grid.addWidget(self._create_input_block("👔 Docente Tiempo Completo (FT)", "Tope máximo contractual", self.ft_spin), 0, 0)

        self.pt_spin = QSpinBox()
        self.pt_spin.setRange(5, 40)
        self.pt_spin.setSuffix(" hrs/semana")
        limits_grid.addWidget(self._create_input_block("⏱️ Docente Medio Tiempo (PT)", "Tope máximo contractual", self.pt_spin), 0, 1)

        self.cat_spin = QSpinBox()
        self.cat_spin.setRange(4, 30)
        self.cat_spin.setSuffix(" hrs/semana")
        limits_grid.addWidget(self._create_input_block("🎓 Docente de Cátedra", "Tope máximo contractual", self.cat_spin), 1, 0)

        self.consec_spin = QSpinBox()
        self.consec_spin.setRange(2, 8)
        self.consec_spin.setSuffix(" hrs seguidas")
        limits_grid.addWidget(self._create_input_block("⏳ Horas Continuas Máximas", "Límite pedagógico sin descanso", self.consec_spin), 1, 1)

        h_card_layout.addLayout(limits_grid)

        # Saturday Operation Toggle Pill
        sat_frame = QFrame()
        sat_frame.setStyleSheet("""
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 10px 14px;
        """)
        sat_layout = QHBoxLayout(sat_frame)
        self.sat_check = QCheckBox("Habilitar Sábados para clases académicas institucionales (Jornada hasta las 17:00 / 5:00 p.m.)")
        self.sat_check.setStyleSheet("font-weight: 700; color: #1e293b;")
        sat_layout.addWidget(self.sat_check)
        sat_layout.addStretch()
        h_card_layout.addWidget(sat_frame)

        # Payment Agreement Operation Toggle Pill
        pay_frame = QFrame()
        pay_frame.setStyleSheet("""
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 10px 14px;
        """)
        pay_layout = QHBoxLayout(pay_frame)
        self.payment_agreement_check = QCheckBox("Permitir Matrícula de Horario a Estudiantes con Acuerdo de Pago (Financiación)")
        self.payment_agreement_check.setStyleSheet("font-weight: 700; color: #1e293b;")
        pay_layout.addWidget(self.payment_agreement_check)
        pay_layout.addStretch()
        h_card_layout.addWidget(pay_frame)

        main_layout.addWidget(hard_card)

        # -------------------------------------------------------------
        # 3. Restricciones Blandas (Ponderaciones Multicriterio)
        # -------------------------------------------------------------
        soft_card = QFrame()
        soft_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 14px;
                padding: 18px;
            }
        """)
        s_card_layout = QVBoxLayout(soft_card)
        s_card_layout.setSpacing(14)

        soft_title = QLabel("⚖️ Ponderaciones del Optimizador Matemático (Función Objetivo CP-SAT)")
        soft_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #1e3a8a;")
        s_card_layout.addWidget(soft_title)

        weights_grid = QGridLayout()
        weights_grid.setSpacing(12)

        self.pref_weight = QDoubleSpinBox()
        self.pref_weight.setRange(0.0, 1.0)
        self.pref_weight.setSingleStep(0.05)
        weights_grid.addWidget(self._create_input_block("🎯 Preferencias y Afinidad", "Prioridad asignación docente-materia", self.pref_weight), 0, 0)

        self.gap_weight = QDoubleSpinBox()
        self.gap_weight.setRange(0.0, 1.0)
        self.gap_weight.setSingleStep(0.05)
        weights_grid.addWidget(self._create_input_block("🪟 Minimización de Huecos", "Compactación horaria sin ventanas", self.gap_weight), 0, 1)

        self.load_weight = QDoubleSpinBox()
        self.load_weight.setRange(0.0, 1.0)
        self.load_weight.setSingleStep(0.05)
        weights_grid.addWidget(self._create_input_block("⚖️ Balance de Carga Laboral", "Distribución equitativa docente", self.load_weight), 1, 0)

        self.room_weight = QDoubleSpinBox()
        self.room_weight.setRange(0.0, 1.0)
        self.room_weight.setSingleStep(0.05)
        weights_grid.addWidget(self._create_input_block("📍 Eficiencia de Aulas", "Optimización de espacio físico", self.room_weight), 1, 1)

        self.dist_weight = QDoubleSpinBox()
        self.dist_weight.setRange(0.0, 1.0)
        self.dist_weight.setSingleStep(0.05)
        weights_grid.addWidget(self._create_input_block("📅 Distribución Semanal", "Separación regular de sesiones", self.dist_weight), 2, 0)

        # Informative box to balance row 2
        info_weight_box = QFrame()
        info_weight_box.setStyleSheet("""
            QFrame {
                background-color: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 10px;
                padding: 10px 14px;
            }
        """)
        iw_layout = QVBoxLayout(info_weight_box)
        iw_layout.setSpacing(4)
        iw_title = QLabel("💡 Normalización de Pesos Multicriterio")
        iw_title.setStyleSheet("font-size: 12px; font-weight: 800; color: #1e40af;")
        iw_desc = QLabel("Los 5 coeficientes calibran la función objetivo de Google OR-Tools CP-SAT para equilibrar confort docente y uso de recursos.")
        iw_desc.setWordWrap(True)
        iw_desc.setStyleSheet("font-size: 11px; color: #3b82f6;")
        iw_layout.addWidget(iw_title)
        iw_layout.addWidget(iw_desc)
        weights_grid.addWidget(info_weight_box, 2, 1)

        s_card_layout.addLayout(weights_grid)
        main_layout.addWidget(soft_card)
        main_layout.addSpacing(60)

        self.load_config()

    def _create_input_block(self, title, desc, widget):
        box = QFrame()
        box.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 10px 14px;
            }
        """)
        l = QVBoxLayout(box)
        l.setSpacing(4)

        t = QLabel(title)
        t.setStyleSheet("font-size: 12px; font-weight: 800; color: #1e293b;")
        d = QLabel(desc)
        d.setStyleSheet("font-size: 11px; color: #64748b;")

        l.addWidget(t)
        l.addWidget(d)
        l.addWidget(widget)
        return box

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
            self.payment_agreement_check.setChecked(config.payment_agreement_allowed if hasattr(config, "payment_agreement_allowed") and config.payment_agreement_allowed is not None else True)

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
            config.payment_agreement_allowed = self.payment_agreement_check.isChecked()

            config.pref_weight = self.pref_weight.value()
            config.gap_weight = self.gap_weight.value()
            config.load_weight = self.load_weight.value()
            config.room_weight = self.room_weight.value()
            config.dist_weight = self.dist_weight.value()

            db.commit()
            QMessageBox.information(self, "Configuración Actualizada", "¡Las fechas institucionales, límites de contratación y pesos de optimización se guardaron exitosamente!")
        finally:
            db.close()
