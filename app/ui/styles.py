GLOBAL_STYLE = """
/* ========================================================================= */
/* OptiSchedule UMB - Modern Pastel SaaS Design System (Lovable Style)       */
/* ========================================================================= */

QWidget {
    font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    color: #0f172a;
}

/* Backgrounds & Window Panels */
QMainWindow, QDialog {
    background-color: #f8fafc;
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
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {
    border: 2px solid #6366f1;
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
    border: 2px solid #6366f1;
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
    selection-color: #3730a3;
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
    padding: 10px;
    font-weight: 700;
    font-size: 12px;
    border: none;
    border-right: 1px solid #334155;
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
    padding: 16px 14px 14px 14px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 8px;
    background-color: #ffffff;
    border-radius: 4px;
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
    min-height: 24px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
