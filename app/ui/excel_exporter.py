import os
import csv
from PySide6.QtWidgets import QFileDialog, QMessageBox

def export_schedule_dialog(parent, default_filename, table_widget, assignments=None, title="Horario Institucional UMB"):
    if not default_filename.endswith(".xlsx"):
        base_name = os.path.splitext(default_filename)[0]
        default_filename = f"{base_name}.xlsx"

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
                _export_to_excel(file_path, table_widget, assignments, title)
            except ImportError:
                # If openpyxl is not installed, fallback to CSV with notice
                csv_path = file_path.rsplit(".", 1)[0] + ".csv"
                _export_to_csv(csv_path, table_widget, assignments, title)
                QMessageBox.information(
                    parent,
                    "Exportación Realizada (Formato CSV)",
                    f"El horario se ha exportado con éxito en formato estructurado a:\n\n{csv_path}"
                )
                return
        else:
            if not file_path.lower().endswith(".csv"):
                file_path += ".csv"
            _export_to_csv(file_path, table_widget, assignments, title)

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

def _export_to_excel(file_path, table_widget, assignments, title):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws_matrix = wb.active
    ws_matrix.title = "Matriz Semanal"
    ws_matrix.views.sheetView[0].showGridLines = True

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

    shift_fills = {
        "MAÑANA": PatternFill(start_color="F0F9FF", end_color="F0F9FF", fill_type="solid"),
        "TARDE": PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid"),
        "NOCHE": PatternFill(start_color="FAF5FF", end_color="FAF5FF", fill_type="solid"),
    }
    default_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

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

    if assignments:
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
                row_vals = [
                    asg.get("id", row_idx - 1),
                    asg.get("day", ""),
                    asg.get("shift", ""),
                    asg.get("start_time", ""),
                    asg.get("end_time", ""),
                    asg.get("subject_name", ""),
                    asg.get("semester", ""),
                    asg.get("group_name", ""),
                    asg.get("teacher_name", ""),
                    asg.get("teacher_type", ""),
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
                cell = ws_detail.cell(row=row_idx, column=c_idx, value=val)
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
    with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([f"=== {title.upper()} ==="])
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

        if assignments:
            writer.writerow([])
            writer.writerow(["=== DETALLE INDIVIDUAL DE ASIGNACIONES ==="])
            writer.writerow(["ID", "Día", "Jornada", "Hora Inicio", "Hora Fin", "Asignatura", "Semestre", "Grupo", "Docente", "Tipo Contrato", "Aula", "Tipo Aula"])
            for idx, asg in enumerate(assignments, start=1):
                if isinstance(asg, dict):
                    writer.writerow([
                        asg.get("id", idx),
                        asg.get("day", ""),
                        asg.get("shift", ""),
                        asg.get("start_time", ""),
                        asg.get("end_time", ""),
                        asg.get("subject_name", ""),
                        asg.get("semester", ""),
                        asg.get("group_name", ""),
                        asg.get("teacher_name", ""),
                        asg.get("teacher_type", ""),
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
                            getattr(subj, "semester_id", "") if subj else "",
                            getattr(group, "name", "") if group else "",
                            getattr(teacher, "name", "") if teacher else "",
                            teacher.teacher_type.value if teacher and hasattr(getattr(teacher, "teacher_type", None), "value") else "",
                            getattr(room, "name", "") if room else "",
                            getattr(room, "room_type", "") if room else ""
                        ])
                    except Exception:
                        writer.writerow([getattr(asg, "id", idx), "", "", "", "", "", "", "", "", "", "", ""])

