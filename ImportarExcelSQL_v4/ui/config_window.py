from PyQt6 import QtWidgets
import winreg
from core.db_manager import (
    load_settings,
    save_settings,
    test_connection,
    get_server_info,
    set_theme,
    get_theme,
)

def get_sqlserver_drivers():
    drivers = []
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers"
        )
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                if "SQL Server" in name and value == "Installed":
                    drivers.append(name)
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except OSError:
        pass

    drivers.sort()
    return drivers

class ConfigWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ASESYS - Configuración de Conexión SQL Server")
        self.setModal(True)
        self.setMinimumWidth(460)

        cfg = load_settings()

        self.txt_server = QtWidgets.QLineEdit(cfg.get("server", ""))
        self.txt_db = QtWidgets.QLineEdit(cfg.get("database", "DGII_Importador"))
        self.txt_user = QtWidgets.QLineEdit(cfg.get("user", "sa"))
        self.txt_pass = QtWidgets.QLineEdit(cfg.get("password", ""))
        self.txt_pass.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        self.txt_table_head = QtWidgets.QLineEdit(cfg.get("table_encabezado", "ImportacionEncabezado"))
        self.txt_table_det_prefix = QtWidgets.QLineEdit(cfg.get("table_detalle_prefix", "ImportacionDetalle"))

        # Checkbox para validar duplicados
        self.chk_validate_duplicates = QtWidgets.QCheckBox("Validar duplicados antes de insertar")
        self.chk_validate_duplicates.setChecked(cfg.get("validate_duplicates", True))
        self.chk_validate_duplicates.setToolTip(
            "Si está activado, el sistema verificará si ya existen registros con el mismo ENCF+RNCEmisor antes de insertar"
        )

        # theme combo
        self.cbo_theme = QtWidgets.QComboBox()
        self.cbo_theme.addItems(["light","dark"])
        self.cbo_theme.setCurrentText(cfg.get("theme","light"))

        # driver combo
        self.cbo_driver = QtWidgets.QComboBox()
        detected = get_sqlserver_drivers()
        if detected:
            self.cbo_driver.addItems(detected)
        else:
            self.cbo_driver.addItem("⚠ No se detectaron drivers ODBC de SQL Server")

        current_driver = cfg.get("driver", "")
        if current_driver and current_driver in detected:
            self.cbo_driver.setCurrentText(current_driver)
        elif detected:
            self.cbo_driver.setCurrentText(detected[-1])
        else:
            if current_driver:
                self.cbo_driver.setCurrentText(current_driver)

        form = QtWidgets.QFormLayout()
        form.addRow("Servidor / Instancia:", self.txt_server)
        form.addRow("Base de Datos:", self.txt_db)
        form.addRow("Tabla Encabezado:", self.txt_table_head)
        form.addRow("Prefijo Tablas Detalle:", self.txt_table_det_prefix)
        form.addRow("Usuario:", self.txt_user)
        form.addRow("Contraseña:", self.txt_pass)
        form.addRow("Driver ODBC:", self.cbo_driver)
        form.addRow("", self.chk_validate_duplicates)
        form.addRow("Tema visual:", self.cbo_theme)

        self.btn_test = QtWidgets.QPushButton("Probar conexión")
        self.btn_save = QtWidgets.QPushButton("Guardar configuración")
        self.lbl_status = QtWidgets.QLabel("")
        self.lbl_status.setWordWrap(True)

        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(self.btn_test)
        btns.addWidget(self.btn_save)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(btns)
        layout.addWidget(self.lbl_status)
        self.setLayout(layout)

        self.btn_test.clicked.connect(self._on_test)
        self.btn_save.clicked.connect(self._on_save)

    def _on_test(self):
        tmp_cfg = {
            "server": self.txt_server.text().strip(),
            "database": self.txt_db.text().strip(),
            "user": self.txt_user.text().strip(),
            "password": self.txt_pass.text(),
            "table_encabezado": self.txt_table_head.text().strip(),
            "table_detalle_prefix": self.txt_table_det_prefix.text().strip(),
            "driver": self.cbo_driver.currentText(),
            "validate_duplicates": self.chk_validate_duplicates.isChecked(),
            "theme": self.cbo_theme.currentText(),
        }
        save_settings(tmp_cfg)

        try:
            ok, error_msg = test_connection()
            if ok:
                version, driver = get_server_info()
                main_line = version.splitlines()[0] if version else "SQL Server"
                self.lbl_status.setText(
                    f"✅ Conexión exitosa.\nDriver: {driver}\n{main_line}"
                )
            else:
                self.lbl_status.setText(
                    f"❌ Error al conectar:\n{error_msg}"
                )
        except Exception as e:
            self.lbl_status.setText(f"❌ Error al obtener detalles: {e}")

    def _on_save(self):
        cfg = {
            "server": self.txt_server.text().strip(),
            "database": self.txt_db.text().strip(),
            "user": self.txt_user.text().strip(),
            "password": self.txt_pass.text(),
            "table_encabezado": self.txt_table_head.text().strip(),
            "table_detalle_prefix": self.txt_table_det_prefix.text().strip(),
            "driver": self.cbo_driver.currentText(),
            "validate_duplicates": self.chk_validate_duplicates.isChecked(),
            "theme": self.cbo_theme.currentText(),
        }
        save_settings(cfg)
        set_theme(self.cbo_theme.currentText())
        self.accept()
