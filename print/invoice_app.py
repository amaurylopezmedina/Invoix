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

        # Generate QR code and related data outside the loop to make it available for every page
        codigoseguridad = self.invoice_data.get("codigoseguridad", "")
        fechafirma = self.invoice_data.get("fechafirma", "")
        url_qr = self.invoice_data.get("URLQR", "")
        qr_image = self.generate_qr_code(url_qr)

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

            # Generate page HTML - pass current_page and total_pages to header
            page_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; font-size: 5pt; margin: 20px; width=100%;">
                    {self.generate_header_html(current_page, total_pages, copy_label)}
                    {self.generate_detail_html_page(products_html, pagos_html, total_descuento, is_last_page,total_quantity,counts_per_page )}
                    {self.generate_footer_html(note, note2, note3, note4, realizado, qr_image, codigoseguridad, fechafirma, total_quantity, copy_label) if is_last_page else self.generate_page_footer(counts_per_page[page_index], qr_image, codigoseguridad, fechafirma)}
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
                        "concodigo": config.get(
                            "concodigo", 0
                        ),  # Add default value here
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
        descuento_global = self.descuento_recargo.get("monto")

        # Initialize note3 as an empty string or collect all notes
        all_notes = []

        # Call the local function without self
        config = load_printer_config()
        concodigo = config.get(
            "concodigo", 0
        )  # This variable determines if the code column should be shown
        conunidad = config.get("conunidad", 0)
        condesc = config.get("condescuento", 0)
        concantidaddecimal = config.get("concantidaddecimal", 0)
        numerodecimales = config.get("numerodecimales", 2)

        # Crear formato para cantidades basado en numerodecimales
        cantidad_format = f"{{:,.{numerodecimales}f}}"

        if concantidaddecimal == 1:
            ent = "cantidad"
        else:
            ent = "int(cantidad)"
        for product in products:
            cantidad = Decimal(str(product["cantidad"]))
            precio = Decimal(str(product["precio"])) / tasa1
            descuento = Decimal(str(product.get("descuento", 0))) / tasa1
            valor = Decimal(str(product.get("valor", 0))) / tasa1
            itbis = Decimal(str(product.get("itbis", 0))) / tasa1

            # Collect notes from all products
            if "nota3" in product and product.get("nota3"):
                all_notes.append(product.get("nota3", ""))

            # Determinar cómo mostrar la cantidad basado en concantidaddecimal
            if concantidaddecimal == 1:
                # Mostrar como decimal con numerodecimales
                try:
                    cantidad_display = cantidad_format.format(cantidad)
                except Exception as e:
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
                    </tr>
                """
            elif concodigo == 0 and conunidad == 0:
                descuento_cell = (
                    f'<td style="padding: 1px; text-align: right;">{descuento:,.2f}</td>'
                    if condesc == 1
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
                    </tr>
                """
            elif concodigo == 1 and conunidad == 0:
                descuento_cell = (
                    f'<td style="padding: 1px; text-align: right;">{descuento:,.2f}</td>'
                    if condesc == 1
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
                    </tr>
                """
            elif concodigo == 0 and conunidad == 1:
                descuento_cell = (
                    f'<td style="padding: 1px; text-align: right;">{descuento:,.2f}</td>'
                    if condesc == 1
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
                fecha_formateada = fecha.strftime("%d-%m-%Y")
            elif isinstance(fecha, str):
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_formateada = fecha.strftime("%d/%m/%Y")
            else:
                fecha_formateada = ""

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

        tasa_html = (
            f"<p style='margin: 0; padding: 0;'>TASA: {self.invoice_data.get('Tasa', ''):.2f}</p>"
            if self.invoice_data.get("Tasa", "")
            else ""
        )
        '''valido_html = f"<p style='margin: 0; padding: 0;'>VÁLIDO HASTA: {fecha_formateada, ''}</p>" if {fecha_formateada} != '' else ""'''

        print("Fecha y hora actual:", fecha_formateada3)

        # valores formateados con la taza
        tasa1 = self.invoice_data.get("Tasa")

        total_descuento_formateado = total_descuento

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

        tipopago = self.invoice_data.get("tipopago", "")
        if tipopago == 2:
            email = f"<b>CORREO</b>:"
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
                            {self.company_data.get('direccion', '')}<br />
                            RNC: {self.company_data.get('rnc', '')} | Tel.: {self.company_data.get('telefono', '')}<br>&nbsp;
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
                            <p style="margin: 0; padding: 0;">FECHA FACT: {self.invoice_data.get('fecha', '').strftime('%d-%m-%Y')}</p>
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

        # Call the local function without self
        config = load_printer_config()
        concodigo = config.get("concodigo", 0)
        conunidad = config.get("conunidad", 0)
        condesc = config.get("condescuento", 0)
        firma = config.get("firma", 0)  # Add firma configuration
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
            table_html = f"""
                <table width="100%" style="border-collapse: collapse; margin-top: 0px; font-family: sans-serif; font-size: {tamano_general};">
                    <tr>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CANTIDAD</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">DESCRIPCION</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">PRECIO</th>
                        {descuento_th}
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">ITBIS</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">VALOR</th>
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

    def generate_page_footer(self, item_count, qr_image, codigoseguridad, fechafirma):
        """Genera un footer individual para cada ítem."""

        def load_printer_config():
            """Carga la configuración de la impresora desde un archivo JSON."""
            config_path = "config/config_print.json"
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    config = json.load(file)
                    return {
                        "tamano_general": config.get("tamano_general", "10pt"),
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                print(
                    "Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada."
                )
                return {
                    "tamano_general": "10pt",
                }

        config = load_printer_config()
        tamano_general = config.get("tamano_general", "10pt")

        fecha_hora_actual = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        return f"""
                <table width="100%" style="border-collapse: collapse; margin: 2px 0; font-family: Verdana, sans-serif; font-size: 5pt;">
                    <tr><td style="border-top: 1px solid black;"></td></tr>
                    <tr>
                        <td align="left" style="padding-right: 15px;">Items: {item_count}</td>
                    </tr>
                </table>
                <div style="text-align: left; margin-top: 10px; font-family: Verdana, sans-serif; font-size: {tamano_general};">
                    <img src="{qr_image}" width="54" height="54" alt="QR Code"><br>
                    <span style="font-size: {tamano_general};">Código de Seguridad: {codigoseguridad}</span><br>
                    <span style="font-size: {tamano_general};">Fecha de Firma Digital: {fechafirma}</span>
                </div>
                <hr>
                <div style="font-size: 7px; border-top: 1px solid black; border-bottom: 1px solid black; padding: 5px 0; text-align: left; font-family: Verdana, sans-serif; font-size: {tamano_general};">
                    <span>IMPRESO: {fecha_hora_actual}</span>
                </div>
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
        show_copy_labels = config.get("show_copy_labels", True)
        tamano_general = config.get("tamano_general", "10pt")
        copy_label_html = (
            f'<div style="text-align: center; font-size: 5pt; font-weight: bold; margin-top: 2px;">{copy_label}</div>'
            if copy_label and show_copy_labels
            else ""
        )
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
                        <p style="margin: 0; font-size: 7px;">{realizado if self.invoice_data.get('cajero') not in [None, '' ] and firma == 1 else '&nbsp;'}</p>
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
        printer_name = config["printer_name"] or self.get_default_printer()
        tipo_ecf = self.invoice_data.get("tipoecf", 0)
        controlportipo = config.get("controlportipo", 0)

        # Determinar número de copias según configuración
        if controlportipo == 1:
            # Busca en numerodeimpresionesportipo según el TipoECF
            copies = config.get("numerodeimpresionesportipo", {}).get(str(tipo_ecf), 1)
        else:
            copies = config["copies"]

        return printer_name, copies, config["copy_labels"]

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
            copy_label = copy_labels[i] if i < len(copy_labels) else f"COPIA {i+1}"
            print(
                f"Imprimiendo {copy_label} | NCF: {self.invoice_data.get('ncf', '')} | RNC Emisor: {self.company_data.get('rnc', '')} ..."
            )

            # Generate PDF with the copy_label parameter
            self.generate_pdf(printer, copy_label=copy_label)

        # Cerrar la aplicación Qt si no hay ventanas abiertas
        if app is not None and not QApplication.topLevelWidgets():
            app.quit()