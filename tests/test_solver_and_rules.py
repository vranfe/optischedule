import pytest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.database.database import get_db
from app.database.models import Teacher, Group, Config, ScheduleAssignment, TeacherType
from app.optimization.constraint_solver import ScheduleSolver
from scripts.generate_data import create_data

@pytest.fixture(scope="module")
def setup_db():
    create_data(force_reset=True)

def test_solver_generates_assignments(setup_db):
    db = next(get_db())
    solver = ScheduleSolver(db)
    solver.build_model()
    result = solver.solve(time_limit_seconds=10.0)

    assert result["status"] == "SUCCESS", f"Solver failed: {result.get('msg')}"
    assert len(result["assignments"]) > 0

def test_teacher_workload_hard_constraint(setup_db):
    db = next(get_db())
    solver = ScheduleSolver(db)
    solver.build_model()
    result = solver.solve(time_limit_seconds=10.0)
    assert result["status"] == "SUCCESS"

    # Count assignments per teacher
    t_counts = {}
    for asg in result["assignments"]:
        tid = asg["teacher_id"]
        t_counts[tid] = t_counts.get(tid, 0) + 1

    config = db.query(Config).first()
    for tid, count in t_counts.items():
        teacher = db.query(Teacher).filter_by(id=tid).first()
        hours = count * 2
        if teacher.teacher_type == TeacherType.FULL_TIME:
            assert hours <= config.full_time_hours
        elif teacher.teacher_type == TeacherType.PART_TIME:
            assert hours <= config.part_time_hours
        elif teacher.teacher_type == TeacherType.CATEDRA:
            assert hours <= config.catedra_hours
