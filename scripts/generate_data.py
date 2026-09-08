import sys
import os
import random
from datetime import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.database.database import get_db, init_db, Base, engine, SessionLocal
from app.database.models import (
    Semester, Subject, Teacher, Room, Group, Student, 
    StudentPreference, TimeSlot, Config, TeacherType, ShiftType, DayOfWeek, 
    TeacherAvailability, User, UserRole, TeacherSubjectPreference
)

def create_data(force_reset=False):
    if force_reset:
        Base.metadata.drop_all(bind=engine)
    init_db()
    
    # Check if complete data already exists
    check_session = SessionLocal()
    try:
        user_count = check_session.query(User).count()
    except Exception:
        user_count = 0
    finally:
        check_session.close()

    if not force_reset and user_count > 10:
        print(f"Data already exists with {user_count} users. Ready.")
        return

    print("Populating database with full enterprise dataset...")
    # Wipe and recreate if partial/outdated
    Base.metadata.drop_all(bind=engine)
    init_db()
    db = SessionLocal()

    # Configuration
    config = Config(
        full_time_hours=42,
        part_time_hours=21,
        catedra_hours=23,
        max_subjects=32,
        max_semesters=4,
        max_consecutive_hours=4,
        allow_saturday=True,
        pref_weight=0.35,
        gap_weight=0.25,
        load_weight=0.20,
        dist_weight=0.10,
        room_weight=0.10,
        payment_agreement_allowed=True,
        enrollment_start_regular="2026-09-01",
        enrollment_end_regular="2026-09-15",
        enrollment_start_irregular="2026-09-16",
        enrollment_end_irregular="2026-09-30",
        system_current_date="2026-09-08"
    )
    db.add(config)
    db.commit()
    
    # Create Admin User
    admin_user = User(username="admin", password="123", role=UserRole.ADMIN)
    db.add(admin_user)
    db.commit()
    
    # Time slots (M-F 8-10, 10-12, 13-15, 15-17, 18-20, 20-22)
    shifts = {
        ShiftType.MORNING: [
            (time(8, 0), time(10, 0)),
            (time(10, 0), time(12, 0))
        ],
        ShiftType.AFTERNOON: [
            (time(13, 0), time(15, 0)),
            (time(15, 0), time(17, 0))
        ],
        ShiftType.NIGHT: [
            (time(18, 0), time(20, 0)),
            (time(20, 0), time(22, 0))
        ]
    }
    
    db_slots = []
    for shift, times in shifts.items():
        for start, end in times:
            slot = TimeSlot(shift=shift, start_time=start, end_time=end)
            db.add(slot)
            db_slots.append(slot)
    db.commit()

    # 4 Semesters
    db_semesters = []
    for i in range(1, 5):
        sem = Semester(number=i)
        db.add(sem)
        db_semesters.append(sem)
    db.commit()
    
    # 32 Subjects (8 per semester)
    db_subjects = []
    subject_count = 1
    for sem in db_semesters:
        for _ in range(8):
            subj = Subject(name=f"Asignatura {subject_count}", hours_per_week=4, semester_id=sem.id)
            db.add(subj)
            db_subjects.append(subj)
            subject_count += 1
    db.commit()
    
    # Rooms
    db_rooms = []
    for i in range(1, 11):
        cap = random.choice([25, 30, 35, 40])
        rtype = "Normal" if i <= 7 else "Laboratorio"
        room = Room(name=f"Aula {i:02d}", capacity=cap, room_type=rtype)
        db.add(room)
        db_rooms.append(room)
    db.commit()
    
    # Teachers
    teacher_types = [TeacherType.FULL_TIME, TeacherType.PART_TIME, TeacherType.CATEDRA]
    db_teachers = []
    for i in range(1, 21):
        t_type = teacher_types[(i - 1) % len(teacher_types)]
        t = Teacher(name=f"Docente {i}", teacher_type=t_type)
        db.add(t)
        db.flush()
        
        # User for teacher
        u = User(username=f"docente{i}", password="123", role=UserRole.TEACHER, teacher_id=t.id)
        db.add(u)
        db_teachers.append(t)
    db.commit()
    
    # Teacher Availabilities and Subject Preferences
    days = list(DayOfWeek)
    for t in db_teachers:
        # Availabilities
        for d in days:
            if d == DayOfWeek.SATURDAY:
                # Saturday only allows morning and afternoon slots up to 17:00 (5:00 PM)
                valid_slots = [s for s in db_slots if s.shift in [ShiftType.MORNING, ShiftType.AFTERNOON] and s.end_time <= time(17, 0)]
            else:
                valid_slots = db_slots
                
            # Sample available slots (60% availability)
            sample_count = max(2, int(len(valid_slots) * 0.6))
            for slot in random.sample(valid_slots, k=sample_count):
                avail = TeacherAvailability(teacher_id=t.id, day=d, time_slot_id=slot.id)
                db.add(avail)
                
        # Subject Preferences (3 to 6 preferred subjects)
        preferred_subjs = random.sample(db_subjects, k=random.randint(3, 6))
        for subj in preferred_subjs:
            score = random.randint(3, 5) # 3: Normal, 4: Alta, 5: Muy Alta
            pref = TeacherSubjectPreference(teacher_id=t.id, subject_id=subj.id, preference_score=score)
            db.add(pref)
            
    db.commit()
    
    # Students
    db_students = []
    for i in range(1, 121): # 120 students
        sem = random.choice(db_semesters)
        has_payment = random.random() < 0.15
        is_regular = random.random() < 0.75 # 75% nivelados, 25% no nivelados
        enrolled = True
        student = Student(
            name=f"Estudiante {i}", 
            semester_id=sem.id, 
            has_payment_agreement=has_payment, 
            is_enrolled=enrolled,
            is_regular=is_regular
        )
        db.add(student)
        db.flush()
        
        # User for student
        u = User(username=f"estudiante{i}", password="123", role=UserRole.STUDENT, student_id=student.id)
        db.add(u)
        db_students.append(student)
    db.commit()
    
    # Student Preferences
    for student in db_students:
        pref1 = StudentPreference(student_id=student.id, shift=random.choice(list(ShiftType)), priority=1)
        db.add(pref1)
    db.commit()
    
    # Groups (1 per subject with appropriate size)
    for subj in db_subjects:
        sem_students = sum(1 for s in db_students if s.semester_id == subj.semester_id and s.is_enrolled)
        num_groups = max(1, sem_students // 30 + (1 if sem_students % 30 > 0 else 0))
        for g in range(1, num_groups + 1):
            expected = max(15, min(35, sem_students // num_groups if num_groups > 0 else 20))
            group = Group(name=f"G{g}-{subj.name}", subject_id=subj.id, expected_students=expected)
            db.add(group)
    db.commit()
    db.close()

    print("Complete enterprise dataset successfully generated with RBAC users!")

if __name__ == "__main__":
    create_data(force_reset=True)

