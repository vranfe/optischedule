from PySide6.QtCore import QThread, Signal
from app.database.database import get_db
from app.optimization.constraint_solver import ScheduleSolver

class SolverWorker(QThread):
    started_signal = Signal()
    progress_signal = Signal(int, str)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, time_limit_seconds=15.0):
        super().__init__()
        self.time_limit_seconds = time_limit_seconds

    def run(self):
        try:
            self.started_signal.emit()
            self.progress_signal.emit(10, "Cargando datos y configuraciones...")
            
            db = next(get_db())
            solver = ScheduleSolver(db)
            
            self.progress_signal.emit(30, "Construyendo modelo de restricciones duras y blandas...")
            solver.build_model()
            
            self.progress_signal.emit(60, "Ejecutando algoritmo de optimización (OR-Tools CP-SAT)...")
            result = solver.solve(time_limit_seconds=self.time_limit_seconds)
            
            self.progress_signal.emit(100, "Finalizado.")
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))
