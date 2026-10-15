import sys
from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import (
    QApplication, QSpinBox, QDoubleSpinBox, QComboBox, 
    QSlider, QDateEdit, QTimeEdit, QDateTimeEdit
)
from app.ui.main_window import MainWindow
from app.ui.styles import GLOBAL_STYLE
from app.database.database import init_db
import app.database.models  # Required for SQLAlchemy to know the tables before init_db
from scripts.generate_data import create_data

class GlobalWheelFilter(QObject):
    """
    Global event filter to prevent mouse wheel events from inadvertently
    changing values in spinboxes, comboboxes, sliders, and date/time edits
    when scrolling through pages. Forwards wheel events to parent scroll areas.
    """
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            if isinstance(obj, (QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit, QTimeEdit, QDateTimeEdit)):
                # If combobox dropdown popup is open, allow wheel navigation inside popup
                if isinstance(obj, QComboBox) and obj.view() and obj.view().isVisible():
                    return False

                event.ignore()
                parent = obj.parent()
                if parent:
                    QApplication.sendEvent(parent, event)
                return True
        return super().eventFilter(obj, event)

def main():
    init_db()
    try:
        create_data()
    except Exception as e:
        print("Error generating data:", e)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(GLOBAL_STYLE)

    # Install mouse wheel filter globally across the entire app
    wheel_filter = GlobalWheelFilter(app)
    app.installEventFilter(wheel_filter)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

