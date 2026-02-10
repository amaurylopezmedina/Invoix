import os
import json
import smtplib
from cryptography.fernet import Fernet
from PyQt5 import QtWidgets, QtCore, QtGui

# ------------------------------------------------------------
# RUTAS
# ------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(CONFIG_DIR, "config_rcorreo.json")
KEY_FILE = os.path.join(CONFIG_DIR, "email_key.key")

from db.uDB import ConectarDB  # importante


# ------------------------------------------------------------
# COLUMNAS REQUERIDAS PARA EL QUERY PRINCIPAL
# ------------------------------------------------------------
COLUMNAS_REQUERIDAS = [
    "NumeroFacturaInterna",
    "eNCF",
    "RNCComprador",
    "RazonSocialComprador",
    "EstadoFiscal",
    "ResultadoEstadoFiscal",
]


# ------------------------------------------------------------
# CIFRADO
# ------------------------------------------------------------
def load_or_create_key():
    if os.path.exists(KEY_FILE):
        return open(KEY_FILE, "rb").read()

    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key


def encrypt_value(text, key):
    return Fernet(key).encrypt(text.encode()).decode()


def decrypt_value(token, key):
    return Fernet(key).decrypt(token.encode()).decode()


# ------------------------------------------------------------
# CONFIG DEFAULT
# ------------------------------------------------------------
def default_config():
    return {
        "hora_envio": "01:00",
        "formato24": True,
        "periodicidad": "diario",
        "enviar_al_entrar": False,
        # Query principal
        "query_resumen": "SELECT NumeroFacturaInterna, eNCF, RNCComprador, RazonSocialComprador, "
        "EstadoFiscal, ResultadoEstadoFiscal "
        "FROM vFEEncabezado WITH (NOLOCK) "
        "WHERE CONVERT(date, FechaEmision) = CONVERT(date, DATEADD(day,-1,GETDATE())) "
        "ORDER BY NumeroFacturaInterna;",
        # Query Totales (Estado + ResultadoEstadoFiscal)
        "query_totales_estado": "SELECT EstadoFiscal, ResultadoEstadoFiscal, COUNT(*) AS Cantidad "
        "FROM vFEEncabezado WITH (NOLOCK) "
        "WHERE CONVERT(date, FechaEmision) = CONVERT(date, DATEADD(day,-1,GETDATE())) "
        "GROUP BY EstadoFiscal, ResultadoEstadoFiscal "
        "ORDER BY EstadoFiscal, ResultadoEstadoFiscal;",
        # Query nombre de archivo
        "query_nombre_archivo": "SELECT TOP 1 CONCAT('Resumen_', FORMAT(GETDATE(),'yyyyMMdd'), '.xlsx') AS NombreArchivo;",
        # Query RNC + Empresa
        "query_empresa": "SELECT TOP 1 RNC, RazonSocial FROM empresa WITH (NOLOCK);",
        # SMTP
        "correo": {
            "smtp_server": "smtpout.secureserver.net",
            "smtp_port": 465,
            "username": "info@asesys.com.do",
            "password_encrypted": "",
            "from_address": "info@asesys.com.do",
            "to_addresses": ["licitaciones@asesys.com.do"],
        },
    }


# ------------------------------------------------------------
# CARGAR CONFIG
# ------------------------------------------------------------
def load_config(key):
    if not os.path.exists(CONFIG_FILE):
        cfg = default_config()
        cfg["correo"]["password_claro"] = ""
        return cfg

    cfg = json.load(open(CONFIG_FILE, "r", encoding="utf8"))
    base = default_config()

    # merge
    for k, v in base.items():
        cfg.setdefault(k, v)
    for k, v in base["correo"].items():
        cfg["correo"].setdefault(k, v)

    # queries nuevos
    cfg.setdefault("query_totales_estado", base["query_totales_estado"])
    cfg.setdefault("query_nombre_archivo", base["query_nombre_archivo"])
    cfg.setdefault("query_empresa", base["query_empresa"])

    # desencriptar password
    pwd = ""
    if cfg["correo"].get("password_encrypted"):
        try:
            pwd = decrypt_value(cfg["correo"]["password_encrypted"], key)
        except Exception:
            pwd = ""

    cfg["correo"]["password_claro"] = pwd
    return cfg


# ------------------------------------------------------------
# GUARDAR
# ------------------------------------------------------------
def save_config(cfg, key, password_claro):
    if password_claro:
        cfg["correo"]["password_encrypted"] = encrypt_value(password_claro, key)

    cfg["correo"].pop("password_claro", None)

    with open(CONFIG_FILE, "w", encoding="utf8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)


# ------------------------------------------------------------
# VALIDACIÓN DE HORA
# ------------------------------------------------------------
def validar_hora_24(txt):
    return QtCore.QTime.fromString(txt, "HH:mm").isValid()


def validar_hora_12(txt):
    txt = txt.upper().replace("AM", " AM").replace("PM", " PM")
    formatos = ["h:mm AP", "hh:mm AP", "h AP", "hh AP"]
    return any(QtCore.QTime.fromString(txt, f).isValid() for f in formatos)


# ------------------------------------------------------------
# UI PRINCIPAL
# ------------------------------------------------------------
class ConfigWindow(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Configuración — Servicio Resumen eCF")
        self.resize(820, 1000)

        font = self.font()
        font.setPointSize(12)
        self.setFont(font)

        self.key = load_or_create_key()
        self.config = load_config(self.key)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        # ------------------------------
        # Hora
        # ------------------------------
        self.txtHora = QtWidgets.QLineEdit(self.config["hora_envio"])
        self.txtHora.textChanged.connect(self.validar_hora_visual)
        form.addRow("Hora de envío:", self.txtHora)

        self.chkFormato24 = QtWidgets.QCheckBox("Usar formato 24h")
        self.chkFormato24.setChecked(self.config["formato24"])
        self.chkFormato24.stateChanged.connect(self.validar_hora_visual)
        form.addRow("", self.chkFormato24)

        # periodicidad
        self.cmbPeriodicidad = QtWidgets.QComboBox()
        self.cmbPeriodicidad.addItems(["diario", "semanal", "mensual"])
        try:
            i = self.cmbPeriodicidad.findText(self.config["periodicidad"])
            self.cmbPeriodicidad.setCurrentIndex(i)
        except:
            pass
        form.addRow("Periodicidad:", self.cmbPeriodicidad)

        self.chkEnviar = QtWidgets.QCheckBox("Enviar al iniciar servicio")
        self.chkEnviar.setChecked(self.config["enviar_al_entrar"])
        form.addRow("", self.chkEnviar)

        # ------------------------------
        # QUERY RESUMEN
        # ------------------------------
        form.addRow(QtWidgets.QLabel("—— QUERY PRINCIPAL DEL RESUMEN ——"))

        self.txtQueryResumen = QtWidgets.QTextEdit()
        self.txtQueryResumen.setPlainText(self.config["query_resumen"])
        self.txtQueryResumen.setMinimumHeight(150)
        form.addRow(self.txtQueryResumen)

        """form.addRow(
            QtWidgets.QLabel(
                "<i>Debe devolver EXACTAMENTE estas columnas:<br>"
                "NumeroFacturaInterna, eNCF, RNCComprador,<br>"
                "RazonSocialComprador, EstadoFiscal, ResultadoEstadoFiscal</i>"
            )
        )"""

        # ------------------------------
        # QUERY TOTALES
        # ------------------------------
        form.addRow(QtWidgets.QLabel("—— QUERY TOTALES POR ESTADO + RESULTADO ——"))

        self.txtQueryTotales = QtWidgets.QTextEdit()
        self.txtQueryTotales.setPlainText(self.config["query_totales_estado"])
        self.txtQueryTotales.setMinimumHeight(100)
        form.addRow(self.txtQueryTotales)

        # ------------------------------
        # QUERY NOMBRE ARCHIVO
        # ------------------------------
        form.addRow(QtWidgets.QLabel("—— QUERY NOMBRE DEL ARCHIVO ——"))

        self.txtQueryArchivo = QtWidgets.QTextEdit()
        self.txtQueryArchivo.setPlainText(self.config["query_nombre_archivo"])
        self.txtQueryArchivo.setMinimumHeight(80)
        form.addRow(self.txtQueryArchivo)

        # ------------------------------
        # QUERY EMPRESA (RNC + Nombre)
        # ------------------------------
        form.addRow(QtWidgets.QLabel("—— QUERY EMPRESA ——"))

        self.txtQueryEmpresa = QtWidgets.QTextEdit()
        self.txtQueryEmpresa.setPlainText(self.config["query_empresa"])
        self.txtQueryEmpresa.setMinimumHeight(80)
        form.addRow(self.txtQueryEmpresa)

        # ------------------------------
        # SMTP
        # ------------------------------
        form.addRow(QtWidgets.QLabel("—— SMTP ——"))

        self.txtSMTP = QtWidgets.QLineEdit(self.config["correo"]["smtp_server"])
        form.addRow("Servidor SMTP:", self.txtSMTP)

        self.spnPort = QtWidgets.QSpinBox()
        self.spnPort.setRange(1, 65535)
        self.spnPort.setValue(self.config["correo"]["smtp_port"])
        form.addRow("Puerto SMTP:", self.spnPort)

        self.txtUser = QtWidgets.QLineEdit(self.config["correo"]["username"])
        form.addRow("Usuario:", self.txtUser)

        self.txtPassword = QtWidgets.QLineEdit(self.config["correo"]["password_claro"])
        self.txtPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        form.addRow("Contraseña:", self.txtPassword)

        self.txtFrom = QtWidgets.QLineEdit(self.config["correo"]["from_address"])
        form.addRow("Correo From:", self.txtFrom)

        toaddrs = ";".join(self.config["correo"]["to_addresses"])
        self.txtTo = QtWidgets.QLineEdit(toaddrs)
        form.addRow("Destinatarios (; separados):", self.txtTo)

        # ------------------------------
        # BOTONES
        # ------------------------------
        btns = QtWidgets.QHBoxLayout()
        layout.addLayout(btns)

        self.btnGuardar = QtWidgets.QPushButton("Guardar")
        self.btnProbarSMTP = QtWidgets.QPushButton("Probar SMTP")
        self.btnProbarQuery = QtWidgets.QPushButton("Probar Query Principal")
        self.btnEnviarPrueba = QtWidgets.QPushButton("Enviar Correo de Prueba")
        self.btnSalir = QtWidgets.QPushButton("Salir")

        btns.addWidget(self.btnGuardar)
        btns.addWidget(self.btnProbarSMTP)
        btns.addWidget(self.btnProbarQuery)
        btns.addWidget(self.btnEnviarPrueba)
        btns.addWidget(self.btnSalir)

        # eventos
        self.btnGuardar.clicked.connect(self.guardar)
        self.btnProbarSMTP.clicked.connect(self.probar_smtp)
        self.btnProbarQuery.clicked.connect(self.probar_query)
        self.btnEnviarPrueba.clicked.connect(self.enviar_prueba)
        self.btnSalir.clicked.connect(self.close)

        self.validar_hora_visual()

    # ------------------------------------------------------------
    # VALIDAR VISUAL DE HORA
    # ------------------------------------------------------------
    def validar_hora_visual(self):
        txt = self.txtHora.text().strip()
        es24 = self.chkFormato24.isChecked()

        valido = validar_hora_24(txt) if es24 else validar_hora_12(txt)
        color = "#ccffcc" if valido else "#ffcccc"
        self.txtHora.setStyleSheet(f"background-color: {color}")

    # ------------------------------------------------------------
    # GUARDAR
    # ------------------------------------------------------------
    def guardar(self):
        self.config["hora_envio"] = self.txtHora.text().strip()
        self.config["formato24"] = self.chkFormato24.isChecked()
        self.config["periodicidad"] = self.cmbPeriodicidad.currentText()
        self.config["enviar_al_entrar"] = self.chkEnviar.isChecked()

        self.config["query_resumen"] = self.txtQueryResumen.toPlainText().strip()
        self.config["query_totales_estado"] = self.txtQueryTotales.toPlainText().strip()
        self.config["query_nombre_archivo"] = self.txtQueryArchivo.toPlainText().strip()
        self.config["query_empresa"] = self.txtQueryEmpresa.toPlainText().strip()

        c = self.config["correo"]
        c["smtp_server"] = self.txtSMTP.text().strip()
        c["smtp_port"] = int(self.spnPort.value())
        c["username"] = self.txtUser.text().strip()
        c["from_address"] = self.txtFrom.text().strip()

        to_raw = self.txtTo.text().replace(",", ";")
        c["to_addresses"] = [t.strip() for t in to_raw.split(";") if t.strip()]

        save_config(self.config, self.key, self.txtPassword.text().strip())

        QtWidgets.QMessageBox.information(
            self, "OK", "Configuración guardada correctamente."
        )

    # ------------------------------------------------------------
    # PROBAR SMTP
    # ------------------------------------------------------------
    def probar_smtp(self):
        server = self.txtSMTP.text().strip()
        port = int(self.spnPort.value())

        try:
            smtp = smtplib.SMTP(server, port, timeout=10)
            smtp.noop()
            smtp.quit()
            QtWidgets.QMessageBox.information(self, "OK", "Conexión SMTP exitosa.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    # ------------------------------------------------------------
    # PROBAR QUERY PRINCIPAL
    # ------------------------------------------------------------
    def probar_query(self):
        query = self.txtQueryResumen.toPlainText().strip()

        if not query:
            QtWidgets.QMessageBox.warning(self, "Error", "El query está vacío.")
            return

        query_test = query

        try:
            cn = ConectarDB()
            cur = cn.connection.cursor()
            cur.execute(query_test)
            columnas = [c[0] for c in cur.description]

            faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in columnas]

            if faltantes:
                QtWidgets.QMessageBox.critical(
                    self, "Columnas faltantes", "\n".join(faltantes)
                )
            else:
                QtWidgets.QMessageBox.information(self, "OK", "El query es válido.")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error SQL", str(e))

    # ------------------------------------------------------------
    # ENVIAR CORREO DE PRUEBA
    # ------------------------------------------------------------
    def enviar_prueba(self):
        try:
            from FEEnvioCorreoECF import EmailConfig, EmailSender
        except:
            QtWidgets.QMessageBox.critical(
                self, "Error", "No existe FEEnvioCorreoECF.py"
            )
            return

        smtp = self.txtSMTP.text().strip()
        port = int(self.spnPort.value())
        user = self.txtUser.text().strip()
        pwd = self.txtPassword.text().strip()
        from_addr = self.txtFrom.text().strip()

        to_list = [
            t.strip()
            for t in self.txtTo.text().replace(",", ";").split(";")
            if t.strip()
        ]

        if not pwd:
            QtWidgets.QMessageBox.warning(self, "Error", "Debe ingresar password.")
            return

        try:
            cfg = EmailConfig(
                smtp_server=smtp, smtp_port=port, username=user, password=pwd
            )
            sender = EmailSender(cfg)

            sender.send_email(
                from_address=from_addr,
                to_addresses=to_list,
                subject="Prueba de Configuración — Resumen eCF",
                body="Este es un correo de prueba generado por el configurador.",
                attachments=None,
            )

            QtWidgets.QMessageBox.information(
                self, "OK", "Correo enviado correctamente."
            )

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    import sys

    app = QtWidgets.QApplication(sys.argv)

    f = app.font()
    f.setPointSize(10)
    app.setFont(f)

    w = ConfigWindow()
    w.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
