from PySide6.QtCore import QThread, Signal
from app.database.database import SessionLocal
from app.optimization.constraint_solver import ScheduleSolver
from app.optimization.evaluator import Evaluator

class AlternativesWorker(QThread):
    started_signal = Signal()
    progress_signal = Signal(int, str)
    finished_signal = Signal(list)
    error_signal = Signal(str)

    def __init__(self, time_limit_per_profile=15.0):
        super().__init__()
        self.time_limit_per_profile = time_limit_per_profile

    def run(self):
        try:
            self.started_signal.emit()
            
            profiles = [
                ("Solución Base (Equilibrada)", "balanced"),
                ("Alternativa A (Prioridad Afinidad Docente)", "preferences"),
                ("Alternativa B (Prioridad Aulas y Carga)", "load_balance"),
                ("Alternativa C (Prioridad Compactación)", "compact")
            ]

            generated_solutions = []
            total_profiles = len(profiles)

            for idx, (name, prof) in enumerate(profiles):
                percent = int((idx / total_profiles) * 100)
                self.progress_signal.emit(percent, f"Calculando '{name}' ({idx + 1}/{total_profiles})...")

                db = SessionLocal()
                try:
                    solver = ScheduleSolver(db, profile=prof)
                    solver.build_model()
                    res = solver.solve(time_limit_seconds=self.time_limit_per_profile)
                    
                    if res["status"] == "SUCCESS":
                        evaluator = Evaluator(db)
                        eval_res = evaluator.evaluate(res["assignments"])
                        generated_solutions.append({
                            "name": name,
                            "profile": prof,
                            "data": eval_res,
                            "assignments": res["assignments"]
                        })
                finally:
                    db.close()

            self.progress_signal.emit(100, "Cálculo de alternativas completado.")
            
            # Rank by global score descending
            generated_solutions.sort(key=lambda x: x["data"]["global_score"], reverse=True)
            self.finished_signal.emit(generated_solutions)

        except Exception as e:
            self.error_signal.emit(str(e))
