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

        # 0. Credit Limit & Subject Count Validation (Enterprise Business Rule: Max 22 credits, Max 10 subjects)
        selected_subjects = self.db.query(Subject).filter(Subject.id.in_(selected_subject_ids)).all()
        total_credits = sum(s.credits if hasattr(s, "credits") and s.credits else 3 for s in selected_subjects)
        
        if total_credits > 22:
            return {
                "status": "FAILED", 
                "msg": f"Has superado el límite institucional de créditos permitidos ({total_credits} / 22 créditos). Por favor desmarca asignaturas para continuar.", 
                "options": []
            }

        if len(selected_subject_ids) > 10:
            return {
                "status": "FAILED", 
                "msg": f"Has seleccionado {len(selected_subject_ids)} asignaturas. El límite máximo de inscripción es de 10 asignaturas por periodo.", 
                "options": []
            }

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

        # 2. Backtracking Search with Branch-and-Bound Safety (Fast & Non-blocking)
        subject_list = list(selected_subject_ids)
        feasible_combinations = []
        max_combinations = 60
        search_counter = [0]

        def search_combinations(subj_idx, current_groups, occupied_slots):
            if len(feasible_combinations) >= max_combinations or search_counter[0] > 3000:
                return
            search_counter[0] += 1

            if subj_idx == len(subject_list):
                feasible_combinations.append(list(current_groups))
                return

            current_subj = subject_list[subj_idx]
            for g_id, g_info in subject_group_slots[current_subj].items():
                g_slots = {(s["day"], s["time_slot_id"]) for s in g_info["slots"]}
                if not g_slots.intersection(occupied_slots):
                    search_combinations(
                        subj_idx + 1,
                        current_groups + [(current_subj, g_id, g_info)],
                        occupied_slots.union(g_slots)
                    )

        search_combinations(0, [], set())

        # If no full combination exists for all subjects, evaluate best nearest subset (at most 1 drop)
        if not feasible_combinations and len(subject_list) > 1:
            from itertools import combinations
            subset_size = len(subject_list) - 1
            for sub_list in combinations(subject_list, subset_size):
                def search_subset(s_idx, c_groups, occ_slots):
                    if len(feasible_combinations) >= 10:
                        return
                    if s_idx == len(sub_list):
                        feasible_combinations.append(list(c_groups))
                        return
                    c_s = sub_list[s_idx]
                    for g_id, g_info in subject_group_slots[c_s].items():
                        g_slots = {(s["day"], s["time_slot_id"]) for s in g_info["slots"]}
                        if not g_slots.intersection(occ_slots):
                            search_subset(
                                s_idx + 1,
                                c_groups + [(c_s, g_id, g_info)],
                                occ_slots.union(g_slots)
                            )
                search_subset(0, [], set())
                if feasible_combinations:
                    break

        if not feasible_combinations:
            return {
                "status": "INFEASIBLE",
                "msg": "No existe una combinación factible sin cruces de horario para las asignaturas seleccionadas.",
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

            avg_classes_per_day = total_slots / len(days_used) if days_used else 1
            compactness_score = min(1.0, avg_classes_per_day / 3.0)

            # Free days score (max 6 days)
            free_days = 6 - len(days_used)
            free_day_score = min(1.0, free_days / 3.0)

            # Completeness penalty if subset
            completeness_score = len(combo) / len(selected_subject_ids)

            # Composite Score (0 - 100%)
            global_score = (
                shift_score * shift_weight +
                compactness_score * gap_weight +
                free_day_score * free_day_weight
            ) * completeness_score * 100

            scored_options.append({
                "global_score": round(global_score, 1),
                "shift_score": round(shift_score * 100, 1),
                "compactness_score": round(compactness_score * 100, 1),
                "free_days": free_days,
                "days_used_count": len(days_used),
                "subjects_included": len(combo),
                "total_requested": len(selected_subject_ids),
                "groups": combo
            })

        # Sort by best score descending
        scored_options.sort(key=lambda x: x["global_score"], reverse=True)
        top_options = scored_options[:3]

        all_included = (top_options[0]["subjects_included"] == len(selected_subject_ids))
        status_msg = (
            f"Se encontraron {len(scored_options)} combinaciones factibles sin cruce de horario."
            if all_included else
            f"Se encontraron combinaciones parciales ({top_options[0]['subjects_included']}/{len(selected_subject_ids)} materias) debido a cruces en el horario institucional."
        )

        return {
            "status": "SUCCESS",
            "total_feasible": len(scored_options),
            "msg": status_msg,
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
