from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QLabel, QPushButton, QHBoxLayout, QLineEdit, QHeaderView, 
    QFrame, QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QComboBox, QCheckBox, QApplication
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from sqlalchemy import Enum as SAEnum
from app.database.database import get_db

class GenericTableView(QWidget):
    def __init__(self, title, headers, model_class, field_keys, enum_mappings=None, read_only_keys=None):
        """
        Generic CRUD Table Widget.
        :param title: Display name of the entity (e.g., "Estudiantes", "Docentes")
        :param headers: Column titles (e.g., ["ID", "Nombre", "Semestre", ...])
        :param model_class: SQLAlchemy Model Class (e.g., Student, Teacher, Subject, Group, Room)
        :param field_keys: Model attribute names matching headers (e.g., ["id", "name", "semester_id", ...])
        :param enum_mappings: Optional dict of {field_name: enum_class} for Enum fields
        :param read_only_keys: Optional list of field keys that are read-only (computed or uneditable)
        """
        super().__init__()
        self.title = title
        self.headers = headers
        self.model_class = model_class
        self.field_keys = field_keys
        self.enum_mappings = enum_mappings or {}
        self.read_only_keys = list(read_only_keys) if read_only_keys is not None else ["id"]
        self.raw_data = []
        self.is_loading = False
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header Card
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px;")
        header_layout = QHBoxLayout(header_card)
        
        title_label = QLabel(f"Gestión de {title}")
        title_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #1e3a8a;")
        header_layout.addWidget(title_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar...")
        self.search_input.setFixedWidth(180)
        self.search_input.setStyleSheet("color: #0f172a; background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px;")
        self.search_input.textChanged.connect(self.filter_data)
        header_layout.addWidget(self.search_input)

        self.count_badge = QLabel("0 registros")
        self.count_badge.setStyleSheet("font-size: 12px; font-weight: bold; color: #2563eb; padding: 4px 8px; background-color: #dbeafe; border-radius: 4px;")
        header_layout.addWidget(self.count_badge)

        # CRUD Action Buttons
        add_btn = QPushButton("➕ Nuevo")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold; padding: 7px 12px; border-radius: 6px;")
        add_btn.clicked.connect(self.add_record_dialog)
        header_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Editar")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; padding: 7px 12px; border-radius: 6px;")
        edit_btn.clicked.connect(self.edit_selected_record)
        header_layout.addWidget(edit_btn)

        del_btn = QPushButton("🗑️ Eliminar")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 7px 12px; border-radius: 6px;")
        del_btn.clicked.connect(self.delete_selected_record)
        header_layout.addWidget(del_btn)

        self.refresh_btn = QPushButton("🔄 Recargar")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 7px 12px; border-radius: 6px;")
        self.refresh_btn.clicked.connect(self.load_data)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(header_card)
        
        # Info note
        note_lbl = QLabel("💡 <i>Tip: Puedes hacer doble clic en una celda para editarla directamente o seleccionar una fila y presionar '✏️ Editar'. Los cambios se guardan inmediatamente en la base de datos.</i>")
        note_lbl.setStyleSheet("font-size: 11px; color: #64748b; margin-left: 5px;")
        layout.addWidget(note_lbl)

        # Table with Item-based Smooth Scrolling and Complete Visibility
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self._apply_headers()
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.verticalHeader().setMinimumSectionSize(32)
        
        # Smart Column Sizing: Compact ID, stretched name / descriptive cols
        for c_i in range(len(headers)):
            if c_i == 0:
                self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            elif c_i == 1 or (len(headers) > 4 and c_i == 2):
                self.table.horizontalHeader().setSectionResizeMode(c_i, QHeaderView.Stretch)
            else:
                self.table.horizontalHeader().setSectionResizeMode(c_i, QHeaderView.ResizeToContents)

        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #cbd5e1;
                background-color: #ffffff;
                color: #0f172a;
                font-size: 13px;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
            }
            QHeaderView {
                background-color: #1e293b;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 8px 12px;
                font-weight: 800;
                font-size: 12px;
                border: none;
                border-right: 1px solid #334155;
                border-bottom: 2px solid #4f46e5;
            }
            QTableWidget::item:selected {
                background-color: #e0e7ff;
                color: #1e3a8a;
            }
        """)
        self.table.itemChanged.connect(self.on_cell_edited)
        layout.addWidget(self.table, 1)
        
        self.load_data()

    def _apply_headers(self):
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.horizontalHeader().setVisible(True)
        
    def load_data(self):
        self.is_loading = True
        self.refresh_btn.setText("⏳ Cargando...")
        self.refresh_btn.setEnabled(False)
        self.count_badge.setText("⏳ Consultando...")
        QApplication.processEvents()

        self._apply_headers()
        db = next(get_db())
        try:
            records = db.query(self.model_class).all()
            self.raw_data = []
            for r in records:
                row_vals = []
                for k in self.field_keys:
                    val = getattr(r, k, "")
                    if hasattr(val, "value"): # Enum
                        val = val.value
                    elif isinstance(val, bool):
                        if k == "is_regular":
                            val = "🟢 Sí (Nivelado)" if val else "🟡 No (Rezagado)"
                        elif k == "has_payment_agreement":
                            val = "📋 Con Acuerdo" if val else "💳 Al Día (Paz y Salvo)"
                        elif k == "is_enrolled":
                            val = "✅ Matriculado" if val else "❌ No Inscrito"
                        else:
                            val = "🟢 Sí" if val else "🔴 No"
                    elif val is None:
                        val = ""
                    row_vals.append(val)
                self.raw_data.append(row_vals)
        finally:
            db.close()
            self.is_loading = False
            self.refresh_btn.setText("🔄 Recargar")
            self.refresh_btn.setEnabled(True)

        self.filter_data(self.search_input.text())
        
    def filter_data(self, query=""):
        self.is_loading = True
        self._apply_headers()
        query = query.strip().lower()
        if not query:
            filtered = self.raw_data
        else:
            filtered = [
                row for row in self.raw_data 
                if any(query in str(col).lower() for col in row)
            ]

        self.count_badge.setText(f"{len(filtered)} registros")
        self.table.setRowCount(len(filtered))
        
        for row_idx, row_data in enumerate(filtered):
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                key = self.field_keys[col_idx] if col_idx < len(self.field_keys) else ""
                if key in self.read_only_keys:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    if col_idx == 0:
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setForeground(QColor("#64748b"))
                if any(badge_icon in str(col_data) for badge_icon in ["🟢", "🟡", "🔴", "✅", "❌", "📋", "💳"]):
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    if key not in self.read_only_keys or col_idx != 0:
                        item.setForeground(QColor("#000000"))
                self.table.setItem(row_idx, col_idx, item)
        self.is_loading = False

    def _clean_field_value(self, model_instance, key, raw_val):
        """
        Safely casts and cleans incoming input values according to the SQLAlchemy model
        column type, preventing crashes when binding Enums to String columns and vice versa.
        """
        # 1. Enums / Enum Mappings
        if key in self.enum_mappings:
            enum_cls = self.enum_mappings[key]
            if hasattr(raw_val, "value"):
                match = raw_val
            else:
                raw_str = str(raw_val).strip().upper()
                match = next((e for e in enum_cls if str(e.value).strip().upper() == raw_str or e.name.strip().upper() == raw_str), None)

            # Inspect model column definition
            col_attr = getattr(self.model_class, key, None)
            is_sa_enum = False
            if col_attr is not None and hasattr(col_attr, "type") and isinstance(col_attr.type, SAEnum):
                is_sa_enum = True

            if match:
                return match if is_sa_enum else match.value
            return str(raw_val).strip()

        # 2. Booleans and UI Status Badges
        curr_val = getattr(model_instance, key, None) if model_instance else None
        if isinstance(curr_val, bool) or key in ["is_enrolled", "has_payment_agreement", "allow_saturday", "is_regular"]:
            if isinstance(raw_val, bool):
                return raw_val
            clean_str = str(raw_val).strip().lower()
            return clean_str in ["sí", "si", "true", "1", "yes", "activo", "🟢 sí (nivelado)", "📋 con acuerdo", "✅ matriculado"]

        # 3. Integers (Credits, Hours, Semester, Capacities)
        if isinstance(curr_val, int) or key in ["credits", "hours_per_week", "capacity", "expected_students", "semester_id", "number"]:
            val_str = str(raw_val).strip()
            try:
                return int(float(val_str)) if val_str else 0
            except ValueError:
                return 0

        # 4. Floats (Weights, Scores)
        if isinstance(curr_val, float):
            val_str = str(raw_val).strip()
            try:
                return float(val_str) if val_str else 0.0
            except ValueError:
                return 0.0

        # 5. Strings
        return str(raw_val).strip() if raw_val is not None else ""

    def on_cell_edited(self, item):
        if self.is_loading or not item:
            return

        row = item.row()
        col = item.column()
        
        # ID is column 0
        id_item = self.table.item(row, 0)
        if not id_item:
            return

        db = None
        try:
            record_id = int(id_item.text())
            field_name = self.field_keys[col]
            if field_name in self.read_only_keys:
                return
            new_val_str = item.text().strip()

            db = next(get_db())
            record = db.query(self.model_class).filter_by(id=record_id).first()
            if record:
                new_val = self._clean_field_value(record, field_name, new_val_str)
                setattr(record, field_name, new_val)
                db.commit()

                # Update in-memory raw_data
                for r in self.raw_data:
                    if r[0] == record_id:
                        disp_val = new_val.value if hasattr(new_val, "value") else ("Sí" if isinstance(new_val, bool) and new_val else ("No" if isinstance(new_val, bool) else new_val))
                        r[col] = disp_val
                        # Format cell text nicely
                        self.is_loading = True
                        item.setText(str(disp_val))
                        self.is_loading = False
                        break
        except Exception as e:
            if db:
                db.rollback()
            print(f"Error updating cell in {self.title}: {e}")
            QMessageBox.warning(self, "Error al Actualizar", f"No se pudo actualizar el campo:\n{e}")
            self.load_data()
        finally:
            if db:
                db.close()

    def edit_selected_record(self):
        curr_row = self.table.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Selección Requerida", "Por favor selecciona una fila de la tabla para editar.")
            return

        id_item = self.table.item(curr_row, 0)
        if not id_item:
            return

        record_id = int(id_item.text())
        db = next(get_db())
        try:
            record = db.query(self.model_class).filter_by(id=record_id).first()
            if not record:
                QMessageBox.critical(self, "Error", "No se encontró el registro en la base de datos.")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Editar Registro #{record_id} - {self.title}")
            dialog.setFixedWidth(420)
            
            d_layout = QVBoxLayout(dialog)
            form_layout = QFormLayout()
            
            inputs = {}
            for idx, key in enumerate(self.field_keys):
                if key == "id" or key in self.read_only_keys:
                    continue
                curr_val = getattr(record, key, "")
                
                if key in self.enum_mappings:
                    enum_cls = self.enum_mappings[key]
                    combo = QComboBox()
                    for e in enum_cls:
                        combo.addItem(e.value, e)
                    curr_enum_val = curr_val.value if hasattr(curr_val, "value") else str(curr_val)
                    idx_enum = combo.findText(curr_enum_val)
                    if idx_enum >= 0:
                        combo.setCurrentIndex(idx_enum)
                    form_layout.addRow(QLabel(f"<b>{self.headers[idx]}:</b>"), combo)
                    inputs[key] = combo
                elif isinstance(curr_val, bool) or key in ["is_enrolled", "has_payment_agreement", "allow_saturday", "is_regular"]:
                    cb = QCheckBox("Activo / Sí (Nivelado)")
                    cb.setChecked(bool(curr_val))
                    form_layout.addRow(QLabel(f"<b>{self.headers[idx]}:</b>"), cb)
                    inputs[key] = cb
                else:
                    inp = QLineEdit(str(curr_val if curr_val is not None else ""))
                    inp.setStyleSheet("color: #0f172a; background-color: #ffffff; padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px;")
                    form_layout.addRow(QLabel(f"<b>{self.headers[idx]}:</b>"), inp)
                    inputs[key] = inp

            d_layout.addLayout(form_layout)
            
            btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
            btn_box.accepted.connect(dialog.accept)
            btn_box.rejected.connect(dialog.reject)
            d_layout.addWidget(btn_box)

            if dialog.exec() == QDialog.Accepted:
                db_save = None
                try:
                    db_save = next(get_db())
                    rec = db_save.query(self.model_class).filter_by(id=record_id).first()
                    if not rec:
                        raise ValueError("No se encontró el registro para actualizar.")

                    for key, widget in inputs.items():
                        if isinstance(widget, QComboBox):
                            raw_val = widget.currentData()
                        elif isinstance(widget, QCheckBox):
                            raw_val = widget.isChecked()
                        else:
                            raw_val = widget.text().strip()
                        
                        val = self._clean_field_value(rec, key, raw_val)
                        setattr(rec, key, val)

                    db_save.commit()
                    QMessageBox.information(self, "Actualización Exitosa", f"El registro #{record_id} de {self.title} se actualizó correctamente.")
                    self.load_data()
                except Exception as e:
                    if db_save:
                        db_save.rollback()
                    QMessageBox.critical(self, "Error al Actualizar", f"No se pudo guardar la modificación:\n{e}")
                finally:
                    if db_save:
                        db_save.close()
        finally:
            db.close()

    def add_record_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Agregar Nuevo Registro - {self.title}")
        dialog.setFixedWidth(420)
        
        d_layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        inputs = {}
        for idx, key in enumerate(self.field_keys):
            if key == "id" or key in self.read_only_keys:
                continue
            
            if key in self.enum_mappings:
                enum_cls = self.enum_mappings[key]
                combo = QComboBox()
                for e in enum_cls:
                    combo.addItem(e.value, e)
                form_layout.addRow(QLabel(f"<b>{self.headers[idx]}:</b>"), combo)
                inputs[key] = combo
            elif key in ["is_enrolled", "has_payment_agreement", "allow_saturday", "is_regular"]:
                cb = QCheckBox("Activo / Sí (Nivelado)")
                cb.setChecked(True)
                form_layout.addRow(QLabel(f"<b>{self.headers[idx]}:</b>"), cb)
                inputs[key] = cb
            else:
                inp = QLineEdit()
                inp.setStyleSheet("color: #0f172a; background-color: #ffffff; padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px;")
                form_layout.addRow(QLabel(f"<b>{self.headers[idx]}:</b>"), inp)
                inputs[key] = inp

        d_layout.addLayout(form_layout)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        d_layout.addWidget(btn_box)

        if dialog.exec() == QDialog.Accepted:
            db = None
            try:
                db = next(get_db())
                new_obj = self.model_class()
                for key, widget in inputs.items():
                    if isinstance(widget, QComboBox):
                        raw_val = widget.currentData()
                    elif isinstance(widget, QCheckBox):
                        raw_val = widget.isChecked()
                    else:
                        raw_val = widget.text().strip()

                    val = self._clean_field_value(new_obj, key, raw_val)
                    setattr(new_obj, key, val)
                    
                db.add(new_obj)
                db.commit()
                QMessageBox.information(self, "Registro Creado", f"El nuevo registro de {self.title} se ha guardado exitosamente.")
                self.load_data()
            except Exception as e:
                if db:
                    db.rollback()
                QMessageBox.critical(self, "Error", f"No se pudo crear el registro:\n{e}")
            finally:
                if db:
                    db.close()

    def delete_selected_record(self):
        curr_row = self.table.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Selección Requerida", "Por favor selecciona una fila de la tabla para eliminar.")
            return

        id_item = self.table.item(curr_row, 0)
        if not id_item:
            return

        record_id = int(id_item.text())
        reply = QMessageBox.question(
            self, "Confirmar Eliminación", 
            f"¿Estás seguro de que deseas eliminar el registro ID #{record_id} de {self.title}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            db = None
            try:
                db = next(get_db())
                db.query(self.model_class).filter_by(id=record_id).delete()
                db.commit()
                QMessageBox.information(self, "Eliminado", "Registro eliminado exitosamente.")
                self.load_data()
            except Exception as e:
                if db:
                    db.rollback()
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el registro:\n{e}")
            finally:
                if db:
                    db.close()

