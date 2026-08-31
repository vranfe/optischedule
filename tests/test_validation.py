import pytest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.database.models import Room, Group, Student, Config
from app.optimization.evaluator import Evaluator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.database import Base

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Setup some test data
    config = Config()
    db.add(config)
    db.commit()
    
    yield db
    db.close()

def test_room_capacity_logic(test_db):
    room = Room(name="Aula 1", capacity=20, room_type="Normal")
    group = Group(name="G1", expected_students=25)
    test_db.add(room)
    test_db.add(group)
    test_db.commit()
    
    assert room.capacity < group.expected_students, "Room capacity should be insufficient"
    
def test_student_payment_agreement(test_db):
    student1 = Student(name="A", has_payment_agreement=True)
    student2 = Student(name="B", has_payment_agreement=False)
    test_db.add_all([student1, student2])
    test_db.commit()
    
    assert student1.has_payment_agreement is True
    assert student2.has_payment_agreement is False

def test_evaluator_empty(test_db):
    evaluator = Evaluator(test_db)
    res = evaluator.evaluate()
    assert res["hard_constraint_violations"] == 0
    assert res["global_score"] == 0.0
