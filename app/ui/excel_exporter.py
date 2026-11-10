import os
import re
import csv
from PySide6.QtWidgets import QFileDialog, QMessageBox

def sanitize_filename(name):
    """Sanitize filename to be safe across Windows and POSIX filesystems."""
    # Remove characters illegal on Windows: < > : " / \ | ? *
    name = re.sub(r'[<>:"/\\|?*]', '_', str(name))
    # Keep printable non-control chars and strip whitespace/dots
    name = "".join(c for c in name if c.isprintable()).strip(". ")
    return name or "Horario_UMB"

def _sanitize_cell_value(val):
    if hasattr(val, "value"):
        return str(val.value)
    if isinstance(val, (int, float, str, bool)) or val is None:
        return val
    return str(val)

def _extract_semester_id(asg):
    if isinstance(asg, dict):
        s_id = asg.get("semester_id")
        if s_id is not None and isinstance(s_id, int):
            return s_id
        sem_str = str(asg.get("semester", ""))
        digits = re.findall(r'\d+', sem_str)
        if digits:
            return int(digits[0])
    else:
        group = getattr(asg, "group", None)
        subj = getattr(group, "subject", None) if group else None
        if subj and getattr(subj, "semester_id", None) is not None:
            return subj.semester_id
    return None

def _enrich_assignments_if_needed(assignments):
    if not assignments:
        return []
    
    needs_enrichment = False
    for a in assignments:
        if isinstance(a, dict) and not a.get("subject_name") and (a.get("group_id") or a.get("time_slot_id")):
            needs_enrichment = True
            break
            
    if not needs_enrichment:
        return assignments

    try:
        from app.database.database import SessionLocal
        from app.database.models import Group, Teacher, Room, TimeSlot
        from sqlalchemy.orm import joinedload
        
        db = SessionLocal()
        try:
            groups = {g.id: g for g in db.query(Group).options(joinedload(Group.subject)).all()}
            teachers = {t.id: t for t in db.query(Teacher).all()}
            rooms = {r.id: r for r in db.query(Room).all()}
            slots = {s.id: s for s in db.query(TimeSlot).all()}
            
            enriched = []
            for a in assignments:
                if isinstance(a, dict):
                    ac = dict(a)
                    g = groups.get(ac.get("group_id"))
                    t = teachers.get(ac.get("teacher_id"))
                    r = rooms.get(ac.get("room_id"))
                    s = slots.get(ac.get("time_slot_id"))
                    
                    if not ac.get("subject_name") and g and g.subject:
                        ac["subject_name"] = g.subject.name
                    if not ac.get("group_name") and g:
                        ac["group_name"] = g.name
                    if not ac.get("semester") and g and g.subject:
                        ac["semester"] = f"Semestre {g.subject.semester_id}"
                        ac["semester_id"] = g.subject.semester_id
                    elif ac.get("semester") and isinstance(ac.get("semester"), int):
                        ac["semester_id"] = ac.get("semester")
                        ac["semester"] = f"Semestre {ac.get('semester')}"
                    if not ac.get("teacher_name") and t:
                        ac["teacher_name"] = t.name
                    if not ac.get("teacher_type") and t:
                        ac["teacher_type"] = t.teacher_type.value if hasattr(t.teacher_type, "value") else str(t.teacher_type)
                    if not ac.get("room_name") and r:
                        ac["room_name"] = r.name
                    if not ac.get("room_type") and r:
                        ac["room_type"] = r.room_type
                    if s:
                        if not ac.get("shift"):
                            ac["shift"] = s.shift.value if hasattr(s.shift, "value") else str(s.shift)
                        if not ac.get("start_time"):
                            ac["start_time"] = s.start_time.strftime('%H:%M') if s.start_time else ""
                        if not ac.get("end_time"):
                            ac["end_time"] = s.end_time.strftime('%H:%M') if s.end_time else ""
                    if hasattr(ac.get("shift"), "value"):
                        ac["shift"] = ac["shift"].value
                    elif ac.get("shift") is not None:
                        ac["shift"] = str(ac["shift"])

                    if hasattr(ac.get("day"), "value"):
                        ac["day"] = ac["day"].value
                    elif ac.get("day") is not None:
                        ac["day"] = str(ac["day"])

                    if hasattr(ac.get("teacher_type"), "value"):
                        ac["teacher_type"] = ac["teacher_type"].value
                    elif ac.get("teacher_type") is not None:
                        ac["teacher_type"] = str(ac["teacher_type"])

                    enriched.append(ac)
                else:
                    enriched.append(a)
            return enriched
        finally:
            db.close()
    except Exception:
        return assignments

def export_schedule_dialog(parent, default_filename, table_widget, assignments=None, title="Horario Institucional UMB", is_institutional=None):
    if is_institutional is None:
        title_lower = title.lower()
        file_lower = default_filename.lower()
        if "docente" in title_lower or "docente" in file_lower or "estudiante" in title_lower or "estudiante" in file_lower:
            is_institutional = False
        elif "institucional" in title_lower or "institucional" in file_lower:
            is_institutional = True
        else:
            is_institutional = False

    base_name = os.path.splitext(default_filename)[0]
    safe_base = sanitize_filename(base_name)
    default_filename = f"{safe_base}.xlsx"

    file_path, selected_filter = QFileDialog.getSaveFileName(
        parent,
        f"Exportar Horario - {title}",
        default_filename,
        "Libro de Excel (*.xlsx);;Archivo CSV (*.csv)"
    )

    if not file_path:
        return

    try:
        if file_path.lower().endswith(".xlsx") or "xlsx" in selected_filter.lower():
            if not file_path.lower().endswith(".xlsx"):
                file_path += ".xlsx"
            try:
                _export_to_excel(file_path, table_widget, assignments, title, is_institutional=is_institutional)
            except Exception as ex_excel:
                # If Excel creation fails for any reason (e.g. missing submodule), fallback to CSV
                csv_path = file_path.rsplit(".", 1)[0] + ".csv"
                _export_to_csv(csv_path, table_widget, assignments, title, is_institutional=is_institutional)
                QMessageBox.information(
                    parent,
                    "Exportación Realizada (Formato CSV)",
                    f"El horario se ha exportado con éxito en formato estructurado a:\n\n{csv_path}\n\n(Nota: Se usó formato CSV compatible con Excel: {ex_excel})"
                )
                return
        else:
            if not file_path.lower().endswith(".csv"):
                file_path += ".csv"
            _export_to_csv(file_path, table_widget, assignments, title, is_institutional=is_institutional)

        QMessageBox.information(
            parent,
            "Exportación Exitosa",
            f"El horario se ha exportado con éxito en formato de tabla a:\n\n{file_path}"
        )
    except Exception as e:
        QMessageBox.critical(
            parent,
            "Error de Exportación",
            f"No se pudo guardar el archivo:\n\n{e}"
        )

def _enrich_assignments_if_needed(assignments):
    if not assignments:
        return []
    
    needs_enrichment = False
    for a in assignments:
        if isinstance(a, dict) and not a.get("subject_name") and (a.get("group_id") or a.get("time_slot_id")):
            needs_enrichment = True
            break
            
    if not needs_enrichment:
        return assignments

    try:
        from app.database.database import SessionLocal
        from app.database.models import Group, Teacher, Room, TimeSlot
        from sqlalchemy.orm import joinedload
        
        db = SessionLocal()
        try:
            groups = {g.id: g for g in db.query(Group).options(joinedload(Group.subject)).all()}
            teachers = {t.id: t for t in db.query(Teacher).all()}
            rooms = {r.id: r for r in db.query(Room).all()}
            slots = {s.id: s for s in db.query(TimeSlot).all()}
            
            enriched = []
            for a in assignments:
                if isinstance(a, dict):
                    ac = dict(a)
                    g = groups.get(ac.get("group_id"))
                    t = teachers.get(ac.get("teacher_id"))
                    r = rooms.get(ac.get("room_id"))
                    s = slots.get(ac.get("time_slot_id"))
                    
                    if not ac.get("subject_name") and g and g.subject:
                        ac["subject_name"] = g.subject.name
                    if not ac.get("group_name") and g:
                        ac["group_name"] = g.name
                    if not ac.get("semester") and g and g.subject:
                        ac["semester"] = f"Semestre {g.subject.semester_id}"
                        ac["semester_id"] = g.subject.semester_id
                    elif ac.get("semester") and isinstance(ac.get("semester"), int):
                        ac["semester_id"] = ac.get("semester")
                        ac["semester"] = f"Semestre {ac.get('semester')}"
                    if not ac.get("teacher_name") and t:
                        ac["teacher_name"] = t.name
                    if not ac.get("teacher_type") and t:
                        ac["teacher_type"] = t.teacher_type.value if hasattr(t.teacher_type, "value") else str(t.teacher_type)
                    if not ac.get("room_name") and r:
                        ac["room_name"] = r.name
                    if not ac.get("room_type") and r:
                        ac["room_type"] = r.room_type
                    if s:
                        if not ac.get("shift"):
                            ac["shift"] = s.shift.value if hasattr(s.shift, "value") else str(s.shift)
                        if not ac.get("start_time"):
                            ac["start_time"] = s.start_time.strftime('%H:%M') if s.start_time else ""
                        if not ac.get("end_time"):
                            ac["end_time"] = s.end_time.strftime('%H:%M') if s.end_time else ""
                    if hasattr(ac.get("shift"), "value"):
                        ac["shift"] = ac["shift"].value
                    elif ac.get("shift") is not None:
                        ac["shift"] = str(ac["shift"])

                    if hasattr(ac.get("day"), "value"):
                        ac["day"] = ac["day"].value
                    elif ac.get("day") is not None:
                        ac["day"] = str(ac["day"])

                    if hasattr(ac.get("teacher_type"), "value"):
                        ac["teacher_type"] = ac["teacher_type"].value
                    elif ac.get("teacher_type") is not None:
                        ac["teacher_type"] = str(ac["teacher_type"])

                    enriched.append(ac)
                else:
                    enriched.append(a)
            return enriched
        finally:
            db.close()
    except Exception:
        return assignments

def _sanitize_cell_value(val):
    if hasattr(val, "value"):
        return str(val.value)
    if isinstance(val, (int, float, str, bool)) or val is None:
        return val
    return str(val)

def _extract_semester_id(asg):
    if isinstance(asg, dict):
        s_id = asg.get("semester_id")
        if s_id is not None and isinstance(s_id, int):
            return s_id
        sem_str = str(asg.get("semester", ""))
        digits = re.findall(r'\d+', sem_str)
        if digits:
            return int(digits[0])
    else:
        group = getattr(asg, "group", None)
        subj = getattr(group, "subject", None) if group else None
        if subj and getattr(subj, "semester_id", None) is not None:
            return subj.semester_id
    return None

def _export_to_excel(file_path, table_widget, assignments, title):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    assignments = _enrich_assignments_if_needed(assignments)

    wb = openpyxl.Workbook()

    title_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    title_font = Font(name="Segoe UI", size=14, bold=True, color="FFFFFF")
    
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")

    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )

    shift_fills = {
        "MAÑANA": PatternFill(start_color="F0F9FF", end_color="F0F9FF", fill_type="solid"),
        "TARDE": PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid"),
        "NOCHE": PatternFill(start_color="FAF5FF", end_color="FAF5FF", fill_type="solid"),
    }
    default_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    # Detect multi-semester assignments
    sem_ids = []
    if assignments:
        raw_sems = set(_extract_semester_id(a) for a in assignments)
        sem_ids = sorted([s for s in raw_sems if s is not None])

    # Case 1: Multiple Semesters -> Create separate sheets per semester
    if len(sem_ids) > 1:
        from app.database.database import SessionLocal
        from app.database.models import TimeSlot, ShiftType, DayOfWeek

        db = SessionLocal()
        try:
            db_slots = db.query(TimeSlot).all()
        finally:
            db.close()

        SHIFT_ORDER = {
            ShiftType.MORNING: 0,
            ShiftType.AFTERNOON: 1,
            ShiftType.NIGHT: 2,
            "MAÑANA": 0,
            "TARDE": 1,
            "NOCHE": 2
        }
        sorted_slots = sorted(db_slots, key=lambda s: (SHIFT_ORDER.get(s.shift, 99), s.start_time))
        days = [d.value for d in DayOfWeek]

        for s_idx, sem in enumerate(sem_ids):
            ws = wb.active if s_idx == 0 else wb.create_sheet(title=f"Semestre {sem}")
            ws.title = f"Semestre {sem}"
            ws.views.sheetView[0].showGridLines = True

            col_count = len(days) + 1
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=col_count)
            t_cell = ws.cell(row=1, column=1, value=f"OPTISCHEDULE UMB - HORARIO SEMESTRE {sem}")
            t_cell.fill = title_fill
            t_cell.font = title_font
            t_cell.alignment = Alignment(horizontal="center", vertical="center")
            ws.row_dimensions[1].height = 36

            headers = ["Franja Horaria / Jornada"] + days
            for col_i, h_text in enumerate(headers, start=1):
                c = ws.cell(row=2, column=col_i, value=h_text)
                c.fill = header_fill
                c.font = header_font
                c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                c.border = thin_border
            ws.row_dimensions[2].height = 26

            # Filter assignments for this semester
            sem_asgs = [a for a in assignments if _extract_semester_id(a) == sem]

            for r_i, slot in enumerate(sorted_slots):
                excel_row = r_i + 3
                shift_label = slot.shift.value if hasattr(slot.shift, "value") else str(slot.shift)
                time_range = f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
                row_label = f"{shift_label} - {time_range}"

                rh_cell = ws.cell(row=excel_row, column=1, value=row_label)
                rh_cell.fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
                rh_cell.font = Font(name="Segoe UI", size=10, bold=True, color="1E293B")
                rh_cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                rh_cell.border = thin_border

                max_lines = 1
                for c_i, d_name in enumerate(days):
                    col_idx = c_i + 2
                    cell = ws.cell(row=excel_row, column=col_idx)
                    cell.border = thin_border
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

                    # Match assignment
                    matching = [
                        a for a in sem_asgs
                        if (a.get("day") == d_name or (hasattr(a.get("day"), "value") and a.get("day").value == d_name)) and
                           (a.get("time_slot_id") == slot.id or a.get("start_time") == slot.start_time.strftime('%H:%M'))
                    ]

                    if matching:
                        texts = []
                        for m in matching:
                            texts.append(f"📘 {m.get('subject_name', '')} ({m.get('group_name', '')})\n👨‍🏫 {m.get('teacher_name', '')}\n📍 {m.get('room_name', '')}")
                        cell_val = "\n\n─────────────\n\n".join(texts)
                        cell.value = cell_val

                        lines = cell_val.count("\n") + 1
                        if lines > max_lines:
                            max_lines = lines

                        applied_fill = shift_fills.get(shift_label.upper(), default_fill)
                        cell.fill = applied_fill
                        cell.font = Font(name="Segoe UI", size=9, bold=True, color="0F172A")
                    else:
                        cell.value = ""
                        cell.fill = default_fill

                ws.row_dimensions[excel_row].height = max(38, max_lines * 16)

            ws.column_dimensions["A"].width = 24
            for c_i in range(len(days)):
                col_letter = get_column_letter(c_i + 2)
                ws.column_dimensions[col_letter].width = 32

    # Case 2: Single Semester or table_widget provided
    else:
        ws_matrix = wb.active
        single_sem_title = f"Semestre {sem_ids[0]}" if (len(sem_ids) == 1) else "Matriz Semanal"
        ws_matrix.title = single_sem_title
        ws_matrix.views.sheetView[0].showGridLines = True

        col_count = max(1, table_widget.columnCount() + 1)
        ws_matrix.merge_cells(start_row=1, start_column=1, end_row=1, end_column=col_count)
        title_cell = ws_matrix.cell(row=1, column=1, value=f"OPTISCHEDULE UMB - {title.upper()}")
        title_cell.fill = title_fill
        title_cell.font = title_font
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws_matrix.row_dimensions[1].height = 36

        headers = ["Franja Horaria / Jornada"] + [table_widget.horizontalHeaderItem(c).text() if table_widget.horizontalHeaderItem(c) else f"Día {c+1}" for c in range(table_widget.columnCount())]
        for col_idx, h_text in enumerate(headers, start=1):
            c = ws_matrix.cell(row=2, column=col_idx, value=h_text)
            c.fill = header_fill
            c.font = header_font
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = thin_border
        ws_matrix.row_dimensions[2].height = 26

        for r in range(table_widget.rowCount()):
            excel_row = r + 3
            v_item = table_widget.verticalHeaderItem(r)
            row_label = v_item.text().replace("\n", " - ") if v_item else f"Franja {r+1}"
            
            rh_cell = ws_matrix.cell(row=excel_row, column=1, value=row_label)
            rh_cell.fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
            rh_cell.font = Font(name="Segoe UI", size=10, bold=True, color="1E293B")
            rh_cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            rh_cell.border = thin_border

            max_lines = 1
            for c in range(table_widget.columnCount()):
                item = table_widget.item(r, c)
                cell_val = item.text().strip() if item and item.text() else ""
                cell = ws_matrix.cell(row=excel_row, column=c + 2, value=cell_val)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

                if cell_val:
                    lines = cell_val.count("\n") + 1
                    if lines > max_lines:
                        max_lines = lines
                    
                    applied_fill = default_fill
                    for s_key, s_f in shift_fills.items():
                        if s_key in row_label.upper():
                            applied_fill = s_f
                            break
                    cell.fill = applied_fill
                    cell.font = Font(name="Segoe UI", size=9, bold=True, color="0F172A")
                else:
                    cell.fill = default_fill

            ws_matrix.row_dimensions[excel_row].height = max(38, max_lines * 16)

        ws_matrix.column_dimensions["A"].width = 24
        for c in range(table_widget.columnCount()):
            col_letter = get_column_letter(c + 2)
            ws_matrix.column_dimensions[col_letter].width = 30

        ws_matrix.column_dimensions["A"].width = 24
        for c in range(table_widget.columnCount()):
            col_letter = get_column_letter(c + 2)
            ws_matrix.column_dimensions[col_letter].width = 30

    # Detail sheet ONLY when is_institutional is True!
    # "la separación de páginas solo debe ocurrir en la exportación del horario institucional"
    if is_institutional and assignments:
        ws_detail = wb.create_sheet(title="Detalle de Clases")
        ws_detail.views.sheetView[0].showGridLines = True

        detail_headers = [
            "ID", "Día", "Jornada", "Hora Inicio", "Hora Fin", 
            "Asignatura", "Semestre", "Grupo", "Docente", "Tipo Contrato", "Aula", "Tipo Aula"
        ]
        
        for c_idx, h_text in enumerate(detail_headers, start=1):
            cell = ws_detail.cell(row=1, column=c_idx, value=h_text)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
        ws_detail.row_dimensions[1].height = 26

        alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

        for row_idx, asg in enumerate(assignments, start=2):
            if isinstance(asg, dict):
                shift_val = asg.get("shift", "")
                if hasattr(shift_val, "value"):
                    shift_val = shift_val.value
                day_val = asg.get("day", "")
                if hasattr(day_val, "value"):
                    day_val = day_val.value
                t_type = asg.get("teacher_type", "")
                if hasattr(t_type, "value"):
                    t_type = t_type.value

                row_vals = [
                    asg.get("id", row_idx - 1),
                    day_val,
                    shift_val,
                    asg.get("start_time", ""),
                    asg.get("end_time", ""),
                    asg.get("subject_name", ""),
                    asg.get("semester", ""),
                    asg.get("group_name", ""),
                    asg.get("teacher_name", ""),
                    t_type,
                    asg.get("room_name", ""),
                    asg.get("room_type", "")
                ]
            else:
                try:
                    slot = getattr(asg, "time_slot", None)
                    group = getattr(asg, "group", None)
                    subj = getattr(group, "subject", None) if group else None
                    teacher = getattr(asg, "teacher", None)
                    room = getattr(asg, "room", None)
                    day_val = asg.day.value if hasattr(getattr(asg, "day", None), "value") else str(getattr(asg, "day", ""))

                    shift_val = slot.shift.value if slot and hasattr(getattr(slot, "shift", None), "value") else (str(getattr(slot, "shift", "")) if slot else "")
                    start_t = slot.start_time.strftime('%H:%M') if slot and getattr(slot, "start_time", None) else ""
                    end_t = slot.end_time.strftime('%H:%M') if slot and getattr(slot, "end_time", None) else ""
                    subj_name = getattr(subj, "name", "") if subj else ""
                    sem_str = f"Semestre {getattr(subj, 'semester_id', '')}" if subj and getattr(subj, 'semester_id', None) is not None else ""
                    group_name = getattr(group, "name", "") if group else ""
                    teacher_name = getattr(teacher, "name", "") if teacher else ""
                    t_type = teacher.teacher_type.value if teacher and hasattr(getattr(teacher, "teacher_type", None), "value") else (str(getattr(teacher, "teacher_type", "")) if teacher else "")
                    room_name = getattr(room, "name", "") if room else ""
                    room_type = getattr(room, "room_type", "") if room else ""

                    row_vals = [
                        getattr(asg, "id", row_idx - 1),
                        day_val,
                        shift_val,
                        start_t,
                        end_t,
                        subj_name,
                        sem_str,
                        group_name,
                        teacher_name,
                        t_type,
                        room_name,
                        room_type
                    ]
                except Exception:
                    row_vals = [getattr(asg, "id", row_idx - 1), "", "", "", "", "", "", "", "", "", "", ""]

            is_even = (row_idx % 2 == 0)
            r_fill = alt_fill if is_even else default_fill

            for c_idx, val in enumerate(row_vals, start=1):
                clean_val = _sanitize_cell_value(val)
                cell = ws_detail.cell(row=row_idx, column=c_idx, value=clean_val)
                cell.fill = r_fill
                cell.border = thin_border
                cell.font = Font(name="Segoe UI", size=10)
                cell.alignment = Alignment(horizontal="center" if c_idx in [1, 2, 3, 4, 5, 7, 8, 11, 12] else "left", vertical="center")
            ws_detail.row_dimensions[row_idx].height = 22

        for col in ws_detail.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws_detail.column_dimensions[col_letter].width = max(12, min(36, max_len + 3))

    wb.save(file_path)

def _export_to_csv(file_path, table_widget, assignments, title):
    assignments = _enrich_assignments_if_needed(assignments)
    sem_ids = []
    if assignments:
        raw_sems = set(_extract_semester_id(a) for a in assignments)
        sem_ids = sorted([s for s in raw_sems if s is not None])

    with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([f"=== {title.upper()} ==="])
        
        if len(sem_ids) > 1:
            from app.database.database import SessionLocal
            from app.database.models import TimeSlot, ShiftType, DayOfWeek

            db = SessionLocal()
            try:
                db_slots = db.query(TimeSlot).all()
            finally:
                db.close()

            SHIFT_ORDER = {
                ShiftType.MORNING: 0,
                ShiftType.AFTERNOON: 1,
                ShiftType.NIGHT: 2,
                "MAÑANA": 0,
                "TARDE": 1,
                "NOCHE": 2
            }
            sorted_slots = sorted(db_slots, key=lambda s: (SHIFT_ORDER.get(s.shift, 99), s.start_time))
            days = [d.value for d in DayOfWeek]

            for sem in sem_ids:
                writer.writerow([])
                writer.writerow([f"=== HORARIO INSTITUCIONAL - SEMESTRE {sem} ==="])
                writer.writerow(["Franja Horaria / Jornada"] + days)
                sem_asgs = [a for a in assignments if _extract_semester_id(a) == sem]

                for slot in sorted_slots:
                    shift_label = slot.shift.value if hasattr(slot.shift, "value") else str(slot.shift)
                    time_range = f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
                    row_data = [f"{shift_label} - {time_range}"]
                    for d_name in days:
                        matching = [
                            a for a in sem_asgs
                            if (a.get("day") == d_name or (hasattr(a.get("day"), "value") and a.get("day").value == d_name)) and
                               (a.get("time_slot_id") == slot.id or a.get("start_time") == slot.start_time.strftime('%H:%M'))
                        ]
                        if matching:
                            texts = [f"{m.get('subject_name', '')} ({m.get('group_name', '')}) | {m.get('teacher_name', '')} | {m.get('room_name', '')}" for m in matching]
                            row_data.append(" // ".join(texts))
                        else:
                            row_data.append("---")
                    writer.writerow(row_data)
        else:
            headers = ["Franja Horaria / Jornada"] + [table_widget.horizontalHeaderItem(c).text() if table_widget.horizontalHeaderItem(c) else f"Día {c+1}" for c in range(table_widget.columnCount())]
            writer.writerow(headers)

            for r in range(table_widget.rowCount()):
                v_item = table_widget.verticalHeaderItem(r)
                row_label = v_item.text().replace("\n", " ") if v_item else f"Franja {r+1}"
                row_data = [row_label]
                for c in range(table_widget.columnCount()):
                    item = table_widget.item(r, c)
                    text = item.text().replace("\n", " | ") if item and item.text() else "---"
                    row_data.append(text)
                writer.writerow(row_data)

        if is_institutional and assignments:
            writer.writerow([])
            writer.writerow(["=== DETALLE INDIVIDUAL DE ASIGNACIONES ==="])
            writer.writerow(["ID", "Día", "Jornada", "Hora Inicio", "Hora Fin", "Asignatura", "Semestre", "Grupo", "Docente", "Tipo Contrato", "Aula", "Tipo Aula"])
            for idx, asg in enumerate(assignments, start=1):
                if isinstance(asg, dict):
                    shift_val = asg.get("shift", "")
                    if hasattr(shift_val, "value"):
                        shift_val = shift_val.value
                    day_val = asg.get("day", "")
                    if hasattr(day_val, "value"):
                        day_val = day_val.value
                    t_type = asg.get("teacher_type", "")
                    if hasattr(t_type, "value"):
                        t_type = t_type.value

                    writer.writerow([
                        asg.get("id", idx),
                        day_val,
                        shift_val,
                        asg.get("start_time", ""),
                        asg.get("end_time", ""),
                        asg.get("subject_name", ""),
                        asg.get("semester", ""),
                        asg.get("group_name", ""),
                        asg.get("teacher_name", ""),
                        t_type,
                        asg.get("room_name", ""),
                        asg.get("room_type", "")
                    ])
                else:
                    try:
                        slot = getattr(asg, "time_slot", None)
                        group = getattr(asg, "group", None)
                        subj = getattr(group, "subject", None) if group else None
                        teacher = getattr(asg, "teacher", None)
                        room = getattr(asg, "room", None)
                        day_val = asg.day.value if hasattr(getattr(asg, "day", None), "value") else str(getattr(asg, "day", ""))
                        writer.writerow([
                            getattr(asg, "id", idx),
                            day_val,
                            slot.shift.value if slot and hasattr(getattr(slot, "shift", None), "value") else (str(getattr(slot, "shift", "")) if slot else ""),
                            slot.start_time.strftime('%H:%M') if slot and getattr(slot, "start_time", None) else "",
                            slot.end_time.strftime('%H:%M') if slot and getattr(slot, "end_time", None) else "",
                            getattr(subj, "name", "") if subj else "",
                            f"Semestre {getattr(subj, 'semester_id', '')}" if subj else "",
                            getattr(group, "name", "") if group else "",
                            getattr(teacher, "name", "") if teacher else "",
                            teacher.teacher_type.value if teacher and hasattr(getattr(teacher, "teacher_type", None), "value") else "",
                            getattr(room, "name", "") if room else "",
                            getattr(room, "room_type", "") if room else ""
                        ])
                    except Exception:
                        writer.writerow([getattr(asg, "id", idx), "", "", "", "", "", "", "", "", "", "", ""])
