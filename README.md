# 🎓 OptiSchedule UMB — Sistema Inteligente de Optimización y Asignación de Horarios

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20(Qt%206)-green.svg)](https://www.qt.io/)
[![Design](https://img.shields.io/badge/Design-Pastel%20React--Like-purple.svg)]()
[![Solver](https://img.shields.io/badge/Solver-Google%20OR--Tools%20CP--SAT-orange.svg)](https://developers.google.com/optimization)
[![Database](https://img.shields.io/badge/Database-SQLite%203%20%2B%20SQLAlchemy-lightgrey.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-15%20Passed%20(100%25)-brightgreen.svg)]()

**OptiSchedule UMB** es una plataforma institucional de escritorio diseñada para la **Universidad Manuela Beltrán**, orientada a la resolución automatizada del problema de asignación de horarios universitarios (*University Course Timetabling Problem - UCTP*) mediante programación matemática con restricciones (**Google OR-Tools CP-SAT**), algoritmos genéticos y una interfaz gráfica moderna inspirada en sistemas SaaS reactivos (*Lovable / React Design System*).

---

## ⚡ 1. ¿Cómo Ejecutar el Programa? (Instrucciones Claras)

### ⚠️ ¿Por qué falló `python main.py` al ejecutarlo directamente en tu PC?
En Windows, cuando escribes `python` en PowerShell o CMD sin activar el entorno virtual, el sistema ejecuta el alias global de la tienda de Windows (`C:\Users\...\AppData\Local\Microsoft\WindowsApps\python.exe`). Ese Python global **no tiene instaladas las librerías del proyecto**, provocando el error:
```text
ModuleNotFoundError: No module named 'ortools'
```
Todas las dependencias requeridas (`PySide6`, `ortools`, `SQLAlchemy`, `pandas`, `numpy==2.2.0`, `matplotlib`) están correctamente instaladas en el entorno virtual `.venv` ubicado en la raíz de este repositorio.

---

### 🚀 Opciones para Ejecutar (Elige la que prefieras):

#### Opción A (La más fácil — 1 Clic con `run.bat`):
Simplemente haz **doble clic** en el archivo **`run.bat`** en el Explorador de Windows, o escribe en tu terminal:
```cmd
.\run.bat
```
*Este script detecta automáticamente el entorno virtual del proyecto, verifica dependencias y lanza la aplicación sin que tengas que configurar nada.*

---

#### Opción B (Línea de comandos directa sin activar nada):
Ejecuta directamente el Python del entorno virtual:
```powershell
.\.venv\Scripts\python.exe main.py
```

---

#### Opción C (Activando el entorno virtual en PowerShell):
Si deseas activar el entorno en tu sesión de PowerShell:
```powershell
# 1. Permitir ejecución de scripts en la sesión actual
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 2. Activar el entorno virtual
.\.venv\Scripts\Activate.ps1

# 3. Ejecutar el programa
python main.py
```

---

## 🏛️ 2. Arquitectura y Módulos del Sistema

```
optischedule/
├── app/
│   ├── auth/                 # Control de acceso y sesiones (RBAC: Admin, Docente, Estudiante)
│   ├── database/             # Modelos ORM (SQLAlchemy) y conexión SQLite con WAL & timeout
│   ├── optimization/         # Núcleo matemático de optimización
│   │   ├── constraint_solver.py   # Solver principal Google OR-Tools CP-SAT (multi-perfil)
│   │   ├── student_optimizer.py   # Optimizador combinatorio de horarios del estudiante
│   │   ├── genetic_algorithm.py   # Algoritmo Genético complementario
│   │   └── evaluator.py           # Evaluación cuantitativa multicriterio (0 - 100%)
│   └── ui/                   # Interfaz de usuario moderna (PySide6 / Qt6)
│       ├── styles.py              # Sistema de diseño con paleta pastel y bordes redondeados
│       ├── main_window.py         # Barra superior persistente, menú lateral y navegación
│       ├── schedule_view.py       # Grilla institucional interactiva con exportación CSV
│       ├── generic_table_view.py  # Tablas CRUD con edición en celda y persistencia en DB
│       ├── widgets/
│       │   └── animated_stack.py  # Transiciones suaves de desvanecimiento (fade-in) estilo React
│       ├── dialogs/
│       │   ├── schedule_preview_dialog.py  # Visualización modal completa de horarios en pastel
│       │   └── credentials_dialog.py       # Directorio de cuentas para entorno de evaluación
│       ├── views/                 # Vistas especializadas por rol
│       └── workers/               # Hilos en segundo plano (QThread) sin congelamiento de UI
├── data/                     # Base de datos local SQLite (optischedule.db)
├── scripts/                  # Generación de datos semilla institucionales
├── tests/                    # Suite de pruebas automatizadas (pytest)
├── requirements.txt          # Dependencias fijadas (incluye numpy==2.2.0 certificado)
└── run.bat                   # Lanzador automático de un solo clic
```

---

## 🎨 3. Novedades y Mejoras Implementadas

### 🌸 1. Interfaz Gráfica Pastel (React / Lovable SaaS Style)
- **Paleta de Colores Refrescantes:** Acentos suaves de menta (`#10b981`), lavanda (`#6366f1`), cielo (`#0ea5e9`), durazno/ámbar (`#f59e0b`) y rosa suave (`#f43f5e`) sobre fondo slate ultralimpio (`#f8fafc`).
- **Transiciones Animadas:** Integración de `AnimatedStackedWidget` con animaciones de opacidad (*fade-in*) entre secciones.
- **Adiós a los cuadros rígidos:** Reemplazo de los marcos toscos de `QGroupBox` por tarjetas modernas con bordes redondeados (`14px`) y elevación sutil.

### 🔐 2. Login Formal Institucional
- Pantalla de acceso formal y autorizada de la **Universidad Manuela Beltrán**, eliminando los accesos directos de demo en la tarjeta central.
- Campo para Usuario/Código Institucional y Contraseña con alternador de visibilidad (icono de ojo).
- Indicador de seguridad institucional SSL/TLS.
- Directorio de cuentas de prueba disponible de forma discreta en el pie de página para revisiones académicas.

### 👁️ 3. Visualización Completa de Horarios Optimizados
- **Modal de Pantalla Completa (`SchedulePreviewDialog`):** Permite ver en cualquier momento el horario institucional o del estudiante con bloques coloreados en tonos pastel, métricas de calidad y botón de exportación a CSV.
- **Resolución Automática:** Si la solución proviene de OR-Tools con IDs, el visualizador cruza la base de datos para mostrar los nombres de la Asignatura, Docente, Aula y Grupo.
- **En la vista del estudiante:** Se precargan automáticamente las mejores alternativas y la grilla de previsualización está activa inmediatamente.

### 🚪 4. Cierre de Sesión Siempre Accesible
El botón de **Cerrar Sesión** está presente en 3 puntos clave:
1. **Barra Superior (Navbar):** Visible en todo momento junto al chip del usuario activo y la fecha académica.
2. **Pie de la Barra Lateral (Sidebar):** Anclado fijamente en la base con botón destacado en tono pastel rose.
3. **Menú de Navegación:** Ítem seleccionable directo en las vistas de Docente y Estudiante.

### 📅 5. Calendario y Ventanas de Inscripción (Nivelados vs Rezagados)
- **Configuración Universitaria (`RulesView`):**
  - Fechas independientes de matrícula para **Estudiantes Nivelados** (Ordinaria / Prioritaria).
  - Fechas independientes para **Estudiantes No Nivelados / Rezagados** (Extraordinaria / Ajustes).
  - **Simulador de Fecha Actual del Sistema:** Permite cambiar la fecha virtual para probar cómo reacciona el sistema en tiempo real.
- **Interfaz del Estudiante (`StudentScheduleView`):**
  - Muestra badges de estado: `🎓 Estudiante Nivelado` o `⚠️ No Nivelado (Rezagado)`.
  - Notifica si la inscripción está habilitada (`🟢 Habilitada`) o si se encuentra fuera de fecha (`🔴 Fuera de Fecha`), permitiendo solicitudes de excepción autorizada.

---

## 🔑 4. Cuentas Institucionales para Pruebas (RBAC)

Todas las cuentas vienen preconfiguradas con la contraseña `123`:

| Rol | Usuario | Contraseña | Perfil / Detalles |
|---|---|---|---|
| **Administrador** | `admin` | `123` | Control total del sistema, configuración de reglas, calendario y generación institucional |
| **Docente TC** | `docente1` $\dots$ `docente5` | `123` | Tiempo Completo (Tope 42 hrs/semana) |
| **Docente MT** | `docente6` $\dots$ `docente10` | `123` | Medio Tiempo (Tope 21 hrs/semana) |
| **Docente Cátedra** | `docente11` $\dots$ `docente20` | `123` | Cátedra (Tope 23 hrs/semana) |
| **Estudiante Nivelado** | `estudiante1` | `123` | Semestre 1, al día en materias y pagos |
| **Estudiante No Nivelado**| `estudiante2` | `123` | Semestre 1, materias pendientes de otros semestres |

---

## 🧪 5. Suite de Pruebas Automatizadas

El proyecto incluye 15 pruebas unitarias e integrales que validan autenticación, solvers matemáticos, evaluación cuantitativa, restricciones duras y optimización combinatoria:

```powershell
.\.venv\Scripts\pytest.exe -v
```

Resultado esperado:
```text
tests/test_auth.py::test_admin_authentication PASSED
tests/test_auth.py::test_teacher_authentication PASSED
tests/test_auth.py::test_student_authentication PASSED
tests/test_auth.py::test_invalid_login PASSED
tests/test_auth.py::test_logout PASSED
tests/test_crud_table.py::test_student_crud_update PASSED
tests/test_crud_table.py::test_teacher_crud_update_enum PASSED
tests/test_crud_table.py::test_room_crud_capacity PASSED
tests/test_solver_and_rules.py::test_solver_generates_assignments PASSED
tests/test_solver_and_rules.py::test_teacher_workload_hard_constraint PASSED
tests/test_student_optimizer.py::test_student_optimization_finds_options PASSED
tests/test_student_optimizer.py::test_student_save_schedule PASSED
tests/test_validation.py::test_room_capacity_logic PASSED
tests/test_validation.py::test_student_payment_agreement PASSED
tests/test_validation.py::test_evaluator_empty PASSED

============================= 15 passed =============================
```

---

## 📄 Licencia y Créditos
Proyecto desarrollado para el semillero de investigación y taller de programación de la **Universidad Manuela Beltrán (UMB)**.
