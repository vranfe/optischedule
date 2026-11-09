# System Architecture Specification: OptiSchedule UMB

## 1. Architectural Style & Paradigms

OptiSchedule UMB is engineered following a **Layered Architecture (N-Tier Architecture)** combined with **Model-View-Controller (MVC) Desktop Patterns** and an **Event-Driven Reactive Model** powered by Qt's Signals & Slots.

The application guarantees strict separation of concerns, decoupling user interface presentation from core business logic, algebraic optimization engines, and relational data persistence.

```
+-------------------------------------------------------------------------+
|                        PRESENTATION LAYER (UI)                         |
|   PySide6 Desktop GUI: Views, Modals, Custom Widgets, Styles (QSS)      |
+-------------------------------------------------------------------------+
       |                                                    |
       v (Asynchronous Signals / Slots)                     v (Direct Call)
+------------------------------------+   +--------------------------------+
|       CONCURRENCY WORKERS          |   |       SECURITY & SESSION       |
| QThread: SolverWorker, Alternatives|   | Auth: RBAC, PBKDF2, Session    |
+------------------------------------+   +--------------------------------+
       |                                                    |
       v                                                    v
+-------------------------------------------------------------------------+
|                       DOMAIN & OPTIMIZATION LAYER                       |
|   ScheduleSolver (CP-SAT) | StudentScheduleOptimizer | Evaluator (0-100%)|
+-------------------------------------------------------------------------+
                                   |
                                   v (SQLAlchemy ORM 2.0)
+-------------------------------------------------------------------------+
|                        DATA PERSISTENCE LAYER                           |
|       SessionLocal / Engine -> SQLite 3 Database (optischedule.db)      |
+-------------------------------------------------------------------------+
```

---

## 2. Directory Structure and Module Responsibilities

The codebase is organized into modular packages located under the project root:

```
optischedule/
|-- data/
|   `-- optischedule.db               # SQLite 3 serverless relational database file
|-- scripts/
|   `-- generate_data.py              # Data seeding and database bootstrap engine
|-- tests/
|   |-- test_auth.py                  # RBAC, login security, and password policy unit tests
|   |-- test_crud_table.py            # Generic table view and CRUD integration tests
|   |-- test_solver_and_rules.py      # Hard/soft constraint validation with CP-SAT
|   |-- test_student_optimizer.py     # Student combinatorics, night shifts, and enrollment persistence
|   `-- test_validation.py            # Form validation, credit limits, and leveling rules
|-- app/
|   |-- auth/
|   |   |-- security.py               # PBKDF2-HMAC-SHA256 password hashing and validation
|   |   `-- session.py                # Thread-safe in-memory session manager (current user, role)
|   |-- database/
|   |   |-- database.py               # Engine configuration, NullPool, PRAGMA WAL, SessionLocal
|   |   `-- models.py                 # SQLAlchemy declarative models, Enums, and relationships
|   |-- optimization/
|   |   |-- constraint_solver.py      # Google OR-Tools CP-SAT macro institutional timetabler
|   |   |-- evaluator.py              # Multicriteria normalized quality auditor (0 to 100%)
|   |   `-- student_optimizer.py      # Micro student combinatorics (Backtracking + Heuristic Ordering)
|   `-- ui/
|       |-- dialogs/                  # Modal windows (QuickAccountsDialog, ScheduleDetailModal)
|       |-- views/                    # Main views (Dashboard, Timetable, StudentView, AdminCRUDs)
|       |-- widgets/                  # Reusable UI widgets and animated containers
|       |-- workers/                  # QThread workers (SolverWorker, AlternativesWorker)
|       |-- excel_exporter.py         # Multi-sheet academic schedule export using OpenPyXL
|       |-- styles.py                 # UMB corporate color palette, CSS/QSS definitions
|       `-- main_window.py            # Top-level window, dynamic sidebar navigation by role
|-- main.py                           # Application bootstrap and entry point
|-- OptiSchedule-UMB.spec             # PyInstaller production build manifest
`-- requirements.txt                  # Python dependency specifications
```

---

## 3. Subsystem Breakdown

### 3.1. Security and Access Control (`app/auth/`)
- **Authentication:** Verifies credentials against hashed passwords stored in SQLite. Passwords utilize standard PBKDF2-HMAC-SHA256 with 100,000 salt-hashed iterations.
- **Role-Based Access Control (RBAC):** Three distinct personas are enforced:
  1. `ADMINISTRADOR`: Full access to configuration parameters, CRUD modules (teachers, rooms, groups, subjects, students), solver execution, and institutional alternatives comparison.
  2. `DOCENTE`: Read-only access to assigned personal schedules, workload metrics, and read-write access to weekly availability and subject preference surveys.
  3. `ESTUDIANTE`: Access to personal study plan, prerequisites, leveling status, interactive weighting sliders, schedule alternative generator, and enrollment confirmation.
- **Session Management:** The `SessionManager` singleton maintains the currently logged-in user, active role, and associated entity ID (`teacher_id` or `student_id`).

### 3.2. Data Persistence Layer (`app/database/`)
- **Engine & Concurrency Configuration:** Configured in `app/database/database.py` using `sqlite:///data/optischedule.db` with `NullPool` to prevent lock contention across multiple threads. Connection events enforce `PRAGMA journal_mode=WAL` (Write-Ahead Logging) and `PRAGMA busy_timeout=30000` (30 seconds) for seamless concurrent read/write operations.
- **Declarative ORM:** Models mapped with SQLAlchemy 2.0 define relational cascades, foreign keys, and enumerated fields (e.g., `ShiftType`, `DayOfWeek`, `TeacherType`, `KnowledgeArea`).

### 3.3. Algorithmic Optimization Layer (`app/optimization/`)
- **Institutional Timetabler (`constraint_solver.py`):** Translates physical, pedagogical, and administrative requirements into an integer programming model solved via Google OR-Tools CP-SAT.
- **Solution Evaluator (`evaluator.py`):** Audits any candidate timetable (whether generated by solver or already saved) across five normalized objective axes ($S_{\text{pref}}, S_{\text{gap}}, S_{\text{load}}, S_{\text{room}}, S_{\text{dist}}$), providing an objective quality score between 0% and 100%.
- **Student Optimizer (`student_optimizer.py`):** Resolves individual enrollment by navigating conflict-free group combinations matching student preferences.

### 3.4. User Interface Layer (`app/ui/`)
- **PySide6 (Qt 6.11+):** Desktop client providing native Windows rendering, fluid layouts, collapsible sidebars, and styled cards.
- **Reactive UI & Asynchronous Concurrency:** Heavy algebraic computations are dispatched to `QThread` workers:
  - `SolverWorker`: Runs `ScheduleSolver.solve()` in the background, emitting progress signals and returning the assignment matrix upon completion.
  - `AlternativesWorker`: Generates, evaluates, and ranks multiple institutional schedule alternatives concurrently across four optimization profiles (`balanced`, `preferences`, `load_balance`, `compact`).
  - **Thread Safety:** Workers never touch UI widgets directly; all communication occurs via Qt Signals and Slots, preventing UI thread freezing and "Not Responding" OS warnings.
- **Excel Export Engine (`excel_exporter.py`):** Utilizes `OpenPyXL` to format and generate institutional Excel reports with custom column widths, colored headers, semester sheets, and teacher schedules.

---

## 4. Software Evolution and Iterative Development

The application was designed and hardened through four major iterative phases:
- **Phase 1 (Iterations 1-5) - Foundations:** Relational database schema with SQLAlchemy, preliminary CP-SAT model for basic room/teacher unicity, basic PySide6 window skeleton, and RBAC login.
- **Phase 2 (Iterations 6-10) - Academic Domain Rules:** UMB daily shifts (Morning, Afternoon, Night), Saturday 17:00 hard cutoff, faculty contract limits (Full-Time 42h, Part-Time 21h, Cátedra 23h), and academic leveling for irregular students.
- **Phase 3 (Iterations 11-15) - Student Optimizer & UX:** Combinatorial student optimizer, zero-sum preference sliders (100%), full-screen timetable modal visualizers, and multi-sheet Excel export.
- **Phase 4 (Iterations 16-20+) - Robustness, Stability & Defect Resolution:** Knowledge area filtering (`knowledge_area`) for faculty assignment, real-time group capacity quotas with color-coded status badges, Best-First heuristic branch ordering to eliminate morning-bias truncation in student schedules, and full 18-test automated regression suite.
