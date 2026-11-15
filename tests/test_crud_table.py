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

def test_subject_crud_update_credits_hours_and_area(setup_data):
    db = next(get_db())
    subject = db.query(Subject).first()
    assert subject is not None

    orig_credits = subject.credits
    orig_hours = subject.hours_per_week
    orig_area = subject.knowledge_area

    # Update credits and hours
    subject.credits = 5
    subject.hours_per_week = 6
    subject.knowledge_area = "Ciencias Básicas y Matemáticas"
    db.commit()

    db2 = next(get_db())
    updated_sub = db2.query(Subject).filter_by(id=subject.id).first()
    assert updated_sub.credits == 5
    assert updated_sub.hours_per_week == 6
    assert updated_sub.knowledge_area == "Ciencias Básicas y Matemáticas"

    # Restore
    updated_sub.credits = orig_credits
    updated_sub.hours_per_week = orig_hours
    updated_sub.knowledge_area = orig_area
    db2.commit()

def test_generic_table_view_clean_field_value(qapp):
    from app.ui.generic_table_view import GenericTableView
    from app.database.models import KnowledgeArea

    view = GenericTableView(
        title="Asignaturas",
        headers=["ID", "Nombre", "Créditos", "Horas", "Semestre", "Área"],
        model_class=Subject,
        field_keys=["id", "name", "credits", "hours_per_week", "semester_id", "knowledge_area"],
        enum_mappings={"knowledge_area": KnowledgeArea}
    )

    # 1. Setting enum into a String column should produce a string
    val_area = view._clean_field_value(None, "knowledge_area", KnowledgeArea.SOFTWARE)
    assert isinstance(val_area, str)
    assert val_area == "Ingeniería de Software y Programación"

    # 2. Setting credits as text integer
    val_credits = view._clean_field_value(None, "credits", "4")
    assert isinstance(val_credits, int)
    assert val_credits == 4

    # 3. Setting hours_per_week as text integer
    val_hours = view._clean_field_value(None, "hours_per_week", "6")
    assert isinstance(val_hours, int)
    assert val_hours == 6
