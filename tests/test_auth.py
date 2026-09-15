import pytest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.database.database import get_db, init_db
from app.database.models import User, UserRole, Teacher, Student
from app.auth.auth_service import AuthService
from app.auth.session import session
from scripts.generate_data import create_data

@pytest.fixture(scope="module")
def setup_data():
    create_data(force_reset=True)

def test_admin_authentication(setup_data):
    success, user = AuthService.authenticate("admin", "123")
    assert success is True
    assert user is not None
    assert user.role == UserRole.ADMIN
    assert session.is_authenticated is True
    assert session.role == UserRole.ADMIN

def test_teacher_authentication(setup_data):
    success, user = AuthService.authenticate("docente1", "123")
    assert success is True
    assert user.role == UserRole.TEACHER
    assert user.teacher_id is not None
    assert session.teacher_id == user.teacher_id

def test_student_authentication(setup_data):
    success, user = AuthService.authenticate("estudiante1", "123")
    assert success is True
    assert user.role == UserRole.STUDENT
    assert user.student_id is not None
    assert session.student_id == user.student_id

def test_invalid_login(setup_data):
    success, user = AuthService.authenticate("nonexistent", "wrongpass")
    assert success is False
    assert user is None

def test_logout(setup_data):
    AuthService.authenticate("admin", "123")
    assert session.is_authenticated is True
    AuthService.logout()
    assert session.is_authenticated is False

def test_role_views_instantiation(setup_data):
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    from app.ui.main_window import MainWindow

    # Test Admin view creation (includes SolutionComparisonView)
    AuthService.authenticate("admin", "123")
    w_admin = MainWindow()
    w_admin.setup_role_navigation(UserRole.ADMIN)
    assert w_admin is not None

    # Test Teacher view creation (includes TeacherScheduleView)
    AuthService.authenticate("docente1", "123")
    w_teacher = MainWindow()
    w_teacher.setup_role_navigation(UserRole.TEACHER)
    assert w_teacher is not None

    # Test Student view creation (includes StudentScheduleView)
    AuthService.authenticate("estudiante1", "123")
    w_student = MainWindow()
    w_student.setup_role_navigation(UserRole.STUDENT)
    assert w_student is not None

