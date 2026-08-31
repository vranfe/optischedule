from app.database.models import ScheduleAssignment, Group, Subject, ShiftType, DayOfWeek, StudentEnrollment
from app.database.database import get_db

class StudentScheduleOptimizer:
    def __init__(self, db, student_id):
        self.db = db
        self.student_id = student_id

    def optimize_student_schedule(self, selected_subject_ids, preferred_shift=None, shift_weight=0.5, gap_weight=0.3, free_day_weight=0.2):
        """
        Finds all conflict-free group combinations for the chosen subjects
        and ranks them by student preferences.
        """
        if not selected_subject_ids:
            return {"status": "FAILED", "msg": "No seleccionaste ninguna asignatura.", "options": []}

        # 1. Fetch all assignments grouped by group_id
        all_assignments = self.db.query(ScheduleAssignment).all()
        if not all_assignments:
            return {"status": "FAILED", "msg": "No hay un horario institucional generado aún por la universidad.", "options": []}

        # Group assignments by subject_id -> group_id -> list of slots (day, slot_id, shift, start_time)
        subject_group_slots = {}
        for asg in all_assignments:
            s_id = asg.group.subject_id
            if s_id in selected_subject_ids:
                if s_id not in subject_group_slots:
                    subject_group_slots[s_id] = {}
                g_id = asg.group_id
                if g_id not in subject_group_slots[s_id]:
                    subject_group_slots[s_id][g_id] = {
                        "group_name": asg.group.name,
                        "subject_name": asg.group.subject.name,
                        "teacher_name": asg.teacher.name,
                        "room_name": asg.room.name,
                        "slots": []
                    }
                subject_group_slots[s_id][g_id]["slots"].append({
                    "day": asg.day.value,
                    "time_slot_id": asg.time_slot_id,
                    "shift": asg.time_slot.shift if asg.time_slot else None,
                    "start_time": asg.time_slot.start_time if asg.time_slot else None,
                    "end_time": asg.time_slot.end_time if asg.time_slot else None,
                    "assignment_id": asg.id
                })

        # Verify all selected subjects have at least one group
        missing_subjects = [s_id for s_id in selected_subject_ids if s_id not in subject_group_slots or not subject_group_slots[s_id]]
        if missing_subjects:
            return {"status": "FAILED", "msg": f"Algunas asignaturas no tienen grupos programados en el horario institucional.", "options": []}

        # 2. Backtracking / Combinatorial Search for conflict-free schedules
        subject_list = list(selected_subject_ids)
        feasible_combinations = []

        def search_combinations(subj_idx, current_groups, occupied_slots):
            if subj_idx == len(subject_list):
                feasible_combinations.append(list(current_groups))
                return

            current_subj = subject_list[subj_idx]
            for g_id, g_info in subject_group_slots[current_subj].items():
                # Check for collision
                g_slots = {(s["day"], s["time_slot_id"]) for s in g_info["slots"]}
                if not g_slots.intersection(occupied_slots):
                    # No collision, proceed
                    search_combinations(
                        subj_idx + 1,
                        current_groups + [(current_subj, g_id, g_info)],
                        occupied_slots.union(g_slots)
                    )

        search_combinations(0, [], set())

        if not feasible_combinations:
            return {
                "status": "INFEASIBLE",
                "msg": "No existe una combinación factible sin cruces de horario para las asignaturas seleccionadas. Prueba seleccionando otros grupos o materias.",
                "options": []
            }

        # 3. Score and rank each feasible combination
        scored_options = []
        for combo in feasible_combinations:
            total_slots = sum(len(g_info["slots"]) for _, _, g_info in combo)
            
            # Metric A: Shift preference score
            matched_shift_slots = 0
            if preferred_shift:
                for _, _, g_info in combo:
                    for s in g_info["slots"]:
                        if s["shift"] == preferred_shift:
                            matched_shift_slots += 1
                shift_score = (matched_shift_slots / total_slots) if total_slots > 0 else 1.0
            else:
                shift_score = 1.0

            # Metric B: Day gaps & compact schedule score
            days_used = set()
            day_slot_counts = {}
            for _, _, g_info in combo:
                for s in g_info["slots"]:
                    d = s["day"]
                    days_used.add(d)
                    day_slot_counts[d] = day_slot_counts.get(d, 0) + 1

            # Gaps calculation: more classes per day = fewer gaps/trips
            avg_classes_per_day = total_slots / len(days_used) if days_used else 1
            compactness_score = min(1.0, avg_classes_per_day / 3.0)

            # Free days score (max 6 days)
            free_days = 6 - len(days_used)
            free_day_score = min(1.0, free_days / 3.0)

            # Composite Score (0 - 100%)
            global_score = (
                shift_score * shift_weight +
                compactness_score * gap_weight +
                free_day_score * free_day_weight
            ) * 100

            scored_options.append({
                "global_score": round(global_score, 1),
                "shift_score": round(shift_score * 100, 1),
                "compactness_score": round(compactness_score * 100, 1),
                "free_days": free_days,
                "days_used_count": len(days_used),
                "groups": combo
            })

        # Sort by best score descending
        scored_options.sort(key=lambda x: x["global_score"], reverse=True)
        top_options = scored_options[:3]

        return {
            "status": "SUCCESS",
            "total_feasible": len(scored_options),
            "msg": f"Se encontraron {len(scored_options)} combinaciones factibles sin cruce de horario.",
            "options": top_options
        }

    def save_selected_schedule(self, selected_group_ids):
        """Persists the chosen student schedule into database enrollments"""
        self.db.query(StudentEnrollment).filter_by(student_id=self.student_id).delete()
        for g_id in selected_group_ids:
            enrollment = StudentEnrollment(student_id=self.student_id, group_id=g_id)
            self.db.add(enrollment)
        self.db.commit()
        return True
