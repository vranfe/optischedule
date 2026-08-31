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
