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
                shift_val = asg.time_slot.shift.value if asg.time_slot and hasattr(asg.time_slot.shift, "value") else (str(asg.time_slot.shift) if asg.time_slot else "")
                day_val = asg.day.value if hasattr(asg.day, "value") else str(asg.day)
                subject_group_slots[s_id][g_id]["slots"].append({
                    "day": day_val,
                    "time_slot_id": asg.time_slot_id,
                    "shift": shift_val,
                    "start_time": asg.time_slot.start_time if asg.time_slot else None,
                    "end_time": asg.time_slot.end_time if asg.time_slot else None,
                    "assignment_id": asg.id
                })

        # Verify all selected subjects have at least one group
        missing_subjects = [s_id for s_id in selected_subject_ids if s_id not in subject_group_slots or not subject_group_slots[s_id]]
        if missing_subjects:
            return {"status": "FAILED", "msg": f"Algunas asignaturas no tienen grupos programados en el horario institucional.", "options": []}

        # 2. Conflict-Free Combinations Backtracking Search (Exhaustive & Unbiased)
        from itertools import combinations
        subject_list = list(selected_subject_ids)
        feasible_combinations = []
        max_combinations = 5000
        search_counter = [0]
        seen_combos = set()

        def add_feasible_combination(cur):
            combo_key = tuple(sorted(g_id for _, g_id, _ in cur))
            if combo_key not in seen_combos:
                seen_combos.add(combo_key)
                feasible_combinations.append(list(cur))

        # Dynamic Candidate Ordering: Prioritizes search direction based on user slider intent
        def get_candidate_groups(subj_id):
            candidates = list(subject_group_slots[subj_id].items())
            if not preferred_shift or shift_weight < 0.1:
                return candidates

            pref_val = preferred_shift.value if hasattr(preferred_shift, "value") else str(preferred_shift)
            pref_val_upper = pref_val.upper()

            def group_affinity(item):
                g_id, g_info = item
                score = 0
                g_name = g_info.get("group_name", "").upper()

                if pref_val_upper == "NOCHE" and ("NOCHE" in g_name or "G3" in g_name):
                    score += 25
                elif ("MAÑANA" in pref_val_upper or "MAANA" in pref_val_upper) and ("MAÑANA" in g_name or "MAANA" in g_name or "G1" in g_name):
                    score += 25
                elif pref_val_upper == "TARDE" and ("TARDE" in g_name or "G2" in g_name):
                    score += 25

                for s in g_info.get("slots", []):
                    s_shift = s["shift"].value if hasattr(s["shift"], "value") else str(s["shift"]).upper()
                    s_day = s["day"].value if hasattr(s["day"], "value") else str(s["day"]).upper()
                    if s_shift == pref_val_upper:
                        score += 5
                    elif pref_val_upper == "NOCHE" and ("SÁBADO" in s_day or "SABADO" in s_day) and ("NOCHE" in g_name or "G3" in g_name):
                        score += 5
                return score

            candidates.sort(key=group_affinity, reverse=True)
            return candidates

        # Multi-shift compact day search: actively discovers compact day allocations when student values free days
        all_days = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO"]
        if free_day_weight > 0.0:
            for target_days in [3, 4, 5]:
                if len(feasible_combinations) >= 600:
                    break
                for allowed_days in combinations(all_days, target_days):
                    if len(feasible_combinations) >= 600:
                        break
                    allowed_set = set(allowed_days)
                    if not all(any(all(s["day"] in allowed_set for s in g["slots"]) for g in subject_group_slots[sid].values()) for sid in subject_list):
                        continue

                    def search_day_subset(idx, cur, occ):
                        if len(feasible_combinations) >= max_combinations or search_counter[0] > 35000:
                            return
                        search_counter[0] += 1
                        if idx == len(subject_list):
                            add_feasible_combination(cur)
                            return
                        s_id = subject_list[idx]
                        for g_id, g_info in subject_group_slots[s_id].items():
                            if all(s["day"] in allowed_set for s in g_info["slots"]):
                                g_slots = {(s["day"], s["time_slot_id"]) for s in g_info["slots"]}
                                if not g_slots.intersection(occ):
                                    search_day_subset(idx + 1, cur + [(s_id, g_id, g_info)], occ.union(g_slots))
                    search_day_subset(0, [], set())

        # Main unbiased backtracking search
        def search_combinations(subj_idx, current_groups, occupied_slots):
            if len(feasible_combinations) >= max_combinations or search_counter[0] > 50000:
                return
            search_counter[0] += 1

            if subj_idx == len(subject_list):
                add_feasible_combination(current_groups)
                return

            current_subj = subject_list[subj_idx]
            for g_id, g_info in get_candidate_groups(current_subj):
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
                    if len(feasible_combinations) >= 30:
                        return
                    if s_idx == len(sub_list):
                        add_feasible_combination(c_groups)
                        return
                    c_s = sub_list[s_idx]
                    for g_id, g_info in get_candidate_groups(c_s):
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
        combos_data = []
        for combo in feasible_combinations:
            total_slots = sum(len(g_info["slots"]) for _, _, g_info in combo)

            # Metric A: Shift preference score
            matched_shift_slots = 0
            if preferred_shift:
                pref_val = preferred_shift.value if hasattr(preferred_shift, "value") else str(preferred_shift)
                pref_val_upper = pref_val.upper()
                for _, _, g_info in combo:
                    g_name = g_info.get("group_name", "").upper()
                    for s in g_info["slots"]:
                        s_shift = s["shift"].value if hasattr(s["shift"], "value") else str(s["shift"]).upper()
                        s_day = s["day"].value if hasattr(s["day"], "value") else str(s["day"]).upper()
                        if s_shift == pref_val_upper:
                            matched_shift_slots += 1
                        elif pref_val_upper == "NOCHE" and ("SÁBADO" in s_day or "SABADO" in s_day) and ("NOCHE" in g_name or "G3" in g_name):
                            matched_shift_slots += 1
                shift_score = (matched_shift_slots / total_slots) if total_slots > 0 else 1.0
            else:
                shift_score = 1.0

            # Metric B: Real gap detection (by chronological start and end times per day)
            day_slots = {}
            for _, _, g_info in combo:
                for s in g_info["slots"]:
                    day_slots.setdefault(s["day"], []).append(s)

            total_gaps = 0
            for d, slist in day_slots.items():
                if len(slist) > 1 and all(s.get("start_time") and s.get("end_time") for s in slist):
                    # Sort chronologically by start_time
                    s_sorted = sorted(slist, key=lambda x: x["start_time"])
                    for i in range(len(s_sorted) - 1):
                        curr_end = s_sorted[i]["end_time"]
                        next_start = s_sorted[i + 1]["start_time"]
                        gap_minutes = (next_start.hour * 60 + next_start.minute) - (curr_end.hour * 60 + curr_end.minute)
                        if gap_minutes > 0:
                            total_gaps += max(1, gap_minutes // 120)
                elif len(slist) > 1:
                    # Fallback to slot ID contiguous math if time objects are missing
                    slot_ids = sorted([s["time_slot_id"] for s in slist])
                    total_gaps += (slot_ids[-1] - slot_ids[0] + 1) - len(slot_ids)

            # Metric C: Free days score (out of 6 days Mon-Sat)
            free_days = 6 - len(day_slots)

            combos_data.append({
                "combo": combo,
                "total_slots": total_slots,
                "shift_score": shift_score,
                "total_gaps": total_gaps,
                "free_days": free_days,
                "days_used_count": len(day_slots),
                "completeness_score": len(combo) / len(selected_subject_ids)
            })

        min_gaps = min(cd["total_gaps"] for cd in combos_data)
        max_gaps = max(cd["total_gaps"] for cd in combos_data)
        min_free = min(cd["free_days"] for cd in combos_data)
        max_free = max(cd["free_days"] for cd in combos_data)

        scored_options = []
        for cd in combos_data:
            # Absolute gap score:
            # 1.0 (100%) if 0 gaps. Each gap slot reduces score by 10%
            gap_score = max(0.0, 1.0 - cd["total_gaps"] * 0.10)

            # Dynamic proportional free day score relative to the achievable benchmark
            if max_free > 0:
                free_day_score = cd["free_days"] / max_free
            else:
                free_day_score = 1.0 if cd["free_days"] == 0 else 0.0

            # Composite Score (0 - 100%)
            global_score = (
                cd["shift_score"] * shift_weight +
                gap_score * gap_weight +
                free_day_score * free_day_weight
            ) * cd["completeness_score"] * 100

            scored_options.append({
                "global_score": round(global_score, 1),
                "shift_score": round(cd["shift_score"] * 100, 1),
                "compactness_score": round(gap_score * 100, 1),
                "free_day_score": round(free_day_score * 100, 1),
                "total_gaps": cd["total_gaps"],
                "free_days": cd["free_days"],
                "max_possible_free_days": max_free,
                "min_possible_gaps": min_gaps,
                "days_used_count": cd["days_used_count"],
                "subjects_included": len(cd["combo"]),
                "total_requested": len(selected_subject_ids),
                "groups": cd["combo"]
            })

        # Multi-factor deterministic tie-breaking respecting student priority weights
        if shift_weight >= free_day_weight and shift_weight >= gap_weight:
            scored_options.sort(
                key=lambda x: (x["global_score"], x["shift_score"], x["free_days"], -x["total_gaps"]),
                reverse=True
            )
        elif free_day_weight >= gap_weight:
            scored_options.sort(
                key=lambda x: (x["global_score"], x["free_days"], -x["total_gaps"], x["shift_score"]),
                reverse=True
            )
        else:
            scored_options.sort(
                key=lambda x: (x["global_score"], -x["total_gaps"], x["free_days"], x["shift_score"]),
                reverse=True
            )

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
