GLOBAL_STYLE = """
/* ========================================================================= */
/* OptiSchedule UMB - Modern Pastel SaaS Design System (High Contrast)       */
/* ========================================================================= */

QWidget {
    font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    color: #0f172a;
}

/* Backgrounds & Window Panels */
QMainWindow, QDialog, QMessageBox {
    background-color: #f8fafc;
    color: #0f172a;
}

QFrame {
    color: #0f172a;
}

QFrame#card, QFrame#content_card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}

/* Typography & Titles */
QLabel {
    color: #0f172a;
    font-size: 13px;
}

QLabel#title {
    font-size: 22px;
    font-weight: 800;
    color: #1e3a8a;
    letter-spacing: -0.4px;
}

QLabel#subtitle {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
}

/* Form Inputs, Date Edits, Spinners */
QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #4f46e5;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {
    border: 2px solid #4f46e5;
    background-color: #ffffff;
}

QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QDateEdit:disabled, QTimeEdit:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border: 1px solid #e2e8f0;
}

/* Modern ComboBox */
QComboBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 600;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #94a3b8;
}

QComboBox:focus {
    border: 2px solid #4f46e5;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #e2e8f0;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    selection-background-color: #e0e7ff;
    selection-color: #312e81;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 6px;
    outline: none;
}

/* Modern Rounded Buttons */
QPushButton {
    background-color: #4f46e5;
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    border-radius: 8px;
    padding: 9px 18px;
    border: none;
}

QPushButton:hover {
    background-color: #4338ca;
}

QPushButton:pressed {
    background-color: #3730a3;
}

QPushButton:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
}

/* QMessageBox, QDialog & QInputDialog Styling - Crisp White Background, Strong Border & High Contrast */
QDialog, QMessageBox, QInputDialog {
    background-color: #ffffff;
    border: 2px solid #cbd5e1;
    border-radius: 12px;
}

QMessageBox QLabel, QInputDialog QLabel, QDialog QLabel {
    color: #0f172a;
    font-size: 13px;
    font-weight: 600;
}

QMessageBox QLabel {
    min-height: 40px;
    padding: 8px;
}

/* Primary Confirmation & Action Buttons in Dialogs */
QMessageBox QPushButton, QDialogButtonBox QPushButton, QDialog QPushButton, QInputDialog QPushButton {
    background-color: #10b981;
    color: #ffffff;
    font-size: 13px;
    font-weight: 800;
    border-radius: 8px;
    padding: 9px 24px;
    min-width: 95px;
    min-height: 28px;
    border: 1.5px solid #059669;
}

QMessageBox QPushButton:hover, QDialogButtonBox QPushButton:hover, QDialog QPushButton:hover, QInputDialog QPushButton:hover {
    background-color: #059669;
    border-color: #047857;
}

QMessageBox QPushButton:pressed, QDialogButtonBox QPushButton:pressed, QDialog QPushButton:pressed, QInputDialog QPushButton:pressed {
    background-color: #047857;
}

/* Explicit Action: OK / Sí / Yes / Aceptar / Guardar / Confirmar / Inscribir */
QMessageBox QPushButton[text="&Sí"], QMessageBox QPushButton[text="Sí"],
QMessageBox QPushButton[text="&Yes"], QMessageBox QPushButton[text="Yes"],
QMessageBox QPushButton[text="&OK"], QMessageBox QPushButton[text="OK"],
QMessageBox QPushButton[text="&Aceptar"], QMessageBox QPushButton[text="Aceptar"],
QMessageBox QPushButton[text="&Confirmar"], QMessageBox QPushButton[text="Confirmar"],
QMessageBox QPushButton[text="&Inscribir"], QMessageBox QPushButton[text="Inscribir"],
QDialogButtonBox QPushButton[text="&OK"], QDialogButtonBox QPushButton[text="OK"],
QDialogButtonBox QPushButton[text="&Save"], QDialogButtonBox QPushButton[text="Save"],
QDialogButtonBox QPushButton[text="Guardar"], QDialogButtonBox QPushButton[text="&Guardar"],
QDialogButtonBox QPushButton[text="&Aceptar"], QDialogButtonBox QPushButton[text="Aceptar"],
QDialogButtonBox QPushButton[text="&Confirmar"], QDialogButtonBox QPushButton[text="Confirmar"] {
    background-color: #10b981;
    color: #ffffff;
    border: 2px solid #059669;
}

QMessageBox QPushButton[text="&Sí"]:hover, QMessageBox QPushButton[text="Sí"]:hover,
QMessageBox QPushButton[text="&Yes"]:hover, QMessageBox QPushButton[text="Yes"]:hover,
QMessageBox QPushButton[text="&OK"]:hover, QMessageBox QPushButton[text="OK"]:hover,
QMessageBox QPushButton[text="&Aceptar"]:hover, QMessageBox QPushButton[text="Aceptar"]:hover,
QDialogButtonBox QPushButton[text="&OK"]:hover, QDialogButtonBox QPushButton[text="OK"]:hover,
QDialogButtonBox QPushButton[text="&Save"]:hover, QDialogButtonBox QPushButton[text="Save"]:hover,
QDialogButtonBox QPushButton[text="Guardar"]:hover, QDialogButtonBox QPushButton[text="&Guardar"]:hover {
    background-color: #059669;
    border-color: #047857;
}

/* Secondary / Dismiss / No / Cancelar Buttons in Dialogs */
QMessageBox QPushButton[text="No"], QMessageBox QPushButton[text="&No"],
QMessageBox QPushButton[text="Cancelar"], QMessageBox QPushButton[text="&Cancelar"],
QMessageBox QPushButton[text="Cancel"], QMessageBox QPushButton[text="&Cancel"],
QMessageBox QPushButton[text="Cerrar"], QMessageBox QPushButton[text="&Cerrar"],
QDialogButtonBox QPushButton[text="No"], QDialogButtonBox QPushButton[text="&No"],
QDialogButtonBox QPushButton[text="Cancelar"], QDialogButtonBox QPushButton[text="&Cancelar"],
QDialogButtonBox QPushButton[text="Cancel"], QDialogButtonBox QPushButton[text="&Cancel"],
QDialogButtonBox QPushButton[text="Close"], QDialogButtonBox QPushButton[text="&Close"] {
    background-color: #e2e8f0;
    color: #0f172a;
    font-weight: 800;
    border: 2px solid #94a3b8;
}

QMessageBox QPushButton[text="No"]:hover, QMessageBox QPushButton[text="&No"]:hover,
QMessageBox QPushButton[text="Cancelar"]:hover, QMessageBox QPushButton[text="&Cancelar"]:hover,
QMessageBox QPushButton[text="Cancel"]:hover, QMessageBox QPushButton[text="&Cancel"]:hover,
QMessageBox QPushButton[text="Cerrar"]:hover, QMessageBox QPushButton[text="&Cerrar"]:hover,
QDialogButtonBox QPushButton[text="No"]:hover, QDialogButtonBox QPushButton[text="&No"]:hover,
QDialogButtonBox QPushButton[text="Cancelar"]:hover, QDialogButtonBox QPushButton[text="&Cancelar"]:hover,
QDialogButtonBox QPushButton[text="Cancel"]:hover, QDialogButtonBox QPushButton[text="&Cancel"]:hover {
    background-color: #cbd5e1;
    color: #000000;
    border-color: #64748b;
}

/* Danger / Delete Action Buttons in Dialogs */
QMessageBox QPushButton[text="Eliminar"], QMessageBox QPushButton[text="&Eliminar"],
QMessageBox QPushButton[text="Borrar"], QMessageBox QPushButton[text="&Borrar"],
QDialogButtonBox QPushButton[text="Eliminar"], QDialogButtonBox QPushButton[text="&Eliminar"] {
    background-color: #dc2626;
    color: #ffffff;
    font-weight: 800;
    border: 2px solid #b91c1c;
}

QMessageBox QPushButton[text="Eliminar"]:hover, QMessageBox QPushButton[text="&Eliminar"]:hover,
QDialogButtonBox QPushButton[text="Eliminar"]:hover, QDialogButtonBox QPushButton[text="&Eliminar"]:hover {
    background-color: #b91c1c;
    border-color: #991b1b;
}

/* Button Variants */
QPushButton#btn_success, QPushButton.btn-success {
    background-color: #10b981;
    color: #ffffff;
}
QPushButton#btn_success:hover, QPushButton.btn-success:hover {
    background-color: #059669;
}

QPushButton#btn_danger, QPushButton.btn-danger {
    background-color: #f43f5e;
    color: #ffffff;
}
QPushButton#btn_danger:hover, QPushButton.btn-danger:hover {
    background-color: #e11d48;
}

QPushButton#btn_secondary, QPushButton.btn-secondary {
    background-color: #ffffff;
    color: #334155;
    border: 1.5px solid #cbd5e1;
}
QPushButton#btn_secondary:hover, QPushButton.btn-secondary:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
    color: #0f172a;
}

QPushButton#btn_info, QPushButton.btn-info {
    background-color: #0284c7;
    color: #ffffff;
}
QPushButton#btn_info:hover, QPushButton.btn-info:hover {
    background-color: #0369a1;
}

/* Sleek Tables */
QTableWidget {
    background-color: #ffffff;
    color: #0f172a;
    gridline-color: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    selection-background-color: #e0e7ff;
    selection-color: #312e81;
    font-size: 12px;
}

QTableWidget::item {
    padding: 8px 10px;
    color: #0f172a;
}

QTableWidget::item:selected {
    background-color: #e0e7ff;
    color: #312e81;
    font-weight: 600;
}

QHeaderView::section {
    background-color: #1e293b;
    color: #ffffff;
    padding: 10px 12px;
    font-weight: 800;
    font-size: 12px;
    border: none;
    border-right: 1.5px solid #334155;
    border-bottom: 2px solid #4f46e5;
}

/* Modern Tabs */
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    background-color: #ffffff;
    border-radius: 12px;
    top: -1px;
    padding: 14px;
}

QTabBar::tab {
    background-color: #f1f5f9;
    color: #475569;
    padding: 9px 20px;
    font-weight: 700;
    font-size: 13px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #4f46e5;
    border: 1px solid #e2e8f0;
    border-bottom: 3px solid #4f46e5;
}

/* GroupBox Card Styling */
QGroupBox {
    font-weight: 800;
    font-size: 13px;
    color: #1e3a8a;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    margin-top: 14px;
    padding: 18px 14px 14px 14px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 8px;
    background-color: #ffffff;
    border-radius: 4px;
    color: #1e3a8a;
}

/* CheckBox */
QCheckBox {
    color: #0f172a;
    font-size: 13px;
    font-weight: 600;
    spacing: 10px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #94a3b8;
    border-radius: 6px;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #4f46e5;
    background-color: #eef2ff;
}

QCheckBox::indicator:checked {
    border-color: #4f46e5;
    background-color: #4f46e5;
}

/* RadioButton */
QRadioButton {
    color: #0f172a;
    font-size: 13px;
    font-weight: 600;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #94a3b8;
    border-radius: 10px;
    background-color: #ffffff;
}

QRadioButton::indicator:hover {
    border-color: #4f46e5;
    background-color: #eef2ff;
}

QRadioButton::indicator:checked {
    border-color: #4f46e5;
    background-color: #4f46e5;
}

/* Modern Pill Sliders */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #e2e8f0;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #4f46e5;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 2.5px solid #4f46e5;
    width: 18px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #eef2ff;
    border-color: #4338ca;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    text-align: center;
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 700;
    height: 22px;
}

QProgressBar::chunk {
    background-color: #10b981;
    border-radius: 7px;
}

/* Fluid, Modern ScrollBars (Vertical and Horizontal) */
QScrollBar:vertical {
    border: none;
    background: #f1f5f9;
    width: 14px;
    margin: 0px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background: #94a3b8;
    min-height: 32px;
    border-radius: 7px;
    border: 2px solid #f1f5f9;
}

QScrollBar::handle:vertical:hover {
    background: #64748b;
}

QScrollBar::handle:vertical:pressed {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #f1f5f9;
    height: 14px;
    margin: 0px;
    border-radius: 7px;
}

QScrollBar::handle:horizontal {
    background: #94a3b8;
    min-width: 32px;
    border-radius: 7px;
    border: 2px solid #f1f5f9;
}

QScrollBar::handle:horizontal:hover {
    background: #64748b;
}

QScrollBar::handle:horizontal:pressed {
    background: #475569;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""
