from ortools.sat.python import cp_model
from app.database.models import Group, Teacher, Room, TimeSlot, TeacherAvailability, DayOfWeek, Config, TeacherSubjectPreference, TeacherType
from app.database.database import get_db
from datetime import time

class ScheduleSolver:
    def __init__(self, db, profile="balanced"):
        """
        CP-SAT Solver for Institutional Timetable Generation.
        :param db: SQLAlchemy database session
        :param profile: Optimization focus profile: 'balanced', 'preferences', 'compact', 'load_balance'
        """
        self.db = db
        self.profile = profile
        self.model = cp_model.CpModel()
        
        self.groups = self.db.query(Group).all()
        self.teachers = self.db.query(Teacher).all()
        self.rooms = self.db.query(Room).all()
        self.time_slots = self.db.query(TimeSlot).all()
        self.config = self.db.query(Config).first()
        
        # Filter days based on saturday allowance
        if self.config and not self.config.allow_saturday:
            self.days = [d for d in DayOfWeek if d != DayOfWeek.SATURDAY]
        else:
            self.days = list(DayOfWeek)
        
        self.teacher_avail = self.db.query(TeacherAvailability).all()
        self.teacher_avail_dict = {}
        for ta in self.teacher_avail:
            self.teacher_avail_dict[(ta.teacher_id, ta.day.value, ta.time_slot_id)] = True

        # Teacher Subject Preferences map: (teacher_id, subject_id) -> score (1..5)
        self.teacher_prefs = self.db.query(TeacherSubjectPreference).all()
        self.pref_map = {}
        for tp in self.teacher_prefs:
            self.pref_map[(tp.teacher_id, tp.subject_id)] = tp.preference_score

        # Candidate teachers per subject (affinity >= 2 or fallback to all teachers)
        self.subject_teachers = {}
        for g in self.groups:
            s_id = g.subject_id
            if s_id not in self.subject_teachers:
                cands = [t for t in self.teachers if (t.id, s_id) in self.pref_map and self.pref_map[(t.id, s_id)] >= 2]
                if not cands:
                    cands = [t for t in self.teachers if (t.id, s_id) in self.pref_map]
                if not cands:
                    cands = self.teachers
                self.subject_teachers[s_id] = cands

        self.variables = {}
        # assign[(g.id, t.id, r.id, d.value, s.id)] = boolean variable
    
    def build_model(self):
        # 1. Variables Creation (Pruned by Availability, Sábados hasta las 17:00, y Capacidad de Aulas)
        for g in self.groups:
            valid_rooms = [r for r in self.rooms if r.capacity >= g.expected_students]
            if not valid_rooms:
                valid_rooms = self.rooms # Fallback
            for t in self.teachers:
                for r in valid_rooms:
                    for d in self.days:
                        for s in self.time_slots:
                            # Saturday restriction: max until 17:00 (5:00 PM)
                            if d == DayOfWeek.SATURDAY and s.end_time > time(17, 0):
                                continue

                            # Availability check
                            if (t.id, d.value, s.id) in self.teacher_avail_dict:
                                var_name = f"g{g.id}_t{t.id}_r{r.id}_d{d.name}_s{s.id}"
                                self.variables[(g.id, t.id, r.id, d.value, s.id)] = self.model.NewBoolVar(var_name)
        
        # 2. Hard Constraints
        
        # Each group must have exactly its required hours (slots = hours / 2)
        for g in self.groups:
            required_slots = max(1, g.subject.hours_per_week // 2) if g.subject else 2
            vars_for_group = [
                self.variables[k] for k in self.variables if k[0] == g.id
            ]
            if vars_for_group:
                self.model.Add(sum(vars_for_group) == required_slots)
            
        # A group can only have at most one slot at the same (day, time_slot)
        for g in self.groups:
            for d in self.days:
                for s in self.time_slots:
                    g_vars = [
                        self.variables[k] for k in self.variables 
                        if k[0] == g.id and k[3] == d.value and k[4] == s.id
                    ]
                    if g_vars:
                        self.model.AddAtMostOne(g_vars)
                    
        # A teacher can only teach at most one group at the same (day, time_slot)
        for t in self.teachers:
            for d in self.days:
                for s in self.time_slots:
                    t_vars = [
                        self.variables[k] for k in self.variables 
                        if k[1] == t.id and k[3] == d.value and k[4] == s.id
                    ]
                    if t_vars:
                        self.model.AddAtMostOne(t_vars)
                    
        # A room can only host at most one group at the same (day, time_slot)
        for r in self.rooms:
            for d in self.days:
                for s in self.time_slots:
                    r_vars = [
                        self.variables[k] for k in self.variables 
                        if k[2] == r.id and k[3] == d.value and k[4] == s.id
                    ]
                    if r_vars:
                        self.model.AddAtMostOne(r_vars)
                    
        # Teacher max load constraint (in hours): 42h FT, 21h PT, 23h Cátedra
        for t in self.teachers:
            max_hours = self.config.full_time_hours if self.config else 42
            if t.teacher_type == TeacherType.PART_TIME:
                max_hours = self.config.part_time_hours if self.config else 21
            elif t.teacher_type == TeacherType.CATEDRA:
                max_hours = self.config.catedra_hours if self.config else 23
                
            max_slots = max_hours // 2
            t_all_vars = [
                self.variables[k] for k in self.variables if k[1] == t.id
            ]
            if t_all_vars:
                self.model.Add(sum(t_all_vars) <= max_slots)

        # 3. Soft Constraints / Multi-Objective Function
        pref_w = self.config.pref_weight if self.config else 0.35
        w_pref = max(1, int(pref_w * 10))
        if self.profile == "preferences":
            w_pref = 10
        elif self.profile == "compact":
            w_pref = 3
        elif self.profile == "load_balance":
            w_pref = 4

        group_map = {g.id: g for g in self.groups}
        objective_terms = []
        for (g_id, t_id, r_id, d_val, s_id), var in self.variables.items():
            g = group_map.get(g_id)
            if g:
                score = self.pref_map.get((t_id, g.subject_id), 3)
                objective_terms.append((score * w_pref) * var)

        if objective_terms:
            self.model.Maximize(sum(objective_terms))
            
    def solve(self, time_limit_seconds=15.0):
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(time_limit_seconds)
        solver.parameters.num_workers = 4
        status = solver.Solve(self.model)
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            assignments = []
            for key, var in self.variables.items():
                if solver.Value(var) == 1:
                    g_id, t_id, r_id, d_val, s_id = key
                    assignments.append({
                        "group_id": g_id,
                        "teacher_id": t_id,
                        "room_id": r_id,
                        "day": d_val,
                        "time_slot_id": s_id
                    })
            status_desc = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
            return {
                "status": "SUCCESS", 
                "solver_status": status_desc,
                "assignments": assignments, 
                "msg": f"Solución {status_desc} encontrada con éxito ({len(assignments)} clases asignadas)."
            }
        else:
            return {"status": "FAILED", "assignments": [], "msg": "No se encontró una solución factible con las restricciones actuales."}

