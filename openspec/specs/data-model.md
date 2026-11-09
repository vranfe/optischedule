# Relational Data Model Specification: OptiSchedule UMB

## 1. Overview and Storage Engine Architecture

OptiSchedule UMB relies on an embedded **SQLite 3** relational database managed via **SQLAlchemy 2.0 ORM**.

To guarantee robust multi-threaded desktop concurrency without lock contention between background solvers (`QThread`) and UI presentation threads, the database engine is configured with:
- **`NullPool` Connection Strategy:** Prevents thread-affine socket/connection sharing across distinct OS threads.
- **Write-Ahead Logging (`PRAGMA journal_mode=WAL`):** Enables non-blocking concurrent readers while a write transaction is committed.
- **Extended Busy Timeout (`PRAGMA busy_timeout=30000`):** Grants a 30-second window to resolve disk lock contention.

---

## 2. Entity-Relationship Schema

```
 +--------------------+       1:N       +----------------------+
 |      Semester      |----------------<|       Subject        |
 +--------------------+                 +----------------------+
          | 1:N                                     | 1:N
          v                                         v
 +--------------------+       1:N       +----------------------+
 |      Student       |----------------<|        Group         |
 +--------------------+                 +----------------------+
   | 1:1         | 1:N                      | 1:N          | 1:N
   v             v                          v              v
+------+ +-------------------+   +--------------------+ +-------------------+
| User | | StudentPreference |   | ScheduleAssignment | | StudentEnrollment |
+------+ +-------------------+   +--------------------+ +-------------------+
   ^                                        ^                      ^
   | 1:1                                    |                      |
+------+                                    |                      |
|Teacher|-----------------------------------+                      |
+------+     1:N                                                   |
   |                                                               |
   +---------------------------------------------------------------+
```

---

## 3. Enumerated Types (Domain Definitions)

### 3.1. `UserRole`
- `ADMINISTRADOR`: Master academic registrar and scheduling director.
- `DOCENTE`: Academic faculty member.
- `ESTUDIANTE`: Undergraduate student.

### 3.2. `TeacherType` (Employment Contracts)
- `TIEMPO COMPLETO`: Full-Time faculty, statutory limit 42 hours/week, priority weight $\Omega = 3$.
- `MEDIO TIEMPO`: Half-Time faculty, statutory limit 21 hours/week, priority weight $\Omega = 2$.
- `CATEDRA`: Adjunct faculty, statutory limit 23 hours/week, priority weight $\Omega = 1$.

### 3.3. `ShiftType` (Institutional Academic Shifts)
- `MAÑANA`: Morning shift (06:00 - 12:00).
- `TARDE`: Afternoon shift (12:00 - 18:00).
- `NOCHE`: Night shift (18:00 - 22:00 weekdays; morning/afternoon intensive on Saturdays up to 17:00).

### 3.4. `DayOfWeek`
- `LUNES`, `MARTES`, `MIÉRCOLES`, `JUEVES`, `VIERNES`, `SÁBADO`.

### 3.5. `KnowledgeArea` (Academic Faculties)
- `SOFTWARE`: Ingeniería de Software y Programación
- `MATH_SCIENCE`: Ciencias Básicas y Matemáticas
- `INFRASTRUCTURE`: Infraestructura, Redes y Hardware
- `HUMANITIES_RESEARCH`: Investigación, Humanidades y Gestión
- `LANGUAGES`: Idiomas y Lenguas Extranjeras

---

## 4. Entity Definitions and Schema Mapping

### 4.1. `configuration` (`Config`)
Stores master parameters and multi-criteria evaluation weights.
- `id` (`Integer`, PK)
- `full_time_hours` (`Integer`, Default: 42)
- `part_time_hours` (`Integer`, Default: 21)
- `catedra_hours` (`Integer`, Default: 23)
- `max_subjects` (`Integer`, Default: 36)
- `max_semesters` (`Integer`, Default: 4)
- `max_consecutive_hours` (`Integer`, Default: 4)
- `allow_saturday` (`Boolean`, Default: True)
- `pref_weight` (`Float`, Default: 0.35)
- `gap_weight` (`Float`, Default: 0.25)
- `load_weight` (`Float`, Default: 0.20)
- `dist_weight` (`Float`, Default: 0.10)
- `room_weight` (`Float`, Default: 0.10)
- `payment_agreement_allowed` (`Boolean`, Default: True)
- `enrollment_start_regular` (`String`, Default: "2026-09-01")
- `enrollment_end_regular` (`String`, Default: "2026-09-15")
- `enrollment_start_irregular` (`String`, Default: "2026-09-16")
- `enrollment_end_irregular` (`String`, Default: "2026-09-30")
- `system_current_date` (`String`, Default: "2026-09-08")

### 4.2. `users` (`User`)
Stores authentication records and RBAC mappings.
- `id` (`Integer`, PK, Index)
- `username` (`String`, Unique, Index)
- `password` (`String`): PBKDF2-HMAC-SHA256 salted hash.
- `role` (`Enum(UserRole)`, Index)
- `teacher_id` (`Integer`, FK -> `teachers.id`, Nullable)
- `student_id` (`Integer`, FK -> `students.id`, Nullable)

### 4.3. `semesters` (`Semester`)
Represents academic terms in the curriculum.
- `id` (`Integer`, PK, Index)
- `number` (`Integer`, Unique, Index)

### 4.4. `subjects` (`Subject`)
Curricular course units.
- `id` (`Integer`, PK, Index)
- `name` (`String`, Index)
- `credits` (`Integer`, Default: 3)
- `hours_per_week` (`Integer`, Default: 4): Direct input to slot count ($K_g = \lfloor \text{hours} / 2 \rfloor$).
- `knowledge_area` (`String`, Default: "Ingeniería de Software y Programación")
- `semester_id` (`Integer`, FK -> `semesters.id`)

### 4.5. `teachers` (`Teacher`)
Faculty records and contractual parameters.
- `id` (`Integer`, PK, Index)
- `name` (`String`, Index)
- `teacher_type` (`Enum(TeacherType)`)
- `knowledge_area` (`String`, Default: "Ingeniería de Software y Programación")
- Cascades: `availabilities` (delete-orphan), `subject_preferences` (delete-orphan).

### 4.6. `teacher_availabilities` (`TeacherAvailability`)
Explicit availability matrix submitted by faculty.
- `id` (`Integer`, PK, Index)
- `teacher_id` (`Integer`, FK -> `teachers.id`)
- `day` (`Enum(DayOfWeek)`)
- `time_slot_id` (`Integer`, FK -> `time_slots.id`)

### 4.7. `teacher_subject_preferences` (`TeacherSubjectPreference`)
Pedagogical affinity survey responses.
- `id` (`Integer`, PK, Index)
- `teacher_id` (`Integer`, FK -> `teachers.id`)
- `subject_id` (`Integer`, FK -> `subjects.id`)
- `preference_score` (`Integer`, Default: 3, Range: 1 to 5)

### 4.8. `rooms` (`Room`)
Physical classrooms and computer laboratories.
- `id` (`Integer`, PK, Index)
- `name` (`String`, Index)
- `capacity` (`Integer`): Maximum student seating limit.
- `room_type` (`String`, Default: "Normal")

### 4.9. `groups` (`Group`)
Scheduled class cohorts for a subject.
- `id` (`Integer`, PK, Index)
- `name` (`String`): Follows cohort notation, e.g., `G1-Mañana`, `G2-Tarde`, `G3-Noche`.
- `subject_id` (`Integer`, FK -> `subjects.id`)
- `expected_students` (`Integer`, Default: 0)
- **Computed Properties:**
  - `enrolled_count`: $\text{count}(\text{enrollments})$
  - `max_capacity`: Room capacity if assigned; fallback to `expected_students` or 35.
  - `available_quota`: $\max(0, \text{max\_capacity} - \text{enrolled\_count})$
  - `availability_status`: Visual indicator badge:
    - 🔴 `Lleno (enrolled/cap)` if `available_quota == 0`
    - 🟡 `X libres (enrolled/cap)` if `available_quota <= 5`
    - 🟢 `X libres (enrolled/cap)` if `available_quota > 5`

### 4.10. `students` (`Student`)
Enrolled student body records.
- `id` (`Integer`, PK, Index)
- `name` (`String`)
- `semester_id` (`Integer`, FK -> `semesters.id`)
- `has_payment_agreement` (`Boolean`, Default: False): Grants registration clearance during financial review periods.
- `is_enrolled` (`Boolean`, Default: True)
- `is_regular` (`Boolean`, Default: True): Distinguishes leveled students (`True`) from irregular/lagged students (`False`).
- `pending_subject_ids` (`String`, Default: ""): Comma-separated subject IDs from lower semesters that must be leveled first.

### 4.11. `student_enrollments` (`StudentEnrollment`)
Active subject/group enrollment per student.
- `id` (`Integer`, PK, Index)
- `student_id` (`Integer`, FK -> `students.id`)
- `group_id` (`Integer`, FK -> `groups.id`)

### 4.12. `student_preferences` (`StudentPreference`)
Student shift priorities.
- `id` (`Integer`, PK, Index)
- `student_id` (`Integer`, FK -> `students.id`)
- `shift` (`Enum(ShiftType)`)
- `priority` (`Integer`, Default: 1)

### 4.13. `time_slots` (`TimeSlot`)
Standard institutional two-hour time blocks.
- `id` (`Integer`, PK, Index)
- `shift` (`Enum(ShiftType)`)
- `start_time` (`Time`)
- `end_time` (`Time`)

### 4.14. `schedule_assignments` (`ScheduleAssignment`)
Master schedule matrix produced by solver or manual administrative adjustments.
- `id` (`Integer`, PK, Index)
- `group_id` (`Integer`, FK -> `groups.id`)
- `teacher_id` (`Integer`, FK -> `teachers.id`)
- `room_id` (`Integer`, FK -> `rooms.id`)
- `day` (`Enum(DayOfWeek)`)
- `time_slot_id` (`Integer`, FK -> `time_slots.id`)

---

## 5. Enterprise Business Rules & Invariants

1. **Academic Credit Cap:** A student cannot enroll in more than **22 academic credits** per term:
   $$\sum_{s \in \text{SelectedSubjects}} \text{Credits}(s) \le 22$$
2. **Subject Limit:** A student cannot select more than **10 subjects** in a single registration period:
   $$|\text{SelectedSubjects}| \le 10$$
3. **Academic Leveling & Irregular Student Flow:**
   - When a student is flagged as `is_regular = False`, their `pending_subject_ids` dictate the mandatory remedial curriculum.
   - The UI displays remedial subjects with a distinctive warning badge.
   - Remedial subjects MUST be selected before subjects from their active semester can be unlocked.
4. **Group Capacity Invariant:**
   - When a student confirms enrollment in group $g$, the system writes to `StudentEnrollment`.
   - The group's `available_quota` decreases by 1.
   - If `available_quota == 0`, new enrollments are rejected unless an administrator reassigns a larger room.
5. **Saturday Curfew Invariant:**
   - No assignment in `ScheduleAssignment` can possess `day == SATURDAY` with `time_slot.end_time > 17:00`.
