import datetime
import os
import sys
import time

import portalocker
import pyodbc
import requests
import win32print
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)
from sqlalchemy import Column, MetaData, String, Table, create_engine, select, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from db.CDT import *
from db.database import *
from db.uDB import *
from glib.ufe import *
from glib.uGlobalVar import *
from logG import *

# from glib.ufe import GConfig
from print.impresion import *
from print.invoice_app import PDFGenerator

logger = setup_logger("FEImpresionASESYS.log")


def seleccionar_impresoras_y_copias(config_path):
    """Muestra una ventana para seleccionar impresoras y número de copias."""
    log_event(
        logger, "info", "Iniciando selección de impresoras y copias..."
    )  # Mensaje de depuración
    with open(config_path, "r") as file:
        config = json.load(file)

    # Crear la aplicación de PyQt5 si no existe
    app = QtWidgets.QApplication.instance()
    if app is None:
        log_event(
            logger, "info", "Inicializando QApplication..."
        )  # Mensaje de depuración
        app = QtWidgets.QApplication(sys.argv)

    dialog = QDialog()
    dialog.setWindowTitle("Impresión")
    dialog.resize(600, 400)  # Ajustar el tamaño de la ventana
    dialog.setFixedSize(600, 400)  # Fijar el tamaño de la ventana
    dialog.setWindowFlags(
        QtCore.Qt.Window
        | QtCore.Qt.WindowTitleHint
        | QtCore.Qt.CustomizeWindowHint
        | QtCore.Qt.WindowStaysOnTopHint
    )  # Siempre encima

    layout = QVBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)  # Márgenes internos

    # Título estilizado
    title_label = QLabel("Impresión")
    title_label.setStyleSheet(
        "font-size: 18px; font-weight: bold; margin-bottom: 20px;"
    )
    layout.addWidget(title_label)

    # Obtener lista de impresoras disponibles
    try:
        impresoras_disponibles = [
            printer[2]
            for printer in win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
        ]
    except Exception as e:
        log_event(logger, "info", f"Error al obtener la lista de impresoras: {e}")
        impresoras_disponibles = []

    # Selección de impresora principal
    label_impresora1 = QLabel("Seleccione la impresora:")
    label_impresora1.setStyleSheet("font-size: 14px; margin-bottom: 5px;")
    combo_impresora1 = QComboBox()
    combo_impresora1.addItems(impresoras_disponibles)
    combo_impresora1.setCurrentText(config.get("printer_name", ""))
    layout.addWidget(label_impresora1)
    layout.addWidget(combo_impresora1)

    # Selección de número de copias
    label_copias = QLabel("Número de copias:")
    label_copias.setStyleSheet("font-size: 14px; margin-top: 15px; margin-bottom: 5px;")
    input_copias = QLineEdit()
    input_copias.setText(str(config["copies"]))
    input_copias.setStyleSheet("padding: 5px; font-size: 14px;")
    layout.addWidget(label_copias)
    layout.addWidget(input_copias)

    # Botones de guardar y cerrar
    button_layout = QVBoxLayout()
    btn_guardar = QPushButton("Aceptar")
    btn_guardar.setStyleSheet(
        "background-color: #4CAF50; color: white; font-size: 14px; padding: 10px; border: none; border-radius: 5px;"
    )
    btn_guardar.clicked.connect(dialog.accept)
    button_layout.addWidget(btn_guardar)

    layout.addLayout(button_layout)
    dialog.setLayout(layout)

    # Centrar la ventana en la pantalla
    screen_geometry = app.desktop().screenGeometry()
    x = (screen_geometry.width() - dialog.width()) // 2
    y = (screen_geometry.height() - dialog.height()) // 2
    dialog.move(x, y)

    log_event(
        logger, "info", "Mostrando diálogo de selección de impresoras..."
    )  # Mensaje de depuración
    dialog.exec_()

    # Actualizar configuración si se guardó
    if dialog.result() == QDialog.Accepted:
        config["printer_name"] = combo_impresora1.currentText()
        config["copies"] = int(input_copias.text())
        with open(config_path, "w") as file:
            json.dump(config, file, indent=4)
        return config["printer_name"], config["printer_name2"], config["copies"]
    else:
        log_event(logger, "info", "El usuario cerró la ventana sin guardar.")
        return None, None, None


def crear_filtro_caja(caja, imprimir_sin_caja=False):
    """
    Función que recibe un string, lo convierte a mayúsculas,
    lo divide en caracteres individuales y crea una condición
    de filtro para cada carácter.

    Si imprimir_sin_caja es True, agrega la condición de incluir
    facturas cuyo primer carácter no sea letra.
    """
    filtrocaja = ""
    if caja:
        caja = caja.upper()
        condiciones = []

        for caracter in caja:
            condicion = f"SUBSTRING(NumeroFacturaInterna, 1, 1)='{caracter}'"
            condiciones.append(condicion)

        if condiciones:
            if imprimir_sin_caja:
                # OR extra con condición de NO ser letra
                filtrocaja = (
                    " AND (("
                    + " OR ".join(condiciones)
                    + ") OR SUBSTRING(NumeroFacturaInterna, 1, 1) NOT LIKE '[a-zA-Z]')"
                )
            else:
                filtrocaja = " AND (" + " OR ".join(condiciones) + ")"
    return filtrocaja


# Ensure GConfig has a method named cargar
# If not, define it in the appropriate module

if __name__ == "__main__":

    # Evitar que el programa se ejecute mas de una vez
    ################################################################################################
    lock_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "FEImpresionASESYS.lock"
    )

    # Abrir el archivo para bloqueo
    lock_file = open(lock_file_path, "w")
    try:
        # Intentar bloquear el archivo de forma exclusiva y no bloqueante
        portalocker.lock(lock_file, portalocker.LOCK_EX | portalocker.LOCK_NB)

        # Si llegamos aquí, tenemos el bloqueo

        # Escribir el PID para identificación
        lock_file.write(f"{os.getpid()}")
        lock_file.flush()
    except portalocker.LockException:
        print("¡Ya hay otra instancia del programa en ejecución!")
        sys.exit(1)
    ################################################################################################

    UnlockCK()
    # Check if GConfig.cargar exists and is correctly implemented
    try:
        GConfig.cargar(1)  # Cargar la configuración de impresoras con GConfig.cargar(1)
        log_event(logger, "info", "Configuracion Cargada")
    except AttributeError as e:
        log_event(logger, "info", f"Error: {e}")
        # Handle the error or define the method if missing

    # Conexión a la base de datos J
    cn1 = ConectarDB()
    frame = inspect.currentframe()
    archivo = frame.f_code.co_filename
    mostrarConfiguracion(GConfig, cn1, archivo)

    PConfig = load_printer_config()

    caja = PConfig.get("caja", None)
    imprimir_sin_caja = PConfig.get("imprimir_sin_caja", False)
    Impresion_grande = PConfig.get("Impresion_grande", 0)
    impresion_pdv = PConfig.get("impresion_pdv", 0)
    sinpdf = PConfig.get("sinpdf", 0)
    tipo_pago_grande = PConfig.get("tipo_pago_grande", "CRCO")
    tipo_pago_pdv = PConfig.get("tipo_pago_pdv", "CRCO")
    con_pantalla = PConfig.get("conpantalla", 0)
    config_path = PConfig.get("config_path1", "config.json")
    EquipoImpresion = PConfig.get("EquipoImpresion", None)

    # Abrir asistente

    # Asegurar la tabla de log de actividades

    ensure_table("LogActividadesFE", campos_log)

    while True:
        try:
            filtrocaja = ""
            if caja is not None:
                filtrocaja = crear_filtro_caja(caja, imprimir_sin_caja)
            filtroequipo = ""
            if EquipoImpresion is not None:
                if isinstance(EquipoImpresion, list):
                    # Si es una lista, crear condiciones OR para cada valor
                    condiciones = [
                        f"EquipoImpresion = '{equipo}'" for equipo in EquipoImpresion
                    ]
                    filtroequipo = " AND (" + " OR ".join(condiciones) + ")"
                else:
                    # Si es un solo valor, mantener el comportamiento actual
                    filtroequipo = f" AND EquipoImpresion = '{EquipoImpresion}'"
            query = (
                "SELECT * FROM vFEEncabezado "
                "WHERE EstadoFiscal in(5,6) AND codigoseguridad is not null AND EstadoImpresion in(1,3) "
                + filtrocaja
                + filtroequipo
                + " ORDER BY FechaCreacion"
            )
            # log_event(logger, "info", query)
            vFEEncabezado = cn1.fetch_query(query)

            for row in vFEEncabezado:
                try:
                    (
                        company_data,
                        invoice_data,
                        products,
                        forms,
                        descuento_recargo,
                    ) = fetch_invoice_data(cn1, row.RNCEmisor.strip(), row.eNCF.strip())

                    invoice_app = PDFGenerator(
                        company_data,
                        invoice_data,
                        products,
                        forms,
                        descuento_recargo,
                    )

                    impresion = Impresion(
                        company_data,
                        invoice_data,
                        products,
                        forms,
                        descuento_recargo,
                    )

                    NombrePDF = f"{row.RNCEmisor.strip()}{row.eNCF.strip()}"
                    Ruta = os.path.join(os.path.abspath(os.sep), "XMLValidar", "RI")
                    extension = ".pdf"

                    # Crear nombre completo del archivo
                    nombre_archivo = os.path.join(Ruta, f"{NombrePDF}{extension}")

                    # Si existe, crear un nombre único
                    contador = 1
                    while os.path.exists(nombre_archivo):
                        nombre_archivo = os.path.join(
                            Ruta, f"{NombrePDF}_{contador}{extension}"
                        )
                        contador += 1

                    if con_pantalla == 1:
                        log_event(
                            logger,
                            "info",
                            "Mostrando pantalla de selección de impresoras...",
                        )  # Mensaje de depuración
                        printer_name, printer_name2, copies = (
                            seleccionar_impresoras_y_copias(config_path)
                        )
                        log_event(
                            logger,
                            "info",
                            f"Impresora principal: {printer_name}, Impresora secundaria: {printer_name2}, Copias: {copies}",
                        )

                    if tipo_pago_grande == "CO" and Impresion_grande == 1:

                        if row.TipoPago == 1 and row.TipoECF in [
                            "31",
                            "32",
                            "44",
                            "45",
                            "46",
                            "41",
                            "47",
                        ]:
                            if sinpdf == 0:
                                invoice_app.print_pdf2(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf2(Ruta, nombre_archivo)

                        # Nota de débito
                        elif row.TipoPago == 1 and row.TipoECF == "33":
                            if sinpdf == 0:
                                invoice_app.print_pdf_nota_debito(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf_nota_debito(Ruta, nombre_archivo)

                        # Nota de crédito
                        elif (
                            row.TipoPago == 1
                            and row.TipoECF == "34"
                            and row.TipoDocumento.strip() == "02"
                        ):
                            if sinpdf == 0:
                                invoice_app.print_pdf_nota_credito(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf_nota_credito(Ruta, nombre_archivo)

                        # Otros tipos de documentos
                        elif (
                            row.TipoPago == 1
                            and row.TipoECF == "34"
                            and row.TipoDocumento.strip() in ["03", "17", "05"]
                        ):
                            if sinpdf == 0:
                                invoice_app.print_pdf2(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf2(Ruta, nombre_archivo)

                        # Caja chica
                        elif row.TipoPago == 1 and row.TipoECF == "43":
                            if sinpdf == 0:
                                invoice_app.print_pdf_caja_chica(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf_caja_chica(Ruta, nombre_archivo)

                    if tipo_pago_grande == "CR" and Impresion_grande == 1:

                        if row.TipoPago == 2 and row.TipoECF in [
                            "31",
                            "32",
                            "44",
                            "45",
                            "46",
                            "41",
                            "47",
                        ]:
                            if sinpdf == 0:
                                invoice_app.print_pdf2(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf2(Ruta, nombre_archivo)

                        # Nota de débito
                        elif row.TipoPago == 2 and row.TipoECF == "33":
                            if sinpdf == 0:
                                invoice_app.print_pdf_nota_debito(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf_nota_debito(Ruta, nombre_archivo)

                        # Nota de crédito
                        elif (
                            row.TipoPago == 2
                            and row.TipoECF == "34"
                            and row.TipoDocumento.strip() == "02"
                        ):
                            if sinpdf == 0:
                                invoice_app.print_pdf_nota_credito(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf_nota_credito(Ruta, nombre_archivo)

                        # Otros tipos de documentos
                        elif (
                            row.TipoPago == 2
                            and row.TipoECF == "34"
                            and row.TipoDocumento.strip() in ["03", "17", "05"]
                        ):
                            if sinpdf == 0:
                                invoice_app.print_pdf2(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf2(Ruta, nombre_archivo)

                        # Caja chica
                        elif row.TipoPago == 2 and row.TipoECF == "43":
                            if sinpdf == 0:
                                invoice_app.print_pdf_caja_chica(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf_caja_chica(Ruta, nombre_archivo)

                    if tipo_pago_pdv == "CO" and impresion_pdv == 1:

                        if row.TipoPago == 1 and row.TipoECF in [
                            "31",
                            "32",
                            "44",
                            "45",
                            "46",
                            "41",
                            "47",
                        ]:
                            if sinpdf == 0:
                                impresion.imprimir_factura(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                                # Nota de débito
                        if row.TipoPago == 1 and row.TipoECF == "33":
                            if sinpdf == 0:
                                impresion.imprimir_nota_debito(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_nota_debitospdf(Ruta, nombre_archivo)

                                # Nota de crédito
                        if (
                            row.TipoPago == 1
                            and row.TipoECF == "34"
                            and row.TipoDocumento.strip() == "02"
                        ):
                            if sinpdf == 0:
                                impresion.imprimir_nota_credito(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_nota_creditospdf(
                                    Ruta, nombre_archivo
                                )

                                # Otros tipos de documentos
                        elif (
                            row.TipoPago == 1
                            and row.TipoECF == "34"
                            and row.TipoDocumento.strip() in ["03", "17", "05"]
                        ):
                            if sinpdf == 0:
                                impresion.imprimir_factura(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                                # Caja chica
                        elif (
                            row.TipoPago == 1
                            and impresion_pdv == 1
                            and row.TipoECF == "43"
                        ):
                            if sinpdf == 0:
                                impresion.imprimir_caja_chica(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_caja_chicaspdf(Ruta, nombre_archivo)

                    if tipo_pago_pdv == "CR" and impresion_pdv == 1:

                        if row.TipoPago == 2 and row.TipoECF in [
                            "31",
                            "32",
                            "44",
                            "45",
                            "46",
                            "41",
                            "47",
                        ]:
                            if sinpdf == 0:
                                impresion.imprimir_factura(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                                # Nota de débito
                        if row.TipoPago == 2 and row.TipoECF == "33":
                            if sinpdf == 0:
                                impresion.imprimir_nota_debito(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_nota_debitospdf(Ruta, nombre_archivo)

                                # Nota de crédito
                        if (
                            row.TipoPago == 2
                            and row.TipoECF == "34"
                            and row.TipoDocumento.strip() == "02"
                        ):
                            if sinpdf == 0:
                                impresion.imprimir_nota_credito(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_nota_creditospdf(
                                    Ruta, nombre_archivo
                                )

                                # Otros tipos de documentos
                        elif (
                            row.TipoPago == 2
                            and row.TipoECF == "34"
                            and row.TipoDocumento.strip() in ["03", "17", "05"]
                        ):
                            if sinpdf == 0:
                                impresion.imprimir_factura(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                                # Caja chica
                        elif (
                            row.TipoPago == 2
                            and impresion_pdv == 1
                            and row.TipoECF == "43"
                        ):
                            if sinpdf == 0:
                                impresion.imprimir_caja_chica(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_caja_chicaspdf(Ruta, nombre_archivo)

                    if tipo_pago_pdv == "CRCO" or tipo_pago_grande == "CRCO":
                        # Generar el PDF según el tipo de documento
                        if Impresion_grande == 1 and row.TipoECF in [
                            "31",
                            "32",
                            "44",
                            "45",
                            "46",
                            "41",
                            "47",
                        ]:
                            if sinpdf == 0:
                                invoice_app.print_pdf2(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf2(Ruta, nombre_archivo)
                        elif impresion_pdv == 1 and row.TipoECF in [
                            "31",
                            "32",
                            "44",
                            "45",
                            "46",
                            "41",
                            "47",
                        ]:
                            if sinpdf == 0:
                                impresion.imprimir_factura(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                        # Nota de débito
                        elif Impresion_grande == 1 and row.TipoECF == "33":
                            if sinpdf == 0:
                                invoice_app.print_pdf_nota_debito(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf_nota_debito(Ruta, nombre_archivo)
                        elif impresion_pdv == 1 and row.TipoECF == "33":
                            if sinpdf == 0:
                                impresion.imprimir_nota_debito(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_nota_debitospdf(Ruta, nombre_archivo)

                        # Nota de crédito
                        elif (
                            Impresion_grande == 1
                            and row.TipoECF == "34"
                            and row.TipoDocumento.strip() == "02"
                        ):
                            if sinpdf == 0:
                                invoice_app.print_pdf_nota_credito(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf_nota_credito(Ruta, nombre_archivo)
                        elif (
                            impresion_pdv == 1
                            and row.TipoECF == "34"
                            and row.TipoDocumento.strip() == "02"
                        ):
                            if sinpdf == 0:
                                impresion.imprimir_nota_credito(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_nota_creditospdf(
                                    Ruta, nombre_archivo
                                )

                        # Otros tipos de documentos
                        elif (
                            Impresion_grande == 1
                            and row.TipoECF == "34"
                            and row.TipoDocumento.strip() in ["03", "17", "05"]
                        ):
                            if sinpdf == 0:
                                invoice_app.print_pdf2(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf2(Ruta, nombre_archivo)
                        elif (
                            impresion_pdv == 1
                            and row.TipoECF == "34"
                            and row.TipoDocumento.strip() in ["03", "17", "05"]
                        ):
                            if sinpdf == 0:
                                impresion.imprimir_factura(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_facturaspdf(Ruta, nombre_archivo)

                        # Caja chica
                        elif Impresion_grande == 1 and row.TipoECF == "43":
                            if sinpdf == 0:
                                invoice_app.print_pdf_caja_chica(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                invoice_app.print_pdf_caja_chica(Ruta, nombre_archivo)
                        elif impresion_pdv == 1 and row.TipoECF == "43":
                            if sinpdf == 0:
                                impresion.imprimir_caja_chica(Ruta, nombre_archivo)
                            elif sinpdf == 1:
                                impresion.imprimir_caja_chicaspdf(Ruta, nombre_archivo)

                    query = (
                        f"UPDATE {row.Tabla.strip()} "
                        f"SET EstadoImpresion = 2 "
                        f"WHERE {row.campo1.strip()} = '{row.RNCEmisor.strip()}' "
                        f"AND {row.campo2.strip()} = '{row.eNCF.strip()}'"
                    )
                    cn1.execute_query(query)

                    imp = ""
                    if Impresion_grande == 1:
                        imp = PConfig.get("printer_name", "")
                    elif impresion_pdv == 1:
                        imp = PConfig.get("printer_name2", "")

                    registrar_actividad_log(
                        row.RNCEmisor.strip() if row.RNCEmisor else "",
                        row.eNCF.strip() if row.eNCF else "",
                        "Impresión",
                        datetime.now(),
                        EquipoImpresion or "",
                        Ruta or "",
                        imp or "",
                    )
                except Exception as e:
                    log_event(
                        logger,
                        "info",
                        f"Error procesando documento {row.eNCF.strip()}: {e}",
                    )

            # Pequeña pausa opcional para no saturar
            # time.sleep(5)

        except Exception as e:
            log_event(logger, "info", f"Error en el bucle principal: {e}")
        finally:
            # Desbloquear el archivo al salir
            lock_file.close()
