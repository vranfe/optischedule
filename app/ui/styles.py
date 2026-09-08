GLOBAL_STYLE = """
/* ========================================================================= */
/* OptiSchedule UMB - Modern Pastel Design System (React/Lovable SaaS Style)  */
/* ========================================================================= */

QWidget {
    font-family: 'Plus Jakarta Sans', 'Inter', 'Segoe UI Variable Display', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
    color: #0f172a;
}

/* Backgrounds & Base Containers */
QMainWindow, QDialog {
    background-color: #f8fafc;
}

QFrame {
    color: #0f172a;
}

/* Modern Rounded Cards */
QFrame#card, QFrame#content_card, QFrame.card-frame {
    background-color: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
}

QFrame#card:hover, QFrame.card-frame:hover {
    border-color: #cbd5e1;
}

/* Typography */
QLabel {
    color: #0f172a;
}

QLabel#title, .title-lg {
    font-size: 22px;
    font-weight: 800;
    color: #1e3a8a;
    letter-spacing: -0.4px;
}

QLabel#subtitle, .text-muted {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
}

/* Inputs, Spinners, and Date Pickers (Clean & Soft) */
QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    padding: 9px 14px;
    font-size: 13px;
    font-weight: 500;
    selection-background-color: #e0e7ff;
    selection-color: #3730a3;
}

QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QDateEdit:hover, QTimeEdit:hover {
    border-color: #cbd5e1;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {
    border: 2px solid #6366f1;
    background-color: #ffffff;
}

QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QDateEdit:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border: 1px solid #e2e8f0;
}

/* ComboBox */
QComboBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 600;
    min-height: 22px;
}

QComboBox:hover {
    border-color: #cbd5e1;
}

QComboBox:focus {
    border: 2px solid #6366f1;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #f1f5f9;
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    selection-background-color: #eef2ff;
    selection-color: #4338ca;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    padding: 6px;
    outline: none;
}

/* Modern Rounded Buttons (Soft, Elevated, Fresh) */
QPushButton {
    background-color: #4f46e5;
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    border-radius: 10px;
    padding: 10px 18px;
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
    border: 1.5px solid #e2e8f0;
}
QPushButton#btn_secondary:hover, QPushButton.btn-secondary:hover {
    background-color: #f8fafc;
    border-color: #cbd5e1;
    color: #0f172a;
}

QPushButton#btn_info, QPushButton.btn-info {
    background-color: #0284c7;
    color: #ffffff;
}
QPushButton#btn_info:hover, QPushButton.btn-info:hover {
    background-color: #0369a1;
}

/* Tables with Soft Grid & Rounded Aesthetic */
QTableWidget {
    background-color: #ffffff;
    color: #0f172a;
    gridline-color: #f1f5f9;
    border: 1.5px solid #e2e8f0;
    border-radius: 12px;
    selection-background-color: #eef2ff;
    selection-color: #3730a3;
    font-size: 12px;
}

QTableWidget::item {
    padding: 10px 12px;
    color: #0f172a;
    border-bottom: 1px solid #f8fafc;
}

QTableWidget::item:selected {
    background-color: #eef2ff;
    color: #3730a3;
    font-weight: 600;
}

QHeaderView::section {
    background-color: #0f172a;
    color: #ffffff;
    padding: 11px 12px;
    font-weight: 700;
    font-size: 12px;
    border: none;
    border-right: 1px solid #1e293b;
}

/* Tabs */
QTabWidget::pane {
    border: 1.5px solid #e2e8f0;
    background-color: #ffffff;
    border-radius: 14px;
    top: -1px;
    padding: 16px;
}

QTabBar::tab {
    background-color: #f1f5f9;
    color: #64748b;
    padding: 10px 22px;
    font-weight: 700;
    font-size: 13px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 6px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #4f46e5;
    border: 1.5px solid #e2e8f0;
    border-bottom: 3px solid #4f46e5;
}

/* GroupBox Card Styling (Clean, Modern, No Ugly Windows Frames) */
QGroupBox {
    font-weight: 800;
    font-size: 13px;
    color: #1e3a8a;
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
    margin-top: 14px;
    padding: 18px 16px 16px 16px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 10px;
    background-color: #ffffff;
    border-radius: 6px;
}

/* CheckBox */
QCheckBox {
    color: #1e293b;
    font-size: 13px;
    font-weight: 600;
    spacing: 10px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #cbd5e1;
    border-radius: 6px;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #6366f1;
    background-color: #eef2ff;
}

QCheckBox::indicator:checked {
    border-color: #4f46e5;
    background-color: #4f46e5;
}

/* RadioButton */
QRadioButton {
    color: #1e293b;
    font-size: 13px;
    font-weight: 600;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #cbd5e1;
    border-radius: 10px;
    background-color: #ffffff;
}

QRadioButton::indicator:hover {
    border-color: #6366f1;
    background-color: #eef2ff;
}

QRadioButton::indicator:checked {
    border-color: #4f46e5;
    background-color: #4f46e5;
}

/* Sliders */
QSlider::groove:horizontal {
    border: none;
    height: 7px;
    background: #e2e8f0;
    border-radius: 4px;
}

QSlider::sub-page:horizontal {
    background: #6366f1;
    border-radius: 4px;
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
    border-radius: 10px;
    text-align: center;
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 700;
    height: 24px;
}

QProgressBar::chunk {
    background-color: #10b981;
    border-radius: 9px;
}

/* ScrollBar */
QScrollBar:vertical {
    border: none;
    background: #f8fafc;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 26px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
