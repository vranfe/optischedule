GLOBAL_STYLE = """
/* Global Application Style */
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: #0f172a;
}

/* Backgrounds & Panels */
QMainWindow, QDialog {
    background-color: #f1f5f9;
}

QFrame#card, QFrame#content_card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}

/* Labels */
QLabel {
    color: #0f172a;
}

QLabel#title {
    font-size: 20px;
    font-weight: 700;
    color: #1e3a8a;
}

QLabel#subtitle {
    font-size: 12px;
    color: #64748b;
}

/* LineEdits & SpinBoxes */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #2563eb;
    background-color: #ffffff;
}

QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #f8fafc;
    color: #94a3b8;
    border: 1px solid #e2e8f0;
}

/* ComboBox */
QComboBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
}

QComboBox:focus {
    border: 2px solid #2563eb;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid #cbd5e1;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px;
}

/* PushButtons */
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
    border-radius: 6px;
    padding: 8px 16px;
    border: none;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:pressed {
    background-color: #1e40af;
}

QPushButton:disabled {
    background-color: #94a3b8;
    color: #f1f5f9;
}

QPushButton#btn_success {
    background-color: #16a34a;
}
QPushButton#btn_success:hover {
    background-color: #15803d;
}

QPushButton#btn_danger {
    background-color: #dc2626;
}
QPushButton#btn_danger:hover {
    background-color: #b91c1c;
}

QPushButton#btn_secondary {
    background-color: #ffffff;
    color: #334155;
    border: 1.5px solid #cbd5e1;
}
QPushButton#btn_secondary:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
}

/* Tables */
QTableWidget {
    background-color: #ffffff;
    color: #0f172a;
    gridline-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    selection-background-color: #dbeafe;
    selection-color: #1e3a8a;
    font-size: 12px;
}

QTableWidget::item {
    padding: 6px;
    color: #0f172a;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #1e293b;
    padding: 8px;
    font-weight: 700;
    font-size: 12px;
    border: none;
    border-bottom: 2px solid #cbd5e1;
    border-right: 1px solid #e2e8f0;
}

/* TabWidget */
QTabWidget::pane {
    border: 1px solid #cbd5e1;
    background-color: #ffffff;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #e2e8f0;
    color: #475569;
    padding: 8px 18px;
    font-weight: 600;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 3px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1e3a8a;
    border: 1px solid #cbd5e1;
    border-bottom: 2px solid #2563eb;
}

/* GroupBox */
QGroupBox {
    font-weight: 700;
    color: #1e3a8a;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    margin-top: 14px;
    padding: 14px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #ffffff;
}

/* CheckBox & RadioButton */
QCheckBox, QRadioButton {
    color: #0f172a;
    font-size: 13px;
    spacing: 8px;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
}

/* ProgressBar */
QProgressBar {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    text-align: center;
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 700;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 5px;
}

/* ScrollBar */
QScrollBar:vertical {
    border: none;
    background: #f1f5f9;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
