# 🎓 OptiSchedule UMB — Sistema Inteligente de Optimización y Asignación de Horarios

[![CI Pipeline](https://github.com/vranfe/optischedule/actions/workflows/ci.yml/badge.svg)](https://github.com/vranfe/optischedule/actions/workflows/ci.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=vranfe_optischedule&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=vranfe_optischedule)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20(Qt%206)-green.svg)](https://www.qt.io/)
[![Solver](https://img.shields.io/badge/Solver-Google%20OR--Tools%20CP--SAT-orange.svg)](https://developers.google.com/optimization)
[![Optimizer](https://img.shields.io/badge/Optimizer-Multi--Objective%20Combinatorial-purple.svg)]()
[![Database](https://img.shields.io/badge/Database-SQLite%203%20%2B%20SQLAlchemy-lightgrey.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-24%20Passed%20(100%25)-brightgreen.svg)]()

**OptiSchedule UMB** es una plataforma institucional de escritorio de grado universitario desarrollada para la **Universidad Manuela Beltrán (UMB)**. Su propósito es resolver de forma automatizada y matemáticamente óptima el problema de asignación de horarios universitarios (*University Course Timetabling Problem - UCTP*), balanceando la carga docente, aforos de aulas, disponibilidad institucional y las preferencias de los estudiantes.

---

## ⚡ 1. ¿Cómo Ejecutar el Programa?

### 🚀 Opción A (La más rápida y directa — Terminal):
Simplemente abre tu terminal en la carpeta del proyecto y ejecuta:
```powershell
python main.py
```
*No necesitas activar ningún entorno virtual ni ejecutar pasos previos si ya tienes instaladas las librerías en tu Python.*

---

### 🖱️ Opción B (Doble Clic con `run.bat`):
Haz doble clic en el archivo **`run.bat`** en el explorador de Windows, o escribe en la consola:
```cmd
.\run.bat
```
*El script detecta automáticamente el intérprete de Python disponible y lanza la aplicación de inmediato.*

---

### 📦 Opción C (Instalación de dependencias si estás en un equipo nuevo):
Si vas a clonar o ejecutar este proyecto en otra computadora desde cero:
```powershell
# 1. (Opcional) Crear y activar entorno virtual aislado
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Instalar dependencias fijadas
pip install -r requirements.txt

# 3. Iniciar la aplicación
python main.py
```

---

## 🔑 2. Cuentas y Contraseñas de Acceso (RBAC)

Las contraseñas se encuentran **cifradas de manera unidireccional en la base de datos SQLite** utilizando el algoritmo estándar de la industria **PBKDF2-HMAC-SHA256** (con sal aleatoria de 16 bytes y 100.000 iteraciones).

Para ingresar y evaluar el sistema, utiliza las siguientes credenciales maestras:

| Rol | Usuario | Contraseña Maestra | Alcance y Funcionalidades |
|---|---|---|---|
| **Administrador** | `admin` | `AdminUMB2026!*` | Configuración de calendario, reglas institucionales, comparación de alternativas de horarios, CRUDs de estudiantes, docentes, materias, grupos y aulas con semáforo de disponibilidad. |
| **Docente** | `docente1` $\dots$ `docente12` | `DocenteUMB2026!*` | Horario semanal asignado, calificación de afinidad temática (filtrada por su área de conocimiento), disponibilidad horaria y visualización de carga laboral. |
| **Estudiante** | `estudiante1` $\dots$ `estudiante120` | `EstudianteUMB2026!*` | Planificador de horarios, selección de asignaturas (con desbloqueo dinámico para rezagados), optimización de alternativas según balance de preferencias (100% suma cero), matrícula y horario oficial. |

*Tip:* En la pantalla de inicio de sesión puedes hacer clic en **"📋 Ver Cuentas de Acceso (Entorno de Pruebas)"** para desplegar el modal interactivo con todas las cuentas disponibles.

---

## 🧠 3. Los 2 Motores de Optimización de OptiSchedule

El sistema opera mediante una arquitectura de optimización dual especializada: un motor institucional global y un motor combinatorio personal:

```
                      ARQUITECTURA DE OPTIMIZACIÓN DUAL DE OPTISCHEDULE
                                             │
         ┌───────────────────────────────────┴───────────────────────────────────┐
         ▼                                                                       ▼
┌───────────────────────────────────────────────┐       ┌───────────────────────────────────────────────┐
│     1. MOTOR INSTITUCIONAL GLOBAL             │       │     2. MOTOR COMBINATORIO ESTUDIANTIL         │
│     Google OR-Tools CP-SAT                    │       │     Optimizador de Matrícula Personal         │
│     (app/optimization/constraint_solver.py)   │       │     (app/optimization/student_optimizer.py)   │
├───────────────────────────────────────────────┤       ├───────────────────────────────────────────────┤
│ • Programación por Restricciones + SAT solver │       │ • Búsqueda combinatoria en árbol con poda     │
│   matemático exacto de Google.                │       │   anticipada (backtracking + forward check).  │
│ • Resuelve el macro-horario de la facultad    │       │ • Explora las combinaciones de grupos de las  │
│   garantizando 0 choques de aula o docente.   │       │   materias elegidas por cada estudiante.      │
│ • Respeta topes semanales de horas docentes   │       │ • Aplica la fórmula de suma cero al 100%      │
│   y áreas de conocimiento obligatorias.       │       │   sobre jornada, huecos y días libres.        │
│ • Genera las 4 alternativas del comparador    │       │ • Valida aforos reales de salones y cupos     │
│   (Equilibrado, Afinidad, Aulas, Compactación)│       │   disponibles antes de confirmar inscripción. │
└───────────────────────────────────────────────┘       └───────────────────────────────────────────────┘
```

1. **Google OR-Tools CP-SAT (`app/optimization/constraint_solver.py`):**
   * Es un motor matemático exacto desarrollado por Google para problemas combinatorios masivos.
   * Modela el horario universitario como un problema de satisfacción booleana (*SAT*) y programación por restricciones (*CP*).
   * **Restricciones duras (*Hard Constraints*):** Un profesor no puede estar en dos salones a la vez, un aula no puede albergar dos grupos en la misma franja, los profesores solo dictan materias de su misma área académica (`knowledge_area`), y se respetan los topes semanales de horas según el tipo de vinculación (TC: 42h, MT: 21h, Cátedra: 23h).
   * **Restricciones blandas (*Soft Constraints*):** Minimizar horas dispersas (huecos) y concentrar los grupos en sus jornadas objetivo (mañana, tarde o noche).

2. **Optimizador de Horario del Estudiante (`app/optimization/student_optimizer.py`):**
   * Algoritmo de búsqueda combinatoria con poda hacia adelante (*forward checking*).
   * Toma las materias seleccionadas por el alumno y busca combinaciones de grupos que **no tengan ningún choque horario**.
   * Califica cada combinación según las preferencias del estudiante (prioridad de jornada, minimizar ventanas y maximizar días libres), respetando la **regla de suma cero al 100%**.
   * Valida en tiempo real los aforos y cupos disponibles de cada aula antes de permitir la confirmación de matrícula.

---

## 🏛️ 4. Arquitectura de Software Desacoplada en Capas

El sistema sigue una **Arquitectura en Capas Limpia (Layered Architecture)**, asegurando que la interfaz gráfica no manipule directamente el motor matemático ni las consultas SQL a bajo nivel:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. CAPA DE PRESENTACIÓN (UI - PySide6 / Qt6)                                │
│    main_window.py | views/ | dialogs/ | widgets/ | generic_table_view.py    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Señales, eventos y llamadas a servicios
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. CAPA DE SEGURIDAD Y CONTROL DE SESIÓN (app/auth/)                         │
│    auth_service.py | security.py (PBKDF2) | session.py                      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Solicitudes de cálculo y reglas de negocio
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. CAPA DE LÓGICA DE NEGOCIO Y OPTIMIZACIÓN (app/optimization/)              │
│    constraint_solver.py | student_optimizer.py | genetic_algorithm.py       │
│    evaluator.py (Métricas multicriterio)                                    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Sesiones y mapeo relacional (ORM)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. CAPA DE PERSISTENCIA Y MODELO DE DOMINIO (app/database/)                 │
│    models.py (Entidades y relaciones) | database.py (SQLite Engine & Pool)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 5. Estructura Completa del Proyecto y Catálogo de Archivos

```
optischedule/
├── main.py                         # Punto de entrada principal de la aplicación
├── requirements.txt                # Dependencias fijadas del proyecto
├── run.bat                         # Lanzador rápido en 1 clic para Windows
├── README.md                       # Documentación técnica general
├── data/
│   └── optischedule.db             # Base de datos SQLite persistente
├── scripts/
│   └── generate_data.py            # Semilla institucional (docentes, materias, aulas, estudiantes)
├── tests/                          # Suite de pruebas automatizadas (pytest)
│   ├── test_auth.py                # Pruebas de autenticación, roles y contraseñas
│   ├── test_crud_table.py          # Pruebas de edición y persistencia en tablas
│   ├── test_solver_and_rules.py    # Pruebas del solver OR-Tools y restricciones duras
│   ├── test_student_optimizer.py   # Pruebas del optimizador estudiantil y combinatoria
│   └── test_validation.py          # Pruebas de acuerdos de pago, cupos y evaluador
└── app/
    ├── __init__.py                 # Inicializador de paquete
    ├── auth/                       # Módulo de Autenticación y Seguridad
    │   ├── __init__.py
    │   ├── auth_service.py         # Orquestador de login, validación de credenciales y logout
    │   ├── security.py             # Políticas de contraseñas, hashing PBKDF2 y validaciones
    │   └── session.py              # Almacenamiento en memoria de la sesión activa
    ├── database/                   # Módulo de Acceso a Datos (ORM)
    │   ├── __init__.py
    │   ├── database.py             # Conexión SQLite con WAL, pool y SessionLocal
    │   └── models.py               # Definición de tablas y relaciones de dominio
    ├── optimization/               # Módulo de Inteligencia Matemática
    │   ├── __init__.py
    │   ├── constraint_solver.py    # Solver Google OR-Tools CP-SAT (Horario institucional)
    │   ├── student_optimizer.py    # Generador de alternativas y combinatoria del estudiante
    │   └── evaluator.py            # Evaluador cuantitativo de calidad (0 a 100%)
    └── ui/                         # Módulo de Interfaz de Usuario (PySide6)
        ├── __init__.py
        ├── main_window.py          # Ventana principal, navegación lateral y orquestación
        ├── schedule_view.py        # Grilla gráfica de horarios institucionales
        ├── generic_table_view.py   # Tabla CRUD genérica con campos calculados y solo lectura
        ├── excel_exporter.py       # Utilidad de exportación a hojas de cálculo (.xlsx / .csv)
        ├── styles.py               # Hoja de estilos QSS, paleta y variables visuales
        ├── dialogs/
        │   ├── credentials_dialog.py      # Modal con directorio de cuentas de prueba
        │   └── schedule_preview_dialog.py # Modal a pantalla completa para visualizar horarios
        ├── views/
        │   ├── login_view.py              # Pantalla formal de login institucional UMB
        │   ├── dashboard_view.py          # Panel de bienvenida y resumen de métricas
        │   ├── rules_view.py              # Calendario de matrículas y reglas académicas
        │   ├── preferences_view.py        # Disponibilidad y afinidad docente (filtrada por área)
        │   ├── workload_view.py           # Análisis de carga y horas semanales docentes
        │   ├── solution_comparison_view.py# Comparador de alternativas y activación de horario
        │   ├── student_schedule_view.py   # Planificador del estudiante y horario oficial
        │   └── student_preferences_view.py# Configuración de jornada preferida del alumno
        ├── widgets/
        │   ├── __init__.py
        │   └── animated_stack.py   # Contenedor con transición animada de desvanecimiento
        └── workers/
            ├── solver_worker.py        # Hilo en segundo plano para Google OR-Tools
            └── alternatives_worker.py  # Hilo en segundo plano para generar soluciones múltiples
```

---

## 📈 6. Proceso de Desarrollo: Metodología Iterativa e Incremental

El desarrollo de OptiSchedule no siguió el modelo rígido de "cascada", sino un **ciclo de vida iterativo e incremental** de más de 20 iteraciones continuas:

```
[Iteración 1-5: Fundación]
  • Modelado relacional en SQLAlchemy y arquitectura de base de datos.
  • Implementación inicial de Google OR-Tools CP-SAT con restricciones de aula y docente.
  • Esqueleto básico de interfaz con PySide6 y navegación por roles (RBAC).

[Iteración 6-10: Restricciones Académicas y Refinamiento]
  • Reglas de jornada UMB (Mañana, Tarde, Noche) y restricción de sábados a las 17:00.
  • Tipos de contratación docente (Tiempo Completo, Medio Tiempo, Cátedra) y topes semanales.
  • Manejo de estudiantes regulares e irregulares (rezagados) con materias adeudadas.

[Iteración 11-15: Optimizador Estudiantil y Experiencia de Usuario]
  • Creación del motor combinatorio personal para estudiantes (`StudentScheduleOptimizer`).
  • Sliders interactivos de ponderación de preferencias con regla de suma cero (100%).
  • Exportación formal a Excel (.xlsx) y visualizadores modales a pantalla completa.

[Iteración 16-20: Robustez, Estabilidad y Respaldo Institucional]
  • Erradicación de errores críticos en pestañas ocultas (estiramiento de celdas y clamping).
  • Filtrado estricto por área académica docente (`knowledge_area`) para evitar asignaciones incongruentes.
  • Desbloqueo dinámico para alumnos rezagados al marcar sus asignaturas adeudadas.
  • Incorporación de disponibilidad en tiempo real con semáforo en el CRUD de Grupos.
  • Corrección de incompatibilidad de tipos Enum en SQLite (`_clean_field_value`).
  • Medición cronológica de huecos en horas reales (`gap_hours`).
  • Supresión de inanición docente (*no teacher starvation*) en CP-SAT.

[Iteración 21-25: DevSecOps, Integración Continua (CI/CD) y Calidad Estática]
  • Creación del pipeline de CI/CD en GitHub Actions (`.github/workflows/ci.yml`) con ejecución headless de PySide6 (`QT_QPA_PLATFORM=offscreen`).
  • Integración de pruebas automatizadas con reporte de cobertura XML (`coverage.xml`, 63% de cobertura total).
  • Implementación de Mutation Testing automatizado con `mutmut` (`scripts/run_mutation_tests.py`, umbral mínimo 50%).
  • Configuración de análisis estático y Quality Gate con SonarCloud (`sonar-project.properties`).
  • Auditoría semanal automática de dependencias y parches de seguridad con Dependabot (`.github/dependabot.yml`).
  • Suite automatizada ampliada y verificada a 24 tests (100% aprobados).
```

---

## 🧪 7. Verificación y Pruebas Automatizadas

Para ejecutar la batería completa de 24 pruebas con reporte de cobertura en terminal:
```powershell
python -m pytest tests/ --cov=app --cov-report=term -v
```

Resultado verificado de la suite:
```text
tests/test_auth.py::test_hash_password_generates_salt_and_hash PASSED                    [  4%]
tests/test_auth.py::test_verify_password_correct_and_incorrect PASSED                    [  8%]
tests/test_auth.py::test_validate_password_strength PASSED                               [ 12%]
tests/test_auth.py::test_authenticate_user_success PASSED                                 [ 16%]
tests/test_auth.py::test_authenticate_user_invalid_credentials PASSED                     [ 20%]
tests/test_auth.py::test_session_management PASSED                                       [ 25%]
tests/test_auth.py::test_session_has_role PASSED                                         [ 29%]
tests/test_auth.py::test_session_clear PASSED                                            [ 33%]
tests/test_crud_table.py::test_student_crud_update PASSED                                 [ 37%]
tests/test_crud_table.py::test_teacher_crud_update_enum PASSED                            [ 41%]
tests/test_crud_table.py::test_room_crud_capacity PASSED                                  [ 45%]
tests/test_crud_table.py::test_subject_crud_update_credits_hours_and_area PASSED          [ 50%]
tests/test_crud_table.py::test_generic_table_view_clean_field_value PASSED                [ 54%]
tests/test_solver_and_rules.py::test_solver_feasibility_and_hard_constraints PASSED       [ 58%]
tests/test_solver_and_rules.py::test_no_saturday_night_slots PASSED                      [ 62%]
tests/test_solver_and_rules.py::test_no_teacher_starvation_in_candidate_pool PASSED      [ 66%]
tests/test_student_optimizer.py::test_student_optimizer_basic_flow PASSED                 [ 70%]
tests/test_student_optimizer.py::test_student_optimizer_compact_free_days PASSED          [ 75%]
tests/test_student_optimizer.py::test_student_optimizer_gap_calculation PASSED           [ 79%]
tests/test_student_optimizer.py::test_student_optimizer_saturday_night_allowed PASSED     [ 83%]
tests/test_student_optimizer.py::test_student_optimizer_tie_breaker_respects_shift_weight PASSED [ 87%]
tests/test_validation.py::test_student_payment_agreement PASSED                          [ 91%]
tests/test_validation.py::test_room_capacity_limits PASSED                               [ 95%]
tests/test_validation.py::test_irregular_student_rules PASSED                            [100%]

======================== 24 passed in 129.85s (0:02:09) ========================
```

---

## 🚀 8. Pipeline de CI/CD y DevSecOps (`.github/workflows/`)

OptiSchedule UMB cuenta con un ecosistema de Integración Continua, Análisis Estático de Código (SAST) y Gestión de Dependencias automatizado en GitHub Actions:

### 1. `ci.yml` — Integración Continua, Cobertura y Mutation Testing
* **Ubicación:** `.github/workflows/ci.yml`
* **Disparadores:** En cada `push` y `pull_request` sobre la rama `main`.
* **Entorno:** Ubuntu Linux (`ubuntu-latest`) con Python 3.12.
* **Funcionalidad:**
  1. Instala dependencias gráficas de sistema (`libegl1`, `libxkbcommon`, `xvfb`) para emular el entorno de ventanas sin requerir servidor físico.
  2. Activa `QT_QPA_PLATFORM=offscreen` permitiendo que PySide6 y los componentes de interfaz ejecuten sus pruebas en modo headless.
  3. Ejecuta los 24 tests mediante **PyTest** y genera el reporte `coverage.xml` (63% de cobertura global, superando el 85-94% en los motores de optimización).
  4. Ejecuta el runner de **Mutation Testing** (`scripts/run_mutation_tests.py`), asegurando que las aserciones de prueba maten mutantes artificiales con un puntaje superior al 50%.
  5. Envía las métricas de calidad y cobertura al Quality Gate de **SonarCloud**.

### 2. `dependabot.yml` — Auditoría Automatizada de Dependencias
* **Ubicación:** `.github/dependabot.yml`
* **Frecuencia:** Semanal.
* **Funcionalidad:** Monitorea las dependencias de Python en `requirements.txt` y las versiones de las acciones de GitHub Actions (`checkout`, `setup-python`), abriendo Pull Requests automáticos ante vulnerabilidades o parches de seguridad.

---

## 📄 9. Créditos y Autoría
Proyecto desarrollado para taller de programación de la **Universidad Manuela Beltrán (UMB)**.
