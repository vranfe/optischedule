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
            ("Estado de Factibilidad", "status"),
            ("Violaciones Restricciones Duras", "hard_constraint_violations"),
            ("Satisfacción de Preferencias", "preference_score"),
            ("Minimización de Huecos (Ventanas)", "gap_score"),
            ("Balance de Carga Docente", "teacher_load_score"),
            ("Utilización Eficiente de Aulas", "room_utilization_score"),
            ("Distribución Semanal de Clases", "distribution_score"),
            ("Calidad Global Ponderada (0 - 100%)", "global_score")
        ]
        
        for label_text, key in metrics:
            lbl = QLabel("-")
            lbl.setStyleSheet("font-size: 15px; color: #1e293b; font-weight: 600;")
            self.form_layout.addRow(QLabel(f"<b>{label_text}:</b>"), lbl)
            self.labels[key] = lbl
            
        self.layout.addLayout(self.form_layout)
        
    def evaluate(self):
        db = next(get_db())
        evaluator = Evaluator(db)
        results = evaluator.evaluate()
        
        if results["hard_constraint_violations"] == 0 and results["global_score"] > 0:
            self.labels["status"].setText("FACTIBLE (0 violaciones)")
            self.labels["status"].setStyleSheet("color: #16a34a; font-weight: bold; font-size: 16px;")
        elif results["global_score"] == 0 and results["status"] == "NO HAY HORARIO":
            self.labels["status"].setText("NO HAY HORARIO GENERADO")
            self.labels["status"].setStyleSheet("color: #64748b; font-weight: bold; font-size: 16px;")
        else:
            self.labels["status"].setText(f"NO FACTIBLE ({results['hard_constraint_violations']} violaciones)")
            self.labels["status"].setStyleSheet("color: #dc2626; font-weight: bold; font-size: 16px;")
            
        for key, lbl in self.labels.items():
            if key == "status":
                continue
            if key in results:
                val = results[key]
                if "score" in key and isinstance(val, (int, float)):
                    lbl.setText(f"{val:.1f}%")
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

