import random
from app.database.database import get_db
from app.database.models import ScheduleAssignment, TimeSlot, Room
from app.optimization.evaluator import Evaluator

class GeneticAlgorithmOptimizer:
    def __init__(self, db, population_size=10, generations=5):
        self.db = db
        self.population_size = population_size
        self.generations = generations
        self.base_assignments = self.db.query(ScheduleAssignment).all()
        self.slots = self.db.query(TimeSlot).all()
        self.rooms = self.db.query(Room).all()
        
    def optimize(self):
        if not self.base_assignments:
            return False, "No hay horario base para optimizar."
            
        print("Iniciando algoritmo genético...")
        best_score = self._evaluate_db()
        print(f"Score inicial: {best_score}")
        
        # En un MVP real, aquí serializaríamos los assignments en cromosomas, 
        # haríamos cruces y mutaciones (cambiando slots o aulas validando constraints).
        # Por simplicidad del MVP de escritorio directo, haremos una simulación 
        # de Búsqueda Local Aleatoria (Local Search / Mutación) directa en memoria.
        
        improved = False
        for gen in range(self.generations):
            # Mutar: Intentar cambiar de aula a un assignment aleatorio
            if not self.base_assignments:
                break
                
            asg_to_mutate = random.choice(self.base_assignments)
            original_room_id = asg_to_mutate.room_id
            
            # Intentar con otra aula que tenga capacidad
            valid_rooms = [r for r in self.rooms if r.capacity >= asg_to_mutate.group.expected_students and r.id != original_room_id]
            
            if valid_rooms:
                new_room = random.choice(valid_rooms)
                
                # Comprobar conflicto de aula en el mismo slot
                conflict = self.db.query(ScheduleAssignment).filter(
                    ScheduleAssignment.room_id == new_room.id,
                    ScheduleAssignment.day == asg_to_mutate.day,
                    ScheduleAssignment.time_slot_id == asg_to_mutate.time_slot_id
                ).first()
                
                if not conflict:
                    # Aplicar mutación
                    asg_to_mutate.room_id = new_room.id
                    self.db.commit()
                    
                    new_score = self._evaluate_db()
                    if new_score > best_score:
                        best_score = new_score
                        improved = True
                        print(f"Mejora en generación {gen}: {best_score}")
                    else:
                        # Revertir
                        asg_to_mutate.room_id = original_room_id
                        self.db.commit()
                        
        print(f"Score final: {best_score}")
        return True, "Optimización completada."
        
    def _evaluate_db(self):
        evaluator = Evaluator(self.db)
        res = evaluator.evaluate()
        if res["hard_constraint_violations"] > 0:
            return 0.0
        return res["global_score"]
