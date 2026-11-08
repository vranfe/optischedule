import pytest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.database.database import get_db
from app.database.models import Student, Subject, ScheduleAssignment, StudentEnrollment, ShiftType
from app.optimization.constraint_solver import ScheduleSolver
from app.optimization.student_optimizer import StudentScheduleOptimizer
from scripts.generate_data import create_data

@pytest.fixture(scope="module")
def setup_with_schedule():
    create_data(force_reset=True)
    db = next(get_db())
    try:
        # Generate an institutional schedule first
        solver = ScheduleSolver(db)
        solver.build_model()
        res = solver.solve(time_limit_seconds=15.0)
        assert res["status"] == "SUCCESS"
        
        from app.database.models import DayOfWeek
        db.query(ScheduleAssignment).delete()
        for asg in res["assignments"]:
            assignment = ScheduleAssignment(
                group_id=asg["group_id"],
                teacher_id=asg["teacher_id"],
                room_id=asg["room_id"],
                day=DayOfWeek(asg["day"]) if isinstance(asg["day"], str) else asg["day"],
                time_slot_id=asg["time_slot_id"]
            )
            db.add(assignment)
        db.commit()
    finally:
        db.close()

def test_student_optimization_finds_options(setup_with_schedule):
    db = next(get_db())
    try:
        student = db.query(Student).first()
        assert student is not None

        subjects = db.query(Subject).filter_by(semester_id=student.semester_id).all()
        selected_ids = [s.id for s in subjects[:4]]

        optimizer = StudentScheduleOptimizer(db, student.id)
        result = optimizer.optimize_student_schedule(
            selected_subject_ids=selected_ids,
            preferred_shift=ShiftType.MORNING,
            shift_weight=0.5,
            gap_weight=0.3,
            free_day_weight=0.2
        )

        assert result["status"] == "SUCCESS"
        assert len(result["options"]) > 0
        top_option = result["options"][0]
        assert "global_score" in top_option
        assert "groups" in top_option
        assert len(top_option["groups"]) == len(selected_ids)
    finally:
        db.close()

def test_student_save_schedule(setup_with_schedule):
    db = next(get_db())
    try:
        student = db.query(Student).first()
        subjects = db.query(Subject).filter_by(semester_id=student.semester_id).all()
        selected_ids = [s.id for s in subjects[:3]]

        optimizer = StudentScheduleOptimizer(db, student.id)
        result = optimizer.optimize_student_schedule(selected_ids)
        assert result["status"] == "SUCCESS"
        assert len(result["options"]) > 0

        chosen_groups = [g_id for _, g_id, _ in result["options"][0]["groups"]]
        success = optimizer.save_selected_schedule(chosen_groups)
        assert success is True

        # Check persistence in DB
        db2 = next(get_db())
        try:
            enrollments = db2.query(StudentEnrollment).filter_by(student_id=student.id).all()
            enrolled_group_ids = [e.group_id for e in enrollments]
            assert set(enrolled_group_ids) == set(chosen_groups)
        finally:
            db2.close()
    finally:
        db.close()


def test_student_optimizer_night_shift_priority(setup_with_schedule):
    db = next(get_db())
    try:
        student = db.query(Student).filter_by(semester_id=3).first()
        assert student is not None
        subjects = db.query(Subject).filter_by(semester_id=3).all()
        selected_ids = [s.id for s in subjects]

        optimizer = StudentScheduleOptimizer(db, student.id)
        result = optimizer.optimize_student_schedule(
            selected_subject_ids=selected_ids,
            preferred_shift=ShiftType.NIGHT,
            shift_weight=1.0,
            gap_weight=0.0,
            free_day_weight=0.0
        )
        assert result["status"] == "SUCCESS"
        assert len(result["options"]) > 0
        top = result["options"][0]
        # Regular students with full night cohort should achieve high night match (>= 90%)
        assert top["shift_score"] >= 90.0, f"Expected night score >= 90%, got {top['shift_score']}%"
        # Confirm groups assigned are predominantly G3
        night_group_count = sum(1 for _, _, g in top["groups"] if "G3" in g["group_name"] or "NOCHE" in g["group_name"].upper())
        assert night_group_count >= len(selected_ids) - 1
    finally:
        db.close()
