from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QLabel, QPushButton, QHBoxLayout, QLineEdit, QHeaderView, 
    QFrame, QMessageBox, QDialog, QFormLayout, QDialogButtonBox
)
from PySide6.QtCore import Qt
from app.database.database import get_db

class GenericTableView(QWidget):
    def __init__(self, title, headers, model_class, field_keys, fetch_data_func=None):
        super().__init__()
        self.title = title
        self.headers = headers
        self.model_class = model_class
        self.field_keys = field_keys # List of attribute names e.g. ["id", "name", "capacity", "room_type"]
        self.fetch_data_func = fetch_data_func
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
        self.search_input.setFixedWidth(200)
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
        note_lbl = QLabel("💡 <i>Tip: Puedes hacer doble clic en cualquier celda para editar su valor y se guardará automáticamente en la base de datos.</i>")
        note_lbl.setStyleSheet("font-size: 11px; color: #64748b; margin-left: 5px;")
        layout.addWidget(note_lbl)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #cbd5e1;
                background-color: #ffffff;
                color: #0f172a;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #ffffff;
                padding: 8px;
                font-weight: bold;
            }
        """)
        self.table.itemChanged.connect(self.on_cell_edited)
        layout.addWidget(self.table)
        
        self.load_data()
        
    def load_data(self):
        self.is_loading = True
        db = next(get_db())
        
        if self.fetch_data_func:
            self.raw_data = self.fetch_data_func(db)
        else:
            records = db.query(self.model_class).all()
            self.raw_data = []
            for r in records:
                row_vals = []
                for k in self.field_keys:
                    val = getattr(r, k, "")
                    if hasattr(val, "value"): # Enum
                        val = val.value
                    row_vals.append(val)
                self.raw_data.append(row_vals)

        self.filter_data(self.search_input.text())
        self.is_loading = False
        
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
                if col_idx == 0: # ID column non-editable
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setForeground(Qt.darkGray)
                else:
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
                if isinstance(curr_attr, int):
                    new_val = int(new_val_str)
                elif isinstance(curr_attr, float):
                    new_val = float(new_val_str)
                elif isinstance(curr_attr, bool):
                    new_val = (new_val_str.lower() in ["true", "1", "sí", "si"])
                else:
                    new_val = new_val_str

                setattr(record, field_name, new_val)
                db.commit()
                # Update in-memory raw_data
                for r in self.raw_data:
                    if r[0] == record_id:
                        r[col] = new_val
                        break
        except Exception as e:
            print(f"Error updating cell: {e}")

    def add_record_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Agregar Nuevo Registro - {self.title}")
        dialog.setFixedWidth(380)
        
        d_layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        inputs = {}
        for idx, key in enumerate(self.field_keys):
            if key == "id":
                continue
            inp = QLineEdit()
            inp.setStyleSheet("color: #0f172a; background-color: #ffffff; padding: 6px;")
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
                for key, inp in inputs.items():
                    val = inp.text().strip()
                    if key in ["hours_per_week", "capacity", "expected_students", "semester_id"]:
                        val = int(val) if val else 0
                    elif key in ["has_payment_agreement", "is_enrolled"]:
                        val = (val.lower() in ["true", "1", "si", "sí"])
                    setattr(new_obj, key, val)
                    
                db.add(new_obj)
                db.commit()
                QMessageBox.information(self, "Registro Creado", "El nuevo registro se ha guardado exitosamente.")
                self.load_data()
            except Exception as e:
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
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el registro:\n{e}")

        
    def load_data(self):
        db = next(get_db())
        self.raw_data = self.fetch_data_func(db)
        self.filter_data(self.search_input.text())
        
    def filter_data(self, query=""):
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
                item.setForeground(Qt.black)
                self.table.setItem(row_idx, col_idx, item)

