from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFormLayout, QHBoxLayout
from app.database.database import get_db
from app.optimization.evaluator import Evaluator

class ResultsView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        title = QLabel("Resultados de Evaluación")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        self.refresh_btn = QPushButton("Evaluar Actual")
        self.refresh_btn.clicked.connect(self.evaluate)
        
        self.optimize_btn = QPushButton("Optimizar (GA/LS)")
        self.optimize_btn.clicked.connect(self.optimize)
        
        header.addWidget(title)
        header.addWidget(self.refresh_btn)
        header.addWidget(self.optimize_btn)
        
        self.layout.addLayout(header)
        
        self.form_layout = QFormLayout()
        self.labels = {}
        
        metrics = [
            ("Estado", "status"),
            ("Violaciones Duras", "hard_constraint_violations"),
            ("Puntuación Preferencias", "preference_score"),
            ("Puntuación Huecos", "gap_score"),
            ("Carga Docente", "teacher_load_score"),
            ("Utilización Aulas", "room_utilization_score"),
            ("Distribución", "distribution_score"),
            ("Score Global (0-1)", "global_score")
        ]
        
        for label_text, key in metrics:
            lbl = QLabel("-")
            lbl.setStyleSheet("font-size: 16px;")
            self.form_layout.addRow(QLabel(label_text + ":"), lbl)
            self.labels[key] = lbl
            
        self.layout.addLayout(self.form_layout)
        
    def evaluate(self):
        db = next(get_db())
        evaluator = Evaluator(db)
        results = evaluator.evaluate()
        
        if results["hard_constraint_violations"] == 0 and results["global_score"] > 0:
            self.labels["status"].setText("FACTIBLE")
            self.labels["status"].setStyleSheet("color: green; font-weight: bold;")
        elif results["global_score"] == 0:
            self.labels["status"].setText("NO HAY HORARIO")
            self.labels["status"].setStyleSheet("color: gray;")
        else:
            self.labels["status"].setText("NO FACTIBLE")
            self.labels["status"].setStyleSheet("color: red; font-weight: bold;")
            
        for key, lbl in self.labels.items():
            if key in results:
                val = results[key]
                if "score" in key:
                    lbl.setText(f"{val * 100:.1f}%")
                else:
                    lbl.setText(str(val))
                        
    def optimize(self):
        from app.optimization.genetic_algorithm import GeneticAlgorithmOptimizer
        from PySide6.QtWidgets import QMessageBox
        
        self.optimize_btn.setEnabled(False)
        self.optimize_btn.setText("Optimizando...")
        
        db = next(get_db())
        optimizer = GeneticAlgorithmOptimizer(db)
        success, msg = optimizer.optimize()
        
        if success:
            QMessageBox.information(self, "Optimización", msg)
            self.evaluate()
        else:
            QMessageBox.warning(self, "Optimización", msg)
            
        self.optimize_btn.setEnabled(True)
        self.optimize_btn.setText("Optimizar (GA/LS)")

