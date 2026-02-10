import base64
import io
import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from zoneinfo import ZoneInfo

import num2words
import qrcode
import win32api
import win32print
from babel.dates import format_datetime
from PIL import Image
from PyQt5 import QtCore, QtGui, QtPrintSupport, QtWidgets
from PyQt5.QtCore import QDateTime, QSizeF, Qt
from PyQt5.QtGui import QPageSize, QPainter
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter, QPrinterInfo
from PyQt5.QtWidgets import QApplication, QFileDialog

# Configurar zona horaria de República Dominicana
rd_timezone = ZoneInfo("America/Santo_Domingo")
now = datetime.now(rd_timezone)


class PDFGenerator:
    def __init__(self, company_data, invoice_data, products, forms, descuento_recargo):
        self.company_data = company_data
        self.invoice_data = invoice_data
        self.products = products
        self.forms = forms
        self.descuento_recargo = descuento_recargo
        self.printer_name = self.get_printer_name()

        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # ________________________________FACTURA______________________________________________________________________

    def generate_pdf(self, printer, copy_label=None):
        document = QtGui.QTextDocument()

        def load_printer_config():
            """Carga la configuración de la impresora desde un archivo JSON."""
            config_path = "config/config_print.json"
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    config = json.load(file)
                    return {
                        "printer_name": config.get("printer_name", None),
                        "copies": config.get(
                            "copies", 1
                        ),  # Default to 1 copy if not specified
                        "copy_labels": config.get(
                            "copy_labels",
                            [
                                "ORIGINAL - CLIENTE",
                                "COPIA - CAJA",
                                "COPIA - CONTABILIDAD",
                                "COPIA - ARCHIVO",
                            ],
                        ),
                        "nump": config.get("nump", 0),
                        "concodigo": config.get(
                            "concodigo", 0
                        ),  # Add default value here
                        "conunidad": config.get("conunidad", 0),
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                print(
                    "Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada."
                )
                return {
                    "printer_name": None,
                    "copies": 0,
                    "concodigo": 0,
                    "conunidad": 0,
                    "nump": 0,
                }

        def calculate_lines_for_product(product, max_line_length=50):
            """
            Calcula cuántas líneas ocupa un producto basado en la longitud de su descripción.

            Args:
                product (dict): Producto con la clave 'descripcion'.
                max_line_length (int): Longitud máxima de una línea antes de dividir.

            Returns:
                int: Número de líneas que ocupa el producto.
            """
            description = product.get("descripcion", "")
            return (len(description) // max_line_length) + 1

        def split_products_into_pages(products, products_per_page, max_line_length=50):
            """
            Divide los productos en páginas considerando que algunos productos pueden ocupar más de una línea.

            Args:
                products (list): Lista de productos.
                products_per_page (int): Número máximo de líneas por página.
                max_line_length (int): Longitud máxima de una línea antes de dividir.

            Returns:
                dict: Diccionario con las claves 'pages' y 'counts_per_page'.
                    'pages' contiene las listas de productos por página.
                    'counts_per_page' contiene la cantidad de productos por cada página.
            """
            pages = []
            counts_per_page = []
            current_page = []
            current_count = 0

            for product in products:
                lines = calculate_lines_for_product(product, max_line_length)
                if current_count + lines > products_per_page:
                    pages.append(current_page)
                    counts_per_page.append(len(current_page))
                    current_page = []
                    current_count = 0
                current_page.append(product)
                current_count += lines

            if current_page:
                pages.append(current_page)
                counts_per_page.append(len(current_page))

            return {"pages": pages, "counts_per_page": counts_per_page}

        # Calculate how many products per page
        config = load_printer_config()
        nump = config.get(
            "nump", 0
        )  # Default to 0 if not specified in the configuration
        PRODUCTS_PER_PAGE = nump

        # Split products into pages
        results = split_products_into_pages(self.products, PRODUCTS_PER_PAGE)
        pages = results["pages"]
        counts_per_page = [count for count in results["counts_per_page"]]
        total_pages = len(pages)

        # Initialize final HTML
        final_html = []

        for page_index, page_products in enumerate(pages):
            current_page = page_index + 1
            is_last_page = current_page == total_pages

            # Generate HTML for current page's products and get running totals
            products_html, total_descuento, total_quantity, note3, pagos_html = (
                self.generate_products_html_page(
                    page_products, self.forms, include_totals=is_last_page
                )
            )

            # Calculate total only on the last page

            # Get additional fields for the last page
            note = (
                "\n".join(
                    self.invoice_data.get("observacion", "").replace("|", ".<br>")
                    for _ in [1]
                )
                if is_last_page
                else ""
            )
            note2 = (
                "\n".join(
                    self.invoice_data.get("nota", "").replace("|", ".<br>") for _ in [1]
                )
                if is_last_page
                else ""
            )
            note4 = (
                "\n".join(
                    self.invoice_data.get("NotaPago", "").replace("|", ".<br>")
                    for _ in [1]
                )
                if is_last_page
                else ""
            )
            realizado = self.invoice_data.get("cajero") if is_last_page else ""
            codigoseguridad = (
                self.invoice_data.get("codigoseguridad", "") if is_last_page else ""
            )
            fechafirma = self.invoice_data.get("fechafirma", "") if is_last_page else ""
            url_qr = self.invoice_data.get("URLQR", "") if is_last_page else ""

            # Generate QR code only on the last page
            qr_image = self.generate_qr_code(url_qr) if is_last_page else ""

            # Generate page HTML - pass current_page and total_pages to header
            page_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; font-size: 5pt; margin: 20px; width=100%;">
                    {self.generate_header_html(current_page, total_pages, copy_label)}
                    {self.generate_detail_html_page(products_html, pagos_html, total_descuento, is_last_page, total_quantity, counts_per_page)}
                    {self.generate_footer_html(note, note2, note3, note4, realizado, qr_image, codigoseguridad, fechafirma, total_quantity, copy_label) if is_last_page else self.generate_page_footer(counts_per_page)}
                </body>
                </html>
            """

            final_html.append(page_html)

        # Join all pages with page breaks
        complete_html = '<div style="page-break-after: always;"></div>'.join(final_html)
        document.setHtml(complete_html)

        # Configure printer settings
        printer.setOrientation(QPrinter.Portrait)
        printer.setPageSize(QPageSize(QPageSize.Letter))
        printer.setResolution(300)

        # Configure margins
        margin = 0.5
        printer.setPageMargins(margin, margin, margin, margin, QPrinter.Point)

        # Set document size
        page_width = 6.5 * 72
        page_height = 9 * 72
        document.setPageSize(QtCore.QSizeF(page_width, page_height))

        # Print document
        document.print_(printer)

    # ______________________________NOTA DE DEBITO__________________________________________________________________________

    def generate_pdf6(self, printer, copy_label=None):
        # Configura los márgenes de la impresión (en milímetros)
        document = QtGui.QTextDocument()

        # Get note and user who created the invoice
        note = self.invoice_data.get("observacion", "")
        realizado = self.invoice_data.get("cajero", "")

        # Get additional fields
        codigoseguridad = self.invoice_data.get("codigoseguridad", "")
        fechafirma = self.invoice_data.get("fechafirma", "")
        url_qr = self.invoice_data.get("URLQR", "")

        # Generate QR code as base64 image
        qr_image = self.generate_qr_code(url_qr)

        # Load custom layout template if available
        custom_layout = self.load_custom_layout()

        if custom_layout:
            try:
                # Prepare replacements for placeholders in the template
                replacements = {
                    "{note}": note,
                    "{realizado}": realizado,
                    "{qr_image}": qr_image,
                    "{codigoseguridad}": codigoseguridad,
                    "{fechafirma}": fechafirma,
                }
                # Add company and invoice data to replacements
                for key, value in {**self.company_data, **self.invoice_data}.items():
                    replacements[f"{{{key}}}"] = str(value)

                # Replace all placeholders in the custom layout
                for placeholder, replacement in replacements.items():
                    custom_layout = custom_layout.replace(placeholder, replacement)

                html = custom_layout
            except Exception as e:
                print(f"Error applying custom layout: {str(e)}")
                # Use default layout if an error occurs
                html = self.generate_default_html6(
                    realizado, qr_image, codigoseguridad, fechafirma, copy_label
                )
        else:
            html = self.generate_default_html6(
                realizado, qr_image, codigoseguridad, fechafirma, copy_label
            )

        document.setHtml(html)

        # Configura la orientación y el tamaño de la página
        printer.setOrientation(QPrinter.Portrait)
        printer.setPageSize(QPageSize(QPageSize.Letter))

        printer.setResolution(300)

        # Configurar márgenes fijos (en puntos)
        margin = 0.5  # 0.5 pulgadas = 36 puntos
        printer.setPageMargins(margin, margin, margin, margin, QPrinter.Point)

        # Establece el tamaño del documento en función del tamaño de la página del PDF
        page_width = 6.5 * 72  # 72 puntos por pulgada
        page_height = 9 * 72

        # Configurar el tamaño de página fijo
        document.setPageSize(QtCore.QSizeF(page_width, page_height))

        if (
            document.pageSize().width() != page_width
            or document.pageSize().height() != page_height
        ):
            print("Error: El tamaño de la página no es consistente")
            return

        # Imprime el documento en el PDF
        document.print_(printer)

    # ________________________________RECIBO DE INGRESO_____________________________________________________________________

    def generate_pdf5(self, printer):
        # Configura los márgenes de la impresión (en milímetros)
        document = QtGui.QTextDocument()

        # Generate HTML for products and calculate totals
        products_html, subtotal, total_descuento = self.generate_products_html5()
        total = subtotal - total_descuento

        # Get note and user who created the invoice
        note = self.invoice_data.get("observacion", "")
        realizado = self.invoice_data.get("usuario", "")

        # Get additional fields
        codigoseguridad = self.invoice_data.get("codigoseguridad", "")
        fechafirma = self.invoice_data.get("fechafirma", "")
        url_qr = self.invoice_data.get("URLQR", "")

        # Generate QR code as base64 image
        qr_image = self.generate_qr_code(url_qr)

        # Load custom layout template if available
        custom_layout = self.load_custom_layout()

        if custom_layout:
            try:
                # Prepare replacements for placeholders in the template
                replacements = {
                    "{products_html}": products_html,
                    "{subtotal}": f"{subtotal:.2f}",
                    "{total_descuento}": f"{total_descuento:.2f}",
                    "{total}": f"{total:.2f}",
                    "{note}": note,
                    "{realizado}": realizado,
                    "{qr_image}": qr_image,
                    "{codigoseguridad}": codigoseguridad,
                    "{fechafirma}": fechafirma,
                }
                # Add company and invoice data to replacements
                for key, value in {**self.company_data, **self.invoice_data}.items():
                    replacements[f"{{{key}}}"] = str(value)

                # Replace all placeholders in the custom layout
                for placeholder, replacement in replacements.items():
                    custom_layout = custom_layout.replace(placeholder, replacement)

                html = custom_layout
            except Exception as e:
                print(f"Error applying custom layout: {str(e)}")
                # Use default layout if an error occurs
                html = self.generate_default_html5(
                    products_html,
                    subtotal,
                    total_descuento,
                    total,
                    note,
                    realizado,
                    qr_image,
                    codigoseguridad,
                    fechafirma,
                )
        else:
            html = self.generate_default_html5(
                products_html,
                subtotal,
                total_descuento,
                total,
                note,
                realizado,
                qr_image,
                codigoseguridad,
                fechafirma,
            )

        document.setHtml(html)

        # Configura la orientación y el tamaño de la página
        printer.setOrientation(QPrinter.Portrait)
        printer.setPageSize(QPageSize(QPageSize.Letter))

        printer.setResolution(300)

        # Configurar márgenes fijos (en puntos)
        margin = 0.5  # 0.5 pulgadas = 36 puntos
        printer.setPageMargins(margin, margin, margin, margin, QPrinter.Point)

        # Establece el tamaño del documento en función del tamaño de la página del PDF
        page_width = 6.5 * 72  # 72 puntos por pulgada
        page_height = 9 * 72

        # Configurar el tamaño de página fijo
        document.setPageSize(QtCore.QSizeF(page_width, page_height))

        print(f"DPI: {printer.resolution()}")
        print(
            f"Tamaño de página: {document.pageSize().width()} x {document.pageSize().height()}"
        )

        if (
            document.pageSize().width() != page_width
            or document.pageSize().height() != page_height
        ):
            print("Error: El tamaño de la página no es consistente")
            return

        pages = self.split_into_pages(html, page_height)

        # Crear un nuevo documento para cada página con el número de página
        full_html = ""
        for page_num, page_content in enumerate(pages, start=1):
            page_footer = """
            """
            full_html += page_content + page_footer

        # Establecer el contenido HTML completo del documento
        document.setHtml(full_html)

        # Imprime el documento en el PDF
        document.print_(printer)

    def split_into_pages(self, html, page_height):
        """
        Divide el contenido HTML en páginas basadas en la altura de la página.
        """
        # Dividir el contenido en líneas
        lines = html.split("\n")
        pages = []
        current_page = ""
        current_height = 0

        for line in lines:
            # Calcular la altura aproximada de la línea (ajustar según sea necesario)
            line_height = len(line) * 0.0277  # Aproximación simple

            if current_height + line_height > page_height:
                # Si la línea no cabe en la página actual, iniciar una nueva página
                pages.append(current_page)
                current_page = line
                current_height = line_height
            else:
                # Agregar la línea a la página actual
                current_page += "\n" + line
                current_height += line_height

        # Agregar la última página
        if current_page:
            pages.append(current_page)

        return pages

    # ___________________________________________________CAJA CHICA___________________________________________________

    def generate_pdf4(self, printer):
        # Configura los márgenes de la impresión (en milímetros)
        document = QtGui.QTextDocument()

        # Generate HTML for products and calculate totals
        products_html, subtotal, total_descuento = self.generate_products_html4()
        total = subtotal - total_descuento

        # Get note and user who created the invoice
        note = self.invoice_data.get("observacion", "")
        realizado = self.invoice_data.get("usuario", "")
        recibido = self.invoice_data.get("")

        # Get additional fields
        codigoseguridad = self.invoice_data.get("codigoseguridad", "")
        fechafirma = self.invoice_data.get("fechafirma", "")
        url_qr = self.invoice_data.get("URLQR", "")

        # Generate QR code as base64 image
        qr_image = self.generate_qr_code(url_qr)

        # Load custom layout template if available
        custom_layout = self.load_custom_layout()

        if custom_layout:
            try:
                # Prepare replacements for placeholders in the template
                replacements = {
                    "{products_html}": products_html,
                    "{subtotal}": f"{subtotal:.2f}",
                    "{total_descuento}": f"{total_descuento:.2f}",
                    "{total}": f"{total:.2f}",
                    "{note}": note,
                    "{realizado}": realizado,
                    "{qr_image}": qr_image,
                    "{codigoseguridad}": codigoseguridad,
                    "{fechafirma}": fechafirma,
                }
                # Add company and invoice data to replacements
                for key, value in {**self.company_data, **self.invoice_data}.items():
                    replacements[f"{{{key}}}"] = str(value)

                # Replace all placeholders in the custom layout
                for placeholder, replacement in replacements.items():
                    custom_layout = custom_layout.replace(placeholder, replacement)

                html = custom_layout
            except Exception as e:
                print(f"Error applying custom layout: {str(e)}")
                # Use default layout if an error occurs
                html = self.generate_default_html4(
                    products_html,
                    subtotal,
                    total_descuento,
                    total,
                    note,
                    recibido,
                    realizado,
                    qr_image,
                    codigoseguridad,
                    fechafirma,
                )
        else:
            html = self.generate_default_html4(
                products_html,
                subtotal,
                total_descuento,
                total,
                note,
                recibido,
                realizado,
                qr_image,
                codigoseguridad,
                fechafirma,
            )

        document.setHtml(html)

        # Configura la orientación y el tamaño de la página
        printer.setOrientation(QPrinter.Portrait)
        printer.setPageSize(QPageSize(QPageSize.Letter))

        printer.setResolution(300)

        # Configurar márgenes fijos (en puntos)
        margin = 0.5  # 0.5 pulgadas = 36 puntos
        printer.setPageMargins(margin, margin, margin, margin, QPrinter.Point)

        # Establece el tamaño del documento en función del tamaño de la página del PDF
        page_width = 6.5 * 72  # 72 puntos por pulgada
        page_height = 9 * 72

        # Configurar el tamaño de página fijo
        document.setPageSize(QtCore.QSizeF(page_width, page_height))

        print(f"DPI: {printer.resolution()}")
        print(
            f"Tamaño de página: {document.pageSize().width()} x {document.pageSize().height()}"
        )

        if (
            document.pageSize().width() != page_width
            or document.pageSize().height() != page_height
        ):
            print("Error: El tamaño de la página no es consistente")
            return

        pages = self.split_into_pages(html, page_height)
        # Crear un nuevo documento para cada página con el número de página
        full_html = ""
        for page_num, page_content in enumerate(pages, start=1):
            page_footer = """
            """
            full_html += page_content + page_footer

        # Establecer el contenido HTML completo del documento
        document.setHtml(full_html)

        # Imprime el documento en el PDF
        document.print_(printer)

    def split_into_pages(self, html, page_height):
        """
        Divide el contenido HTML en páginas basadas en la altura de la página.
        """
        # Dividir el contenido en líneas
        lines = html.split("\n")
        pages = []
        current_page = ""
        current_height = 0

        for line in lines:
            # Calcular la altura aproximada de la línea (ajustar según sea necesario)
            line_height = len(line) * 0.0277  # Aproximación simple

            if current_height + line_height > page_height:
                # Si la línea no cabe en la página actual, iniciar una nueva página
                pages.append(current_page)
                current_page = line
                current_height = line_height
            else:
                # Agregar la línea a la página actual
                current_page += "\n" + line
                current_height += line_height

        # Agregar la última página
        if current_page:
            pages.append(current_page)

        return pages

    # ___________________________________________________RECIVO DE INGRESO____________________________________________

    def generate_products_html5(self):
        products_html = ""
        subtotal = Decimal("0.00")
        total_descuento = Decimal("0.00")
        tasa1 = self.invoice_data.get("Tasa")

        for product in self.products:
            MONTO = Decimal(str(product["monto"])) / tasa1
            BALANCE = Decimal(str(product["balance"])) / tasa1
            PENDIENTE = Decimal(str(product["pendiente"])) / tasa1

            # Calculate discount and ITBIS
            DESCUENTO = MONTO * (
                (Decimal(str(product.get("descuento", 0))) / Decimal("100")) / tasa1
            )
            valor_despues_descuento = MONTO - DESCUENTO
            ABONO = valor_despues_descuento * (
                (Decimal(str(product.get("abono", 0))) / Decimal("100")) / tasa1
            )

            products_html += f"""
                <tr>
                    <td style="padding: 4px; text-align: right;">{MONTO:,.2f}</td>
                    <td style="padding: 4px; text-align: right;">{BALANCE:,.2f}</td>
                    <td style="padding: 4px; text-align: right;">{ABONO:,.2f}</td>
                    <td style="padding: 4px; text-align: right;">{DESCUENTO:,.2f}</td>
                    <td style="padding: 4px; text-align: right;">{PENDIENTE:,.2f}</td>
                </tr>
            """

            subtotal += MONTO
            total_descuento += DESCUENTO

        return products_html, subtotal, total_descuento

    # ___________________________________________________CAJA CHICA___________________________________________________

    def generate_products_html4(self):
        products_html = ""
        subtotal = Decimal("0.00")
        total_descuento = Decimal("0.00")
        tasa1 = self.invoice_data.get("Tasa")

        for product in self.products:
            CUENTA = str(product["codigo"])
            DESCRPCION = str(product["descripcion"])
            VALOR = Decimal(str(product["valor"])) / tasa1

            # Calculate discount and ITBIS

            products_html += f"""
                <tr>
                    <td style="padding: 4px; text-align: left; width: 100px; /* Ancho fijo */ white-space: nowrap; /* Evita el salto de línea */ overflow: hidden; /* Oculta contenido que exceda el ancho */ text-overflow: ellipsis; /* Muestra puntos suspensivos si el contenido es demasiado largo */"> {CUENTA} </td>
                    <td style="padding: 4px; text-align: left;">{DESCRPCION}</td>
                    <td style="padding: 4px; text-align: right;">{VALOR:,.2f}</td>
                </tr>
            """

        return products_html, subtotal, total_descuento

    #
    # ____________________________________________________NOTA DE CREDITO_____________________________________________

    def generate_pdf2(self, printer, copy_label=None):
        # Configura los márgenes de la impresión (en milímetros)
        document = QtGui.QTextDocument()

        # Generate HTML for products and calculate totals
        products_html, subtotal, total_descuento = self.generate_products_html2()
        total = subtotal - total_descuento

        # Get note and user who created the invoice
        note = self.invoice_data.get("observacion", "")
        realizado = self.invoice_data.get("usuario", "")

        # Get additional fields
        codigoseguridad = self.invoice_data.get("codigoseguridad", "")
        fechafirma = self.invoice_data.get("fechafirma", "")
        url_qr = self.invoice_data.get("URLQR", "")

        # Generate QR code as base64 image
        qr_image = self.generate_qr_code(url_qr)

        # Load custom layout template if available
        custom_layout = self.load_custom_layout()

        if custom_layout:
            try:
                # Prepare replacements for placeholders in the template
                replacements = {
                    "{products_html}": products_html,
                    "{subtotal}": f"{subtotal:.2f}",
                    "{total_descuento}": f"{total_descuento:.2f}",
                    "{total}": f"{total:.2f}",
                    "{note}": note,
                    "{realizado}": realizado,
                    "{qr_image}": qr_image,
                    "{codigoseguridad}": codigoseguridad,
                    "{fechafirma}": fechafirma,
                }
                # Add company and invoice data to replacements
                for key, value in {**self.company_data, **self.invoice_data}.items():
                    replacements[f"{{{key}}}"] = str(value)

                # Replace all placeholders in the custom layout
                for placeholder, replacement in replacements.items():
                    custom_layout = custom_layout.replace(placeholder, replacement)

                html = custom_layout
            except Exception as e:
                print(f"Error applying custom layout: {str(e)}")
                # Use default layout if an error occurs
                html = self.generate_default_html2(
                    products_html,
                    subtotal,
                    total_descuento,
                    total,
                    note,
                    realizado,
                    qr_image,
                    codigoseguridad,
                    fechafirma,
                    copy_label,
                )
        else:
            html = self.generate_default_html2(
                products_html,
                subtotal,
                total_descuento,
                total,
                note,
                realizado,
                qr_image,
                codigoseguridad,
                fechafirma,
                copy_label,
            )

        document.setHtml(html)

        # Configura la orientación y el tamaño de la página
        printer.setOrientation(QPrinter.Portrait)
        printer.setPageSize(QPageSize(QPageSize.Letter))

        printer.setResolution(300)

        # Configurar márgenes fijos (en puntos)
        margin = 0.5  # 0.5 pulgadas = 36 puntos
        printer.setPageMargins(margin, margin, margin, margin, QPrinter.Point)

        # Establece el tamaño del documento en función del tamaño de la página del PDF
        page_width = 6.5 * 72  # 72 puntos por pulgada
        page_height = 9 * 72

        # Configurar el tamaño de página fijo
        document.setPageSize(QtCore.QSizeF(page_width, page_height))

        if (
            document.pageSize().width() != page_width
            or document.pageSize().height() != page_height
        ):
            print("Error: El tamaño de la página no es consistente")
            return

        # Imprime el documento en el PDF
        document.print_(printer)

    # ____________________________________Nota de credito por devolucion________________________________________________

    # ______________________________Nota de credito___________________________________________________________________

    def generate_products_html2(self):
        products_html = ""
        subtotal = Decimal("0.00")
        total_descuento = Decimal("0.00")
        tasa1 = self.invoice_data.get("Tasa")

        FACTURA = self.invoice_data.get("NumeroDocumentoNCFModificado")
        MONTO = Decimal(self.invoice_data.get("MontoNCFModificado") or 0) / tasa1
        BALANCE = Decimal(self.invoice_data.get("MontoNCFModificado") or 0) / tasa1
        PENDIENTE = (
            Decimal(self.invoice_data.get("PendienteNCFModificado") or 0) / tasa1
        )

        # Calculate discount and ITBIS
        DESCUENTO = (
            Decimal(self.invoice_data.get("DescuentoNCFModificado") or 0) / tasa1
        )

        ABONO = Decimal(self.invoice_data.get("AbonoNCFModificado") or 0) / tasa1

        # Supongamos que la fecha está en formato datetime
        fecha = self.invoice_data.get("FechaNCFModificado")

        if fecha:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                fecha_formateada = fecha.strftime("%d-%m-%Y")
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_formateada = fecha.strftime("%d-%m-%Y")

        FECHA = fecha_formateada

        products_html += f"""
            <tr>
                <td style="padding: 4px; text-align: left; width: 100px; /* Ancho fijo */ white-space: nowrap; /* Evita el salto de línea */ overflow: hidden; /* Oculta contenido que exceda el ancho */ text-overflow: ellipsis; /* Muestra puntos suspensivos si el contenido es demasiado largo */"> {FACTURA} </td>
                <td style="padding: 4px; text-align: right;">{FECHA}</td>
                <td style="padding: 4px; text-align: right;">{MONTO:,.2f}</td>
                <td style="padding: 4px; text-align: right;">{BALANCE:,.2f}</td>
                <td style="padding: 4px; text-align: right;">{ABONO:,.2f}</td>
                <td style="padding: 4px; text-align: right;">{DESCUENTO:,.2f}</td>
                <td style="padding: 4px; text-align: right;">{PENDIENTE:,.2f}</td>
            </tr>
        """

        subtotal += MONTO
        total_descuento += DESCUENTO

        return products_html, subtotal, total_descuento

    # __________________________________Factura________________________________________________________
    def generate_products_html_page(self, products, forms, include_totals=False):
        """Generate HTML for a single page of products and calculate running totals."""

        def load_printer_config():
            """Carga la configuración de la impresora desde un archivo JSON."""
            config_path = "config/config_print.json"
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    config = json.load(file)
                    return {
                        "printer_name": config.get("printer_name", None),
                        "copies": config.get(
                            "copies", 1
                        ),  # Default to 1 copy if not specified
                        "copy_labels": config.get(
                            "copy_labels",
                            [
                                "ORIGINAL - CLIENTE",
                                "COPIA - CAJA",
                                "COPIA - CONTABILIDAD",
                                "COPIA - ARCHIVO",
                            ],
                        ),
                        "concodigo": config.get("concodigo", 0),
                        "conlote": config.get("conlote", 0),
                        # Add default value here
                        "conunidad": config.get("conunidad", 0),
                        "condescuento": config.get("condescuento", 0),
                        "concantidaddecimal": config.get("concantidaddecimal", 0),
                        "numerodecimales": config.get("numerodecimales", 2),
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                print(
                    "Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada."
                )
                return {
                    "printer_name": None,
                    "copies": 0,
                    "conlote": 0,
                    "concodigo": 0,
                    "conunidad": 0,
                    "condescuento": 0,
                    "nump": 0,
                    "concantidaddecimal": 0,
                    "numerodecimales": 2,
                }

        products_html = ""
        pagos_html = ""  # Inicializar pagos_html como una cadena vacía
        total_descuento = Decimal("0.00")
        total_quantity = 0

        tasa1 = self.invoice_data.get("Tasa")

        # Initialize note3 as an empty string or collect all notes
        all_notes = []

        # Call the local function without self
        config = load_printer_config()
        concodigo = config.get(
            "concodigo", 0
        )  # This variable determines if the code column should be shown
        conunidad = config.get("conunidad", 0)
        condesc = config.get("condescuento", 0)
        conlote = config.get("conlote", 0)
        concantidaddecimal = config.get("concantidaddecimal", 0)
        numerodecimales = config.get("numerodecimales", 2)

        # Crear formato para cantidades basado en numerodecimales
        cantidad_format = f"{{:,.{numerodecimales}f}}"

        if concantidaddecimal == 1:
            pass
        else:
            pass
        for product in products:
            cantidad = Decimal(str(product["cantidad"]))
            precio = Decimal(str(product["precio"])) / tasa1
            descuento = Decimal(str(product.get("descuento", 0))) / tasa1
            valor = Decimal(str(product.get("valor", 0))) / tasa1
            itbis = Decimal(str(product.get("itbis", 0))) / tasa1
            lote = product.get("lote", "")

            # Collect notes from all products
            if "nota3" in product and product.get("nota3"):
                all_notes.append(product.get("nota3", ""))

            # Determinar cómo mostrar la cantidad basado en concantidaddecimal
            if concantidaddecimal == 1:
                # Mostrar como decimal con numerodecimales
                try:
                    cantidad_display = cantidad_format.format(cantidad)
                except Exception:
                    cantidad_display = f"{cantidad:,.{numerodecimales}f}"
            else:
                # Mostrar como entero
                cantidad_display = str(int(cantidad))
            # Create the product row HTML based on concodigo value
            if concodigo == 1 and conunidad == 1:
                descuento_cell = (
                    f'<td style="padding: 1px; text-align: right;">{descuento:,.2f}</td>'
                    if condesc == 1
                    else ""
                )

                lote_cell = (
                    f'<td style="padding: 1px; text-align: right;">{lote}</td>'
                    if conlote == 1
                    else ""
                )
                products_html += f"""
                    <tr>
                        <td style="padding: 1px; text-align: right; width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"> {cantidad_display} </td>
                        <td style="padding: 1px;text-align: center;">{product['codigo']}</td>
                        <td style="padding: 1px;">{product['unidad']}</td>
                        <td style="padding: 1px;">{product['descripcion']}</td>
                        <td style="padding: 1px; text-align: right;">{precio:,.2f}</td>
                        {descuento_cell}
                        <td style="padding: 1px; text-align: right;">{itbis:,.2f}</td>
                        <td style="padding: 1px; text-align: right;">{valor:,.2f}</td>
                        {lote_cell}
                    </tr>
                """
            elif concodigo == 0 and conunidad == 0:
                descuento_cell = (
                    f'<td style="padding: 1px; text-align: right;">{descuento:,.2f}</td>'
                    if condesc == 1
                    else ""
                )

                lote_cell = (
                    f'<td style="padding: 1px; text-align: right;">{lote}</td>'
                    if conlote == 1
                    else ""
                )

                products_html += f"""
                    <tr>
                        <td style="padding: 1px; text-align: right; width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"> {cantidad_display} </td>
                        <td style="padding: 1px;">{product['descripcion']}</td>
                        <td style="padding: 1px; text-align: right;">{precio:,.2f}</td>
                        {descuento_cell}
                        <td style="padding: 1px; text-align: right;">{itbis:,.2f}</td>
                        <td style="padding: 1px; text-align: right;">{valor:,.2f}</td>
                        {lote_cell}
                    </tr>
                """
            elif concodigo == 1 and conunidad == 0:
                descuento_cell = (
                    f'<td style="padding: 1px; text-align: right;">{descuento:,.2f}</td>'
                    if condesc == 1
                    else ""
                )

                lote_cell = (
                    f'<td style="padding: 1px; text-align: right;">{lote}</td>'
                    if conlote == 1
                    else ""
                )

                products_html += f"""
                    <tr>
                        <td style="padding: 1px; text-align: right; width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"> {cantidad_display} </td>
                        <td style="padding: 1px;text-align: center;">{product['codigo']}</td>
                        <td style="padding: 1px;">{product['descripcion']}</td>
                        <td style="padding: 1px; text-align: right;">{precio:,.2f}</td>
                        {descuento_cell}
                        <td style="padding: 1px; text-align: right;">{itbis:,.2f}</td>
                        <td style="padding: 1px; text-align: right;">{valor:,.2f}</td>
                        {lote_cell}
                    </tr>
                """
            elif concodigo == 0 and conunidad == 1:
                descuento_cell = (
                    f'<td style="padding: 1px; text-align: right;">{descuento:,.2f}</td>'
                    if condesc == 1
                    else ""
                )

                lote_cell = (
                    f'<td style="padding: 1px; text-align: right;">{lote}</td>'
                    if conlote == 1
                    else ""
                )

                products_html += f"""
                    <tr>
                        <td style="padding: 1px; text-align: right; width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"> {cantidad_display} </td>
                        <td style="padding: 1px;">{product['unidad']}</td>
                        <td style="padding: 1px;">{product['descripcion']}</td>
                        <td style="padding: 1px; text-align: right;">{precio:,.2f}</td>
                        {descuento_cell}
                        <td style="padding: 1px; text-align: right;">{itbis:,.2f}</td>
                        <td style="padding: 1px; text-align: right;">{valor:,.2f}</td>
                        {lote_cell}
                    </tr>
                """

            # Always calculate quantity total for the current page
            total_quantity += cantidad

            if include_totals:
                total_descuento += descuento

        # Generar pagos_html
        if forms:
            for forma in forms:
                monto = Decimal(str(forma["MontoPago"])) / tasa1
                pagos_html += f"""
                    <tr>
                    <td style="text-align: right; font-size: 5pt; padding: 2px 4px">{forma['FormaPagoL']}</td>
                    <td style="text-align: right; font-size: 5pt; padding: 2px 4px">{monto:,.2f}</td>
                    </tr>
                """
        else:
            pagos_html = ""

        # Join notes with line breaks if there's a period in the text
        note3 = (
            "\n".join(note.replace("|", ".<br>") for note in all_notes)
            if all_notes
            else ""
        )

        return products_html, total_descuento, total_quantity, note3, pagos_html

    # ______________________________Nota de credito por devolucion___________________________________________________________

    # _____________________________________________________FACTURA_____________________________________________
    def generate_default_html(
        self,
        products_html,
        total_descuento,
        total,
        note,
        realizado,
        qr_image,
        codigoseguridad,
        fechafirma,
        total_quantity,
        pagos_html,
    ):
        # Generar cada sección por separado
        header_html = self.generate_header_html()
        detail_html = self.generate_detail_html(
            products_html, total_descuento, total_quantity, pagos_html, total
        )
        footer_html = self.generate_footer_html(
            note, realizado, qr_image, codigoseguridad, fechafirma, total_quantity
        )
        # Supongamos que la fecha está en formato datetime
        fecha = self.invoice_data.get("fVencimientoNCF", "")

        if fecha:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                pass
            elif isinstance(fecha, str):
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                pass
            else:
                pass

            # Usar la fecha formateada

        # Supongamos que la fecha está en formato datetime
        fecha2 = self.invoice_data.get("fecha", None)

        if fecha2:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha2, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                fecha_formateada2 = fecha2.strftime("%d-%m-%Y")
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_formateada2 = fecha.strftime("%d-%m-%Y")

            # Usar la fecha formateada
            print(f"VÁLIDO HASTA: {fecha_formateada2}")
        else:
            print("Fecha no disponible")

        # Obtener la fecha y hora actual
        fecha_hora_actual = datetime.now()

        # Formatear la fecha y hora como desees
        fecha_formateada3 = fecha_hora_actual.strftime("%d-%m-%Y")

        '''valido_html = f"<p style='margin: 0; padding: 0;'>VÁLIDO HASTA: {fecha_formateada, ''}</p>" if {fecha_formateada} != '' else ""'''

        print("Fecha y hora actual:", fecha_formateada3)

        return f"""
            <html>
            <body style="font-family: Arial, sans-serif; font-size: 5pt; margin: 20px; width=100%;">
                {header_html}
                {detail_html}
                {footer_html}
            </body>
            </html>
        """

    def generate_header_html(self, current_page=1, total_pages=1, copy_label=None):
        """
        Generate HTML for the invoice header, including page numbers

        Args:
            current_page (int): Current page number (starting from 1)
            total_pages (int): Total number of pages

        Returns:
            str: HTML for the header section
        """

        def load_printer_config():
            """Carga la configuración de la impresora desde un archivo JSON."""
            config_path = "config/config_print.json"
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    config = json.load(file)
                    return {
                        "copies": config.get(
                            "copies", 1
                        ),  # Default to 1 copy if not specified
                        "copy_labels": config.get(
                            "copy_labels",
                            [
                                "ORIGINAL - CLIENTE",
                                "COPIA - CAJA",
                                "COPIA - CONTABILIDAD",
                                "COPIA - ARCHIVO",
                            ],
                        ),
                        "show_copy_labels": config.get(
                            "show_copy_labels", True
                        ),  # Add default value for show_copy_labels
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                print(
                    "Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada."
                )
                return {"copies": 0, "concodigo": 0, "show_copy_labels": True}

        # Call the local function without self
        config = load_printer_config()
        show_copy_labels = config.get("show_copy_labels", True)
        copy_label_html = (
            f'<div style="text-align: center; font-size: 5pt; font-weight: bold; margin-top: 2px;">{copy_label}</div>'
            if copy_label and show_copy_labels
            else ""
        )

        config_path = "config/config_print.json"
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config = json.load(file)
                font_sizes = config.get("font_sizes", {})
                font_sizeslogo = config.get("font_sizeslogo", {})
                conlogo = config.get("conlogo", 0)  # Default to 0 if not specified
                ruta_logo = config.get(
                    "ruta_logo", "C:\\Users\\Admin\\Pictures\\logo.png"
                )
                conruta = config.get("conruta", 0)  # Default to 0 if not specified
                conzona = config.get("conzona", 0)  # Default to 0 if not specified
                conalmacen = config.get(
                    "conalmacen", 0
                )  # Default to 0 if not specified
                consubcentro = config.get(
                    "consubcentro", 0
                )  # Default to 0 if not specified
                connotantesproducto = config.get("connotantesproducto", 0)
                convendedor = config.get("convendedor", 0)
                tamano_general = config.get("tamano_general", "10pt")
                tconnotantesproducto = config.get("tconnotantesproducto", "5pt")
        except (FileNotFoundError, json.JSONDecodeError):
            print(
                "Error: No se pudo cargar la configuración de los tamaños de fuente. Usando valores predeterminados."
            )
            font_sizes = {}
            font_sizeslogo = {}
            conlogo = 0  # Default to 0 if not specified
            ruta_logo = "C:\\Users\\Admin\\Pictures\\logo.png"
            conruta = 0  # Default to 0 if not specified
            conzona = 0  # Default to 0 if not specified
            conalmacen = 0  # Default to 0 if not specified
            consubcentro = 0
            convendedor = 0
            connotantesproducto = 0
            tamano_general = "10pt"
            tconnotantesproducto = "5pt"

        # Default font sizes
        empresa_font = font_sizes.get("empresa", "7pt")
        cliente_font = font_sizes.get("cliente", "5pt")
        tipoencf_font = font_sizes.get("tipoencf", "5pt")
        encf_font = font_sizes.get("encf", "5pt")

        # Default font sizes
        logo_width = font_sizeslogo.get("width", "70")
        logo_height = font_sizeslogo.get("height", "70")
        tconnotantesproducto = font_sizes.get("tconnotantesproducto", "6pt")

        # _____________________fecha de vencimiento______________________________________________________
        fecha = self.invoice_data.get("fVencimientoNCF", "")

        if fecha and fecha != " ":
            if isinstance(fecha, datetime):
                # Si ya es un objeto datetime, formatea directamente
                fecha_formateada = fecha.strftime("%d-%m-%Y")
            elif (
                isinstance(fecha, str) and fecha.strip()
            ):  # Verifica que no sea solo espacios en blanco
                try:
                    # Intenta convertir la cadena en un objeto datetime
                    fecha = datetime.strptime(fecha.strip(), "%Y-%m-%d")
                    fecha_formateada = fecha.strftime("%d/%m/%Y")
                except ValueError:
                    fecha_formateada = (
                        ""  # Si el formato es incorrecto, asigna cadena vacía
                    )
            else:
                fecha_formateada = ""
        else:
            fecha_formateada = ""

        valido_html = (
            f"<p style='margin: 0; padding: 0;'>VÁLIDO HASTA: {fecha_formateada}</p>"
            if fecha_formateada.strip()
            else ""
        )
        # _____________________fecha de vencimiento______________________________________________________\

        tasa1 = self.invoice_data.get("Tasa", "")

        tasa_html = (
            f"<p style='margin: 0; padding: 0;'>TASA: {tasa1:.2f}</p>"
            if tasa1 not in [0, 1, "0", "1", "", None]
            else ""
        )

        ncf_afectado = self.invoice_data.get("Ncf_Modificado", "")

        ncf_html = (
            f"<p style='margin: 0; padding: 0;'>NCF AFECTADO: {ncf_afectado}</p>"
            if ncf_afectado.strip()
            else ""
        )

        # Add page number information
        page_info = f"<p style='margin: 0; padding: 0;'><b>PÁGINA: {current_page} de {total_pages}</b></p>"

        if conlogo == 1:
            logo_html = f"""
                <img src="{ruta_logo}" alt="Logo de la empresa" width={logo_width} height={logo_height}>
            """
        else:
            logo_html = ""

        tipopago = self.invoice_data.get("tipopago", "")
        if tipopago == 2:
            vence = f"<p style='margin: 0; padding: 0;'>VENCE: {self.invoice_data.get('FechaLimitePago', '')}</p>"
        else:
            vence = ""

        # _____________________fecha limitepago______________________________________________________
        fecha2 = self.invoice_data.get("FechaLimitePago", "")

        if fecha2 and fecha2 != " ":
            if isinstance(fecha2, datetime):
                # Si ya es un objeto datetime, formatea directamente
                fecha_formateada2 = fecha2.strftime("%d-%m-%Y")
            elif (
                isinstance(fecha2, str) and fecha2.strip()
            ):  # Verifica que no sea solo espacios en blanco
                try:
                    # Intenta convertir la cadena en un objeto datetime
                    fecha2 = datetime.strptime(fecha2.strip(), "%Y-%m-%d")
                    fecha_formateada2 = fecha2.strftime("%d/%m/%Y")
                except ValueError:
                    fecha_formateada2 = (
                        ""  # Si el formato es incorrecto, asigna cadena vacía
                    )
            else:
                fecha_formateada2 = ""
        else:
            fecha_formateada2 = ""

        tipopago = self.invoice_data.get("tipopago", "")
        if tipopago == 2:
            vence = f"<p style='margin: 0; padding: 0;'>VENCE: {fecha_formateada2}</p>"
        else:
            vence = ""

        fecha_emitida = self.invoice_data.get("fecha", "").strftime("%d-%m-%Y")
        fecha_emitida_html = f"<p style='margin: 0; padding: 0;'><strong>Fecha Emision:</strong> {fecha_emitida}</p>"
        # _____________________fecha limitepago______________________________________________________\
        # _____________________con o sin______________________________________________________
        tipopago = self.invoice_data.get("tipopago", "")
        if tipopago == 2 and conruta == 1:
            ruta_html = f"<b>RUTA</b>: {self.invoice_data.get('ruta', '')}<br />"

        else:
            ruta_html = ""

        if tipopago == 2 and conzona == 1:
            zona_html = f"<p style='margin: 0; padding: 0;'>ZONA: {self.invoice_data.get('zona', '')}</p>"

        else:
            zona_html = ""

        if conalmacen == 1:
            almacen_html = f"<p style='margin: 0; padding: 0;'>ALMACEN: {self.invoice_data.get('almacen', '')}</p>"
        else:
            almacen_html = ""

        if consubcentro == 1:
            subcentro_html = f"<b>NOMBRE COMERCIAL</b>: {self.invoice_data.get('ContactoEntrega', '')}<br />"
        else:
            subcentro_html = ""

        if consubcentro == 1:
            direccion_html = f"<b>DIRECCION</b>: {self.invoice_data.get('DireccionEntrega', '')}<br />"
        elif consubcentro == 0:
            direccion_html = f"<b>DIRECCION</b>: {self.invoice_data.get('direccion_cliente', '')}<br />"

        if convendedor == 1:
            vendedor_html = f"<p style='margin: 0; padding: 0;'>VENDEDOR: {self.invoice_data.get('vendedor', '')} - {self.invoice_data.get('nombre_vendedor', '')}</p>"
        elif convendedor == 2:
            vendedor_html = (
                f"<p style='margin: 0; padding: 0;'>VENDEDOR: {self.invoice_data.get('vendedor', '')} - {self.invoice_data.get('nombre_vendedor', '')}</p>"
                f"<p style='margin: 0; padding: 0;'>TELEFONO: {self.invoice_data.get('numero_vendedor', '')}</p>"
            )
        else:
            vendedor_html = ""
        # _____________________con o sin______________________________________________________\

        correo = self.invoice_data.get("CorreoElectronico", "")
        if correo and correo.strip():
            email = f"CORREO: {correo}"
        else:
            email = ""
        # ____________________________________________________________________________________
        if connotantesproducto == 1:
            notaantesp_html = (
                f"<p style='margin: 0; padding: 0; text-align: left; font-size: {tconnotantesproducto}; "
                "background-color: #fff9c4; border-radius: 4px;'>"
                f"<b>{self.invoice_data.get('NotaAntesProducto', '')}</b></p>"
            )
        else:
            notaantesp_html = ""
        # ____________________________________________________________________________________

        return f"""
            <table width="100%" style="margin-bottom: 3px; padding: 0; font-family: Verdana, sans-serif;font-size: {tamano_general};">
                <tr>
                    <td style="text-align: left; vertical-align: top; padding: 0;">
                        {logo_html}
                        <p style="margin: 0; padding: 0; font-size: {empresa_font};"><b>{self.company_data.get('nombre_empresa', '')}</b></p>

                        <p style="margin: 0; padding: 0;">
                            RNC: {self.company_data.get('rnc', '')} | Tel.: {self.company_data.get('telefono', '')}<br />
                            {email}<br />
                            {self.company_data.get('direccion', '')}
                            {fecha_emitida_html}<br>
                        </p>
                        <p style="margin: 0; padding: 0;">

                            <b style="font-size: {cliente_font};">CLIENTE</b>: <span style="font-size: {cliente_font};">{self.invoice_data.get('cliente', '')} - {self.invoice_data.get('nombre_cliente', '')}</span><br />


                            <b>RNC</b>: {self.invoice_data.get('cedula', '')}<br />
                            {direccion_html}
                            {subcentro_html}
                            <b>CIUDAD</b>: {self.invoice_data.get('Ciudad', '')}<br />
                            <b>TELEFONO</b>: {self.invoice_data.get('telefono_cliente', '')}<br />
                            {ruta_html}
                        </p>
                    </td>
                    <td style="text-align: right; vertical-align: top; padding: 0;">
                        <div style="text-align: left; display: inline-block;">
                            <p style="margin: 0; padding: 0;">&nbsp;</p>
                            <p style="margin: 0; padding: 0;font-size: {tipoencf_font};"><b>{self.invoice_data.get("ncf_type", "")}</b></p>
                            <p style="margin: 0; padding: 0; font-size: {encf_font};"><b>e-NCF: {self.invoice_data.get('ncf', '')}</b></p>
                            {ncf_html}
                            {valido_html}
                            <p style="margin: 0; padding: 0;">
                                <hr>
                            </p>
                            <p style="margin: 0; padding: 0;"><b>
                            FACTURA#: {self.invoice_data.get('numero', '')}</b></p>
                            {vence}
                            {vendedor_html}
                            {almacen_html}
                            <p style="margin: 0; padding: 0;">CONDICION: VENTA A {self.invoice_data.get('TipoPagoL', '')} {self.invoice_data.get('TerminoPago', '')}</p>
                            <p style="margin: 0; padding: 0;">Pedido NO.: {self.invoice_data.get('Pedido', '')}</p>
                            {zona_html}
                            {tasa_html}
                            {page_info}
                            {copy_label_html}

                        </div>
                    </td>
                </tr>
            </table>
            {notaantesp_html}
            <p style="margin: 0; padding: 0; text-align: center;"><b>EXPRESADO EN {self.invoice_data.get('moneda_type2', '')}</b></p>
        """

    def generate_detail_html_page(
        self,
        products_html,
        pagos_html,
        total_descuento,
        is_last_page,
        total_quantity,
        counts_per_page,
    ):
        def load_printer_config():
            """Carga la configuración de la impresora desde un archivo JSON."""
            config_path = "config/config_print.json"
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    config = json.load(file)
                    return {
                        "printer_name": config.get("printer_name", None),
                        "copies": config.get(
                            "copies", 1
                        ),  # Default to 1 copy if not specified
                        "copy_labels": config.get(
                            "copy_labels",
                            [
                                "ORIGINAL - CLIENTE",
                                "COPIA - CAJA",
                                "COPIA - CONTABILIDAD",
                                "COPIA - ARCHIVO",
                            ],
                        ),
                        "concodigo": config.get(
                            "concodigo", 0
                        ),  # Add default value here
                        "conlote": config.get("conlote", 0),
                        "conunidad": config.get("conunidad", 0),
                        "condescuento": config.get("condescuento", 0),
                        "firma": config.get("firma", 0),  # Add firma configuration
                        "tamano_general": config.get("tamano_general", "10pt"),
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                print(
                    "Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada."
                )
                return {
                    "printer_name": None,
                    "copies": 0,
                    "conlote": 0,
                    "concodigo": 0,
                    "conunidad": 0,
                    "condescuento": 0,
                    "firma": 0,
                    "tamano_general": "10pt",
                }

        tasa1 = self.invoice_data.get("Tasa")
        MONTOGRAVADO = self.invoice_data.get("Monto_gravado", "")
        MONTOEXENTO = self.invoice_data.get("Monto_exento", "")
        IndicadorMontoGravado = self.invoice_data.get("IndicadorMontoGravado", "")

        monto_total = self.invoice_data.get("Monto_total", 0.00)
        itbis_total = self.invoice_data.get("TotalITBIS", 0.00)
        descuentoglobal = self.descuento_recargo.get("monto", 0.00)
        total_descuento1 = total_descuento + descuentoglobal

        if IndicadorMontoGravado == 0:
            subtotal = (
                (MONTOGRAVADO or 0)
                + (MONTOEXENTO or 0)
                + total_descuento1
                - itbis_total
            )
        else:
            subtotal = (
                (MONTOGRAVADO or 0) + (MONTOEXENTO or 0) + total_descuento1
            )  # + descuentoglobal

        subtotal_total_formateado = subtotal / tasa1
        monto_total_formateado = monto_total / tasa1
        itbis_total_formateado = itbis_total / tasa1
        total_descuento_formateado = total_descuento1 / tasa1

        tipoecf = self.invoice_data.get("tipoecf")
        retencion = self.invoice_data.get("ISR_Retenido", Decimal("0.00")) / tasa1
        itbis_ret = self.invoice_data.get("ITBIS_Retenido", Decimal("0.00")) / tasa1
        adicional_rows = ""
        if tipoecf == '41':
            adicional_rows = f"""
                <tr>
                    <td style="text-align: right; font-weight: bold; padding: 2px 4px; line-height: 1;">Retencion {self.invoice_data.get('moneda_type', '')}:</td>
                    <td style="text-align: right; padding: 2px 4px; line-height: 1;">{retencion:,.2f}</td>
                </tr>
                <tr>
                    <td style="text-align: right; font-weight: bold; padding: 2px 4px; line-height: 1;">ITBIS Ret {self.invoice_data.get('moneda_type', '')}:</td>
                    <td style="text-align: right; padding: 2px 4px; line-height: 1;">{itbis_ret:,.2f}</td>
                </tr>
"""

        # Call the local function without self
        config = load_printer_config()
        concodigo = config.get("concodigo", 0)
        conunidad = config.get("conunidad", 0)
        condesc = config.get("condescuento", 0)
        conlote = config.get("conlote", 0)
        tamano_general = config.get("tamano_general", "10pt")

        # Determine if code column should be shown
        tipo_pago = self.invoice_data.get(
            "tipopago", 0
        )  # Obtener el tipo de pago, por defecto 0
        pagos_html1 = pagos_html if tipo_pago == 1 else ""

        for i in counts_per_page:
            iu = i  # Esto tomará el valor 1, luego 2, luego 3

        # O directamente: iu untimo items
        iu = counts_per_page[-1]  # si quieres el último índice

        """Generate detail HTML for a single page."""
        if concodigo == 1 and conunidad == 1:
            descuento_th = (
                '<th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">DESC.</th>'
                if condesc == 1
                else ""
            )

            lote_th = (
                '<th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">L.</th>'
                if conlote == 1
                else ""
            )
            table_html = f"""
                <table width="100%" style="border-collapse: collapse; margin-top: 0px; font-family: sans-serif; font-size: {tamano_general};">
                    <tr>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CANT.</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CÓDIGO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">UNIDAD</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">DESCRIPCION</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">PRECIO</th>
                        {descuento_th}
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">ITBIS</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">VALOR</th>
                        {lote_th}
                    </tr>
                    {products_html}
                </table>
            """
        elif concodigo == 0 and conunidad == 0:
            descuento_th = (
                '<th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">DESC.</th>'
                if condesc == 1
                else ""
            )

            lote_th = (
                '<th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">L.</th>'
                if conlote == 1
                else ""
            )
            table_html = f"""
                <table width="100%" style="border-collapse: collapse; margin-top: 0px; font-family: sans-serif; font-size: {tamano_general};">
                    <tr>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CANTIDAD</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">DESCRIPCION</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">PRECIO</th>
                        {descuento_th}
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">ITBIS</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">VALOR</th>
                        {lote_th}
                    </tr>
                    {products_html}
                </table>
            """
        elif concodigo == 1 and conunidad == 0:
            descuento_th = (
                '<th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">DESC.</th>'
                if condesc == 1
                else ""
            )

            lote_th = (
                '<th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">L.</th>'
                if conlote == 1
                else ""
            )

            table_html = f"""
                <table width="100%" style="border-collapse: collapse; margin-top: 0px; font-family: sans-serif; font-size: {tamano_general};">
                    <tr>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CANTIDAD</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CÓDIGO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">DESCRIPCION</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">PRECIO</th>
                        {descuento_th}
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">ITBIS</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">VALOR</th>
                        {lote_th}
                    </tr>
                    {products_html}
                </table>
            """
        elif concodigo == 0 and conunidad == 1:
            descuento_th = (
                '<th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">DESC.</th>'
                if condesc == 1
                else ""
            )

            lote_th = (
                '<th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">L.</th>'
                if conlote == 1
                else ""
            )

            table_html = f"""
                <table width="100%" style="border-collapse: collapse; margin-top: 0px; font-family: sans-serif; font-size: {tamano_general};">
                    <tr>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CANTIDAD</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">UNIDAD</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">DESCRIPCION</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">PRECIO</th>
                        {descuento_th}
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">ITBIS</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">VALOR</th>
                        {lote_th}
                    </tr>
                    {products_html}
                </table>
            """
        # Rest of the method remains the same
        if is_last_page:
            descuento_total_row = (
                (
                    f"<tr>\n"
                    f"    <td style=\"text-align: right; font-weight: bold; padding: 2px 4px; line-height: 1;\">- DESCUENTO {self.invoice_data.get('moneda_type', '')}:</td>\n"
                    f'    <td style="text-align: right; padding: 2px 4px; line-height: 1;">{total_descuento_formateado:,.2f}</td>\n'
                    f"</tr>\n"
                )
                if condesc == 1
                else ""
            )
            table_html += f"""
                <p colspan="3" style="text-align: center; font-weight: bold; margin-top: 0px; font-family: Verdana, sans-serif; font-size: {tamano_general};">*****ULTIMA LINEA*****</p>
                <table width="100%" style="border-collapse: collapse; margin: 2px 0;">
                    <tr><td style="border-top: 1px solid black;"></td></tr>
                <span style="margin-right: 15px;">Items: {iu} </span>
                </table>

            <table width="58%" style="border-collapse: collapse; margin-top: 0px; font-size: {tamano_general}; margin-right: 2px; text-align: right;font-family: Verdana, sans-serif; font-size: {tamano_general};">

                <tr>
                    <td style="text-align: right; font-weight: bold; padding: 2px 4px; line-height: 1;">Sub-Total {self.invoice_data.get('moneda_type', '')}:</td>
                    <td style="text-align: right; font-weight: bold; padding: 2px 4px; line-height: 1;">{subtotal_total_formateado:,.2f}</td>
                </tr>
                {descuento_total_row}
                <tr>
                    <td style="text-align: right; font-weight: bold; padding: 2px 4px; line-height: 1;">+ ITBIS {self.invoice_data.get('moneda_type', '')}:</td>
                    <td style="text-align: right; padding: 2px 4px; line-height: 1;">{itbis_total_formateado:,.2f}</td>
                </tr>
                {adicional_rows}
                <tr>
                    <td colspan="2" style="border-top: 1px solid black; padding: 0; line-height: 0;"></td>
                </tr>
                <tr>
                    <td style="text-align: right; font-weight: bold; font-size: 5pt; padding: 0px 4px 2px 4px; line-height: 1;">TOTAL {self.invoice_data.get('moneda_type', '')}:</td>
                    <td style="text-align: right; font-weight: bold; font-size: 5pt; padding: 0px 4px 2px 4px; line-height: 1;">{monto_total_formateado:,.2f}</td>
                    {pagos_html1}
                </tr>
            </table>
            """

        return table_html

    def generate_page_footer(self, item_count):
        """Genera un footer individual para cada ítem."""

        for i in item_count:
            return f"""
                <table width="100%" style="border-collapse: collapse; margin: 2px 0; font-family: Verdana, sans-serif; font-size: 5pt;">
                    <tr><td style="border-top: 1px solid black;"></td></tr>
                    <tr>
                        <td align="left" style="padding-right: 15px;">Items: {i}</td>
                    </tr>
                </table>
            """

    def generate_footer_html(
        self,
        note,
        note2,
        note3,
        note4,
        realizado,
        qr_image,
        codigoseguridad,
        fechafirma,
        total_quantity,
        copy_label=None,
    ):

        def load_printer_config():
            """Carga la configuración de la impresora desde un archivo JSON."""
            config_path = "config/config_print.json"
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    config = json.load(file)
                    return {
                        "printer_name": config.get("printer_name", None),
                        "copies": config.get(
                            "copies", 1
                        ),  # Default to 1 copy if not specified
                        "copy_labels": config.get(
                            "copy_labels",
                            [
                                "ORIGINAL - CLIENTE",
                                "COPIA - CAJA",
                                "COPIA - CONTABILIDAD",
                                "COPIA - ARCHIVO",
                            ],
                        ),
                        "firma_labels": config.get(
                            "firma_labels",
                            {
                                "1": "Realizado/Fecha",
                                "2": "Despachado/Fecha",
                                "3": "Recibido/Fecha",
                            },
                        ),
                        "concodigo": config.get(
                            "concodigo", 0
                        ),  # Add default value here
                        "firma": config.get("firma", 0),  # Add firma configuration
                        "show_copy_labels": config.get(
                            "show_copy_labels", True
                        ),  # Add default value for show_copy_labels
                        "connotapermanente": config.get(
                            "connotapermanente", 0
                        ),  # Add default value for connotapermanente
                        "tiponotap": config.get(
                            "tiponotap", 0
                        ),  # Add default value for tiponotapermanente
                        "tamano_general": config.get("tamano_general", "10pt"),
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                print(
                    "Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada."
                )
                return {
                    "printer_name": None,
                    "copies": 0,
                    "concodigo": 0,
                    "show_copy_labels": True,
                    "firma": 0,
                    "connotapermanente": 0,
                    "tiponotap": 0,
                    "firma_labels": {
                        "1": "Realizado/Fecha",
                        "2": "Despachado/Fecha",
                        "3": "Recibido/Fecha",
                    },
                    "tamano_general": "10pt",
                }

        fecha_hora_actual = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        tasa1 = self.invoice_data.get("Tasa")
        monto_total = self.invoice_data.get("Monto_total", 0.00)
        monto_total_formateado = monto_total / tasa1
        tipo_pago = self.invoice_data.get(
            "tipopago", 0
        )  # Obtener el tipo de pago, por defecto 0
        note5 = self.descuento_recargo.get("descripcion", "")

        # Call the local function without self
        config = load_printer_config()
        tamano_general = config.get("tamano_general", "10pt")
        firma = config.get("firma", 0)  # Add firma configuration
        connotapermanente = config.get(
            "connotapermanente", 0
        )  # Add default value for connotapermanente
        tiponotap = config.get(
            "tiponotap", 0
        )  # Add default value for tiponotapermanente

        realizado_label = config.get("firma_labels", {}).get("1", "Realizado/Fecha")
        despacho_label = config.get("firma_labels", {}).get("2", "Despachado/Fecha")
        recibido_label = config.get("firma_labels", {}).get("3", "Recibido/Fecha")

        if connotapermanente == 1:
            connotapermanente_html = f"""
            <div style="background-color: #e3d899; padding: 10px; font-size: 5pt; margin-top: 10px; font-family: Verdana, sans-serif; font-size: {tamano_general};">
                Por Esta UNICA DE CAMBIO Pagare a CEMAVLOCK, SRL la cantidad de <b>{monto_total_formateado:,.2f}</b><br>
                valor recibido a mi (nuestra) entera satisfacción según factura No. <b>{self.invoice_data.get('numero', '')}</b><br>
                para fiel cumplimiento de pago quedan afectados mis (nuestra) bienes habidos y por haber,
                con renuncia del fuero de domicilio y de cualquier otra ley que pudiera favorecerme (nos), A:
                <b>{self.invoice_data.get('nombre_cliente', '')}</b>
            </div>
            """
        else:
            connotapermanente_html = ""

        if tiponotap == 1 and tipo_pago == 1:
            nota = f"""<p style="margin-top: 10px; font-size: {tamano_general};">{note}</p>"""
        elif tiponotap == 2 and tipo_pago == 1:
            nota = f"""<p style="margin-top: 10px; font-size: {tamano_general}">{note}</p>"""
        elif tiponotap == 3:
            nota = f"""<p style="margin-top: 10px; font-size: {tamano_general}">{note}</p>"""
        else:
            nota = ""

        return f"""
                    <table
                width="100%"
                style="border-collapse: collapse; margin-top: 7px; padding: 0; font-family: Verdana, sans-serif; font-size: {tamano_general};"
                >
                <tr>
                    <!-- Primer Bloque -->
                    <td
                        style="
                            text-align: center;
                            padding: 20px;
                            width: 33%;
                            font-size: 7px;
                            font-weight: bold;
                        "
                    >
                        <p style="margin: 0; font-size: 7px;">{realizado if self.invoice_data.get('cajero') not in [None, ''] and firma == 1 else '&nbsp;'}</p>
                        <hr style="margin: 1px auto; width: 90%; border: 1px solid black;" />
                        <p style="margin: 0; padding: 0;">{realizado_label}</p>
                    </td>

                    <!-- Segundo Bloque -->
                    <td
                        style="
                            text-align: center;
                            padding: 20px;
                            width: 33%;
                            font-size: 7px;
                            font-weight: bold;
                        "
                    >
                        <p style="margin: 0; font-size: 7px;">&nbsp;</p>
                        <hr style="margin: 1px auto; width: 90%; border: 1px solid black;" />
                        <p style="margin: 0; padding: 0;">{despacho_label}</p>
                    </td>
                    <!-- Tercer Bloque -->
                    <td
                        style="
                            text-align: center;
                            padding: 20px;
                            width: 33%;
                            font-size: 7px;
                            font-weight: bold;
                        "
                    >
                        <p style="margin: 0; font-size: 7px;">&nbsp;</p>
                        <hr style="margin: 1px auto; width: 90%; border: 1px solid black;" />
                        <p style="margin: 0; padding: 0;">{recibido_label}</p>
                    </td>
                </tr>

                </table>
            <p style="margin-top: 10px; font-size: {tamano_general};">{nota}</p>
            <p style="margin-top: 10px; font-size: {tamano_general}">{note2}</p>
            <p style="margin-top: 10px; font-size: {tamano_general};">{note3}</p>
            <p style="margin-top: 10px; font-size: {tamano_general}">{note4}</p>
            <p style="margin-top: 10px; font-size: {tamano_general}">{note5}</p>
            {connotapermanente_html}
            <div style="text-align: left; margin-top: 10px; font-family: Verdana, sans-serif; font-size: {tamano_general};">
                <img src="{qr_image}" width="54" height="54" alt="QR Code"><br>
                <span style="font-size: {tamano_general};">Código de Seguridad: {codigoseguridad}</span><br>
                <span style="font-size: {tamano_general};">Fecha de Firma Digital: {fechafirma}</span>
            </div>
            <hr>
            <div style="font-size: 7px; border-top: 1px solid black; border-bottom: 1px solid black; padding: 5px 0; text-align: left; font-family: Verdana, sans-serif; font-size: {tamano_general};">
                <span style="margin-right: 15px;">Cant. Total: {total_quantity:.2f}</span>
                <span>IMPRESO: {fecha_hora_actual}</span>
            </div>
        """

    # ____________________________________________________________NOTA DE DEBITO_____________________________________________________________________________________________________

    def generate_default_html6(
        self, realizado, qr_image, codigoseguridad, fechafirma, copy_label=None
    ):

        # Supongamos que la fecha está en formato datetime
        fecha = self.invoice_data.get("fVencimientoNCF", None)

        if fecha:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                fecha_formateada = fecha.strftime("%d-%m-%Y")
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")

        # Supongamos que la fecha está en formato datetime
        fecha2 = self.invoice_data.get("fecha", None)

        if fecha2:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha2, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                fecha_formateada2 = fecha2.strftime("%d-%m-%Y")
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_formateada2 = fecha.strftime("%d-%m-%Y")

        # Supongamos que la fecha está en formato datetime
        fecha4 = self.invoice_data.get("FechaNCFModificado", None)

        if fecha2:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha4, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                pass
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")

        # Obtener la fecha y hora actual
        fecha_hora_actual = datetime.now()

        # Formatear la fecha y hora como desees
        fecha_formateada3 = fecha_hora_actual.strftime("%d-%m-%Y")

        # valores formateados con la taza
        tasa1 = self.invoice_data.get("Tasa")

        # valores formateados con comppletar
        numero = self.invoice_data.get(
            "numero", ""
        )  # Paréntesis para obtener el valor directamente
        numero_formateado = str(
            numero
        ).zfill()  # Ahora sí, rellena hasta 11 dígitos con ceros

        montototal = Decimal(self.invoice_data.get("Monto_total")) / tasa1
        Monto_total_en_letras = f"{num2words.num2words(int(montototal), lang='es').upper()} CON {int(round(montototal % 1, 2) * 100):02}/100"

        def load_printer_config():
            """Carga la configuración de la impresora desde un archivo JSON."""
            config_path = "config/config_print.json"
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    config = json.load(file)
                    return {
                        "printer_name": config.get("printer_name", None),
                        "copies": config.get(
                            "copies", 1
                        ),  # Default to 1 copy if not specified
                        "copy_labels": config.get(
                            "copy_labels",
                            [
                                "ORIGINAL - CLIENTE",
                                "COPIA - CAJA",
                                "COPIA - CONTABILIDAD",
                                "COPIA - ARCHIVO",
                            ],
                        ),
                        "concodigo": config.get(
                            "concodigo", 0
                        ),  # Add default value here
                        "show_copy_labels": config.get(
                            "show_copy_labels", True
                        ),  # Add default value for show_copy_labels
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                print(
                    "Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada."
                )
                return {
                    "printer_name": None,
                    "copies": 0,
                    "concodigo": 0,
                    "show_copy_labels": True,
                }

        config = load_printer_config()
        show_copy_labels = config.get("show_copy_labels", True)
        copy_label_html = (
            f'<div style="text-align: center; font-size: 5pt; font-weight: bold; margin-top: 2px;">{copy_label}</div>'
            if copy_label and show_copy_labels
            else ""
        )

        # _____________________fecha de vencimiento______________________________________________________
        fecha = self.invoice_data.get("fVencimientoNCF", "")

        if fecha and fecha != " ":
            if isinstance(fecha, datetime):
                # Si ya es un objeto datetime, formatea directamente
                fecha_formateada = fecha.strftime("%d-%m-%Y")
            elif (
                isinstance(fecha, str) and fecha.strip()
            ):  # Verifica que no sea solo espacios en blanco
                try:
                    # Intenta convertir la cadena en un objeto datetime
                    fecha = datetime.strptime(fecha.strip(), "%Y-%m-%d")
                    fecha_formateada = fecha.strftime("%d/%m/%Y")
                except ValueError:
                    fecha_formateada = (
                        ""  # Si el formato es incorrecto, asigna cadena vacía
                    )
            else:
                fecha_formateada = ""
        else:
            fecha_formateada = ""

        valido_html = (
            f"<p style='margin: 0; padding: 0;'>VÁLIDO HASTA: {fecha_formateada}</p>"
            if fecha_formateada.strip()
            else ""
        )
        # _____________________fecha de vencimiento______________________________________________________\

        tasa_html = (
            f"<p style='margin: 0; padding: 0;'>TASA: {self.invoice_data.get('Tasa', '')}</p>"
            if self.invoice_data.get("Tasa", "")
            else ""
        )

        return f"""
            <html>
            <body style="font-family: Arial, sans-serif; font-size: 5pt; margin: 20px; width=100%;">
                <table width="100%" style="margin-bottom: 3px; padding: 0;">
                <tr>
                    <td style="text-align: left; vertical-align: top; padding: 0;">
                    <p style="margin: 0; padding: 0;"><b>{self.company_data.get('nombre_empresa', '')}</b></p>
                    <p style="margin: 0; padding: 0;">
                        {self.company_data.get('direccion', '')}<br />
                        Tel.: {self.company_data.get('telefono', '')}<br />
                        RNC: {self.company_data.get('rnc', '')}<br />
                    </p>
                    <p style="margin: 0; padding: 0;">
                        <b>FECHA:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b> {fecha_formateada2}<br />
                        <b>CLIENTE:</b> <b>{self.invoice_data.get('cliente', '')} - {self.invoice_data.get('nombre_cliente', '')}</b><br />
                    </td>
                    <td style="text-align: right; vertical-align: top; padding: 0;">
                        <div style="text-align: left; display: inline-block;">
                            <p style="margin: 0; padding: 0;">&nbsp;</p>
                            <p style="margin: 0; padding: 0;"><b>{self.invoice_data.get('ncf_type', '')}</b>
                            <p style="margin: 0; padding: 0;"><b>e-NCF # {self.invoice_data.get('ncf', '')}</b>
                            {valido_html}
                            <p style="margin: 0; padding: 0;"><b>NCF AFECTADO # {self.invoice_data.get('Ncf_Modificado', '')}</b></p>
                            <p style="margin: 0; padding: 0;"><b>Documento No.: {numero_formateado}<b/>
                            <p style="margin: 0; padding: 0;">
                            {tasa_html}
                        </div>
                    </td>
                </tr>
                </table>
                <p style="margin: 0; padding: 0; text-align: center;"><b>EXPRESADO EN {self.invoice_data.get('moneda_type2', '')}</b></p>
                <hr>
                    <tr>
                        <td style="text-align: left; font-size: 6pt; padding: 2px 4px;">
                            <strong>EN FECHA:</strong> {fecha_formateada2}
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align: left; font-size: 6pt; padding: 2px 4px;">
                            <strong>HEMOS ACREDITADO A:</strong> {self.invoice_data.get('nombre_cliente', '')}
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align: left; font-size: 6pt; padding: 2px 4px;">
                            <strong>LA SUMA DE:</strong> {Monto_total_en_letras}
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align: left; font-size: 6pt; padding: 2px 4px;">
                            <strong>POR CONCEPTO DE:</strong> {self.invoice_data.get('Razon_modificacion', '')}
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align: left; font-size: 6pt; padding: 2px 4px;">
                            <strong>TOTAL {self.invoice_data.get('moneda_type', '')}:</strong> {montototal:,.2f}
                        </td>
                    </tr>

                </table>
                <hr>
                <table
                width="100%"
                style="border-collapse: collapse; margin-top: 5px; padding: 0;"
                >
                <tr>
                    <!-- Primer Bloque -->
                    <td
                        style="
                            text-align: center;
                            padding: 20px;
                            width: 33%;
                            font-size: 10px;
                            font-weight: bold;
                        "
                    >
                        <p style="margin: 0; font-size: 10px;">{realizado}</p>
                        <hr style="margin: 1px auto; width: 90%; border: 1px solid black;" />
                        <p style="margin: 1px 0 0;">Realizado</p>
                    </td>

                    <!-- Segundo Bloque -->
                    <td
                        style="
                            text-align: center;
                            padding: 20px;
                            width: 33%;
                            font-size: 10px;
                            font-weight: bold;
                        "
                    >
                        <p style="margin: 0; font-size: 10px;">&nbsp;</p>
                        <hr style="margin: 1px auto; width: 90%; border: 1px solid black;" />
                        <p style="margin: 1px 0 0;">Despachado</p>
                    </td>
                </tr>


                </table>


                <div style="text-align: left; margin-top: 5px;">
                    <img src="{qr_image}" width="80" height="80" alt="QR Code"><br>
                    <span style="font-size: 5pt;">Código de Seguridad: {codigoseguridad}</span><br>
                    <span style="font-size: 5pt;">Fecha de Firma Digital: {fechafirma}</span>
                </div>
                <hr>
                <div style="font-family: Arial, sans-serif; font-size: 7px; border-top: 1px solid black; border-bottom: 1px solid black; padding: 5px 0; text-align: left;">
                <span>IMPRESO:{fecha_formateada3}</span>
            </div>
            {copy_label_html}
            </body>
            </html>
        """

    # ____________________________________________________________RECIVO DE INGRESO__________________________________________________________________________________________________

    def generate_default_html5(
        self,
        products_html,
        subtotal,
        total_descuento,
        total,
        note,
        realizado,
        qr_image,
        codigoseguridad,
        fechafirma,
    ):

        # Supongamos que la fecha está en formato datetime
        fecha = self.invoice_data.get("fVencimientoNCF", None)

        if fecha:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                fecha_formateada = fecha.strftime("%d-%m-%Y")
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_formateada = fecha.strftime("%d/%m/%Y")

            # Usar la fecha formateada
            print(f"VÁLIDO HASTA: {fecha_formateada}")
        else:
            print("Fecha no disponible")

        # Supongamos que la fecha está en formato datetime
        fecha2 = self.invoice_data.get("fecha", None)

        if fecha2:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha2, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                fecha_formateada2 = fecha2.strftime("%A, %d %B, %Y")
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_formateada2 = fecha.strftime("%A, %d %B, %Y")

            # Usar la fecha formateada
            print(f"VÁLIDO HASTA: {fecha_formateada2}")
        else:
            print("Fecha no disponible")

        # Obtener la fecha y hora actual
        fecha_hora_actual = datetime.now()

        # Formatear la fecha y hora como desees
        fecha_formateada3 = fecha_hora_actual.strftime("%d-%m-%Y")

        # valores formateados con la taza

        tasa_html = (
            f"<p style='margin: 0; padding: 0;'>TASA: {self.invoice_data.get('Tasa', '')}</p>"
            if self.invoice_data.get("Tasa", "")
            else ""
        )

        print("Fecha y hora actual:", fecha_formateada3)

        return f"""
            <html>
            <body style="font-family: Arial, sans-serif; font-size: 5pt; margin: 20px; width=100%;">
                <table width="100%" style="margin-bottom: 3px; padding: 0;">
                <tr>
                    <td style="text-align: left; vertical-align: top; padding: 0;">
                    <p style="margin: 0; padding: 0;"><b>{self.company_data.get('nombre_empresa', '')}</b></p>
                    <p style="margin: 0; padding: 0;">
                        {self.company_data.get('direccion', '')}<br />
                        Tel.: {self.company_data.get('telefono', '')}<br>
                        <>{self.company_data.get('rnc', '')}<br>&nbsp;

                    </p>
                    <table width="100%" style="border-collapse: collapse; margin-top: 0px;">
                    <p style="margin: 0; padding: 0;">
                        EN FECHA :&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {fecha_formateada2}<br />
                        RECIBI DE :&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{self.invoice_data.get('cliente', '')} - {self.invoice_data.get('nombre_cliente', '')}<br />
                        POR LA SUMA DE:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **MIL CIENTO OCHENTA CON 00/100 ** {self.invoice_data.get('moneda_type', '')}
                    </td>
                    <td style="text-align: right; vertical-align: top; padding: 0;">
                        <div style="text-align: left; display: inline-block;">
                            <p style="margin: 0; padding: 0;">&nbsp;</p>
                            <p style="margin: 0; padding: 0;"><b>RECIBO DE INGRESO {self.invoice_data.get('moneda_type', '')}</b>
                            <p style="margin: 0; padding: 0;"><b>ING.A00000001665</b>
                            <p style="margin: 0; padding: 0;"><b>Tasa</b>: 0.00
                            <p style="margin: 0; padding: 0;">
                            {tasa_html}
                        </div>
                    </td>
                </tr>
                </table>
                <table width="100%" style="border-collapse: collapse; margin-top: 0px;">
                    <tr>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">MONTO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">BALANCE</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">ABONO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">DESCUENTO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">PENDIENTE</th>
                    </tr>
                    {products_html}
                </table>
                <p colspan="3" style="text-align: center; font-weight: bold; margin-top: 0px;">*****ULTIMA LINEA*****</p>
                <hr>
                <!-- Tabla con métodos de pago a la izquierda y montos a la derecha -->
                <table width="60%" style="border-collapse: collapse; margin-top: 5px;">
                    <tr>
                        <td style="text-align: left; font-weight: bold;">EFECTIVO:</td>
                        <td style="text-align: right;">0.00</td>
                        <td style="text-align: right; font-weight: bold;">MONTO INGRESO: RD$</td>
                        <td style="text-align: right;">200.00</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; font-weight: bold;">CHEQUE :</td>
                        <td style="text-align: right;">200.00</td>
                        <td style="text-align: right; font-weight: bold;">MONTO INTERES: RD$</td>
                        <td style="text-align: right;">0.00</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; font-weight: bold;">TARJETA:</td>
                        <td style="text-align: right;">0.00</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; font-weight: bold;">TRANSFE:</td>
                        <td style="text-align: right;">0.00</td>
                    </tr>
                    <tr>
                        <td style="text-align: left; font-weight: bold;">DOLARES:</td>
                        <td style="text-align: right;">0.00</td>
                    </tr>
                </table>
                <table
                width="100%"
                style="border-collapse: collapse; margin-top: 5px; padding: 0;"
                >
                <tr>
                    <!-- Primer Bloque -->
                    <td
                        style="
                            text-align: center;
                            padding: 20px;
                            width: 33%;
                            font-size: 10px;
                            font-weight: bold;
                        "
                    >
                        <p style="margin: 0; font-size: 10px;">{realizado}</p>
                        <hr style="margin: 1px auto; width: 90%; border: 1px solid black;" />
                        <p style="margin: 1px 0 0;">Realizado</p>
                    </td>
                    <!-- Tercer Bloque -->
                    <td
                        style="
                            text-align: center;
                            padding: 20px;
                            width: 33%;
                            font-size: 10px;
                            font-weight: bold;
                        "
                    >
                        <p style="margin: 0; font-size: 10px;">&nbsp;</p>
                        <hr style="margin: 1px auto; width: 90%; border: 1px solid black;" />
                        <p style="margin: 1px 0 0;">Recibido</p>
                    </td>
                </tr>


                </table>
                    <tr>
                <div style="text-align: left; margin-top: 5px;">
                    <img src="{qr_image}" width="80" height="80" alt="QR Code"><br>
                    <span style="font-size: 5pt;">Código de Seguridad: {codigoseguridad}</span><br>
                    <span style="font-size: 5pt;">Fecha de Firma Digital: {fechafirma}</span>
                </div>
                <hr>
                <div style="font-family: Arial, sans-serif; font-size: 7px; border-top: 1px solid black; border-bottom: 1px solid black; padding: 5px 0; text-align: left;">
                <span>IMPRESO:{fecha_formateada3}</span>

            </body>
            </html>
        """

    # ____________________________________________________________CAJA CHICA_________________________________________________________________________________________________________

    def generate_default_html4(
        self,
        products_html,
        subtotal,
        total_descuento,
        total,
        note,
        recibido,
        realizado,
        qr_image,
        codigoseguridad,
        fechafirma,
    ):

        # Supongamos que la fecha está en formato datetime
        fecha = self.invoice_data.get("fVencimientoNCF", None)

        if fecha:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                fecha_formateada = fecha.strftime("%d-%m-%Y")
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_formateada = fecha.strftime("%d/%m/%Y")
            # Usar la fecha formateada
            print(f"VÁLIDO HASTA: {fecha_formateada}")
        else:
            print("Fecha no disponible")

        # Supongamos que la fecha está en formato datetime
        fecha2 = self.invoice_data.get("fecha", None)

        if fecha2:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha2, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                fecha_formateada2 = format_datetime(
                    fecha2, "EEEE, d 'de' MMMM 'de' y", locale="es"
                )
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_formateada2 = fecha.strftime("%A, %d %B, %Y")

            # Usar la fecha formateada
            print(f"VÁLIDO HASTA: {fecha_formateada2}")
        else:
            print("Fecha no disponible")

        # Obtener la fecha y hora actual
        fecha_hora_actual = datetime.now()

        # Formatear la fecha y hora como desees
        fecha_formateada3 = fecha_hora_actual.strftime("%d-%m-%Y")

        # valores formateados con la taza
        tasa1 = self.invoice_data.get("Tasa")
        montototal = self.invoice_data.get("Monto_total")

        tasa1 = self.invoice_data.get("Tasa", "")

        tasa_html = (
            f"<p style='margin: 0; padding: 0;'>TASA: {tasa1:.2f}</p>"
            if tasa1 not in [0, 1, "0", "1", "", None]
            else ""
        )

        valido_html = (
            f"<p style='margin: 0; padding: 0;'>VÁLIDO HASTA: {fecha_formateada}</p>"
            if fecha_formateada.strip()
            else ""
        )

        print("Fecha y hora actual:", fecha_formateada3)

        return f"""
            <html>
            <body style="font-family: Arial, sans-serif; font-size: 5pt; margin: 20px; width=100%;">
                <table width="100%" style="margin-bottom: 3px; padding: 0;">
                <tr>
                    <td style="text-align: left; vertical-align: top; padding: 0;">
                    <p style="margin: 0; padding: 0;"><b>{self.company_data.get('nombre_empresa', '')}</b></p>
                    <p style="margin: 0; padding: 0;">
                        {self.company_data.get('direccion', '')}<br />
                        Tel.: {self.company_data.get('telefono', '')} | Fax: {self.company_data.get('fax', '')}<br />
                        <b>RNC: {self.company_data.get('rnc', '')}</b><br>&nbsp;
                    </p>
                    <p style="margin: 0; padding: 0; text-align: center;"><b>{self.company_data.get('Sucursal', '')}</b></p>
                    <p style="margin: 0; padding: 0;">
                        EN FECHA:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {fecha_formateada2}<br />
                        BENEFICIARIO:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {realizado}<br />
                        POR LA SUMA DE:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {self.invoice_data.get('Monto_total', '')}
                    </td>
                    <td style="text-align: right; vertical-align: top; padding: 0;">
                        <div style="text-align: left; display: inline-block;">
                            <p style="margin: 0; padding: 0;">&nbsp;</p>
                            <p style="margin: 0; padding: 0;"><b>{self.invoice_data.get("ncf_type", "")}</b></p>
                            <p style="margin: 0; padding: 0;">e-NCF # {self.invoice_data.get('ncf', '')}
                            {valido_html}
                            <p style="margin: 0; padding: 0;">
                                <hr>
                            <p style="margin: 0; padding: 0;"><b>TRANS. No. {self.invoice_data.get('numero', '')}</b>
                            <p style="margin: 0; padding: 0;">
                            {tasa_html}
                        </div>
                    </td>
                </tr>
                </table>
                <table width="100%" style="border-collapse: collapse; margin-top: 0px;">
                    <tr>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CUENTA</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">DESCRIPCION</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">VALOR</th>
                    </tr>
                    {products_html}
                </table>
                <p colspan="3" style="text-align: center; font-weight: bold; margin-top: 0px;">*****ULTIMA LINEA*****</p>
                <hr>
                <table width="58%" style="border-collapse: collapse; margin-top: 0px; font-size: 5pt; padding: 10px; margin-right: 2px; text-align: right;">
                    <tr>
                    <td style="text-align: right; font-weight: bold; font-size: 6pt; padding: 2px 4px;">TOTAL {self.invoice_data.get('moneda_type', '')}:</td>
                    <td style="text-align: right; font-weight: bold; font-size: 6pt; padding: 2px 4px;">{montototal:,.2f}</td>
                    </tr>
                </table>
                <table
                width="100%"
                style="border-collapse: collapse; margin-top: 5px; padding: 0;"
                >
                <tr>
                    <!-- Primer Bloque -->
                    <td
                        style="
                            text-align: center;
                            padding: 20px;
                            width: 33%;
                            font-size: 10px;
                            font-weight: bold;
                        "
                    >
                        <p style="margin: 0; font-size: 10px;">&nbsp;</p>
                        <hr style="margin: 1px auto; width: 90%; border: 1px solid black;" />
                        <p style="margin: 1px 0 0;">Realizado</p>
                    </td>

                    <!-- Segundo Bloque -->
                    <td
                        style="
                            text-align: center;
                            padding: 20px;
                            width: 33%;
                            font-size: 10px;
                            font-weight: bold;
                        "
                    >
                        <p style="margin: 0; font-size: 10px;">&nbsp;</p>
                        <hr style="margin: 1px auto; width: 90%; border: 1px solid black;" />
                        <p style="margin: 1px 0 0;">Despachado</p>
                    </td>

                    <!-- Tercer Bloque -->
                    <td
                        style="
                            text-align: center;
                            padding: 20px;
                            width: 33%;
                            font-size: 10px;
                            font-weight: bold;
                        "
                    >
                        <p style="margin: 0; font-size: 10px;">&nbsp;</p>
                        <hr style="margin: 1px auto; width: 90%; border: 1px solid black;" />
                        <p style="margin: 1px 0 0;">Recibido</p>
                    </td>
                </tr>


                </table>

                <p style="margin-top: 10px; font-size:4pt;">{note}</p>
                <div style="text-align: left; margin-top: 5px;">
                    <img src="{qr_image}" width="80" height="80" alt="QR Code"><br>
                    <span style="font-size: 5pt;">Código de Seguridad: {codigoseguridad}</span><br>
                    <span style="font-size: 5pt;">Fecha de Firma Digital: {fechafirma}</span>
                </div>
                <hr>
                <div style="font-family: Arial, sans-serif; font-size: 7px; border-top: 1px solid black; border-bottom: 1px solid black; padding: 5px 0; text-align: left;">
                <span>IMPRESO:{fecha_formateada3}</span>
            </body>
            </html>
        """

    # ____________________________________________________________Nota de credito____________________________________________________________________________________________________

    def generate_default_html2(
        self,
        products_html,
        subtotal,
        total_descuento,
        total,
        note,
        realizado,
        qr_image,
        codigoseguridad,
        fechafirma,
        copy_label=None,
    ):

        # Supongamos que la fecha está en formato datetime
        fecha = self.invoice_data.get("fVencimientoNCF", None)

        if fecha:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                pass
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")

        # Supongamos que la fecha está en formato datetime
        fecha2 = self.invoice_data.get("fecha", None)

        if fecha2:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha2, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                fecha_formateada2 = fecha2.strftime("%d-%m-%Y")
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_formateada2 = fecha.strftime("%d-%m-%Y")

        # Supongamos que la fecha está en formato datetime
        fecha4 = self.invoice_data.get("FechaNCFModificado", None)

        if fecha2:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha4, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                pass
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")

        # Obtener la fecha y hora actual
        fecha_hora_actual = datetime.now()

        # Formatear la fecha y hora como desees
        fecha_formateada3 = fecha_hora_actual.strftime("%d-%m-%Y")

        # valores formateados con la taza
        tasa1 = self.invoice_data.get("Tasa")
        total_formateado = Decimal(self.invoice_data.get("AbonoNCFModificado")) / tasa1

        # valores formateados con comppletar
        numero = self.invoice_data.get(
            "numero", ""
        )  # Paréntesis para obtener el valor directamente
        numero_formateado = str(numero).zfill(
            11
        )  # Ahora sí, rellena hasta 11 dígitos con ceros

        montototal = Decimal(self.invoice_data.get("AbonoNCFModificado")) / tasa1
        Monto_total_en_letras = f"{num2words.num2words(int(montototal), lang='es').upper()} CON {int(round(montototal % 1, 2) * 100):02}/100"

        def load_printer_config():
            """Carga la configuración de la impresora desde un archivo JSON."""
            config_path = "config/config_print.json"
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    config = json.load(file)
                    return {
                        "printer_name": config.get("printer_name", None),
                        "copies": config.get(
                            "copies", 1
                        ),  # Default to 1 copy if not specified
                        "copy_labels": config.get(
                            "copy_labels",
                            [
                                "ORIGINAL - CLIENTE",
                                "COPIA - CAJA",
                                "COPIA - CONTABILIDAD",
                                "COPIA - ARCHIVO",
                            ],
                        ),
                        "concodigo": config.get(
                            "concodigo", 0
                        ),  # Add default value here
                        "show_copy_labels": config.get(
                            "show_copy_labels", True
                        ),  # Add default value for show_copy_labels
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                print(
                    "Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada."
                )
                return {
                    "printer_name": None,
                    "copies": 0,
                    "concodigo": 0,
                    "show_copy_labels": True,
                }

        config = load_printer_config()
        show_copy_labels = config.get("show_copy_labels", True)
        copy_label_html = (
            f'<div style="text-align: center; font-size: 5pt; font-weight: bold; margin-top: 2px;">{copy_label}</div>'
            if copy_label and show_copy_labels
            else ""
        )

        tasa_html = (
            f"<p style='margin: 0; padding: 0;'>TASA: {self.invoice_data.get('Tasa', '')}</p>"
            if self.invoice_data.get("Tasa", "")
            else ""
        )

        copy_label = copy_label

        return f"""
            <html>
            <body style="font-family: Arial, sans-serif; font-size: 5pt; margin: 20px; width=100%;">
                <table width="100%" style="margin-bottom: 3px; padding: 0;">
                <tr>
                    <td style="text-align: left; vertical-align: top; padding: 0;">
                    <p style="margin: 0; padding: 0;"><b>{self.company_data.get('nombre_empresa', '')}</b></p>
                    <p style="margin: 0; padding: 0;">
                        {self.company_data.get('direccion', '')}<br />
                        Tel.: {self.company_data.get('telefono', '')}<br />
                        RNC: {self.company_data.get('rnc', '')}<br />
                    </p>
                    <p style="margin: 0; padding: 0;">
                        <b>EN FECHA:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b> {fecha_formateada2}<br />
                        <b>HEMOS ACREDITADO A:</b> <b>{self.invoice_data.get('cliente', '')} - {self.invoice_data.get('nombre_cliente', '')}</b><br />
                        <b>LA SUMA DE:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b/> {Monto_total_en_letras}
                    </td>
                    <td style="text-align: right; vertical-align: top; padding: 0;">
                        <div style="text-align: left; display: inline-block;">
                            <p style="margin: 0; padding: 0;">&nbsp;</p>
                            <p style="margin: 0; padding: 0;"><b>{self.invoice_data.get('ncf_type', '')}</b>
                            <p style="margin: 0; padding: 0;"><b>e-NCF #</b> {self.invoice_data.get('ncf', '')}
                            <p style="margin: 0; padding: 0;"><b>NCF AFECTADO # {self.invoice_data.get('Ncf_Modificado', '')}</b></p>
                            <p style="margin: 0; padding: 0;"><b>Documento No.: {numero_formateado}<b/>
                            <p style="margin: 0; padding: 0;">
                            {tasa_html}
                        </div>
                    </td>
                </tr>
                </table>
                <p style="margin: 0; padding: 0; text-align: center;"><b>EXPRESADO EN {self.invoice_data.get('moneda_type2', '')}</b></p>
                <table width="100%" style="border-collapse: collapse; margin-top: 0px;">
                    <tr>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">FACTURA</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">FECHA</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">MONTO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">BALANCE</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">ABONO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">DESCUENTO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">PENDIENTE</th>
                    </tr>
                    {products_html}
                </table>
                <p colspan="3" style="text-align: center; font-weight: bold; margin-top: 0px;">*****ULTIMA LINEA*****</p>
                <hr>
                    <tr>
                        <td style="text-align: right; font-weight: bold; font-size: 6pt; padding: 2px 4px;">TOTAL {self.invoice_data.get('moneda_type', '')}:&nbsp;{total_formateado:,.2f}</td>
                        <!--<td style="text-align: right; font-weight: bold; font-size: 6pt; padding: 2px 4px;">{total_formateado:,.2f}</td>!-->
                    </tr>
                </table>
                <table
                width="100%"
                style="border-collapse: collapse; margin-top: 5px; padding: 0;"
                >
                <tr>
                    <!-- Primer Bloque -->
                    <td
                        style="
                            text-align: center;
                            padding: 20px;
                            width: 33%;
                            font-size: 10px;
                            font-weight: bold;
                        "
                    >
                        <p style="margin: 0; font-size: 10px;">{realizado}</p>
                        <hr style="margin: 1px auto; width: 90%; border: 1px solid black;" />
                        <p style="margin: 1px 0 0;">Realizado</p>
                    </td>

                    <!-- Segundo Bloque -->
                    <td
                        style="
                            text-align: center;
                            padding: 20px;
                            width: 33%;
                            font-size: 10px;
                            font-weight: bold;
                        "
                    >
                        <p style="margin: 0; font-size: 10px;">&nbsp;</p>
                        <hr style="margin: 1px auto; width: 90%; border: 1px solid black;" />
                        <p style="margin: 1px 0 0;">Autorizado</p>
                    </td>
                </tr>


                </table>


                <div style="text-align: left; margin-top: 5px;">
                    <img src="{qr_image}" width="80" height="80" alt="QR Code"><br>
                    <span style="font-size: 5pt;">Código de Seguridad: {codigoseguridad}</span><br>
                    <span style="font-size: 5pt;">Fecha de Firma Digital: {fechafirma}</span>
                </div>
                <hr>
                <div style="font-family: Arial, sans-serif; font-size: 7px; border-top: 1px solid black; border-bottom: 1px solid black; padding: 5px 0; text-align: left;">
                <span>IMPRESO:{fecha_formateada3}</span>
                </div>
                {copy_label_html}
            </body>
            </html>
        """

    # _________________________________________________________________Nota de credito por devolucion___________________________________________________________________________________________

    # ______________________________________________________________________________________________________________________________________________________________________________________________
    def generate_qr_code(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=2,
            border=1,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")

        # Convert the QR image to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = QtCore.QByteArray(buffer.getvalue()).toBase64().data().decode("utf-8")
        return f"data:image/png;base64,{img_str}"

    def load_custom_layout(self):
        try:
            with open("custom_layout_template.html", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error loading custom layout: {str(e)}")
            return None

    def preview_pdf(self, parent):
        printer = QtPrintSupport.QPrinter()
        preview = QtPrintSupport.QPrintPreviewDialog(printer, parent)
        preview.paintRequested.connect(self.generate_pdf)
        printer.setPageSize(QtPrintSupport.QPrinter.Letter)
        preview.exec_()

    def print_pdf(self, parent):
        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)

        dialog = QtPrintSupport.QPrintDialog(printer, parent)
        if dialog.exec_() == QtPrintSupport.QPrintDialog.Accepted:
            self.generate_pdf(printer)

    def load_printer_config(self):
        """Carga la configuración de la impresora desde un archivo JSON."""
        config_path = "config/config_print.json"
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config = json.load(file)
                return {
                    "printer_name": config.get("printer_name", None),
                    "controlportipo": config.get("controlportipo", 0),
                    "copies": config.get(
                        "copies", 1
                    ),  # Default to 1 copy if not specified
                    "copy_labels": config.get(
                        "copy_labels",
                        [
                            "ORIGINAL - CLIENTE",
                            "COPIA - CAJA",
                            "COPIA - CONTABILIDAD",
                            "COPIA - ARCHIVO",
                        ],
                    ),
                    "numerodeimpresionesportipo": config.get(
                        "numerodeimpresionesportipo",
                        {"31": 2, "32": 1, "41": 1, "43": 1},
                    ),
                    "numerodeimpresionesportipop": config.get(
                        "numerodeimpresionesportipop",
                        {"1": 2, "2": 1},
                    ),
                }
        except (FileNotFoundError, json.JSONDecodeError):
            print(
                "Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada."
            )
            return {"printer_name": None, "copies": 0}

    def get_default_printer(self):
        """Obtiene la impresora predeterminada del sistema."""
        try:
            return win32print.GetDefaultPrinter()
        except win32print.error:
            print(
                "Advertencia: No hay una impresora predeterminada configurada en el sistema."
            )
            return None

    def get_printer_name(
        self,
    ):
        """Determina la impresora a usar: Configurada en JSON o la predeterminada."""
        config = self.load_printer_config()
        printer_name = config.get("printer_name") or self.get_default_printer()
        tipo_ecf = str(self.invoice_data.get("tipoecf", 0))
        tipopago = str(self.invoice_data.get("tipopago", 0))
        controlportipo = config.get("controlportipo", 0)

        copies_default = config.get("copies", 1)

        # Determinar número de copias según configuración
        if controlportipo == 1:
            # Primero intenta por tipo ECF
            numerodeimpresionesportipo = config.get("numerodeimpresionesportipo", {})
            if tipo_ecf in numerodeimpresionesportipo:
                copies = numerodeimpresionesportipo.get(tipo_ecf, copies_default)
            else:
                # Si no hay configuración por tipo ECF, intenta por tipo de pago
                numerodeimpresionesportipop = config.get(
                    "numerodeimpresionesportipop", {}
                )
                if tipopago in numerodeimpresionesportipop:
                    copies = numerodeimpresionesportipop.get(tipopago, copies_default)
                else:
                    # Si tampoco está, usar el valor por defecto
                    copies = copies_default
        else:
            copies = copies_default

        return printer_name, copies, config.get("copy_labels", [])

    # _____________________________Factura_____________________________________________

    def print_pdf2(self, output_directory, file_name):
        """
        Genera un PDF y lo envía a la impresora configurada en config.json o a la predeterminada del sistema.

        Args:
            output_directory (str): Directorio donde se generará el PDF
            file_name (str): Nombre del archivo PDF a generar
        """
        # Asegurar la existencia de una instancia de QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Asegurar que el directorio de salida exista
        os.makedirs(output_directory, exist_ok=True)

        # Ruta de salida del PDF
        output_path = os.path.join(output_directory, file_name)

        # Configurar el QPrinter para generar PDF
        pdf_printer = QPrinter(QPrinter.HighResolution)
        pdf_printer.setOutputFileName(output_path)
        pdf_printer.setOutputFormat(QPrinter.PdfFormat)

        # Generar el PDF
        self.generate_pdf(pdf_printer)

        # Verificar impresoras disponibles
        available_printers = [
            printer_info.printerName()
            for printer_info in QPrinterInfo.availablePrinters()
        ]

        # Obtener nombre de impresora, número de copias y etiquetas de copia
        printer_name, copies, copy_labels = self.get_printer_name()

        # Validar disponibilidad de la impresora
        if printer_name not in available_printers:
            print(
                f"Advertencia: La impresora '{printer_name}' no está disponible. Usando la predeterminada."
            )
            printer_name = self.get_default_printer()

        if not printer_name:
            print("Error: No hay impresora disponible para imprimir.")
            return

        # Print each copy with its corresponding label
        for i in range(copies):
            # Configurar para impresión física
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.NativeFormat)
            printer.setPrinterName(printer_name)

            # Add copy label to the document
            copy_label = copy_labels[i] if i < len(copy_labels) else f"COPIA {i + 1}"
            print(
                f"Imprimiendo {copy_label} | NCF: {self.invoice_data.get('ncf', '')} | RNC Emisor: {self.company_data.get('rnc', '')} ..."
            )

            # Generate PDF with the copy_label parameter
            self.generate_pdf(printer, copy_label=copy_label)

        # Cerrar la aplicación Qt si no hay ventanas abiertas
        if app is not None and not QApplication.topLevelWidgets():
            app.quit()

    # ________________________________Nota de credito__________________________________________________________ -

    def print_pdf_nota_credito(self, output_directory, file_name):
        """
        Genera un PDF y lo envía a la impresora configurada en config.json o a la predeterminada del sistema.

        Args:
            output_directory (str): Directorio donde se generará el PDF
            file_name (str): Nombre del archivo PDF a generar
        """
        # Asegurar la existencia de una instancia de QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Asegurar que el directorio de salida exista
        os.makedirs(output_directory, exist_ok=True)

        # Ruta de salida del PDF
        output_path = os.path.join(output_directory, file_name)

        # Configurar el QPrinter para generar PDF
        pdf_printer = QPrinter(QPrinter.HighResolution)
        pdf_printer.setOutputFileName(output_path)
        pdf_printer.setOutputFormat(QPrinter.PdfFormat)

        # Generar el PDF
        self.generate_pdf2(pdf_printer)

        # Verificar impresoras disponibles
        available_printers = [
            printer_info.printerName()
            for printer_info in QPrinterInfo.availablePrinters()
        ]

        # Obtener nombre de impresora, número de copias y etiquetas de copia
        printer_name, copies, copy_labels = self.get_printer_name()

        # Validar disponibilidad de la impresora
        if printer_name not in available_printers:
            print(
                f"Advertencia: La impresora '{printer_name}' no está disponible. Usando la predeterminada."
            )
            printer_name = self.get_default_printer()

        if not printer_name:
            print("Error: No hay impresora disponible para imprimir.")
            return

        # Print each copy with its corresponding label
        for i in range(copies):
            # Configurar para impresión física
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.NativeFormat)
            printer.setPrinterName(printer_name)

            # Add copy label to the document
            copy_label = copy_labels[i] if i < len(copy_labels) else f"COPIA {i + 1}"
            print(
                f"Imprimiendo {copy_label} | NCF: {self.invoice_data.get('ncf', '')} | RNC Emisor: {self.company_data.get('rnc', '')} ..."
            )

            # Generate PDF with the copy_label parameter
            self.generate_pdf2(printer, copy_label=copy_label)

        # Cerrar la aplicación Qt si no hay ventanas abiertas
        if app is not None and not QApplication.topLevelWidgets():
            app.quit()

    # __________________________________________Nota de credito por devolucion______________________________________________________________

    # _______________________________________________CAJA CHICA______________________________________________________________________________________

    def print_pdf_caja_chica(self, output_directory, file_name):
        """
        Genera un PDF y lo envía a la impresora configurada en config.json o a la predeterminada del sistema.

        Args:
            output_directory (str): Directorio donde se generará el PDF
            file_name (str): Nombre del archivo PDF a generar
        """
        # Asegurar la existencia de una instancia de QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Asegurar que el directorio de salida exista
        os.makedirs(output_directory, exist_ok=True)

        # Ruta de salida del PDF
        output_path = os.path.join(output_directory, file_name)

        # Configurar el QPrinter para generar PDF
        pdf_printer = QPrinter(QPrinter.HighResolution)
        pdf_printer.setOutputFileName(output_path)
        pdf_printer.setOutputFormat(QPrinter.PdfFormat)

        # Generar el PDF
        self.generate_pdf4(
            pdf_printer
        )  # Método que debes implementar para generar contenido PDF

        # Verificar impresoras disponibles
        available_printers = [
            printer_info.printerName()
            for printer_info in QPrinterInfo.availablePrinters()
        ]

        # Obtener nombre de impresora y número de copias
        printer_name, copies, copy_labels = self.get_printer_name()

        # Validar disponibilidad de la impresora
        if printer_name not in available_printers:
            print(
                f"Advertencia: La impresora '{printer_name}' no está disponible. Usando la predeterminada."
            )
            printer_name = self.get_default_printer()

        if not printer_name:
            print("Error: No hay impresora disponible para imprimir.")
            return

        # Configurar para impresión física
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.NativeFormat)
        printer.setPrinterName(printer_name)

        # Configuración de copias (método alternativo)
        try:
            # Intentar métodos diferentes para establecer copias
            if hasattr(printer, "setCopyCount"):
                printer.setCopyCount(copies)
            elif hasattr(printer, "setCollateCopies"):
                printer.setCollateCopies(copies)
            else:
                print(
                    f"Advertencia: No se pudo establecer el número de copias ({copies})"
                )
        except Exception as e:
            print(f"Error al configurar copias: {e}")

        # Imprimir cada copia con su etiqueta correspondiente
        for i in range(copies):
            copy_label = copy_labels[i] if i < len(copy_labels) else f"COPIA {i + 1}"
            print(
                f"Imprimiendo {copy_label} | NCF: {self.invoice_data.get('ncf', '')} | RNC Emisor: {self.company_data.get('rnc', '')} ..."
            )

        # Enviar el documento a la impresora
        print(f"Enviando {copies} copia(s) a la impresora '{printer_name}'...")
        self.generate_pdf4(printer)  # Generar contenido para impresión

        # Cerrar la aplicación Qt si no hay ventanas abiertas
        if app is not None and not QApplication.topLevelWidgets():
            app.quit()

    # ______________________________________________RECIVO DE INGRESO__________________________________________

    def print_pdf_recivo_de_ingreso(self, output_directory, file_name):
        """
        Genera un PDF y lo envía a la impresora configurada en config.json o a la predeterminada del sistema.

        Args:
            output_directory (str): Directorio donde se generará el PDF
            file_name (str): Nombre del archivo PDF a generar
        """
        # Asegurar la existencia de una instancia de QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Asegurar que el directorio de salida exista
        os.makedirs(output_directory, exist_ok=True)

        # Ruta de salida del PDF
        output_path = os.path.join(output_directory, file_name)

        # Configurar el QPrinter para generar PDF
        pdf_printer = QPrinter(QPrinter.HighResolution)
        pdf_printer.setOutputFileName(output_path)
        pdf_printer.setOutputFormat(QPrinter.PdfFormat)

        # Generar el PDF
        self.generate_pdf5(
            pdf_printer
        )  # Método que debes implementar para generar contenido PDF

        # Verificar impresoras disponibles
        available_printers = [
            printer_info.printerName()
            for printer_info in QPrinterInfo.availablePrinters()
        ]

        # Obtener nombre de impresora y número de copias
        printer_name, copies = self.get_printer_name()

        # Validar disponibilidad de la impresora
        if printer_name not in available_printers:
            print(
                f"Advertencia: La impresora '{printer_name}' no está disponible. Usando la predeterminada."
            )
            printer_name = self.get_default_printer()

        if not printer_name:
            print("Error: No hay impresora disponible para imprimir.")
            return

        # Configurar para impresión física
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.NativeFormat)
        printer.setPrinterName(printer_name)

        # Configuración de copias (método alternativo)
        try:
            # Intentar métodos diferentes para establecer copias
            if hasattr(printer, "setCopyCount"):
                printer.setCopyCount(copies)
            elif hasattr(printer, "setCollateCopies"):
                printer.setCollateCopies(copies)
            else:
                print(
                    f"Advertencia: No se pudo establecer el número de copias ({copies})"
                )
        except Exception as e:
            print(f"Error al configurar copias: {e}")

        # Enviar el documento a la impresora
        print(f"Enviando {copies} copia(s) a la impresora '{printer_name}'...")
        self.generate_pdf5(printer)  # Generar contenido para impresión

        # Cerrar la aplicación Qt si no hay ventanas abiertas
        if app is not None and not QApplication.topLevelWidgets():
            app.quit()

    # _____________________________________NOTA DE DEBITO___________________________________________________________
    def print_pdf_nota_debito(self, output_directory, file_name):
        """
        Genera un PDF y lo envía a la impresora configurada en config.json o a la predeterminada del sistema.

        Args:
            output_directory (str): Directorio donde se generará el PDF
            file_name (str): Nombre del archivo PDF a generar
        """
        # Asegurar la existencia de una instancia de QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Asegurar que el directorio de salida exista
        os.makedirs(output_directory, exist_ok=True)

        # Ruta de salida del PDF
        output_path = os.path.join(output_directory, file_name)

        # Configurar el QPrinter para generar PDF
        pdf_printer = QPrinter(QPrinter.HighResolution)
        pdf_printer.setOutputFileName(output_path)
        pdf_printer.setOutputFormat(QPrinter.PdfFormat)

        # Generar el PDF
        self.generate_pdf6(pdf_printer)

        # Verificar impresoras disponibles
        available_printers = [
            printer_info.printerName()
            for printer_info in QPrinterInfo.availablePrinters()
        ]

        # Obtener nombre de impresora, número de copias y etiquetas de copia
        printer_name, copies, copy_labels = self.get_printer_name()

        # Validar disponibilidad de la impresora
        if printer_name not in available_printers:
            print(
                f"Advertencia: La impresora '{printer_name}' no está disponible. Usando la predeterminada."
            )
            printer_name = self.get_default_printer()

        if not printer_name:
            print("Error: No hay impresora disponible para imprimir.")
            return

        # Print each copy with its corresponding label
        for i in range(copies):
            # Configurar para impresión física
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.NativeFormat)
            printer.setPrinterName(printer_name)

            # Add copy label to the document
            copy_label = copy_labels[i] if i < len(copy_labels) else f"COPIA {i + 1}"
            print(
                f"Imprimiendo {copy_label} | NCF: {self.invoice_data.get('ncf', '')} | RNC Emisor: {self.company_data.get('rnc', '')} ..."
            )

            # Generate PDF with the copy_label parameter
            self.generate_pdf6(printer, copy_label=copy_label)

        # Cerrar la aplicación Qt si no hay ventanas abiertas
        if app is not None and not QApplication.topLevelWidgets():
            app.quit()
