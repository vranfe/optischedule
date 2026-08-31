import sys
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.ui.styles import GLOBAL_STYLE
from app.database.database import init_db
import app.database.models  # Required for SQLAlchemy to know the tables before init_db
from scripts.generate_data import create_data

def main():
    init_db()
    try:
        create_data()
    except Exception as e:
        print("Error generating data:", e)
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
