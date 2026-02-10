import os
import sys
import threading
import time

import pyodbc
import pystray
import requests
import win32print  # Asegúrate de que este módulo esté importado
from PIL import Image, ImageDraw
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

from db.database import *
from db.database import fetch_invoice_data
from db.uDB import *
from glib.ufe import *
from glib.ufe import GConfig
from logG import log_event, setup_logger

# from glib.ufe import GConfig
from print.impresion import *
from print.pdf_generator import PDFGenerator

logger = setup_logger("FEImpresionASESYS.log")


def create_image():
    """Crear el ícono para la bandeja del sistema"""
    image = Image.new("RGB", (64, 64), color=(0, 128, 0))
    d = ImageDraw.Draw(image)
    d.rectangle((16, 16, 48, 48), fill=(255, 255, 0))
    return image


def mostrar_info(icon, item):
    """Mostrar información del estado del programa"""
    icon.notify("ASESYS Impresión", "Proceso de impresión activo")


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


def proceso_principal():
    # Variables globales necesarias
    global caja, imprimir_sin_caja, Impresion_grande, impresion_pdv, sinpdf
    global tipo_pago_grande, tipo_pago_pdv, con_pantalla, config_path
    global cn1, logger

    while True:
        try:
            filtrocaja = ""
            if caja is not None:
                caja = caja.upper()
                filtrocaja = f" AND {'(' if imprimir_sin_caja else ''}SUBSTRING(NumeroFacturaInterna, 1, 1)='{caja}' {" OR SUBSTRING(NumeroFacturaInterna, 1, 1) NOT LIKE '[a-zA-Z]' )" if imprimir_sin_caja else '' }"

            query = (
                "SELECT * FROM vFEEncabezado "
                "WHERE EstadoFiscal >= 3 AND EstadoFiscal < 90 AND EstadoImpresion in(1,3) "
                + filtrocaja
                + "ORDER BY FechaCreacion"
            )
            vFEEncabezado = cn1.fetch_query(query)

            for row in vFEEncabezado:
                if row.EstadoFiscal >= 3 and (
                    row.EstadoImpresion == 1 or row.EstadoImpresion == 3
                ):
                    try:
                        (
                            company_data,
                            invoice_data,
                            products,
                            forms,
                            descuento_recargo,
                        ) = fetch_invoice_data(
                            cn1, row.RNCEmisor.strip(), row.eNCF.strip()
                        )

                        pdf_generator = PDFGenerator(
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
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)

                            # Nota de débito
                            elif row.TipoPago == 1 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )

                            # Nota de crédito
                            elif (
                                row.TipoPago == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )

                            # Otros tipos de documentos
                            elif (
                                row.TipoPago == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)

                            # Caja chica
                            elif row.TipoPago == 1 and row.TipoECF == "43":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )

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
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)

                            # Nota de débito
                            elif row.TipoPago == 2 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )

                            # Nota de crédito
                            elif (
                                row.TipoPago == 2
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )

                            # Otros tipos de documentos
                            elif (
                                row.TipoPago == 2
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() in ["03", "17", "05"]
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)

                            # Caja chica
                            elif row.TipoPago == 2 and row.TipoECF == "43":
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )

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
                                    impresion.imprimir_nota_debitospdf(
                                        Ruta, nombre_archivo
                                    )

                                    # Nota de crédito
                            if (
                                row.TipoPago == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_nota_credito(
                                        Ruta, nombre_archivo
                                    )
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
                                    impresion.imprimir_caja_chicaspdf(
                                        Ruta, nombre_archivo
                                    )

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
                                    impresion.imprimir_nota_debitospdf(
                                        Ruta, nombre_archivo
                                    )

                                    # Nota de crédito
                            if (
                                row.TipoPago == 2
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_nota_credito(
                                        Ruta, nombre_archivo
                                    )
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
                                    impresion.imprimir_caja_chicaspdf(
                                        Ruta, nombre_archivo
                                    )

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
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
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
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_debito(
                                        Ruta, nombre_archivo
                                    )
                            elif impresion_pdv == 1 and row.TipoECF == "33":
                                if sinpdf == 0:
                                    impresion.imprimir_nota_debito(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_nota_debitospdf(
                                        Ruta, nombre_archivo
                                    )

                            # Nota de crédito
                            elif (
                                Impresion_grande == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_nota_credito(
                                        Ruta, nombre_archivo
                                    )
                            elif (
                                impresion_pdv == 1
                                and row.TipoECF == "34"
                                and row.TipoDocumento.strip() == "02"
                            ):
                                if sinpdf == 0:
                                    impresion.imprimir_nota_credito(
                                        Ruta, nombre_archivo
                                    )
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
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf2(Ruta, nombre_archivo)
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
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )
                                elif sinpdf == 1:
                                    pdf_generator.print_pdf_caja_chica(
                                        Ruta, nombre_archivo
                                    )
                            elif impresion_pdv == 1 and row.TipoECF == "43":
                                if sinpdf == 0:
                                    impresion.imprimir_caja_chica(Ruta, nombre_archivo)
                                elif sinpdf == 1:
                                    impresion.imprimir_caja_chicaspdf(
                                        Ruta, nombre_archivo
                                    )

                        query = (
                            f"UPDATE {row.Tabla.strip()} "
                            f"SET EstadoImpresion = 2 "
                            f"WHERE {row.campo1.strip()} = '{row.RNCEmisor.strip()}' "
                            f"AND {row.campo2.strip()} = '{row.eNCF.strip()}'"
                        )
                        cn1.execute_query(query)

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
        time.sleep(5)


# Ensure GConfig has a method named cargar
# If not, define it in the appropriate module

if __name__ == "__main__":
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
    mostrarConfiguracion(GConfig, cn1)
    PConfig = load_printer_config()

    caja = PConfig.get("caja", "")
    imprimir_sin_caja = PConfig.get("imprimir_sin_caja", False)
    Impresion_grande = PConfig.get("Impresion_grande", 0)
    impresion_pdv = PConfig.get("impresion_pdv", 0)
    sinpdf = PConfig.get("sinpdf", 0)
    tipo_pago_grande = PConfig.get("tipo_pago_grande", "CRCO")
    tipo_pago_pdv = PConfig.get("tipo_pago_pdv", "CRCO")
    con_pantalla = PConfig.get("conpantalla", 0)
    config_path = PConfig.get("config_path1", "config.json")

    # Crear y configurar el icono del system tray
    icon = pystray.Icon("ASESYS", icon=create_image(), title="ASESYS Impresión")

    # Configurar menú simple
    icon.menu = pystray.Menu(pystray.MenuItem("Estado", mostrar_info, default=True))

    # Iniciar el proceso principal en un hilo separado
    thread_principal = threading.Thread(target=proceso_principal, daemon=True)
    thread_principal.start()

    # Ejecutar el icono en la bandeja del sistema
    log_event(logger, "info", "Iniciando aplicación en la bandeja del sistema")
    icon.run()
