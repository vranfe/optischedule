from app.database.models import (
    ScheduleAssignment, StudentPreference, Group, Config, Teacher, 
    TeacherSubjectPreference, DayOfWeek, TimeSlot, TeacherType, Room
)
from app.database.database import get_db
from datetime import time

class Evaluator:
    def __init__(self, db):
        self.db = db
        self.config = self.db.query(Config).first()
        self.teachers = self.db.query(Teacher).all()
        self.groups = self.db.query(Group).all()
        self.rooms = self.db.query(Room).all()
        self.slots = self.db.query(TimeSlot).all()
        
        self.group_map = {g.id: g for g in self.groups}
        self.room_map = {r.id: r for r in self.rooms}
        self.teacher_map = {t.id: t for t in self.teachers}
        self.slot_map = {s.id: s for s in self.slots}
        
    def evaluate(self, assignments=None):
        if assignments is None:
            assignments = self.db.query(ScheduleAssignment).all()

        if not assignments:
            return {
                "is_feasible": False,
                "status": "NO HAY HORARIO",
                "hard_constraint_violations": 0,
                "preference_score": 0.0,
                "gap_score": 0.0,
                "teacher_load_score": 0.0,
                "room_utilization_score": 0.0,
                "distribution_score": 0.0,
                "global_score": 0.0
            }
            
        hard_violations = self.check_hard_constraints(assignments)
        is_feasible = (hard_violations == 0)
        
        pref_score = self.calculate_preference_score(assignments)
        gap_score = self.calculate_gap_score(assignments)
        load_score = self.calculate_teacher_load_score(assignments)
        room_score = self.calculate_room_utilization_score(assignments)
        dist_score = self.calculate_distribution_score(assignments)
        
        # Calculate global quality using configured weights
        w_pref = self.config.pref_weight if self.config else 0.35
        w_gap = self.config.gap_weight if self.config else 0.25
        w_load = self.config.load_weight if self.config else 0.20
        w_dist = self.config.dist_weight if self.config else 0.10
        w_room = self.config.room_weight if self.config else 0.10
        
        total_w = w_pref + w_gap + w_load + w_room + w_dist
        if total_w > 0:
            w_pref /= total_w
            w_gap /= total_w
            w_load /= total_w
            w_room /= total_w
            w_dist /= total_w
            
        global_score = (
            pref_score * w_pref +
            gap_score * w_gap +
            load_score * w_load +
            room_score * w_room +
            dist_score * w_dist
        ) if is_feasible else 0.0
        
        return {
            "is_feasible": is_feasible,
            "status": "FACTIBLE" if is_feasible else f"NO FACTIBLE ({hard_violations} violaciones)",
            "hard_constraint_violations": hard_violations,
            "preference_score": round(pref_score * 100, 1),
            "gap_score": round(gap_score * 100, 1),
            "teacher_load_score": round(load_score * 100, 1),
            "room_utilization_score": round(room_score * 100, 1),
            "distribution_score": round(dist_score * 100, 1),
            "global_score": round(global_score * 100, 1)
        }

    def _get_asg_field(self, asg, field):
        if isinstance(asg, dict):
            val = asg.get(field)
            if hasattr(val, "value"):
                return val.value
            return val
        val = getattr(asg, field, None)
        if hasattr(val, "value"):
            return val.value
        return val

    def check_hard_constraints(self, assignments):
        violations = 0
        teacher_slots = set()
        room_slots = set()
        group_slots = set()
        teacher_hours = {}
        
        ft_max = self.config.full_time_hours if self.config else 42
        pt_max = self.config.part_time_hours if self.config else 21
        cat_max = self.config.catedra_hours if self.config else 23

        for asg in assignments:
            t_id = self._get_asg_field(asg, "teacher_id")
            r_id = self._get_asg_field(asg, "room_id")
            g_id = self._get_asg_field(asg, "group_id")
            day_val = self._get_asg_field(asg, "day")
            slot_id = self._get_asg_field(asg, "time_slot_id")

            # 1. Teacher overlap
            t_key = (t_id, day_val, slot_id)
            if t_key in teacher_slots:
                violations += 1
            teacher_slots.add(t_key)
            
            # 2. Room overlap
            r_key = (r_id, day_val, slot_id)
            if r_key in room_slots:
                violations += 1
            room_slots.add(r_key)
            
            # 3. Group overlap
            g_key = (g_id, day_val, slot_id)
            if g_key in group_slots:
                violations += 1
            group_slots.add(g_key)
            
            # 4. Room capacity
            room = self.room_map.get(r_id)
            group = self.group_map.get(g_id)
            if room and group and room.capacity < group.expected_students:
                violations += 1
                
            # 5. Saturday restriction (up to 17:00 / 5:00 PM)
            slot = self.slot_map.get(slot_id)
            if (day_val == DayOfWeek.SATURDAY.value or day_val == "SÁBADO") and slot:
                if slot.end_time > time(17, 0):
                    violations += 1

            # Count hours (each assignment = 2h)
            teacher_hours[t_id] = teacher_hours.get(t_id, 0) + 2

        # 6. Check teacher max load
        for t in self.teachers:
            assigned = teacher_hours.get(t.id, 0)
            limit = ft_max if t.teacher_type == TeacherType.FULL_TIME else (pt_max if t.teacher_type == TeacherType.PART_TIME else cat_max)
            if assigned > limit:
                violations += (assigned - limit) // 2

        return violations

    def calculate_preference_score(self, assignments):
        if not assignments:
            return 0.0

        prefs = self.db.query(TeacherSubjectPreference).all()
        pref_map = {(p.teacher_id, p.subject_id): p.preference_score for p in prefs}
        
        total_possible = len(assignments) * 5
        actual_score = 0
        
        for asg in assignments:
            t_id = self._get_asg_field(asg, "teacher_id")
            g_id = self._get_asg_field(asg, "group_id")
            group = self.group_map.get(g_id)
            s_id = group.subject_id if group else None
            score = pref_map.get((t_id, s_id), 3)
            actual_score += score

        return min(1.0, actual_score / total_possible) if total_possible > 0 else 0.85

    def calculate_gap_score(self, assignments):
        teacher_daily_slots = {}
        for asg in assignments:
            t_id = self._get_asg_field(asg, "teacher_id")
            day_val = self._get_asg_field(asg, "day")
            slot_id = self._get_asg_field(asg, "time_slot_id")
            key = (t_id, day_val)
            if key not in teacher_daily_slots:
                teacher_daily_slots[key] = []
            teacher_daily_slots[key].append(slot_id)

        total_days = len(teacher_daily_slots)
        if total_days == 0:
            return 1.0

        gap_count = 0
        for slots_list in teacher_daily_slots.values():
            sorted_slots = sorted(slots_list)
            for i in range(len(sorted_slots) - 1):
                diff = sorted_slots[i+1] - sorted_slots[i]
                if diff > 1:
                    gap_count += (diff - 1)

        return max(0.2, 1.0 - (gap_count / (total_days * 2.0)))

    def calculate_teacher_load_score(self, assignments):
        ft_max = self.config.full_time_hours if self.config else 42
        pt_max = self.config.part_time_hours if self.config else 21
        cat_max = self.config.catedra_hours if self.config else 23

        t_hours = {}
        for asg in assignments:
            t_id = self._get_asg_field(asg, "teacher_id")
            t_hours[t_id] = t_hours.get(t_id, 0) + 2

        occupations = []
        for t in self.teachers:
            hrs = t_hours.get(t.id, 0)
            limit = ft_max if t.teacher_type == TeacherType.FULL_TIME else (pt_max if t.teacher_type == TeacherType.PART_TIME else cat_max)
            occupations.append(min(1.0, hrs / limit) if limit > 0 else 1.0)

        avg_occ = sum(occupations) / len(occupations) if occupations else 1.0
        return avg_occ

    def calculate_room_utilization_score(self, assignments):
        total_cap = 0
        used_cap = 0
        for asg in assignments:
            r_id = self._get_asg_field(asg, "room_id")
            g_id = self._get_asg_field(asg, "group_id")
            room = self.room_map.get(r_id)
            group = self.group_map.get(g_id)
            if room and group:
                total_cap += room.capacity
                used_cap += group.expected_students
        if total_cap == 0:
            return 0.85
        return min(1.0, used_cap / total_cap)

    def calculate_distribution_score(self, assignments):
        day_counts = {}
        for asg in assignments:
            d = self._get_asg_field(asg, "day")
            day_counts[d] = day_counts.get(d, 0) + 1
        
        if not day_counts:
            return 0.0
        counts = list(day_counts.values())
        avg = sum(counts) / len(counts)
        variance = sum((c - avg) ** 2 for c in counts) / len(counts)
        return max(0.5, 1.0 - (variance / (avg ** 2 + 1e-5)))

