from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QTabWidget, QWidget, QFrame
)
from PySide6.QtCore import Qt, Signal
from app.database.database import SessionLocal
from app.database.models import User, UserRole, Teacher, Student

class CredentialsDialog(QDialog):
    """
    Sleek modal dialog for viewing and auto-selecting system demonstration accounts with industry-standard secure passwords.
    """
    account_selected = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OptiSchedule UMB - Directorio de Cuentas y Credenciales Seguras")
        self.resize(760, 540)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # Header Card
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e3a8a, stop:1 #2563eb);
                border-radius: 10px;
                padding: 12px 16px;
            }
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setSpacing(4)
        
        t = QLabel("🔑 Cuentas y Credenciales de Acceso Empresarial")
        t.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
        s = QLabel("Selecciona cualquier usuario para auto-completar el inicio de sesión. Contraseñas protegidas con PBKDF2-HMAC-SHA256.")
        s.setStyleSheet("font-size: 11px; color: #e2e8f0;")
        h_layout.addWidget(t)
        h_layout.addWidget(s)
        layout.addWidget(header)

        # Tabs by Role
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 16px;
                font-weight: 700;
            }
        """)

        # Admin Tab
        admin_tab = self._create_admin_tab()
        tabs.addTab(admin_tab, "🏛️ Universidad (Admin)")

        # Teachers Tab
        teachers_tab = self._create_teachers_tab()
        tabs.addTab(teachers_tab, "👨‍🏫 Docentes")

        # Students Tab
        students_tab = self._create_students_tab()
        tabs.addTab(students_tab, "🎓 Estudiantes (Nivelados / Rezagados)")

        layout.addWidget(tabs)

        # Footer
        footer = QHBoxLayout()
        hint = QLabel("🔒 <i>Estándar de Seguridad: Mín. 8 caracteres, mayúscula, minúscula, número y símbolo especial.</i>")
        hint.setStyleSheet("font-size: 11px; color: #475569; font-weight: 600;")
        footer.addWidget(hint)
        footer.addStretch()

        close_btn = QPushButton("Cerrar")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("background-color: #f1f5f9; color: #334155; font-weight: 700; padding: 8px 16px; border-radius: 6px; border: 1px solid #cbd5e1;")
        close_btn.clicked.connect(self.reject)
        footer.addWidget(close_btn)

        layout.addLayout(footer)

    def _create_admin_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(10)
        l.setContentsMargins(10, 10, 10, 10)

        card = QFrame()
        card.setStyleSheet("background-color: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 8px; padding: 14px;")
        cl = QVBoxLayout(card)
        cl.setSpacing(8)

        lbl = QLabel("<b>Rol:</b> Administrador / Planeación Académica UMB<br><b>Usuario:</b> <code>admin</code><br><b>Contraseña Segura:</b> <code>AdminUMB2026!*</code>")
        lbl.setStyleSheet("font-size: 13px; color: #1e293b;")
        cl.addWidget(lbl)

        desc = QLabel("Acceso total al panel de control, configuración de reglas, ejecución de OR-Tools CP-SAT, gestión de docentes, aulas, materias y CRUD institucional.")
        desc.setStyleSheet("font-size: 12px; color: #64748b;")
        desc.setWordWrap(True)
        cl.addWidget(desc)

        btn = QPushButton("⚡ Usar Cuenta Administrador (admin)")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: 800; padding: 10px; border-radius: 6px;")
        btn.clicked.connect(lambda: self._select("admin", "AdminUMB2026!*"))
        cl.addWidget(btn)

        l.addWidget(card)
        l.addStretch()
        return w

    def _create_teachers_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 10, 10, 10)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Usuario", "Nombre Docente", "Tipo Contrato", "Acción"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        db = SessionLocal()
        try:
            teachers = db.query(Teacher).all()
            table.setRowCount(len(teachers))
            for r, t in enumerate(teachers):
                u_name = f"docente{t.id}"
                table.setItem(r, 0, QTableWidgetItem(u_name))
                table.setItem(r, 1, QTableWidgetItem(t.name))
                table.setItem(r, 2, QTableWidgetItem(t.teacher_type.value if t.teacher_type else "-"))

                btn = QPushButton("Usar")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 4px 10px; border-radius: 4px;")
                btn.clicked.connect(lambda _, un=u_name: self._select(un, "DocenteUMB2026!*"))
                table.setCellWidget(r, 3, btn)
        finally:
            db.close()

        l.addWidget(table)
        return w

    def _create_students_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 10, 10, 10)

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Usuario", "Nombre", "Semestre", "Nivelación", "Financiero", "Acción"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

        db = SessionLocal()
        try:
            students = db.query(Student).all()
            table.setRowCount(len(students))
            for r, s in enumerate(students):
                u_name = f"estudiante{s.id}"
                table.setItem(r, 0, QTableWidgetItem(u_name))
                table.setItem(r, 1, QTableWidgetItem(s.name))
                table.setItem(r, 2, QTableWidgetItem(f"Semestre {s.semester_id}"))

                # Leveling status
                is_reg = getattr(s, "is_regular", True)
                reg_str = "🎓 Nivelado" if is_reg else "⚠️ No Nivelado"
                table.setItem(r, 3, QTableWidgetItem(reg_str))

                # Financial status
                fin_str = "Con Acuerdo" if s.has_payment_agreement else "Al Día"
                table.setItem(r, 4, QTableWidgetItem(fin_str))

                btn = QPushButton("Usar")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; padding: 4px 10px; border-radius: 4px;")
                btn.clicked.connect(lambda _, un=u_name: self._select(un, "EstudianteUMB2026!*"))
                table.setCellWidget(r, 5, btn)
        finally:
            db.close()

        l.addWidget(table)
        return w

    def _select(self, username, password):
        self.account_selected.emit(username, password)
        self.accept()
