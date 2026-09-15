from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QLabel, QPushButton, QHBoxLayout, QLineEdit, QHeaderView, 
    QFrame, QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QComboBox, QCheckBox
)
from PySide6.QtCore import Qt
from app.database.database import get_db

class GenericTableView(QWidget):
    def __init__(self, title, headers, model_class, field_keys, enum_mappings=None):
        """
        Generic CRUD Table Widget.
        :param title: Display name of the entity (e.g., "Estudiantes", "Docentes")
        :param headers: Column titles (e.g., ["ID", "Nombre", "Semestre", ...])
        :param model_class: SQLAlchemy Model Class (e.g., Student, Teacher, Subject, Group, Room)
        :param field_keys: Model attribute names matching headers (e.g., ["id", "name", "semester_id", ...])
        :param enum_mappings: Optional dict of {field_name: enum_class} for Enum fields
        """
        super().__init__()
        self.title = title
        self.headers = headers
        self.model_class = model_class
        self.field_keys = field_keys
        self.enum_mappings = enum_mappings or {}
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

        refresh_btn = QPushButton("🔄 Recargar")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 7px 12px; border-radius: 6px;")
        refresh_btn.clicked.connect(self.load_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header_card)
        
        # Info note
        note_lbl = QLabel("💡 <i>Tip: Puedes hacer doble clic en una celda para editarla directamente o seleccionar una fila y presionar '✏️ Editar'. Los cambios se guardan inmediatamente en la base de datos.</i>")
        note_lbl.setStyleSheet("font-size: 11px; color: #64748b; margin-left: 5px;")
        layout.addWidget(note_lbl)

        # Table with Pixel-based Fluid Scrolling and High Visibility
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.verticalScrollBar().setSingleStep(12)
        
        # Smart Column Sizing: Compact ID, stretched name
        for c_i in range(len(headers)):
            if c_i == 0:
                self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            elif c_i == 1:
                self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
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
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 9px 12px;
                font-weight: 800;
                font-size: 12px;
                border: none;
                border-right: 1px solid #334155;
            }
            QTableWidget::item:selected {
                background-color: #e0e7ff;
                color: #1e3a8a;
            }
        """)
        self.table.itemChanged.connect(self.on_cell_edited)
        layout.addWidget(self.table)
        
        self.load_data()
        
    def load_data(self):
        self.is_loading = True
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

        self.filter_data(self.search_input.text())
        
    def filter_data(self, query=""):
        self.is_loading = True
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
                if col_idx == 0: # ID column is non-editable
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setForeground(Qt.darkGray)
                else:
                    # Centered alignment for badges/status
                    if any(badge_icon in str(col_data) for badge_icon in ["🟢", "🟡", "🔴", "✅", "❌", "📋", "💳"]):
                        item.setTextAlignment(Qt.AlignCenter)
                    item.setForeground(Qt.black)
                self.table.setItem(row_idx, col_idx, item)
        self.is_loading = False

    def on_cell_edited(self, item):
        if self.is_loading or not item:
            return

        row = item.row()
        col = item.column()
        
        # ID is column 0
        id_item = self.table.item(row, 0)
        if not id_item:
            return

        try:
            record_id = int(id_item.text())
            field_name = self.field_keys[col]
            new_val_str = item.text().strip()

            db = next(get_db())
            record = db.query(self.model_class).filter_by(id=record_id).first()
            if record:
                curr_attr = getattr(record, field_name)
                
                # Type cast
                if field_name in self.enum_mappings:
                    enum_cls = self.enum_mappings[field_name]
                    # Find enum by value or name
                    new_val = next((e for e in enum_cls if e.value.upper() == new_val_str.upper() or e.name.upper() == new_val_str.upper()), curr_attr)
                elif isinstance(curr_attr, bool) or field_name in ["is_enrolled", "has_payment_agreement", "allow_saturday", "is_regular"]:
                    new_val = (new_val_str.lower() in ["sí", "si", "true", "1", "yes"])
                elif isinstance(curr_attr, int):
                    new_val = int(new_val_str) if new_val_str else 0
                elif isinstance(curr_attr, float):
                    new_val = float(new_val_str) if new_val_str else 0.0
                else:
                    new_val = new_val_str

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
            print(f"Error updating cell in {self.title}: {e}")
            QMessageBox.warning(self, "Error al Actualizar", f"No se pudo actualizar el campo:\n{e}")
            self.load_data()

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
            if key == "id":
                continue
            curr_val = getattr(record, key, "")
            
            if key in self.enum_mappings:
                enum_cls = self.enum_mappings[key]
                combo = QComboBox()
                for e in enum_cls:
                    combo.addItem(e.value, e)
                # Set current
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
            try:
                for key, widget in inputs.items():
                    if isinstance(widget, QComboBox):
                        val = widget.currentData()
                    elif isinstance(widget, QCheckBox):
                        val = widget.isChecked()
                    else:
                        val_str = widget.text().strip()
                        curr_attr = getattr(record, key)
                        if isinstance(curr_attr, int):
                            val = int(val_str) if val_str else 0
                        elif isinstance(curr_attr, float):
                            val = float(val_str) if val_str else 0.0
                        else:
                            val = val_str
                    setattr(record, key, val)

                db.commit()
                QMessageBox.information(self, "Actualización Exitosa", f"El registro #{record_id} de {self.title} se actualizó correctamente.")
                self.load_data()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Error al Actualizar", f"No se pudo guardar la modificación:\n{e}")

    def add_record_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Agregar Nuevo Registro - {self.title}")
        dialog.setFixedWidth(420)
        
        d_layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        inputs = {}
        for idx, key in enumerate(self.field_keys):
            if key == "id":
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
            try:
                db = next(get_db())
                new_obj = self.model_class()
                for key, widget in inputs.items():
                    if isinstance(widget, QComboBox):
                        val = widget.currentData()
                    elif isinstance(widget, QCheckBox):
                        val = widget.isChecked()
                    else:
                        val_str = widget.text().strip()
                        if key in ["hours_per_week", "capacity", "expected_students", "semester_id", "number"]:
                            val = int(val_str) if val_str else 0
                        else:
                            val = val_str
                    setattr(new_obj, key, val)
                    
                db.add(new_obj)
                db.commit()
                QMessageBox.information(self, "Registro Creado", f"El nuevo registro de {self.title} se ha guardado exitosamente.")
                self.load_data()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Error", f"No se pudo crear el registro:\n{e}")

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
            try:
                db = next(get_db())
                db.query(self.model_class).filter_by(id=record_id).delete()
                db.commit()
                QMessageBox.information(self, "Eliminado", "Registro eliminado exitosamente.")
                self.load_data()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el registro:\n{e}")

