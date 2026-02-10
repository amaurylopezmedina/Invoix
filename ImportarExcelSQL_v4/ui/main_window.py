from PyQt6 import QtWidgets, QtGui
from ui.config_window import ConfigWindow
from core.excel_loader import load_excel
from core.db_manager import (
    ensure_database_exists,
    ensure_tables_exist,
    split_dataframe,
    insert_dataframes,
    test_connection,
    load_settings,
)

LIGHT_STYLE = """
QWidget {
    background-color: #ffffff;
    color: #1a1a1a;
    font-size: 14px;
    font-family: Segoe UI, sans-serif;
}
QPushButton {
    background-color: #0d6efd;
    color: #ffffff;
    border-radius: 6px;
    padding: 6px 10px;
}
QPushButton:disabled {
    background-color: #9bb8f5;
    color: #eaeaea;
}
QTextEdit, QLineEdit, QComboBox, QProgressBar {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1px solid #999;
    border-radius: 4px;
}
"""

DARK_STYLE = """
QWidget {
    background-color: #1e1e1e;
    color: #f0f0f0;
    font-size: 14px;
    font-family: Segoe UI, sans-serif;
}
QPushButton {
    background-color: #3b82f6;
    color: #ffffff;
    border-radius: 6px;
    padding: 6px 10px;
}
QPushButton:disabled {
    background-color: #4a5568;
    color: #999999;
}
QTextEdit, QLineEdit, QComboBox, QProgressBar {
    background-color: #2b2b2b;
    color: #f0f0f0;
    border: 1px solid #555;
    border-radius: 4px;
}
"""

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ASESYS - Importador DGII SQL")
        self.resize(900, 650)

        cfg = load_settings()
        theme = cfg.get("theme","light")
        self.apply_theme(theme)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        self.btn_config = QtWidgets.QPushButton("⚙ Configuración SQL")
        self.btn_select_file = QtWidgets.QPushButton("📂 Seleccionar Excel")
        self.lbl_file = QtWidgets.QLabel("Archivo: (ninguno seleccionado)")
        
        # Combo para modo de importación
        self.cbo_import_mode = QtWidgets.QComboBox()
        self.cbo_import_mode.addItem("➕ Agregar a tablas existentes", False)
        self.cbo_import_mode.addItem("🔄 Recrear tablas (elimina datos previos)", True)
        self.cbo_import_mode.setCurrentIndex(0)  # Por defecto: Agregar
        
        self.btn_import = QtWidgets.QPushButton("⬆ Importar a SQL Server")
        self.btn_import.setEnabled(False)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.txt_log = QtWidgets.QTextEdit()
        self.txt_log.setReadOnly(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.btn_config)
        layout.addWidget(self.btn_select_file)
        layout.addWidget(self.lbl_file)
        layout.addWidget(QtWidgets.QLabel("Modo de importación:"))
        layout.addWidget(self.cbo_import_mode)
        layout.addWidget(self.btn_import)
        layout.addWidget(self.progress)
        layout.addWidget(QtWidgets.QLabel("Registro de actividad:"))
        layout.addWidget(self.txt_log)
        central.setLayout(layout)

        self.selected_file = None

        self.btn_config.clicked.connect(self.open_config)
        self.btn_select_file.clicked.connect(self.pick_file)
        self.btn_import.clicked.connect(self.run_import)

    def apply_theme(self, theme_name: str):
        if theme_name.lower() == "dark":
            self.setStyleSheet(DARK_STYLE)
        else:
            self.setStyleSheet(LIGHT_STYLE)

    def log(self, msg: str):
        self.txt_log.append(msg)
        self.txt_log.ensureCursorVisible()

    def open_config(self):
        dlg = ConfigWindow(self)
        dlg.exec()
        # re-aplicar tema después de cerrar config
        cfg = load_settings()
        self.apply_theme(cfg.get("theme","light"))

    def pick_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo Excel",
            "",
            "Archivos Excel (*.xlsx *.xls)"
        )
        if path:
            self.selected_file = path
            self.lbl_file.setText(f"Archivo: {path}")
            self.btn_import.setEnabled(True)

    def run_import(self):
        if not self.selected_file:
            self.log("❌ No hay archivo seleccionado.")
            return

        self.log("🔌 Probando conexión a SQL Server...")
        ok, error_msg = test_connection()
        if not ok:
            self.log(f"❌ No se pudo conectar: {error_msg}")
            self.log("   Revise la configuración de conexión.")
            return
        self.log("✅ Conexión OK.")

        try:
            self.progress.setValue(10)
            self.log("📖 Leyendo Excel...")
            df = load_excel(self.selected_file)
            self.log(f"   → {len(df.index)} filas, {len(df.columns)} columnas")

            self.progress.setValue(25)
            self.log("🏗 Creando base de datos si no existe...")
            ensure_database_exists()
            self.log("✅ Base lista.")

            self.progress.setValue(40)
            # Obtener modo de importación seleccionado
            recreate_mode = self.cbo_import_mode.currentData()
            mode_text = "RECREAR (eliminar datos previos)" if recreate_mode else "AGREGAR (preservar datos existentes)"
            self.log(f"🧱 Preparando tablas - Modo: {mode_text}")
            detalle_tables_list = ensure_tables_exist(df, recreate_mode=recreate_mode)
            for t in detalle_tables_list:
                self.log(f"   ✅ Tabla detalle lista: {t}")
            self.log("✅ Tablas listas.")

            self.progress.setValue(60)
            self.log("✂ Dividiendo encabezado y detalle en memoria...")
            df_head, det_tables = split_dataframe(df)
            self.log(f"   → Encabezado cols: {len(df_head.columns)}")
            for tname, dft in det_tables.items():
                self.log(f"   → {tname} cols: {len(dft.columns)}")

            self.progress.setValue(80)
            self.log("⬆ Insertando datos en SQL Server...")
            n_head, inserted_details = insert_dataframes(df_head, det_tables)
            self.log(f"   → Encabezado insertado: {n_head} filas")
            for tname, count in inserted_details.items():
                self.log(f"   → {tname} insertado: {count} filas")

            self.progress.setValue(100)
            self.log("✅ Importación completada con éxito.")

        except Exception as e:
            self.log(f"💥 Error: {str(e)}")
            self.progress.setValue(0)
