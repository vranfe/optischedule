# 🎓 OptiSchedule UMB — Sistema de Optimización y Asignación de Horarios Universitarios

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20(Qt%206)-green.svg)](https://www.qt.io/)
[![Optimization](https://img.shields.io/badge/Solver-Google%20OR--Tools%20CP--SAT-orange.svg)](https://developers.google.com/optimization)
[![Database](https://img.shields.io/badge/Database-SQLite%203%20%2B%20SQLAlchemy-lightgrey.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-15%20Passed-brightgreen.svg)]()

**OptiSchedule UMB** es una plataforma de escritorio de nivel empresarial e investigación académica diseñada para resolver el problema de asignación de horarios universitarios (*University Course Timetabling Problem - UCTP*), mediante programación matemática con restricciones (**Constraint Programming - CP-SAT**).

---

## 🏛️ 1. Arquitectura del Sistema

El software sigue una arquitectura modular en capas desacopladas, garantizando que el motor de optimización matemática sea 100% independiente de la interfaz gráfica y pueda ejecutarse mediante CLI, scripts o servicios automatizados.

```
optischedule/
├── app/
│   ├── auth/                 # Control de acceso y sesiones (RBAC: Admin, Docente, Estudiante)
│   ├── database/             # Modelos ORM (SQLAlchemy) y conexión SQLite con WAL & timeout
│   ├── optimization/         # Núcleo matemático de optimización
│   │   ├── constraint_solver.py   # Solver principal Google OR-Tools CP-SAT
│   │   ├── student_optimizer.py   # Optimizador de horario personal del estudiante
│   │   ├── genetic_algorithm.py   # Algoritmo Genético / Búsqueda Local complementaria
│   │   └── evaluator.py           # Evaluador de factibilidad y calidad multicriterio
│   └── ui/                   # Interfaz de usuario moderna (PySide6 / Qt6)
│       ├── styles.py              # Design System global con diseño redondeado y alto contraste
│       ├── main_window.py         # Navegación y ciclo de vida de vistas
│       ├── schedule_view.py       # Grilla institucional interactiva con exportación CSV
│       ├── generic_table_view.py  # Tablas CRUD con edición en celda y persistencia en DB
│       ├── views/                 # Vistas especializadas por rol
│       └── workers/               # Hilos en segundo plano (QThread) para no congelar la UI
├── data/                     # Base de datos local SQLite (optischedule.db)
├── scripts/                  # Generación de datos semilla institucionales
└── tests/                    # Suite de pruebas automatizadas (pytest)
```

---

## ⚙️ 2. Modelo Matemático y Restricciones

El sistema separa estrictamente **Factibilidad (Restricciones Duras)** de **Calidad (Restricciones Blandas / Función Objetivo)**.

### 🔴 Restricciones Duras (Hard Constraints — 0 Violaciones Permitidas)
1. **Unicidad de Docente:** Un docente no puede dictar más de una clase en el mismo día y franja horaria.
2. **Unicidad de Aula:** Un aula no puede albergar más de un grupo simultáneamente.
3. **Unicidad de Grupo:** Un grupo no puede tener más de una asignatura en la misma franja.
4. **Capacidad de Aulas:** El aforo del aula asignada debe ser mayor o igual a los estudiantes esperados ($Capacidad \ge Estudiantes$).
5. **Topes Contractuales Máximos (Control de Sobrecarga):**
   - **Tiempo Completo (TC):** Máximo **42 horas/semana** (21 bloques de 2h).
   - **Medio Tiempo (MT):** Máximo **21 horas/semana** (10 bloques de 2h).
   - **Cátedra:** Máximo **23 horas/semana** (11 bloques de 2h).
6. **Límite de Sábado:** La jornada de los sábados finaliza estrictamente a las **17:00 (5:00 p. m.)**.
7. **No Solapamiento de Cohorte Académica:** Las asignaturas de un mismo semestre no se solapan entre sí para garantizar que los estudiantes regulares puedan cursar su malla completa sin cruces de horario.

### 🟢 Restricciones Blandas y Ponderaciones de Calidad (Soft Objectives)
La función objetivo multicriterio normalizada ($0\% - 100\%$) optimiza:
- **Satisfacción de Preferencias:** Afinidad de docentes con asignaturas ($1 \dots 5$) y turnos preferidos de estudiantes.
- **Reducción de Subcarga y Balance Docente:** Prioriza asignar horas a la nómina fija (Tiempo Completo y Medio Tiempo) para evitar capacidad ociosa y subutilización de contratos.
- **Minimización de Huecos (Ventanas):** Reduce tiempos muertos entre clases para profesores y alumnos.
- **Eficiencia de Aulas:** Maximiza la tasa de ocupación de pupitres respecto a la capacidad instalada.
- **Distribución Semanal:** Distribuye equilibradamente las sesiones de lunes a sábado.

---

## 👥 3. Flujos del Sistema por Rol

### 🏛️ Rol Administrador (Universidad)
- **Generación Automática Institucional:** Resuelve el horario global en segundo plano mediante `QThread` sin congelar la ventana.
- **Comparador Multicriterio de Soluciones:** Permite contrastar perfiles de solución (*Balanceada*, *Enfoque en Preferencias*, *Enfoque Compacto sin Huecos*) evaluando métricas cuantitativas y seleccionando la mejor alternativa.
- **Gestión de Carga y Subcarga Docente:** Panel con semaforización en tiempo real:
  - ⚠️ *Sobrecarga (>100%):* Exceso de horas contractuales.
  - ✅ *Carga Óptima (80-100%):* Máxima eficiencia.
  - ⚡ *Subcarga (<80%):* Horas libres disponibles para asignación. Botón directo de *Rebalanceo CP-SAT*.
- **CRUD con Edición en Vivo:** Tablas con edición de celdas en doble clic, adición de nuevos registros, eliminación con confirmación y buscador dinámico.

### 🎓 Rol Estudiante
- **Planificador Personal de Matrícula:**
  - Selección libre de materias a cursar.
  - Configuración de turnos preferidos (☀️ Mañana, ⛅ Tarde, 🌙 Noche, 🌐 Cualquiera).
  - Ponderación personalizada de criterios (Importancia de Jornada, Minimizar Huecos, Maximizar Días Libres).
  - Motor de búsqueda combinatoria sin cruces que genera y rankea las **Top 3 mejores alternativas personales**.
  - Confirmación e inscripción oficial de la alternativa seleccionada.
  - Exportación de horario individual en formato CSV.

### 👨‍🏫 Rol Docente
- **Consulta de Asignaciones:** Grilla semanal detallada con aulas, grupos y franjas asignadas.
- **Resumen Contractual:** Monitoreo de horas asignadas vs. horas contratadas.
- **Afinidad y Disponibilidad:** Consulta de asignaturas de preferencia y horarios reportados.

---

## 🚀 4. Instalación y Despliegue

### Requisitos Previos
- **Python 3.11** o superior (recomendado 3.12+).
- Git instalado.

### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/optischedule.git
cd optischedule
```

### Paso 2: Crear y Activar Entorno Virtual
En Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 3: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Generar la Base de Datos Inicial
```bash
python scripts/generate_data.py
```

### Paso 5: Ejecutar la Aplicación
```bash
python main.py
```

---

## 🔑 5. Credenciales de Prueba (RBAC)

Todas las cuentas vienen preconfiguradas con la contraseña `123`:

| Rol | Usuario | Contraseña | Descripción |
|---|---|---|---|
| **Administrador** | `admin` | `123` | Control total, generación institucional y CRUD |
| **Docente** | `docente1` $\dots$ `docente20` | `123` | Consulta de horario docente y carga |
| **Estudiante** | `estudiante1` $\dots$ `estudiante120` | `123` | Planificador y optimizador de horario personal |

*(En la pantalla de Login existen botones de **Acceso Rápido** para iniciar sesión con un solo clic).*

---

## 🧪 6. Ejecución de Pruebas Automatizadas

El sistema cuenta con una suite completa de pruebas unitarias y de integración que validan autenticación, solvers matemáticos, restricciones duras, optimizador del estudiante y operaciones CRUD:

```bash
python -m pytest -v
```

---

## 📦 7. Compilación a Ejecutable `.exe` (PyInstaller)

Para generar el binario independiente para Windows sin requerir Python instalado en la máquina cliente:

```powershell
pyinstaller --onefile --windowed --name OptiSchedule-UMB --collect-all ortools -y main.py
```

El archivo ejecutable se generará en la carpeta `dist/OptiSchedule-UMB.exe`.

---

## 📄 Licencia
Proyecto desarrollado para el semillero de investigación y taller de programación de la **Universidad Manuela Beltrán (UMB)**.
