from ortools.sat.python import cp_model
from app.database.models import Group, Teacher, Room, TimeSlot, TeacherAvailability, DayOfWeek, Config, TeacherSubjectPreference, TeacherType, ShiftType
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

        # Candidate teachers per subject (strictly matched by academic knowledge area, no preference starvation)
        self.subject_teachers = {}
        for g in self.groups:
            s_id = g.subject_id
            if s_id not in self.subject_teachers:
                subj = g.subject
                subj_area = getattr(subj, "knowledge_area", None)
                domain_teachers = [t for t in self.teachers if not subj_area or getattr(t, "knowledge_area", None) == subj_area]
                if not domain_teachers:
                    domain_teachers = self.teachers
                self.subject_teachers[s_id] = domain_teachers

        self.variables = {}
        # assign[(g.id, t.id, r.id, d.value, s.id)] = boolean variable
    
    def build_model(self):
        from collections import defaultdict
        import re

        # Index dictionaries for O(1) constraint generation
        group_vars = defaultdict(list)
        group_day_slot_vars = defaultdict(list)
        teacher_day_slot_vars = defaultdict(list)
        room_day_slot_vars = defaultdict(list)
        teacher_vars = defaultdict(list)
        cohort_day_slot_vars = defaultdict(list)

        # 1. Variables Creation (Pruned by Availability, Sábados hasta las 17:00, y Capacidad de Aulas)
        for g in self.groups:
            valid_rooms = [r for r in self.rooms if r.capacity >= g.expected_students]
            if not valid_rooms:
                valid_rooms = self.rooms # Fallback

            subj_area = getattr(g.subject, "knowledge_area", "") if g.subject else ""
            if "Software" in subj_area or "Redes" in subj_area or "Hardware" in subj_area:
                pref_rooms = [r for r in valid_rooms if r.room_type == "Laboratorio"]
                other_rooms = [r for r in valid_rooms if r.room_type != "Laboratorio"]
            else:
                pref_rooms = [r for r in valid_rooms if r.room_type == "Normal"]
                other_rooms = [r for r in valid_rooms if r.room_type != "Normal"]

            ordered_rooms = pref_rooms + other_rooms
            offset = g.id % max(1, len(ordered_rooms))
            rotated = ordered_rooms[offset:] + ordered_rooms[:offset]
            candidate_rooms = rotated[:8]
            candidate_teachers = self.subject_teachers.get(g.subject_id, self.teachers)
            cohort = g.name.split("-")[0].strip() if "-" in g.name else "G1"
            sem_id = g.subject.semester_id if g.subject else 1

            for t in candidate_teachers:
                for r in candidate_rooms:
                    for d in self.days:
                        for s in self.time_slots:
                            # Saturday restriction: max until 17:00 (5:00 PM)
                            if d == DayOfWeek.SATURDAY and s.end_time > time(17, 0):
                                continue

                            # Shift restriction based on group denomination with regex boundary safety
                            g_name_lower = g.name.lower()
                            is_morning = "mañana" in g_name_lower or "manana" in g_name_lower or bool(re.search(r'\bg1(\.\d+)?\b', g_name_lower))
                            is_afternoon = "tarde" in g_name_lower or bool(re.search(r'\bg2(\.\d+)?\b', g_name_lower))
                            is_night = "noche" in g_name_lower or bool(re.search(r'\bg3(\.\d+)?\b', g_name_lower))

                            if is_morning:
                                if s.shift != ShiftType.MORNING:
                                    continue
                            elif is_afternoon:
                                if s.shift != ShiftType.AFTERNOON:
                                    continue
                            elif is_night:
                                if d != DayOfWeek.SATURDAY and s.shift != ShiftType.NIGHT:
                                    continue
                                if d == DayOfWeek.SATURDAY and s.end_time > time(17, 0):
                                    continue

                            # Availability check
                            if (t.id, d.value, s.id) in self.teacher_avail_dict:
                                var_name = f"g{g.id}_t{t.id}_r{r.id}_d{d.name}_s{s.id}"
                                var = self.model.NewBoolVar(var_name)
                                self.variables[(g.id, t.id, r.id, d.value, s.id)] = var
                                group_vars[g.id].append(var)
                                group_day_slot_vars[(g.id, d.value, s.id)].append(var)
                                teacher_day_slot_vars[(t.id, d.value, s.id)].append(var)
                                room_day_slot_vars[(r.id, d.value, s.id)].append(var)
                                teacher_vars[t.id].append(var)
                                cohort_day_slot_vars[(sem_id, cohort, d.value, s.id)].append(var)
        
        # 2. Hard Constraints
        
        # Each group must have exactly its required hours (slots = hours / 2)
        for g in self.groups:
            required_slots = max(1, g.subject.hours_per_week // 2) if g.subject else 2
            vars_for_group = group_vars[g.id]
            if vars_for_group:
                self.model.Add(sum(vars_for_group) == required_slots)
            
        # A group can only have at most one slot at the same (day, time_slot)
        for g_vars in group_day_slot_vars.values():
            if len(g_vars) > 1:
                self.model.AddAtMostOne(g_vars)

        # A teacher can only teach at most one group at the same (day, time_slot)
        for t_vars in teacher_day_slot_vars.values():
            if len(t_vars) > 1:
                self.model.AddAtMostOne(t_vars)
                    
        # A room can only host at most one group at the same (day, time_slot)
        for r_vars in room_day_slot_vars.values():
            if len(r_vars) > 1:
                self.model.AddAtMostOne(r_vars)

        # Academic Cohort Non-Collision Constraint:
        # Groups belonging to the same cohort of the same semester cannot overlap in time.
        # This guarantees regular students in that semester can enroll in their preferred shift without schedule collisions.
        for c_vars in cohort_day_slot_vars.values():
            if len(c_vars) > 1:
                self.model.AddAtMostOne(c_vars)
                    
        # Teacher max load constraint (in hours): 42h FT, 21h PT, 23h Cátedra
        for t in self.teachers:
            max_hours = self.config.full_time_hours if self.config else 42
            if t.teacher_type == TeacherType.PART_TIME:
                max_hours = self.config.part_time_hours if self.config else 21
            elif t.teacher_type == TeacherType.CATEDRA:
                max_hours = self.config.catedra_hours if self.config else 23
                
            max_slots = max_hours // 2
            t_all_vars = teacher_vars[t.id]
            if t_all_vars:
                self.model.Add(sum(t_all_vars) <= max_slots)

        # Teacher consecutive hours constraint (Institutional Config: max_consecutive_hours)
        max_consec_slots = (self.config.max_consecutive_hours // 2) if (self.config and self.config.max_consecutive_hours) else 2
        daily_slots = sorted(self.time_slots, key=lambda sl: sl.start_time)
        for t in self.teachers:
            for d in self.days:
                for i in range(len(daily_slots) - max_consec_slots):
                    window_slots = daily_slots[i:i + max_consec_slots + 1]
                    window_vars = []
                    for ws in window_slots:
                        window_vars.extend(teacher_day_slot_vars[(t.id, d.value, ws.id)])
                    if len(window_vars) > max_consec_slots:
                        self.model.Add(sum(window_vars) <= max_consec_slots)

        # 3. Soft Constraints & Multi-Objective Function
        # We balance: 
        # (A) Teacher Subject Preferences
        # (B) Teacher Workload Balance & Underload (Subcarga) Minimization for Salaried Faculty
        pref_w = self.config.pref_weight if self.config else 0.35
        load_w = self.config.load_weight if self.config else 0.20
        
        w_pref = max(1, int(pref_w * 10))
        w_load = max(1, int(load_w * 10))
        
        if self.profile == "preferences":
            w_pref = 10
            w_load = 1
        elif self.profile == "compact":
            w_pref = 3
            w_load = 3
        elif self.profile == "load_balance":
            w_pref = 2
            w_load = 12

        group_map = {g.id: g for g in self.groups}
        teacher_map = {t.id: t for t in self.teachers}
        objective_terms = []

        for (g_id, t_id, r_id, d_val, s_id), var in self.variables.items():
            g = group_map.get(g_id)
            t = teacher_map.get(t_id)
            if g and t:
                # Preference score (1..5)
                pref_score = self.pref_map.get((t_id, g.subject_id), 3)
                
                # Salaried faculty weight to avoid underload (Tiempo Completo = 3, Medio Tiempo = 2, Cátedra = 1)
                faculty_salary_weight = 3 if t.teacher_type == TeacherType.FULL_TIME else (2 if t.teacher_type == TeacherType.PART_TIME else 1)
                
                term_coeff = (pref_score * w_pref) + (faculty_salary_weight * w_load)
                objective_terms.append(term_coeff * var)

        if objective_terms:
            self.model.Maximize(sum(objective_terms))
            
    def solve(self, time_limit_seconds=15.0):
        if not self.variables:
            self.build_model()
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(time_limit_seconds)
        solver.parameters.num_workers = 8
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

