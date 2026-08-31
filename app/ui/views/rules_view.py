from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
    QDoubleSpinBox, QCheckBox, QPushButton, QMessageBox, QGroupBox, QFormLayout
)
from app.database.database import get_db
from app.database.models import Config

class RulesView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        title_layout = QVBoxLayout()
        title = QLabel("Reglas Institucionales y Restricciones")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e3a8a;")
        subtitle = QLabel("Configuración de parámetros matemáticos, límites de contratación y pesos de optimización")
        subtitle.setStyleSheet("font-size: 13px; color: #6b7280;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)

        save_btn = QPushButton("💾 Guardar Configuración")
        save_btn.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold; padding: 10px 20px; border-radius: 6px;")
        save_btn.clicked.connect(self.save_config)
        header.addWidget(save_btn)

        main_layout.addLayout(header)

        # Group 1: Hard Constraints (Contractual Limits)
        hard_group = QGroupBox("Restricciones Duras (Límites Contractuales y Operativos)")
        hard_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; color: #1e3a8a; }")
        hard_layout = QFormLayout(hard_group)

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

        self.sat_check = QCheckBox("Habilitar Sábados para clases")
        hard_layout.addRow("Operación Fin de Semana:", self.sat_check)

        main_layout.addWidget(hard_group)

        # Group 2: Soft Constraints (Objective Function Weights)
        soft_group = QGroupBox("Restricciones Blandas (Ponderaciones de Calidad de Horario)")
        soft_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; color: #1e3a8a; }")
        soft_layout = QFormLayout(soft_group)

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

        main_layout.addWidget(soft_group)

        self.load_config()

    def load_config(self):
        db = next(get_db())
        config = db.query(Config).first()
        if not config:
            return

        self.ft_spin.setValue(config.full_time_hours)
        self.pt_spin.setValue(config.part_time_hours)
        self.cat_spin.setValue(config.catedra_hours)
        self.consec_spin.setValue(config.max_consecutive_hours if hasattr(config, "max_consecutive_hours") else 4)
        self.sat_check.setChecked(config.allow_saturday if hasattr(config, "allow_saturday") else True)

        self.pref_weight.setValue(config.pref_weight)
        self.gap_weight.setValue(config.gap_weight)
        self.load_weight.setValue(config.load_weight)
        self.room_weight.setValue(config.room_weight)

    def save_config(self):
        db = next(get_db())
        config = db.query(Config).first()
        if not config:
            config = Config()
            db.add(config)

        config.full_time_hours = self.ft_spin.value()
        config.part_time_hours = self.pt_spin.value()
        config.catedra_hours = self.cat_spin.value()
        config.max_consecutive_hours = self.consec_spin.value()
        config.allow_saturday = self.sat_check.isChecked()

        config.pref_weight = self.pref_weight.value()
        config.gap_weight = self.gap_weight.value()
        config.load_weight = self.load_weight.value()
        config.room_weight = self.room_weight.value()

        db.commit()
        QMessageBox.information(self, "Configuración Guardada", "Las reglas y restricciones se han actualizado exitosamente.")
