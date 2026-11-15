from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QFrame, QGroupBox,
    QCheckBox, QRadioButton, QButtonGroup, QSlider, QTabWidget,
    QMessageBox, QScrollArea, QFileDialog, QGridLayout
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QDate
import csv
from datetime import datetime
from app.database.database import SessionLocal
from app.database.models import (
    Student, ScheduleAssignment, TimeSlot, DayOfWeek, Subject, ShiftType, 
    StudentEnrollment, StudentPreference, Config, Group
)
from app.optimization.student_optimizer import StudentScheduleOptimizer
from app.auth.session import session
from app.ui.dialogs.schedule_preview_dialog import SchedulePreviewDialog
from app.ui.excel_exporter import export_schedule_dialog

class StudentScheduleView(QWidget):
    def __init__(self):
        super().__init__()
        self.optimizer_options = []
        self.current_preview_option = None
        self.subject_checkboxes = {}
        self.days = [d.value for d in DayOfWeek]
        self.is_enrollment_allowed = True
        self.enrollment_status_msg = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header Info Card
        self.info_card = QFrame()
        self.info_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff; 
                border-left: 6px solid #4f46e5; 
                border-radius: 12px; 
                padding: 14px 20px; 
                border-top: 1px solid #e2e8f0;
                border-right: 1px solid #e2e8f0;
                border-bottom: 1px solid #e2e8f0;
            }
        """)
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setSpacing(8)

        top_info_row = QHBoxLayout()
        self.student_name_lbl = QLabel("🎓 Estudiante: -")
        self.student_name_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #1e3a8a;")
        top_info_row.addWidget(self.student_name_lbl)
        top_info_row.addStretch()

        refresh_btn = QPushButton("🔄 Actualizar Datos")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5; 
                color: white; 
                font-weight: bold; 
                padding: 7px 16px; 
                border-radius: 7px;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
        """)
        refresh_btn.clicked.connect(self.load_data)
        top_info_row.addWidget(refresh_btn)
        info_layout.addLayout(top_info_row)

        # Badges Row (Semester, Leveling, Financial, Enrollment Window)
        self.badges_layout = QHBoxLayout()
        self.badges_layout.setSpacing(8)
        
        self.badge_semester = QLabel("Semestre: -")
        self.badge_leveling = QLabel("Nivelación: -")
        self.badge_enrollment = QLabel("Matrícula: -")
        self.badge_financial = QLabel("Financiero: -")
        self.badge_window = QLabel("Ventana: -")

        for b in [self.badge_semester, self.badge_leveling, self.badge_enrollment, self.badge_financial, self.badge_window]:
            b.setStyleSheet("font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 6px; background-color: #f1f5f9; color: #334155;")
            self.badges_layout.addWidget(b)
        
        self.badges_layout.addStretch()
        info_layout.addLayout(self.badges_layout)

        layout.addWidget(self.info_card)

        # Tabs
        self.tabs = QTabWidget()

        # TAB 1: Optimizer & Planner (Scrollable to prevent overlapping / cut off buttons)
        self.planner_scroll = QScrollArea()
        self.planner_scroll.setWidgetResizable(True)
        self.planner_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.planner_tab = QWidget()
        self.setup_planner_tab()
        self.planner_scroll.setWidget(self.planner_tab)

        self.tabs.addTab(self.planner_scroll, "⚡ Planificador Personal y Alternativas")

        # TAB 2: Official Enrolled Timetable
        self.timetable_tab = QWidget()
        self.setup_timetable_tab()
        self.tabs.addTab(self.timetable_tab, "📅 Mi Horario Oficial Inscrito")
        self.tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tabs)
        self.load_data()

    def setup_planner_tab(self):
        p_layout = QVBoxLayout(self.planner_tab)
        p_layout.setSpacing(14)
        p_layout.setContentsMargins(10, 10, 10, 10)

        # Top Controls: 2 Columns
        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        # 1. Subject Selection Box
        subj_group = QGroupBox("1. Selecciona las Asignaturas a Cursar")
        subj_group.setStyleSheet("QGroupBox { font-weight: 800; color: #1e3a8a; }")
        subj_layout = QVBoxLayout(subj_group)
        subj_layout.setSpacing(8)

        # Quick action buttons for selection
        quick_btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("✓ Todas")
        select_all_btn.setCursor(Qt.PointingHandCursor)
        select_all_btn.setStyleSheet("background-color: #e2e8f0; color: #334155; font-size: 11px; padding: 4px 10px; border-radius: 5px; font-weight: bold;")
        select_all_btn.clicked.connect(self.select_all_subjects)
        quick_btn_layout.addWidget(select_all_btn)

        clear_all_btn = QPushButton("✕ Ninguna")
        clear_all_btn.setCursor(Qt.PointingHandCursor)
        clear_all_btn.setStyleSheet("background-color: #e2e8f0; color: #334155; font-size: 11px; padding: 4px 10px; border-radius: 5px; font-weight: bold;")
        clear_all_btn.clicked.connect(self.clear_all_subjects)
        quick_btn_layout.addWidget(clear_all_btn)
        quick_btn_layout.addStretch()

        self.subj_count_lbl = QLabel("0 seleccionadas")
        self.subj_count_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #4f46e5;")
        quick_btn_layout.addWidget(self.subj_count_lbl)
        subj_layout.addLayout(quick_btn_layout)

        # Scrollable area for subject cards
        self.subj_scroll = QScrollArea()
        self.subj_scroll.setWidgetResizable(True)
        self.subj_scroll.setStyleSheet("QScrollArea { border: 1px solid #e2e8f0; border-radius: 8px; background-color: #f8fafc; }")
        self.subj_container = QWidget()
        self.subj_container.setStyleSheet("background-color: transparent;")
        self.subj_checkboxes_layout = QVBoxLayout(self.subj_container)
        self.subj_checkboxes_layout.setSpacing(6)
        self.subj_scroll.setWidget(self.subj_container)
        self.subj_scroll.setMinimumHeight(210)
        subj_layout.addWidget(self.subj_scroll)

        top_row.addWidget(subj_group, 3)

        # 2. Preferences & Weights Box
        pref_group = QGroupBox("2. Tus Preferencias y Ponderaciones")
        pref_group.setStyleSheet("QGroupBox { font-weight: 800; color: #1e3a8a; }")
        pref_layout = QVBoxLayout(pref_group)
        pref_layout.setSpacing(10)

        # Registered Shift Info Card (Loaded from StudentPreferences)
        self.shift_info_card = QFrame()
        self.shift_info_card.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        shift_info_layout = QVBoxLayout(self.shift_info_card)
        shift_info_layout.setSpacing(4)

        self.registered_shift_lbl = QLabel("☀️ Jornada Registrada: <b>Cargando...</b>")
        self.registered_shift_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #1e3a8a;")
        shift_info_layout.addWidget(self.registered_shift_lbl)

        shift_hint = QLabel("💡 Tu jornada preferida se gestiona en <i>☀️ Preferencia de Jornada</i>. Aquí defines cuánto ponderarla frente a huecos y días libres.")
        shift_hint.setStyleSheet("font-size: 11px; color: #64748b;")
        shift_hint.setWordWrap(True)
        shift_info_layout.addWidget(shift_hint)

        pref_layout.addWidget(self.shift_info_card)

        # Sliders for priorities (strictly auto-balanced to 100%)
        weights_container = QVBoxLayout()
        weights_container.setSpacing(8)

        # Total Balance Badge
        balance_row = QHBoxLayout()
        self.lbl_total_w_badge = QLabel("⚖️ Balance Total: 100% (Coherente)")
        self.lbl_total_w_badge.setStyleSheet("font-size: 11px; font-weight: 800; color: #047857; background-color: #ecfdf5; padding: 4px 10px; border-radius: 6px; border: 1px solid #a7f3d0;")
        balance_row.addWidget(self.lbl_total_w_badge)
        balance_row.addStretch()
        weights_container.addLayout(balance_row)

        # Slider 1: Shift Priority
        s1_row = QHBoxLayout()
        self.lbl_shift_w = QLabel("Prioridad de Jornada: <b>40%</b>")
        self.lbl_shift_w.setStyleSheet("color: #1e293b; font-size: 12px;")
        self.shift_weight_slider = QSlider(Qt.Horizontal)
        self.shift_weight_slider.setRange(0, 100)
        self.shift_weight_slider.setValue(40)
        s1_row.addWidget(self.lbl_shift_w, 2)
        s1_row.addWidget(self.shift_weight_slider, 3)
        weights_container.addLayout(s1_row)

        # Slider 2: Minimize Gaps
        s2_row = QHBoxLayout()
        self.lbl_gap_w = QLabel("Minimizar Huecos / Ventanas: <b>40%</b>")
        self.lbl_gap_w.setStyleSheet("color: #1e293b; font-size: 12px;")
        self.gap_weight_slider = QSlider(Qt.Horizontal)
        self.gap_weight_slider.setRange(0, 100)
        self.gap_weight_slider.setValue(40)
        s2_row.addWidget(self.lbl_gap_w, 2)
        s2_row.addWidget(self.gap_weight_slider, 3)
        weights_container.addLayout(s2_row)

        # Slider 3: Maximize Free Days
        s3_row = QHBoxLayout()
        self.lbl_free_w = QLabel("Maximizar Días Libres: <b>20%</b>")
        self.lbl_free_w.setStyleSheet("color: #1e293b; font-size: 12px;")
        self.free_weight_slider = QSlider(Qt.Horizontal)
        self.free_weight_slider.setRange(0, 100)
        self.free_weight_slider.setValue(20)
        s3_row.addWidget(self.lbl_free_w, 2)
        s3_row.addWidget(self.free_weight_slider, 3)
        weights_container.addLayout(s3_row)

        # Connect dynamic auto-balancing signals
        self.shift_weight_slider.valueChanged.connect(lambda: self._on_weight_slider_changed(self.shift_weight_slider))
        self.gap_weight_slider.valueChanged.connect(lambda: self._on_weight_slider_changed(self.gap_weight_slider))
        self.free_weight_slider.valueChanged.connect(lambda: self._on_weight_slider_changed(self.free_weight_slider))

        pref_layout.addLayout(weights_container)

        # Optimize Button
        self.opt_btn = QPushButton("🚀 OPTIMIZAR MI HORARIO PERSONAL")
        self.opt_btn.setCursor(Qt.PointingHandCursor)
        self.opt_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981; 
                color: white; 
                font-weight: 800; 
                padding: 12px; 
                border-radius: 8px; 
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.opt_btn.clicked.connect(self.run_student_optimization)
        pref_layout.addWidget(self.opt_btn)

        top_row.addWidget(pref_group, 4)
        p_layout.addLayout(top_row)

        # 3. Alternatives Comparison Cards & Live Preview
        comp_group = QGroupBox("3. Alternativas Generadas por el Optimizador")
        comp_group.setStyleSheet("QGroupBox { font-weight: 800; color: #1e3a8a; }")
        comp_layout = QVBoxLayout(comp_group)
        comp_layout.setSpacing(12)

        self.options_cards_layout = QHBoxLayout()
        self.options_cards_layout.setSpacing(12)
        comp_layout.addLayout(self.options_cards_layout)

        # Live Preview Header with Modal Button & Height Slider
        preview_bar = QHBoxLayout()
        self.preview_title_lbl = QLabel("Previsualización de la Alternativa Seleccionada:")
        self.preview_title_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #1e293b;")
        preview_bar.addWidget(self.preview_title_lbl)
        preview_bar.addStretch()

        self.open_modal_btn = QPushButton("🔍 Ver en Pantalla Completa / Modal")
        self.open_modal_btn.setCursor(Qt.PointingHandCursor)
        self.open_modal_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; 
                color: white; 
                font-weight: bold; 
                padding: 7px 16px; 
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
                color: #94a3b8;
            }
        """)
        self.open_modal_btn.setEnabled(False)
        self.open_modal_btn.clicked.connect(self.open_current_modal)
        preview_bar.addWidget(self.open_modal_btn)
        comp_layout.addLayout(preview_bar)

        # Container for Preview Table + Fluid Lateral Slider
        preview_container = QHBoxLayout()
        preview_container.setSpacing(8)

        # Live Schedule Preview Table
        self.preview_table = QTableWidget()
        self.days = [d.value for d in DayOfWeek]
        self.preview_table.setColumnCount(len(self.days))
        self.preview_table.setHorizontalHeaderLabels(self.days)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.preview_table.verticalHeader().setMinimumWidth(180)
        self.preview_table.verticalHeader().setDefaultSectionSize(55)
        self.preview_table.setMinimumHeight(240)
        self.preview_table.setStyleSheet("""
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
        preview_container.addWidget(self.preview_table, 1)

        # Fluid Lateral Slider for Preview Table
        p_lat_box = QVBoxLayout()
        p_lat_box.setSpacing(4)
        p_lat_box.setAlignment(Qt.AlignCenter)

        p_top_icon = QLabel("☀️")
        p_top_icon.setAlignment(Qt.AlignCenter)
        p_mid_icon = QLabel("⛅")
        p_mid_icon.setAlignment(Qt.AlignCenter)
        p_bot_icon = QLabel("🌙")
        p_bot_icon.setAlignment(Qt.AlignCenter)

        self.preview_lateral_slider = QSlider(Qt.Vertical)
        self.preview_lateral_slider.setRange(0, 100)
        self.preview_lateral_slider.setValue(0)
        self.preview_lateral_slider.setInvertedAppearance(True)
        self.preview_lateral_slider.setFixedWidth(26)
        self.preview_lateral_slider.setCursor(Qt.PointingHandCursor)
        self.preview_lateral_slider.setToolTip("Desliza lateralmente para navegar por el horario")
        self.preview_lateral_slider.setStyleSheet("""
            QSlider::groove:vertical {
                background: #e2e8f0;
                width: 10px;
                border-radius: 5px;
            }
            QSlider::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4f46e5, stop:1 #3730a3);
                height: 38px;
                margin: 0 -5px;
                border-radius: 7px;
                border: 1.5px solid #ffffff;
            }
            QSlider::handle:vertical:hover {
                background: #4338ca;
            }
        """)
        self.preview_lateral_slider.valueChanged.connect(self._on_preview_lateral_slider_changed)
        self.preview_table.verticalScrollBar().rangeChanged.connect(self._sync_preview_lateral_slider_range)
        self.preview_table.verticalScrollBar().valueChanged.connect(self._sync_preview_lateral_slider_value)

        p_lat_box.addWidget(p_top_icon)
        p_lat_box.addWidget(p_mid_icon)
        p_lat_box.addWidget(self.preview_lateral_slider, 1)
        p_lat_box.addWidget(p_bot_icon)
        preview_container.addLayout(p_lat_box)

        comp_layout.addLayout(preview_container)

        # Save Selected Schedule Button
        self.save_schedule_btn = QPushButton("✅ CONFIRMAR E INSCRIBIR ESTA ALTERNATIVA")
        self.save_schedule_btn.setEnabled(False)
        self.save_schedule_btn.setCursor(Qt.PointingHandCursor)
        self.save_schedule_btn.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5; 
                color: white; 
                font-weight: 800; 
                padding: 13px; 
                border-radius: 8px; 
                font-size: 14px;
                margin-top: 6px;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
            QPushButton:disabled {
                background-color: #e2e8f0;
                color: #94a3b8;
            }
        """)
        self.save_schedule_btn.clicked.connect(self.confirm_enrollment)
        comp_layout.addWidget(self.save_schedule_btn)

        p_layout.addWidget(comp_group)

    def setup_timetable_tab(self):
        t_layout = QVBoxLayout(self.timetable_tab)
        t_layout.setSpacing(12)
        t_layout.setContentsMargins(10, 10, 10, 10)

        t_header = QHBoxLayout()
        t_title = QLabel("Mi Horario Oficial Registrado")
        t_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #1e3a8a;")
        t_header.addWidget(t_title)
        t_header.addStretch()

        refresh_official_btn = QPushButton("🔄 Actualizar Horario")
        refresh_official_btn.setCursor(Qt.PointingHandCursor)
        refresh_official_btn.setStyleSheet("background-color: #4f46e5; color: white; font-weight: bold; padding: 8px 16px; border-radius: 7px;")
        refresh_official_btn.clicked.connect(self.load_official_schedule)
        t_header.addWidget(refresh_official_btn)

        export_btn = QPushButton("📥 Exportar Mi Horario (CSV)")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 8px 16px; border-radius: 7px;")
        export_btn.clicked.connect(self.export_my_schedule)
        t_header.addWidget(export_btn)
        t_layout.addLayout(t_header)

        # Official Table + Fluid Lateral Slider Container
        official_container = QHBoxLayout()
        official_container.setSpacing(8)

        self.official_table = QTableWidget()
        self.official_table.setColumnCount(len(self.days))
        self.official_table.setHorizontalHeaderLabels(self.days)
        self.official_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.official_table.verticalHeader().setMinimumWidth(180)
        self.official_table.verticalHeader().setDefaultSectionSize(55)
        self.official_table.setStyleSheet("""
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
        official_container.addWidget(self.official_table, 1)

        # Fluid Lateral Slider for Official Timetable
        o_lat_box = QVBoxLayout()
        o_lat_box.setSpacing(4)
        o_lat_box.setAlignment(Qt.AlignCenter)

        o_top_icon = QLabel("☀️")
        o_top_icon.setAlignment(Qt.AlignCenter)
        o_mid_icon = QLabel("⛅")
        o_mid_icon.setAlignment(Qt.AlignCenter)
        o_bot_icon = QLabel("🌙")
        o_bot_icon.setAlignment(Qt.AlignCenter)

        self.official_lateral_slider = QSlider(Qt.Vertical)
        self.official_lateral_slider.setRange(0, 100)
        self.official_lateral_slider.setValue(0)
        self.official_lateral_slider.setInvertedAppearance(True)
        self.official_lateral_slider.setFixedWidth(26)
        self.official_lateral_slider.setCursor(Qt.PointingHandCursor)
        self.official_lateral_slider.setToolTip("Desliza lateralmente para navegar por tu horario oficial")
        self.official_lateral_slider.setStyleSheet("""
            QSlider::groove:vertical {
                background: #e2e8f0;
                width: 10px;
                border-radius: 5px;
            }
            QSlider::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4f46e5, stop:1 #3730a3);
                height: 38px;
                margin: 0 -5px;
                border-radius: 7px;
                border: 1.5px solid #ffffff;
            }
            QSlider::handle:vertical:hover {
                background: #4338ca;
            }
        """)
        self.official_lateral_slider.valueChanged.connect(self._on_official_lateral_slider_changed)
        self.official_table.verticalScrollBar().rangeChanged.connect(self._sync_official_lateral_slider_range)
        self.official_table.verticalScrollBar().valueChanged.connect(self._sync_official_lateral_slider_value)

        o_lat_box.addWidget(o_top_icon)
        o_lat_box.addWidget(o_mid_icon)
        o_lat_box.addWidget(self.official_lateral_slider, 1)
        o_lat_box.addWidget(o_bot_icon)
        official_container.addLayout(o_lat_box)

        t_layout.addLayout(official_container)

    def _on_preview_lateral_slider_changed(self, value):
        self.preview_table.verticalScrollBar().setValue(value)

    def _sync_preview_lateral_slider_range(self, min_val, max_val):
        self.preview_lateral_slider.setRange(min_val, max_val)

    def _sync_preview_lateral_slider_value(self, value):
        self.preview_lateral_slider.blockSignals(True)
        self.preview_lateral_slider.setValue(value)
        self.preview_lateral_slider.blockSignals(False)

    def _on_official_lateral_slider_changed(self, value):
        self.official_table.verticalScrollBar().setValue(value)

    def _sync_official_lateral_slider_range(self, min_val, max_val):
        self.official_lateral_slider.setRange(min_val, max_val)

    def _sync_official_lateral_slider_value(self, value):
        self.official_lateral_slider.blockSignals(True)
        self.official_lateral_slider.setValue(value)
        self.official_lateral_slider.blockSignals(False)

    def _on_tab_changed(self, index):
        if index == 1:
            self.load_official_schedule()

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "tabs") and self.tabs.currentIndex() == 1:
            self.load_official_schedule()

    def _on_weight_slider_changed(self, active_slider):
        if getattr(self, "_is_balancing_sliders", False):
            return
        self._is_balancing_sliders = True
        try:
            val = active_slider.value()
            remaining = 100 - val
            sliders = [
                self.shift_weight_slider,
                self.gap_weight_slider,
                self.free_weight_slider
            ]
            others = [s for s in sliders if s is not active_slider]
            s1, s2 = others[0], others[1]
            sum_others = s1.value() + s2.value()

            if sum_others > 0:
                new_v1 = int(round(remaining * (s1.value() / sum_others)))
                new_v2 = remaining - new_v1
            else:
                new_v1 = remaining // 2
                new_v2 = remaining - new_v1

            new_v1 = max(0, min(100, new_v1))
            new_v2 = max(0, min(100, new_v2))

            s1.blockSignals(True)
            s2.blockSignals(True)
            s1.setValue(new_v1)
            s2.setValue(new_v2)
            s1.blockSignals(False)
            s2.blockSignals(False)

            self.lbl_shift_w.setText(f"Prioridad de Jornada: <b>{self.shift_weight_slider.value()}%</b>")
            self.lbl_gap_w.setText(f"Minimizar Huecos / Ventanas: <b>{self.gap_weight_slider.value()}%</b>")
            self.lbl_free_w.setText(f"Maximizar Días Libres: <b>{self.free_weight_slider.value()}%</b>")

            total_sum = self.shift_weight_slider.value() + self.gap_weight_slider.value() + self.free_weight_slider.value()
            self.lbl_total_w_badge.setText(f"⚖️ Balance Total: {total_sum}% (Coherente)")
        finally:
            self._is_balancing_sliders = False

    def on_subject_state_changed(self):
        pending_ids = getattr(self, "pending_subject_ids", set())
        current_ids = getattr(self, "current_sem_subject_ids", set())
        cards = getattr(self, "subject_cards", {})

        if pending_ids:
            # Condition: ALL pending subjects must be checked to lift the current semester lock!
            all_pending_checked = all(
                self.subject_checkboxes[pid].isChecked()
                for pid in pending_ids if pid in self.subject_checkboxes
            )

            for cid in current_ids:
                if cid in cards:
                    card_frame, cb, badge, subj = cards[cid]
                    if all_pending_checked:
                        # Unlock! Prerequisite condition satisfied
                        cb.setEnabled(True)
                        card_frame.setStyleSheet("""
                            QFrame {
                                background-color: #ffffff; 
                                border: 1px solid #e2e8f0; 
                                border-radius: 7px; 
                                padding: 6px 10px;
                            }
                            QFrame:hover {
                                border-color: #6366f1;
                                background-color: #f5f3ff;
                            }
                        """)
                        cb.setStyleSheet("font-weight: 700; color: #1e3a8a;")
                        badge.setText(f"{subj.credits} cr • {subj.hours_per_week}h • Sem {subj.semester_id}")
                        badge.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; background-color: #f1f5f9; padding: 2px 8px; border-radius: 4px;")
                        cb.setToolTip("Asignatura habilitada: Cumples con el requisito de matricular todas tus materias pendientes.")
                    else:
                        # Lock! Prerequisite condition not satisfied
                        cb.blockSignals(True)
                        cb.setChecked(False)
                        cb.setEnabled(False)
                        cb.blockSignals(False)
                        card_frame.setStyleSheet("""
                            QFrame {
                                background-color: #f8fafc; 
                                border: 1px dashed #cbd5e1; 
                                border-radius: 7px; 
                                padding: 6px 10px;
                            }
                        """)
                        cb.setStyleSheet("font-weight: 600; color: #94a3b8;")
                        badge.setText("🔒 Bloqueada (Debes matricular primero todas tus materias pendientes)")
                        badge.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b; background-color: #f1f5f9; padding: 2px 8px; border-radius: 4px; border: 1px solid #e2e8f0;")
                        cb.setToolTip("Inscripción no disponible: Para matricular materias del semestre actual debes tener seleccionadas todas tus materias pendientes.")

        self.update_subject_count()

    def select_all_subjects(self):
        # 1. First ensure all pending subjects are checked so current semester unlocks
        pending_ids = getattr(self, "pending_subject_ids", set())
        for pid in pending_ids:
            if pid in self.subject_checkboxes:
                self.subject_checkboxes[pid].setChecked(True)

        self.on_subject_state_changed()

        # 2. Check all enabled current semester subjects
        for cb in self.subject_checkboxes.values():
            if cb.isEnabled():
                cb.setChecked(True)
        self.update_subject_count()

    def clear_all_subjects(self):
        # Uncheck current semester subjects, leaving pending subjects checked
        current_ids = getattr(self, "current_sem_subject_ids", set())
        for cid in current_ids:
            if cid in self.subject_checkboxes:
                self.subject_checkboxes[cid].setChecked(False)
        self.update_subject_count()

    def update_subject_count(self):
        checked = 0
        total_credits = 0
        subjects_map = getattr(self, "subjects_map", {})
        for s_id, cb in self.subject_checkboxes.items():
            if cb.isChecked():
                checked += 1
                subj = subjects_map.get(s_id)
                total_credits += (subj.credits if subj and hasattr(subj, "credits") and subj.credits else 3)

        if total_credits > 22:
            self.subj_count_lbl.setText(f"⚠️ {checked} materias ({total_credits}/22 créd. EXCEDIDO)")
            self.subj_count_lbl.setStyleSheet("font-size: 11px; font-weight: 800; color: #dc2626; padding: 3px 8px; background-color: #fee2e2; border-radius: 4px; border: 1px solid #f87171;")
        else:
            self.subj_count_lbl.setText(f"{checked} materias • {total_credits}/22 créditos")
            self.subj_count_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #4338ca; padding: 3px 8px; background-color: #e0e7ff; border-radius: 4px;")

    def load_data(self):
        db = SessionLocal()
        try:
            student_id = session.student_id
            if not student_id:
                s = db.query(Student).first()
                student_id = s.id if s else None

            if not student_id:
                return

            student = db.query(Student).filter_by(id=student_id).first()
            if not student:
                return

            config = db.query(Config).first()

            # Leveling status
            is_regular = getattr(student, "is_regular", True)
            if is_regular:
                self.badge_leveling.setText("🎓 Estudiante Nivelado")
                self.badge_leveling.setStyleSheet("background-color: #ecfdf5; color: #065f46; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #a7f3d0;")
            else:
                self.badge_leveling.setText("⚠️ No Nivelado (Rezagado)")
                self.badge_leveling.setStyleSheet("background-color: #fffbeb; color: #92400e; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #fde68a;")

            # Enrollment active status (is_enrolled)
            is_enrolled_active = getattr(student, "is_enrolled", True)
            if is_enrolled_active:
                self.badge_enrollment.setText("✅ Matrícula Activa")
                self.badge_enrollment.setStyleSheet("background-color: #ecfdf5; color: #065f46; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #a7f3d0;")
            else:
                self.badge_enrollment.setText("🔴 Matrícula Inactiva / No Inscrito")
                self.badge_enrollment.setStyleSheet("background-color: #fff1f2; color: #be123c; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #f43f5e;")

            # Financial standing (has_payment_agreement vs payment_agreement_allowed)
            payment_allowed = getattr(config, "payment_agreement_allowed", True) if config else True
            has_financial_block = (getattr(student, "has_payment_agreement", False) and not payment_allowed)

            if not student.has_payment_agreement:
                self.badge_financial.setText("💳 Paz y Salvo (Al Día)")
                self.badge_financial.setStyleSheet("background-color: #eff6ff; color: #1e40af; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #bfdbfe;")
            elif payment_allowed:
                self.badge_financial.setText("📋 Con Acuerdo de Pago (Autorizado)")
                self.badge_financial.setStyleSheet("background-color: #fff7ed; color: #9a3412; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #fed7aa;")
            else:
                self.badge_financial.setText("🔴 Bloqueo Financiero (Acuerdo No Autorizado)")
                self.badge_financial.setStyleSheet("background-color: #fff1f2; color: #be123c; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #f43f5e;")

            self.student_name_lbl.setText(f"🎓 Estudiante: {student.name}")
            self.badge_semester.setText(f"📚 Semestre {student.semester_id}")

            # Check enrollment dates
            curr_date_str = getattr(config, "system_current_date", "2026-09-08") if config else "2026-09-08"
            if is_regular:
                start_date_str = getattr(config, "enrollment_start_regular", "2026-09-01") if config else "2026-09-01"
                end_date_str = getattr(config, "enrollment_end_regular", "2026-09-15") if config else "2026-09-15"
            else:
                start_date_str = getattr(config, "enrollment_start_irregular", "2026-09-16") if config else "2026-09-16"
                end_date_str = getattr(config, "enrollment_end_irregular", "2026-09-30") if config else "2026-09-30"

            try:
                curr_d = datetime.strptime(curr_date_str, "%Y-%m-%d").date()
                start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_d = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                is_in_window = (start_d <= curr_d <= end_d)
            except Exception:
                is_in_window = True

            # Composite Enrollment Clearance Guard
            if not is_enrolled_active:
                self.is_enrollment_allowed = False
                self.enrollment_block_reason = "Matrícula académica inactiva. No estás inscrito como estudiante activo para este período académico."
                self.badge_window.setText("🔴 Inscripción Bloqueada (Matrícula Inactiva)")
                self.badge_window.setStyleSheet("background-color: #fff1f2; color: #be123c; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #f43f5e;")
            elif has_financial_block:
                self.is_enrollment_allowed = False
                self.enrollment_block_reason = "Bloqueo por Tesorería: La Universidad no autoriza inscripciones con acuerdos de pago pendientes en este período."
                self.badge_window.setText("🔴 Inscripción Bloqueada (Trámite Financiero)")
                self.badge_window.setStyleSheet("background-color: #fff1f2; color: #be123c; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #f43f5e;")
            elif not is_in_window:
                self.is_enrollment_allowed = False
                self.enrollment_block_reason = f"Fuera de fecha de matrícula para tu cohorte (Turno: {start_date_str} al {end_date_str})."
                self.badge_window.setText(f"🔴 Fuera de Fecha (Turno: {start_date_str} al {end_date_str})")
                self.badge_window.setStyleSheet("background-color: #fff1f2; color: #be123c; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #f43f5e;")
            else:
                self.is_enrollment_allowed = True
                self.enrollment_block_reason = ""
                self.badge_window.setText(f"🟢 Inscripción Habilitada (Hasta {end_date_str})")
                self.badge_window.setStyleSheet("background-color: #ecfdf5; color: #047857; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #10b981;")

            # Clear subject checkboxes
            while self.subj_checkboxes_layout.count() > 0:
                item = self.subj_checkboxes_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Academic Prerequisite Rule:
            # - Semester 1 students are newcomers (always regular).
            # - Regular students (is_regular == True) enroll in their current semester subjects.
            # - Irregular students: pending subjects are condition to unlock current semester subjects.
            pending_ids = set()
            if is_regular or student.semester_id <= 1:
                subjects = db.query(Subject).filter_by(semester_id=student.semester_id).all()
                pending_subjs = []
                current_subjs = subjects
            else:
                pending_ids_str = getattr(student, "pending_subject_ids", "") or ""
                parsed_ids = [int(x) for x in pending_ids_str.split(",") if x.strip().isdigit()]
                if parsed_ids:
                    pending_subjs = db.query(Subject).filter(Subject.id.in_(parsed_ids)).all()
                else:
                    prev_subjs = db.query(Subject).filter_by(semester_id=student.semester_id - 1).all()
                    pending_subjs = prev_subjs[:1] if prev_subjs else []
                pending_ids = {s.id for s in pending_subjs}
                current_subjs = db.query(Subject).filter_by(semester_id=student.semester_id).all()
                subjects = pending_subjs + current_subjs

            self.pending_subject_ids = pending_ids
            self.current_sem_subject_ids = {s.id for s in current_subjs}
            self.subjects_map = {s.id: s for s in subjects}
            self.subject_checkboxes = {}
            self.subject_cards = {}

            for subj in subjects:
                is_pending = subj.id in pending_ids
                card_frame = QFrame()
                c_l = QHBoxLayout(card_frame)
                c_l.setContentsMargins(8, 5, 8, 5)

                cb = QCheckBox(f"{subj.name}")
                cb.stateChanged.connect(self.on_subject_state_changed)

                if is_pending:
                    # Pending subject from prior semester: defaults to checked
                    card_frame.setStyleSheet("""
                        QFrame {
                            background-color: #fffbeb; 
                            border: 1.5px solid #f59e0b; 
                            border-radius: 7px; 
                            padding: 6px 10px;
                        }
                    """)
                    cb.setStyleSheet("font-weight: 700; color: #92400e;")
                    cb.setChecked(True)
                    cb.setEnabled(True)
                    cb.setToolTip("Asignatura pendiente obligatoria de nivelación. Debes matricularla para desbloquear materias del semestre actual.")
                    badge = QLabel(f"⚠️ Rezagada • Sem {subj.semester_id} • {subj.credits} cr")
                    badge.setStyleSheet("font-size: 11px; font-weight: 800; color: #b45309; background-color: #fef3c7; padding: 2px 8px; border-radius: 4px; border: 1px solid #fde68a;")
                else:
                    # Current semester subject
                    card_frame.setStyleSheet("""
                        QFrame {
                            background-color: #ffffff; 
                            border: 1px solid #e2e8f0; 
                            border-radius: 7px; 
                            padding: 6px 10px;
                        }
                        QFrame:hover {
                            border-color: #6366f1;
                            background-color: #f5f3ff;
                        }
                    """)
                    cb.setStyleSheet("font-weight: 700; color: #1e3a8a;")
                    cb.setChecked(is_regular)
                    cb.setEnabled(True)
                    badge = QLabel(f"{subj.credits} cr • {subj.hours_per_week}h • Sem {subj.semester_id}")
                    badge.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; background-color: #f1f5f9; padding: 2px 8px; border-radius: 4px;")

                c_l.addWidget(cb)
                c_l.addWidget(badge)
                self.subj_checkboxes_layout.addWidget(card_frame)
                self.subject_checkboxes[subj.id] = cb
                self.subject_cards[subj.id] = (card_frame, cb, badge, subj)

            # Trigger leveling rules evaluation initially
            self.on_subject_state_changed()

            # Auto-load registered shift preference from student preferences
            pref = db.query(StudentPreference).filter_by(student_id=student_id, priority=1).first()
            if pref and pref.shift:
                self.current_registered_shift = pref.shift
                shift_names = {
                    ShiftType.MORNING: "☀️ Mañana (06:00 - 12:00)",
                    ShiftType.AFTERNOON: "⛅ Tarde (12:00 - 18:00)",
                    ShiftType.NIGHT: "🌙 Noche (18:00 - 22:00)"
                }
                shift_text = shift_names.get(pref.shift, pref.shift.value)
                self.registered_shift_lbl.setText(f"Jornada Registrada: <b>{shift_text}</b>")
            else:
                self.current_registered_shift = None
                self.registered_shift_lbl.setText("🌐 Jornada Registrada: <b>Sin preferencia / Cualquier jornada</b>")

            self.update_subject_count()
            self.load_official_schedule()
        finally:
            db.close()

    def run_student_optimization(self):
        db = SessionLocal()
        try:
            student_id = session.student_id or 1
            student = db.query(Student).filter_by(id=student_id).first()
            if student and not getattr(student, "is_enrolled", True):
                QMessageBox.warning(
                    self, "Matrícula Inactiva",
                    "Tu matrícula académica se encuentra marcada como INACTIVA.\n\n"
                    "Puedes simular y previsualizar opciones de horario con fines informativos, pero el sistema no te permitirá confirmar la inscripción de asignaturas hasta que Registro Académico active tu matrícula."
                )
            elif student and student.has_payment_agreement:
                config = db.query(Config).first()
                if config and not config.payment_agreement_allowed:
                    QMessageBox.warning(
                        self, "Bloqueo Financiero",
                        "Tu estado de cuenta presenta un acuerdo de pago pendiente de legalización ante Tesorería.\n\n"
                        "Puedes simular y previsualizar opciones de horario, pero la confirmación formal de matrícula permanecerá bloqueada hasta legalizar tu paz y salvo formal."
                    )

            selected_ids = [s_id for s_id, cb in self.subject_checkboxes.items() if cb.isChecked()]
            if not selected_ids:
                QMessageBox.warning(self, "Atención", "Debes seleccionar al menos una asignatura para optimizar tu horario.")
                return

            # Credit limit guard
            subjects_map = getattr(self, "subjects_map", {})
            total_credits = sum(subjects_map.get(sid).credits if subjects_map.get(sid) and hasattr(subjects_map.get(sid), "credits") and subjects_map.get(sid).credits else 3 for sid in selected_ids)
            if total_credits > 22:
                QMessageBox.warning(
                    self, "Límite de Créditos Excedido",
                    f"Has seleccionado {total_credits} créditos en {len(selected_ids)} asignaturas.\n\n"
                    f"El reglamento institucional de la UMB establece un tope máximo de 22 créditos por periodo académico.\n\n"
                    f"Por favor desmarca algunas materias para continuar con la optimización."
                )
                return

            preferred_shift = getattr(self, "current_registered_shift", None)

            w_shift = self.shift_weight_slider.value() / 100.0
            w_gap = self.gap_weight_slider.value() / 100.0
            w_free = self.free_weight_slider.value() / 100.0

            optimizer = StudentScheduleOptimizer(db, student_id)
            result = optimizer.optimize_student_schedule(
                selected_subject_ids=selected_ids,
                preferred_shift=preferred_shift,
                shift_weight=w_shift,
                gap_weight=w_gap,
                free_day_weight=w_free
            )

            if result["status"] != "SUCCESS":
                QMessageBox.warning(self, "Aviso de Optimización", result["msg"])
                return

            self.optimizer_options = result["options"]
            self.render_alternative_cards()
            if self.optimizer_options:
                self.preview_option(0)
        finally:
            db.close()

    def render_alternative_cards(self):
        while self.options_cards_layout.count() > 0:
            item = self.options_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for idx, opt in enumerate(self.optimizer_options):
            card = QFrame()
            is_best = (idx == 0)
            border_color = "#10b981" if is_best else "#cbd5e1"
            bg_color = "#ecfdf5" if is_best else "#ffffff"

            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 10px;
                    padding: 12px;
                }}
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setSpacing(6)

            badge = "⭐ RECOMENDADA" if is_best else f"ALTERNATIVA #{idx + 1}"
            b_lbl = QLabel(badge)
            b_lbl.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {'#047857' if is_best else '#475569'};")
            c_layout.addWidget(b_lbl)

            score_lbl = QLabel(f"<b>Puntaje de Calidad: {opt['global_score']}%</b>")
            score_lbl.setStyleSheet("font-size: 14px; color: #1e3a8a;")
            c_layout.addWidget(score_lbl)

            gap_hrs = opt.get("gap_hours", opt["total_gaps"] * 2)
            details_lbl = QLabel(
                f"• Jornada: {opt['shift_score']}%\n"
                f"• Minimización Huecos: {opt['compactness_score']}% ({gap_hrs} horas de hueco / {opt['total_gaps']} bloques)\n"
                f"• Días Libres: {opt['free_days']} ({opt['free_day_score']}%)\n"
                f"• Materias: {opt['subjects_included']}/{opt['total_requested']}"
            )
            details_lbl.setStyleSheet("font-size: 11px; color: #334155; line-height: 1.4;")
            c_layout.addWidget(details_lbl)

            btn_row = QHBoxLayout()
            btn_row.setSpacing(6)

            btn_view = QPushButton("🔍 Visualizar Horario Completo")
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.setStyleSheet("""
                QPushButton {
                    background-color: #0284c7;
                    color: white;
                    padding: 7px 12px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #0369a1;
                }
            """)
            btn_view.clicked.connect(lambda _, i=idx: self.select_and_open_option(i))
            btn_row.addWidget(btn_view)

            c_layout.addLayout(btn_row)
            self.options_cards_layout.addWidget(card)

    def select_and_open_option(self, option_index):
        self.preview_option(option_index)
        self.open_modal_for_option(option_index)

    def preview_option(self, option_index):
        if option_index >= len(self.optimizer_options):
            return

        self.current_preview_option = self.optimizer_options[option_index]
        self.open_modal_btn.setEnabled(True)
        self.save_schedule_btn.setEnabled(True)
        
        if not self.is_enrollment_allowed:
            reason_txt = getattr(self, "enrollment_block_reason", "RESTRICCIÓN INSTITUCIONAL").upper()
            if "INACTIVA" in reason_txt:
                label_btn = "🚫 MATRÍCULA INACTIVA (NO PUEDES INSCRIBIR)"
            elif "TESORERÍA" in reason_txt or "FINANCIERO" in reason_txt:
                label_btn = "🚫 BLOQUEO FINANCIERO (ACUERDO PENDIENTE)"
            else:
                label_btn = "🚫 INSCRIPCIÓN CERRADA (FUERA DE FECHA)"
            self.save_schedule_btn.setText(label_btn)
            self.save_schedule_btn.setStyleSheet("background-color: #fca5a5; color: #7f1d1d; font-weight: 800; padding: 12px 20px; border-radius: 8px; font-size: 13px; border: 1.5px solid #ef4444;")
        else:
            self.save_schedule_btn.setText(f"✅ CONFIRMAR E INSCRIBIR ALTERNATIVA #{option_index + 1} (Calidad: {self.current_preview_option['global_score']}%)")
            self.save_schedule_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: 800; padding: 12px 20px; border-radius: 8px; font-size: 13px;")

        db = SessionLocal()
        try:
            slots = db.query(TimeSlot).all()
            SHIFT_ORDER = {
                ShiftType.MORNING: 0,
                ShiftType.AFTERNOON: 1,
                ShiftType.NIGHT: 2,
                "MAÑANA": 0,
                "TARDE": 1,
                "NOCHE": 2
            }
            sorted_slots = sorted(slots, key=lambda s: (SHIFT_ORDER.get(s.shift, 99), s.start_time))
            slot_map = {
                s.id: f"{s.shift.value}\n{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}" 
                for s in sorted_slots
            }
            sorted_slot_ids = [s.id for s in sorted_slots]

            self.preview_table.setRowCount(len(sorted_slot_ids))
            self.preview_table.setVerticalHeaderLabels([slot_map[sid] for sid in sorted_slot_ids])

            for r in range(self.preview_table.rowCount()):
                for c in range(self.preview_table.columnCount()):
                    self.preview_table.setItem(r, c, QTableWidgetItem(""))

            day_indices = {d: i for i, d in enumerate(self.days)}
            slot_indices = {sid: i for i, sid in enumerate(sorted_slot_ids)}

            shift_bgs = {
                ShiftType.MORNING: "#f0f9ff",
                ShiftType.AFTERNOON: "#f0fdf4",
                ShiftType.NIGHT: "#faf5ff"
            }

            for _, _, g_info in self.current_preview_option["groups"]:
                for s in g_info["slots"]:
                    if s["time_slot_id"] in slot_indices and s["day"] in day_indices:
                        r_idx = slot_indices[s["time_slot_id"]]
                        c_idx = day_indices[s["day"]]

                        slot_obj = next((sl for sl in sorted_slots if sl.id == s["time_slot_id"]), None)
                        bg_c = shift_bgs.get(slot_obj.shift, "#ffffff") if slot_obj else "#ffffff"

                        text = f"📘 {g_info['subject_name']}\n👥 {g_info['group_name']}\n👨‍🏫 {g_info['teacher_name']}\n📍 {g_info['room_name']}"
                        item = QTableWidgetItem(text)
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setBackground(QColor(bg_c))
                        item.setForeground(QColor("#1e3a8a"))
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                        self.preview_table.setItem(r_idx, c_idx, item)

            self.preview_table.resizeRowsToContents()
            for r in range(self.preview_table.rowCount()):
                h = self.preview_table.rowHeight(r)
                if h < 65:
                    self.preview_table.setRowHeight(r, 65)
                elif h > 88:
                    self.preview_table.setRowHeight(r, 85)
        finally:
            db.close()

    def open_current_modal(self):
        if not self.current_preview_option:
            return
        idx = self.optimizer_options.index(self.current_preview_option) if self.current_preview_option in self.optimizer_options else 0
        self.open_modal_for_option(idx)

    def open_modal_for_option(self, option_index):
        if option_index >= len(self.optimizer_options):
            return
        opt = self.optimizer_options[option_index]
        title = f"Alternativa #{option_index + 1} (Calidad: {opt['global_score']}%)"
        dialog = SchedulePreviewDialog(
            title_text=title,
            groups_data=opt["groups"],
            metrics=opt,
            parent=self,
            on_confirm_callback=self.confirm_enrollment
        )
        dialog.exec()

    def confirm_enrollment(self):
        if not self.current_preview_option:
            return

        db = SessionLocal()
        try:
            student_id = session.student_id or 1
            student = db.query(Student).filter_by(id=student_id).first()
            config = db.query(Config).first()

            # Validación 1: Matrícula Activa en Sistema
            if student and not getattr(student, "is_enrolled", True):
                QMessageBox.warning(
                    self, "Matrícula Inactiva",
                    "Tu registro como estudiante se encuentra marcado como INACTIVO para este período académico.\n\n"
                    "Por favor acércate a la Oficina de Registro y Control Académico de la Universidad Manuela Beltrán para activar tu estado y habilitar la matrícula de asignaturas."
                )
                return

            # Validación 2: Estado Financiero Estudiantil
            if config and not config.payment_agreement_allowed and student and student.has_payment_agreement:
                QMessageBox.warning(
                    self, "Trámite Financiero Requerido",
                    "Tu estado de cuenta presenta un acuerdo de pago pendiente de legalización ante la Universidad Manuela Beltrán.\n\n"
                    "Por favor tramita tu paz y salvo formal ante la Oficina de Tesorería y Cartera para habilitar la inscripción de asignaturas.\n\n"
                    "Este trámite no puede ser omitido o autorizado de manera autónoma por el estudiante."
                )
                return

            # Validación 3: Ventana de Matrícula y Bloqueos
            if not self.is_enrollment_allowed:
                reason = getattr(self, "enrollment_block_reason", "") or "El período de inscripción para tu cohorte ha finalizado."
                QMessageBox.warning(
                    self, "Inscripción No Habilitada",
                    f"{reason}\n\n"
                    "Cualquier solicitud de excepción debe ser radicada y aprobada formalmente ante la Coordinación de Programa de la Universidad."
                )
                return

            group_ids = [g_id for _, g_id, _ in self.current_preview_option["groups"]]

            optimizer = StudentScheduleOptimizer(db, student_id)
            optimizer.save_selected_schedule(group_ids)

            QMessageBox.information(
                self, "Inscripción Exitosa", 
                "¡Tu horario personalizado ha sido confirmado e inscrito exitosamente en el sistema institucional!"
            )
            self.load_official_schedule()
            self.tabs.setCurrentIndex(1)
        finally:
            db.close()

    def load_official_schedule(self):
        db = SessionLocal()
        try:
            student_id = session.student_id or 1
            enrollments = db.query(StudentEnrollment).filter_by(student_id=student_id).all()

            slots = db.query(TimeSlot).all()
            SHIFT_ORDER = {
                ShiftType.MORNING: 0,
                ShiftType.AFTERNOON: 1,
                ShiftType.NIGHT: 2,
                "MAÑANA": 0,
                "TARDE": 1,
                "NOCHE": 2
            }
            sorted_slots = sorted(slots, key=lambda s: (SHIFT_ORDER.get(s.shift, 99), s.start_time))
            slot_map = {
                s.id: f"{s.shift.value}\n{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}" 
                for s in sorted_slots
            }
            sorted_slot_ids = [s.id for s in sorted_slots]

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
                student = db.query(Student).filter_by(id=student_id).first()
                sem_id = student.semester_id if student else 1
                pref = db.query(StudentPreference).filter_by(student_id=student_id).order_by(StudentPreference.priority.asc()).first()
                pref_shift = pref.shift if pref else ShiftType.MORNING
                shift_kw = "Mañana" if pref_shift == ShiftType.MORNING else ("Tarde" if pref_shift == ShiftType.AFTERNOON else "Noche")

                semester_subjs = db.query(Subject).filter_by(semester_id=sem_id).all()
                subj_ids = {s.id for s in semester_subjs}

                # Single group per subject matching preference to avoid stacking multi-shift groups
                matching_groups = db.query(Group).filter(Group.subject_id.in_(subj_ids), Group.name.like(f"%{shift_kw}%")).all()
                if not matching_groups:
                    matching_groups = db.query(Group).filter(Group.subject_id.in_(subj_ids)).all()

                seen_subj = set()
                single_group_ids = set()
                for g in matching_groups:
                    if g.subject_id not in seen_subj:
                        seen_subj.add(g.subject_id)
                        single_group_ids.add(g.id)

                assignments = db.query(ScheduleAssignment).filter(ScheduleAssignment.group_id.in_(single_group_ids)).all()

            for asg in assignments:
                if asg.time_slot_id in slot_indices and asg.day.value in day_indices:
                    r_idx = slot_indices[asg.time_slot_id]
                    c_idx = day_indices[asg.day.value]

                    text = f"📘 {asg.group.subject.name}\n👥 Grupo: {asg.group.name}\n👨‍🏫 {asg.teacher.name}\n📍 {asg.room.name}"
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setBackground(QColor("#eff6ff"))
                    item.setForeground(QColor("#1e3a8a"))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    self.official_table.setItem(r_idx, c_idx, item)

            self.official_table.resizeRowsToContents()
            for r in range(self.official_table.rowCount()):
                h = self.official_table.rowHeight(r)
                if h < 65:
                    self.official_table.setRowHeight(r, 65)
                elif h > 88:
                    self.official_table.setRowHeight(r, 85)
        finally:
            db.close()

    def export_my_schedule(self):
        db = SessionLocal()
        try:
            student_id = session.student_id or 1
            student = db.query(Student).filter_by(id=student_id).first()
            student_name = student.name if student else "Estudiante"
            enrollments = db.query(StudentEnrollment).filter_by(student_id=student_id).all()
            enrolled_group_ids = {e.group_id for e in enrollments}
            raw_asg = db.query(ScheduleAssignment).filter(ScheduleAssignment.group_id.in_(enrolled_group_ids)).all()

            assignments = []
            for asg in raw_asg:
                slot = asg.time_slot
                group = asg.group
                subj = group.subject if group else None
                teacher = asg.teacher
                room = asg.room
                day_val = asg.day.value if hasattr(asg.day, "value") else str(asg.day)
                assignments.append({
                    "id": asg.id,
                    "day": day_val,
                    "shift": slot.shift.value if slot and hasattr(slot.shift, "value") else (str(slot.shift) if slot else ""),
                    "start_time": slot.start_time.strftime('%H:%M') if slot and slot.start_time else "",
                    "end_time": slot.end_time.strftime('%H:%M') if slot and slot.end_time else "",
                    "subject_name": subj.name if subj else "",
                    "semester": f"Semestre {subj.semester_id}" if subj else "",
                    "group_name": group.name if group else "",
                    "teacher_name": teacher.name if teacher else "",
                    "teacher_type": teacher.teacher_type.value if teacher and hasattr(teacher.teacher_type, "value") else "",
                    "room_name": room.name if room else "",
                    "room_type": room.room_type if room else ""
                })

            clean_name = student_name.replace(" ", "_")
            export_schedule_dialog(
                self,
                f"Mi_Horario_{clean_name}.xlsx",
                self.official_table,
                assignments,
                title=f"Horario Oficial Estudiante - {student_name}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {e}")
        finally:
            db.close()

