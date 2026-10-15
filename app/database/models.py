from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Time, Enum
from sqlalchemy.orm import relationship
import enum
from app.database.database import Base

class UserRole(enum.Enum):
    ADMIN = "ADMINISTRADOR"
    TEACHER = "DOCENTE"
    STUDENT = "ESTUDIANTE"

class TeacherType(enum.Enum):
    FULL_TIME = "TIEMPO COMPLETO"
    PART_TIME = "MEDIO TIEMPO"
    CATEDRA = "CATEDRA"

class ShiftType(enum.Enum):
    MORNING = "MAÑANA"
    AFTERNOON = "TARDE"
    NIGHT = "NOCHE"

class DayOfWeek(enum.Enum):
    MONDAY = "LUNES"
    TUESDAY = "MARTES"
    WEDNESDAY = "MIÉRCOLES"
    THURSDAY = "JUEVES"
    FRIDAY = "VIERNES"
    SATURDAY = "SÁBADO"

class KnowledgeArea(enum.Enum):
    SOFTWARE = "Ingeniería de Software y Programación"
    MATH_SCIENCE = "Ciencias Básicas y Matemáticas"
    INFRASTRUCTURE = "Infraestructura, Redes y Hardware"
    HUMANITIES_RESEARCH = "Investigación, Humanidades y Gestión"
    LANGUAGES = "Idiomas y Lenguas Extranjeras"

class Config(Base):
    __tablename__ = "configuration"
    id = Column(Integer, primary_key=True, index=True)
    full_time_hours = Column(Integer, default=42)
    part_time_hours = Column(Integer, default=21)
    catedra_hours = Column(Integer, default=23)
    max_subjects = Column(Integer, default=36)
    max_semesters = Column(Integer, default=4)
    max_consecutive_hours = Column(Integer, default=4)
    allow_saturday = Column(Boolean, default=True)
    pref_weight = Column(Float, default=0.35)
    gap_weight = Column(Float, default=0.25)
    load_weight = Column(Float, default=0.20)
    dist_weight = Column(Float, default=0.10)
    room_weight = Column(Float, default=0.10)
    payment_agreement_allowed = Column(Boolean, default=True)
    enrollment_start_regular = Column(String, default="2026-09-01")
    enrollment_end_regular = Column(String, default="2026-09-15")
    enrollment_start_irregular = Column(String, default="2026-09-16")
    enrollment_end_irregular = Column(String, default="2026-09-30")
    system_current_date = Column(String, default="2026-09-08")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String, default="123456")
    role = Column(Enum(UserRole), index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    
    teacher = relationship("Teacher", back_populates="user")
    student = relationship("Student", back_populates="user")

class Semester(Base):
    __tablename__ = "semesters"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, index=True)
    subjects = relationship("Subject", back_populates="semester")
    students = relationship("Student", back_populates="semester")

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    credits = Column(Integer, default=3)
    hours_per_week = Column(Integer, default=4)
    knowledge_area = Column(String, default="Ingeniería de Software y Programación")
    semester_id = Column(Integer, ForeignKey("semesters.id"))
    semester = relationship("Semester", back_populates="subjects")
    groups = relationship("Group", back_populates="subject")
    teacher_preferences = relationship("TeacherSubjectPreference", back_populates="subject")

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    teacher_type = Column(Enum(TeacherType))
    knowledge_area = Column(String, default="Ingeniería de Software y Programación")
    user = relationship("User", back_populates="teacher", uselist=False)
    availabilities = relationship("TeacherAvailability", back_populates="teacher", cascade="all, delete-orphan")
    subject_preferences = relationship("TeacherSubjectPreference", back_populates="teacher", cascade="all, delete-orphan")
    assignments = relationship("ScheduleAssignment", back_populates="teacher")

class TeacherAvailability(Base):
    __tablename__ = "teacher_availabilities"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    day = Column(Enum(DayOfWeek))
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"))
    teacher = relationship("Teacher", back_populates="availabilities")
    time_slot = relationship("TimeSlot")

class TeacherSubjectPreference(Base):
    __tablename__ = "teacher_subject_preferences"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    preference_score = Column(Integer, default=3) # 1 (Baja) to 5 (Alta)
    
    teacher = relationship("Teacher", back_populates="subject_preferences")
    subject = relationship("Subject", back_populates="teacher_preferences")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    capacity = Column(Integer)
    room_type = Column(String, default="Normal") # e.g., "Normal", "Laboratorio"
    assignments = relationship("ScheduleAssignment", back_populates="room")

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    expected_students = Column(Integer, default=0)
    subject = relationship("Subject", back_populates="groups")
    assignments = relationship("ScheduleAssignment", back_populates="group")
    enrollments = relationship("StudentEnrollment", back_populates="group", cascade="all, delete-orphan")

    @property
    def subject_name(self):
        return self.subject.name if self.subject else (f"Asignatura #{self.subject_id}" if self.subject_id else "-")

    @property
    def enrolled_count(self):
        return len(self.enrollments) if self.enrollments else 0

    @property
    def max_capacity(self):
        if self.assignments:
            for asg in self.assignments:
                if asg.room and asg.room.capacity:
                    return asg.room.capacity
        return self.expected_students or 35

    @property
    def available_quota(self):
        avail = self.max_capacity - self.enrolled_count
        return max(0, avail)

    @property
    def availability_status(self):
        avail = self.available_quota
        cap = self.max_capacity
        enrolled = self.enrolled_count
        if avail == 0:
            return f"🔴 Lleno ({enrolled}/{cap})"
        elif avail <= 5:
            return f"🟡 {avail} libres ({enrolled}/{cap})"
        else:
            return f"🟢 {avail} libres ({enrolled}/{cap})"

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    semester_id = Column(Integer, ForeignKey("semesters.id"))
    has_payment_agreement = Column(Boolean, default=False)
    is_enrolled = Column(Boolean, default=True)
    is_regular = Column(Boolean, default=True) # Nivelado (True) vs No Nivelado/Rezagado (False)
    pending_subject_ids = Column(String, default="") # Comma-separated subject IDs owed from prior semesters
    semester = relationship("Semester", back_populates="students")
    user = relationship("User", back_populates="student", uselist=False)
    preferences = relationship("StudentPreference", back_populates="student", cascade="all, delete-orphan")
    enrollments = relationship("StudentEnrollment", back_populates="student", cascade="all, delete-orphan")

class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    
    student = relationship("Student", back_populates="enrollments")
    group = relationship("Group", back_populates="enrollments")

class StudentPreference(Base):
    __tablename__ = "student_preferences"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    shift = Column(Enum(ShiftType))
    priority = Column(Integer, default=1) # 1 = primary, 2 = secondary, 3 = avoid
    student = relationship("Student", back_populates="preferences")

class TimeSlot(Base):
    __tablename__ = "time_slots"
    id = Column(Integer, primary_key=True, index=True)
    shift = Column(Enum(ShiftType))
    start_time = Column(Time)
    end_time = Column(Time)

class ScheduleAssignment(Base):
    __tablename__ = "schedule_assignments"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    day = Column(Enum(DayOfWeek))
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"))
    
    group = relationship("Group", back_populates="assignments")
    teacher = relationship("Teacher", back_populates="assignments")
    room = relationship("Room", back_populates="assignments")
    time_slot = relationship("TimeSlot")
