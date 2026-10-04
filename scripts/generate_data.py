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
from app.auth.security import PasswordPolicy

# Realistic Colombian Names
COLOMBIAN_FIRST_NAMES_MALE = [
    "Carlos Andrés", "Juan Camilo", "Diego Fernando", "Jorge Eliécer", "Andrés Felipe",
    "Gustavo Adolfo", "Óscar David", "Mauricio Alejandro", "Julián David", "Hernando",
    "Camilo Ernesto", "Javier Orlando", "Rodrigo Alberto", "Santiago", "Mateo",
    "Sebastián", "Alejandro", "Samuel", "Nicolás", "Daniel", "Gabriel", "Esteban",
    "Felipe", "David", "Manuel", "Lucas", "Tomás", "Cristian", "Leonardo", "Iván"
]

COLOMBIAN_FIRST_NAMES_FEMALE = [
    "María Fernanda", "Claudia Patricia", "Ángela Viviana", "Lina Marcela", "Paola Andrea",
    "Diana Carolina", "Nathalia Sofía", "Sandra Milena", "Gloria Inés", "Yolanda Esperanza",
    "Mónica Patricia", "Valentina", "Isabella", "Mariana", "Daniela", "Sofía", "Camila",
    "Luciana", "Salomé", "Valeria", "Gabriela", "Catalina", "Adriana", "Juliana",
    "Laura", "Manuela", "Sara", "Carolina", "Tatiana", "Marcela"
]

COLOMBIAN_LAST_NAMES = [
    "Restrepo", "Jaramillo", "Osorio", "Henao", "Caicedo", "Cárdenas", "Mosquera", "Betancur",
    "Vélez", "Palacios", "Quintero", "Valencia", "Gómez", "Riaño", "Barreto", "Bermúdez",
    "Ospina", "Cuartas", "Villamizar", "Rodríguez", "Peñaloza", "Triviño", "Salamanca",
    "Castañeda", "Muñoz", "Zuluaga", "Aristizábal", "Duque", "Gaviria", "Echeverri",
    "Londoño", "Botero", "Villegas", "Arango", "Uribe", "Correa", "Cardona", "Herrera",
    "Flórez", "Robledo", "Holguín", "Carvajal", "Parra", "Posada", "Mejía", "Cuervo",
    "Peláez", "Chaverra", "Montoya", "Silva", "Rojas", "Perea", "Garzón", "Serna", "Zapata", "Peña", "Pinzón", "Forero", "Ruiz", "Vaca", "Niño"
]

def generate_colombian_name(is_female=None):
    if is_female is None:
        is_female = random.choice([True, False])
    first = random.choice(COLOMBIAN_FIRST_NAMES_FEMALE if is_female else COLOMBIAN_FIRST_NAMES_MALE)
    last1 = random.choice(COLOMBIAN_LAST_NAMES)
    last2 = random.choice([l for l in COLOMBIAN_LAST_NAMES if l != last1])
    return f"{first} {last1} {last2}"

def create_data(force_reset=False):
    if force_reset:
        Base.metadata.drop_all(bind=engine)
    init_db()
    
    # Check if complete data already exists
    check_session = SessionLocal()
    try:
        user_count = check_session.query(User).count()
        subj_count = check_session.query(Subject).count()
    except Exception:
        user_count = 0
        subj_count = 0
    finally:
        check_session.close()

    if not force_reset and user_count > 50 and subj_count == 36:
        print(f"Data already exists with {user_count} users and {subj_count} subjects. Ready.")
        return

    print("Populating database with full official UMB Software Engineering curriculum & Colombian enterprise dataset...")
    # Wipe and recreate
    Base.metadata.drop_all(bind=engine)
    init_db()
    db = SessionLocal()

    # Configuration
    config = Config(
        full_time_hours=42,
        part_time_hours=21,
        catedra_hours=23,
        max_subjects=36,
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
    
    # Industry-Compliant Passwords (hashed with PBKDF2-HMAC-SHA256)
    admin_pw_hash = PasswordPolicy.hash_password("AdminUMB2026!*")
    teacher_pw_hash = PasswordPolicy.hash_password("DocenteUMB2026!*")
    student_pw_hash = PasswordPolicy.hash_password("EstudianteUMB2026!*")

    # Create Admin User
    admin_user = User(username="admin", password=admin_pw_hash, role=UserRole.ADMIN)
    db.add(admin_user)
    db.commit()
    
    # Time slots: Morning (06-12), Afternoon (12-18), Night (18-22)
    shifts = {
        ShiftType.MORNING: [
            (time(6, 0), time(8, 0)),
            (time(8, 0), time(10, 0)),
            (time(10, 0), time(12, 0))
        ],
        ShiftType.AFTERNOON: [
            (time(12, 0), time(14, 0)),
            (time(14, 0), time(16, 0)),
            (time(16, 0), time(18, 0))
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

    # Official Curriculum Data from UMB PDF (Semesters 1 to 4)
    # Format: (Semester, Name, Credits, HoursPerWeek)
    curriculum_data = [
        # Semestre 1 (10 Asignaturas - 19 Créditos)
        (1, "Orientación a la Ingeniería", 1, 2),
        (1, "Lógica de Programación", 3, 4),
        (1, "Teoría General de Sistemas", 2, 2),
        (1, "Taller de Estrategias del Pensamiento", 1, 2),
        (1, "Matemáticas Básicas", 2, 2),
        (1, "Álgebra Lineal", 2, 2),
        (1, "Física Mecánica y Lab", 4, 4),
        (1, "Inglés Inicial", 1, 2),
        (1, "Cátedra Manuela Beltrán", 1, 2),
        (1, "Comunicación Oral y Escrita", 2, 2),

        # Semestre 2 (9 Asignaturas - 20 Créditos)
        (2, "Programación Orientada a Objetos", 3, 4),
        (2, "Arquitectura de Hardware", 3, 4),
        (2, "Taller de Fundamentos de Investigación", 1, 2),
        (2, "Cálculo Diferencial", 3, 4),
        (2, "Matemáticas Discretas", 2, 2),
        (2, "Física Electromagnética y Lab", 3, 4),
        (2, "Inglés Básico I", 1, 2),
        (2, "Filosofía", 2, 2),
        (2, "Electiva I", 2, 2),

        # Semestre 3 (8 Asignaturas - 19 Créditos)
        (3, "Estructuras de Datos", 3, 4),
        (3, "Análisis y Diseño del Software", 4, 4),
        (3, "Infraestructura Tecnológica I", 3, 4),
        (3, "Taller de Investigación Cualitativa", 1, 2),
        (3, "Cálculo Integral", 3, 4),
        (3, "Probabilidad y Estadística", 2, 2),
        (3, "Inglés Básico II", 1, 2),
        (3, "Electiva II", 2, 2),

        # Semestre 4 (9 Asignaturas - 20 Créditos)
        (4, "Taller de Programación", 2, 2),
        (4, "Patrones y Metodologías de la Construcción del Software", 3, 4),
        (4, "Computación Gráfica", 2, 2),
        (4, "Teoría de Bases de Datos", 4, 4),
        (4, "Contabilidad General", 2, 2),
        (4, "Taller de Investigación Cuantitativa", 1, 2),
        (4, "Ecuaciones Diferenciales", 2, 2),
        (4, "Cálculo Vectorial", 3, 4),
        (4, "Inglés Pre-intermedio", 1, 2),
    ]

    db_subjects = []
    for sem_num, name, creds, hrs in curriculum_data:
        sem_obj = db_semesters[sem_num - 1]
        subj = Subject(name=name, credits=creds, hours_per_week=hrs, semester_id=sem_obj.id)
        db.add(subj)
        db_subjects.append(subj)
    db.commit()

    # Rooms (16 realistic academic spaces & specialized labs)
    room_definitions = [
        ("Laboratorio de Software 1", 35, "Laboratorio"),
        ("Laboratorio de Software 2", 35, "Laboratorio"),
        ("Laboratorio de Redes y Hardware", 30, "Laboratorio"),
        ("Laboratorio de Física y Electrónica", 30, "Laboratorio"),
        ("Laboratorio de Computación Gráfica", 30, "Laboratorio"),
        ("Laboratorio de Bases de Datos", 30, "Laboratorio"),
        ("Sala Mac de Desarrollo", 25, "Laboratorio"),
        ("Salón 101 - Bloque A", 40, "Normal"),
        ("Salón 102 - Bloque A", 40, "Normal"),
        ("Salón 201 - Bloque A", 35, "Normal"),
        ("Salón 202 - Bloque A", 35, "Normal"),
        ("Salón 301 - Bloque B", 40, "Normal"),
        ("Salón 302 - Bloque B", 40, "Normal"),
        ("Salón 401 - Bloque B", 35, "Normal"),
        ("Salón 402 - Bloque B", 35, "Normal"),
        ("Auditorio Fundadores", 60, "Auditorio"),
    ]

    db_rooms = []
    for name, cap, rtype in room_definitions:
        room = Room(name=name, capacity=cap, room_type=rtype)
        db.add(room)
        db_rooms.append(room)
    db.commit()

    # 24 Colombian Teachers (8 Tiempo Completo, 8 Medio Tiempo, 8 Cátedra)
    db_teachers = []
    teacher_types = [
        TeacherType.FULL_TIME, TeacherType.FULL_TIME, TeacherType.FULL_TIME, TeacherType.FULL_TIME,
        TeacherType.FULL_TIME, TeacherType.FULL_TIME, TeacherType.FULL_TIME, TeacherType.FULL_TIME,
        TeacherType.PART_TIME, TeacherType.PART_TIME, TeacherType.PART_TIME, TeacherType.PART_TIME,
        TeacherType.PART_TIME, TeacherType.PART_TIME, TeacherType.PART_TIME, TeacherType.PART_TIME,
        TeacherType.CATEDRA, TeacherType.CATEDRA, TeacherType.CATEDRA, TeacherType.CATEDRA,
        TeacherType.CATEDRA, TeacherType.CATEDRA, TeacherType.CATEDRA, TeacherType.CATEDRA
    ]

    teacher_names = [
        "Carlos Andrés Restrepo Gómez",
        "María Fernanda Jaramillo Silva",
        "Juan Camilo Osorio Morales",
        "Claudia Patricia Henao Buendía",
        "Diego Fernando Caicedo Rengifo",
        "Ángela Viviana Cárdenas Rojas",
        "Jorge Eliécer Mosquera Perea",
        "Andrés Felipe Betancur Echeverry",
        "Lina Marcela Vélez Londoño",
        "Gustavo Adolfo Palacios Murillo",
        "Paola Andrea Quintero Castaño",
        "Óscar David Valencia Hurtado",
        "Diana Carolina Gómez Montoya",
        "Mauricio Alejandro Riaño Cuervo",
        "Nathalia Sofía Barreto Chavarro",
        "Julián David Bermúdez Garzón",
        "Hernando de Jesús Ospina Serna",
        "Sandra Milena Cuartas Zapata",
        "Camilo Ernesto Villamizar Peña",
        "Gloria Inés Rodríguez Pinzón",
        "Javier Orlando Peñaloza Forero",
        "Yolanda Esperanza Triviño Ruiz",
        "Rodrigo Alberto Salamanca Vaca",
        "Mónica Patricia Castañeda Niño"
    ]

    for i in range(len(teacher_names)):
        t_type = teacher_types[i]
        t_name = teacher_names[i]
        t = Teacher(name=t_name, teacher_type=t_type)
        db.add(t)
        db.flush()

        # User for teacher with hashed password
        u = User(username=f"docente{t.id}", password=teacher_pw_hash, role=UserRole.TEACHER, teacher_id=t.id)
        db.add(u)
        db_teachers.append(t)
    db.commit()

    # Teacher Availabilities and Subject Preferences
    days = list(DayOfWeek)
    for idx, t in enumerate(db_teachers):
        # Configure rich availability per contract type
        for d in days:
            if d == DayOfWeek.SATURDAY:
                avail_slots = [s for s in db_slots if s.shift in [ShiftType.MORNING, ShiftType.AFTERNOON] and s.end_time <= time(17, 0)]
            else:
                if t.teacher_type == TeacherType.FULL_TIME:
                    # Full time: broad availability across morning, afternoon and some night
                    avail_slots = db_slots
                elif t.teacher_type == TeacherType.PART_TIME:
                    # Part time: morning + afternoon or afternoon + night
                    if idx % 2 == 0:
                        avail_slots = [s for s in db_slots if s.shift in [ShiftType.MORNING, ShiftType.AFTERNOON]]
                    else:
                        avail_slots = [s for s in db_slots if s.shift in [ShiftType.AFTERNOON, ShiftType.NIGHT]]
                else: # CATEDRA
                    # Cátedra: night and morning/saturday
                    if idx % 2 == 0:
                        avail_slots = [s for s in db_slots if s.shift == ShiftType.NIGHT or s.shift == ShiftType.MORNING]
                    else:
                        avail_slots = [s for s in db_slots if s.shift in [ShiftType.NIGHT, ShiftType.AFTERNOON]]

            # Add availabilities
            sample_k = min(len(avail_slots), max(3, int(len(avail_slots) * 0.85)))
            for slot in random.sample(avail_slots, k=sample_k):
                avail = TeacherAvailability(teacher_id=t.id, day=d, time_slot_id=slot.id)
                db.add(avail)

        # Subject Preferences (each teacher prefers 4 to 8 subjects matching faculty domains)
        preferred_subjs = random.sample(db_subjects, k=random.randint(4, 8))
        for subj in preferred_subjs:
            score = random.randint(3, 5) # 3: Normal, 4: Alta, 5: Muy Alta
            pref = TeacherSubjectPreference(teacher_id=t.id, subject_id=subj.id, preference_score=score)
            db.add(pref)

    db.commit()

    # 120 Colombian Students across 4 Semesters
    db_students = []
    used_student_names = set()
    for i in range(1, 121):
        sem = db_semesters[(i - 1) % 4] # Balanced 30 students per semester
        while True:
            s_name = generate_colombian_name()
            if s_name not in used_student_names:
                used_student_names.add(s_name)
                break

        has_payment = (i % 7 == 0) # ~14% with payment agreement
        is_regular = (i % 5 != 0)   # 80% regular/nivelado, 20% irregular
        enrolled = True

        student = Student(
            name=s_name,
            semester_id=sem.id,
            has_payment_agreement=has_payment,
            is_enrolled=enrolled,
            is_regular=is_regular
        )
        db.add(student)
        db.flush()

        # User for student with hashed password
        u = User(username=f"estudiante{student.id}", password=student_pw_hash, role=UserRole.STUDENT, student_id=student.id)
        db.add(u)
        db_students.append(student)
    db.commit()

    # Student Shift Preferences (Distributed among Morning, Afternoon, Night)
    shift_cycle = [ShiftType.MORNING, ShiftType.AFTERNOON, ShiftType.NIGHT]
    for idx, student in enumerate(db_students):
        fav_shift = shift_cycle[idx % 3]
        pref = StudentPreference(student_id=student.id, shift=fav_shift, priority=1)
        db.add(pref)
    db.commit()

    # Groups: Exactly 3 groups per Subject (1 Mañana, 1 Tarde, 1 Noche) = 108 Groups!
    for subj in db_subjects:
        g1 = Group(name=f"G1-Mañana - {subj.name}", subject_id=subj.id, expected_students=25)
        g2 = Group(name=f"G2-Tarde - {subj.name}", subject_id=subj.id, expected_students=25)
        g3 = Group(name=f"G3-Noche - {subj.name}", subject_id=subj.id, expected_students=25)
        db.add(g1)
        db.add(g2)
        db.add(g3)
    db.commit()
    db.close()

    print("Successfully generated official UMB dataset: 36 subjects, 108 shift-varied groups, 24 Colombian teachers, 120 Colombian students, 16 rooms, PBKDF2 hashed security!")

if __name__ == "__main__":
    create_data(force_reset=True)
