import pytest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.database.database import get_db, init_db
from app.database.models import Student, Teacher, Subject, Room, Group, TeacherType
from scripts.generate_data import create_data

@pytest.fixture(scope="module")
def setup_data():
    create_data(force_reset=True)

def test_student_crud_update(setup_data):
    db = next(get_db())
    student = db.query(Student).first()
    assert student is not None

    original_name = student.name
    student.name = "Estudiante Editado Test"
    student.has_payment_agreement = True
    db.commit()

    # Query afresh from new session
    db2 = next(get_db())
    updated_student = db2.query(Student).filter_by(id=student.id).first()
    assert updated_student.name == "Estudiante Editado Test"
    assert updated_student.has_payment_agreement is True

    # Restore
    updated_student.name = original_name
    db2.commit()

def test_teacher_crud_update_enum(setup_data):
    db = next(get_db())
    teacher = db.query(Teacher).first()
    assert teacher is not None

    teacher.teacher_type = TeacherType.CATEDRA
    db.commit()

    db2 = next(get_db())
    updated_teacher = db2.query(Teacher).filter_by(id=teacher.id).first()
    assert updated_teacher.teacher_type == TeacherType.CATEDRA

def test_room_crud_capacity(setup_data):
    db = next(get_db())
    room = db.query(Room).first()
    assert room is not None

    original_cap = room.capacity
    room.capacity = 55
    db.commit()

    db2 = next(get_db())
    updated_room = db2.query(Room).filter_by(id=room.id).first()
    assert updated_room.capacity == 55

    # Restore
    updated_room.capacity = original_cap
    db2.commit()
