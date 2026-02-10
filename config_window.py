import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox
)

CONFIG_FILE = "configuracion.json"

class ConfigWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración de Scripts")
        self.resize(700, 400)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            ["Script", "Nombre compilado", "Icono"]
        )
        layout.addWidget(self.table)

        btn_add = QPushButton("Agregar script")
        btn_save = QPushButton("Guardar configuración")
        layout.addWidget(btn_add)
        layout.addWidget(btn_save)

        btn_add.clicked.connect(self.agregar)
        btn_save.clicked.connect(self.guardar)

        self.cargar()

    def cargar(self):
        if not os.path.exists(CONFIG_FILE):
            return

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.table.setRowCount(0)

        for item in data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(item["script"]))
            self.table.setItem(r, 1, QTableWidgetItem(item["nombre"] or ""))
            self.table.setItem(r, 2, QTableWidgetItem(item["icono"] or ""))

    def agregar(self):
        f, _ = QFileDialog.getOpenFileName(self, "Seleccionar script", "", "Python (*.py)")
        if not f:
            return

        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(f))
        self.table.setItem(r, 1, QTableWidgetItem(""))
        self.table.setItem(r, 2, QTableWidgetItem(""))

    def guardar(self):
        data = []
        for r in range(self.table.rowCount()):
            data.append({
                "script": self.table.item(r, 0).text(),
                "nombre": self.table.item(r, 1).text() or None,
                "icono": self.table.item(r, 2).text() or None
            })

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        QMessageBox.information(self, "OK", "Configuración guardada correctamente")
