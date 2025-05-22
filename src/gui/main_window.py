import os
from pathlib import Path
from threading import Thread

from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Qt

from core.detectors import DETECTORS
from core.exporter import Exporter, DEFAULT_EXTS

try:
    import openai
except ImportError:
    openai = None


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Exportador Multi IA")
        self.resize(900, 600)

        # ---------- widgets ----------
        self.list_projects = QtWidgets.QListWidget()
        btn_add = QtWidgets.QPushButton("Agregar proyecto")
        btn_remove = QtWidgets.QPushButton("Quitar seleccionado")
        self.label_detect = QtWidgets.QLabel("Tipo: N/A")

        self.export_list = QtWidgets.QListWidget()
        btn_list_exp = QtWidgets.QPushButton("Listar exports")
        btn_view_exp = QtWidgets.QPushButton("Ver export")
        btn_extract = QtWidgets.QPushButton("Extraer codigo")

        group_ext = QtWidgets.QGroupBox("Extensiones")
        self.check_ext = {e: QtWidgets.QCheckBox(e) for e in sorted(DEFAULT_EXTS)}
        box_ext = QtWidgets.QVBoxLayout()
        for cb in self.check_ext.values():
            cb.setChecked(True)
            box_ext.addWidget(cb)
        group_ext.setLayout(box_ext)

        self.combo_fmt = QtWidgets.QComboBox()
        self.combo_fmt.addItems(["txt", "md", "json"])
        self.check_only_struct = QtWidgets.QCheckBox("Solo estructura")
        btn_export = QtWidgets.QPushButton("Exportar")

        self.input_key = QtWidgets.QLineEdit()
        self.input_key.setPlaceholderText("OPENAI_API_KEY")
        self.input_key.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)  # Use proper enum value
        btn_send = QtWidgets.QPushButton("Enviar a IA")
        self.text_output = QtWidgets.QTextEdit()
        self.text_output.setReadOnly(True)

        # ---------- layout ----------
        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("Proyectos"))
        left.addWidget(self.list_projects)
        left.addWidget(btn_add)
        left.addWidget(btn_remove)
        left.addWidget(self.label_detect)
        left.addWidget(QtWidgets.QLabel("Exports"))
        left.addWidget(self.export_list)
        left.addWidget(btn_list_exp)
        left.addWidget(btn_view_exp)
        left.addWidget(btn_extract)

        right = QtWidgets.QVBoxLayout()
        right.addWidget(group_ext)
        right.addWidget(QtWidgets.QLabel("Formato"))
        right.addWidget(self.combo_fmt)
        right.addWidget(self.check_only_struct)
        right.addWidget(btn_export)
        right.addSpacing(15)
        right.addWidget(QtWidgets.QLabel("Clave API"))
        right.addWidget(self.input_key)
        right.addWidget(btn_send)
        right.addWidget(QtWidgets.QLabel("Salida"))
        right.addWidget(self.text_output)

        main = QtWidgets.QHBoxLayout()
        main.addLayout(left, 1)
        main.addLayout(right, 2)
        central = QtWidgets.QWidget()
        central.setLayout(main)
        self.setCentralWidget(central)

        # ---------- signals ----------
        btn_add.clicked.connect(self.add_project)
        btn_remove.clicked.connect(self.remove_project)
        self.list_projects.currentItemChanged.connect(self.detect_type)
        btn_list_exp.clicked.connect(self.list_exports_method)
        btn_view_exp.clicked.connect(self.view_export)
        btn_extract.clicked.connect(self.extract_code)
        btn_export.clicked.connect(self.do_export)
        btn_send.clicked.connect(self.send_to_ai)

    def add_project(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Seleccionar proyecto")
        if path:
            self.list_projects.addItem(path)
            self.text_output.append(f"Proyecto agregado: {path}")

    def remove_project(self) -> None:
        for item in self.list_projects.selectedItems():
            self.list_projects.takeItem(self.list_projects.row(item))
        self.label_detect.setText("Tipo: N/A")
        self.export_list.clear()

    def detect_type(self, current, _previous=None) -> None:
        if not current:
            return
        root = current.text()
        best_name, best_score = "N/A", 0.0
        for det in DETECTORS:
            try:
                score = det.match(root)
                if score > best_score:
                    best_name, best_score = det.name(), score
            except Exception as exc:
                self.text_output.append(f"Detector error: {exc}")
        self.label_detect.setText(f"Tipo: {best_name} ({int(best_score * 100)}%)")
        self.text_output.append(f"Detectado tipo: {best_name}")

    def list_exports_method(self) -> None:
        self.export_list.clear()
        proj_item = self.list_projects.currentItem()
        if not proj_item:
            return
        exp_dir = os.path.join(proj_item.text(), "txt_export")
        if not os.path.isdir(exp_dir):
            self.text_output.append("No se encontro carpeta txt_export")
            return
        for fname in sorted(os.listdir(exp_dir)):
            if fname.lower().endswith((".txt", ".md", ".json")):
                self.export_list.addItem(os.path.join(exp_dir, fname))
        self.text_output.append("Lista de exports actualizada.")

    def view_export(self) -> None:
        item = self.export_list.currentItem()
        if not item:
            return
        try:
            with open(item.text(), "r", encoding="utf-8") as fp:
                text = fp.read()
        except Exception as exc:
            self.text_output.append(f"Error leyendo export: {exc}")
            return
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(os.path.basename(item.text()))
        dlg.resize(800, 600)
        layout = QtWidgets.QVBoxLayout(dlg)
        viewer = QtWidgets.QTextEdit()
        viewer.setReadOnly(True)
        viewer.setPlainText(text)
        btn_close = QtWidgets.QPushButton("Cerrar")
        btn_close.clicked.connect(dlg.accept)
        layout.addWidget(viewer)
        layout.addWidget(btn_close)
        dlg.setLayout(layout)
        dlg.exec()

    def extract_code(self) -> None:
        exp_item = self.export_list.currentItem()
        if not exp_item:
            return
        dest = QtWidgets.QFileDialog.getExistingDirectory(self, "Seleccionar destino")
        if not dest:
            return
        created = 0
        cur_file = None
        buffer = []

        def flush():
            nonlocal cur_file, buffer, created
            if cur_file and buffer:
                target = Path(dest) / cur_file
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, "w", encoding="utf-8") as fp:
                    fp.write("".join(buffer))
                created += 1
            cur_file, buffer[:] = None, []

        try:
            with open(exp_item.text(), "r", encoding="utf-8") as fp:
                for line in fp:
                    if line.startswith("//// "):
                        flush()
                        cur_file = line[5:].strip()
                    else:
                        buffer.append(line)
                flush()
            QtWidgets.QMessageBox.information(
                self, "Extraccion", f"Archivos extraidos: {created}"
            )
            self.text_output.append(f"Extraccion completa: {created} archivos.")
        except Exception as exc:
            self.text_output.append(f"Error extrayendo codigo: {exc}")

    def do_export(self) -> None:
        proj_item = self.list_projects.currentItem()
        if not proj_item:
            return
        chosen_exts = {e for e, chk in self.check_ext.items() if chk.isChecked()}
        exporter = Exporter(
            root=proj_item.text(),
            exts=chosen_exts,
            include_content=not self.check_only_struct.isChecked(),
            fmt=self.combo_fmt.currentText(),
        )
        try:
            output_path = exporter.export()
            self.text_output.append(f"Export creado: {output_path}")
            self.list_exports_method()
        except Exception as exc:
            self.text_output.append(f"Error exportando: {exc}")

    def send_to_ai(self) -> None:
        if openai is None:
            self.text_output.append("Paquete openai no instalado.")
            return
        if not hasattr(openai, "OpenAI"):
            self.text_output.append("openai.OpenAI no esta disponible. Instala la version moderna.")
            return

        api_key = self.input_key.text().strip() or os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.text_output.append("Debes ingresar tu API key.")
            return
        exp_item = self.export_list.currentItem()
        if not exp_item:
            self.text_output.append("Selecciona un export.")
            return

        with open(exp_item.text(), "r", encoding="utf-8") as fp:
            content = fp.read()

        def worker() -> None:
            self.text_output.append("Enviando solicitud a OpenAI...")
            try:
                if openai is None:
                    raise ImportError("Módulo openai no está disponible")
                    
                client = openai.OpenAI(api_key=api_key)
                resp = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Asistente para revision de codigo."},
                        {"role": "user", "content": content[:30000]},
                    ],
                    max_tokens=800,
                )
                answer = resp.choices[0].message.content or "[respuesta vacia]"
            except Exception as exc:
                answer = f"ERROR: {exc}"
            self.text_output.append("\n--- RESPUESTA IA ---\n" + answer)

        Thread(target=worker, daemon=True).start()  # Only one thread start
