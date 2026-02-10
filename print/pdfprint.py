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
    def __init__(self, company_data, invoice_data, products, forms):
        self.company_data = company_data
        self.invoice_data = invoice_data
        self.products = products
        self.forms = forms
        self.printer_name = self.get_printer_name()
        
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        
        
        
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
                        "copies": config.get("copies", 1),  # Default to 1 copy if not specified
                        "copy_labels": config.get("copy_labels", ['ORIGINAL - CLIENTE', 'COPIA - CAJA', 'COPIA - CONTABILIDAD', 'COPIA - ARCHIVO']),
                        "nump": config.get("nump", 0),
                        "concodigo": config.get("concodigo", 0),  # Add default value here
                        "conunidad": config.get("conunidad", 0)
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                print("Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada.")
                return {"printer_name": None, "copies": 0, "concodigo": 0, "conunidad": 0, "nump": 0}
				
        def calculate_lines_for_product(product, max_line_length=50):
            """
            Calcula cuántas líneas ocupa un producto basado en la longitud de su descripción.

            Args:
                product (dict): Producto con la clave 'descripcion'.
                max_line_length (int): Longitud máxima de una línea antes de dividir.

            Returns:
                int: Número de líneas que ocupa el producto.
            """
            description = product.get('descripcion', '')
            return (len(description) // max_line_length) + 1

        def split_products_into_pages(products, products_per_page, max_line_length=50):
            """
            Divide los productos en páginas considerando que algunos productos pueden ocupar más de una línea.

            Args:
                products (list): Lista de productos.
                products_per_page (int): Número máximo de productos por página.
                max_line_length (int): Longitud máxima de una línea antes de dividir.

            Returns:
                list: Lista de páginas, cada una con los productos que caben.
            """
            pages = []
            current_page = []
            current_count = 0

            for product in products:
                lines = calculate_lines_for_product(product, max_line_length)
                if current_count + lines > products_per_page:
                    pages.append(current_page)
                    current_page = []
                    current_count = 0
                current_page.append(product)
                current_count += lines

            if current_page:
                pages.append(current_page)

            return pages

        # Calculate how many products per page
        config = load_printer_config()
        nump = config.get("nump", 0)  # Default to 0 if not specified in the configuration
        PRODUCTS_PER_PAGE = nump
        
        # Split products into pages
        pages = split_products_into_pages(self.products, PRODUCTS_PER_PAGE)
        total_pages = len(pages)
        
        # Initialize final HTML
        final_html = []
        
        for page_index, page_products in enumerate(pages):
            current_page = page_index + 1
            is_last_page = current_page == total_pages
            
            # Generate HTML for current page's products and get running totals
            products_html, total_descuento, total_quantity, note3, pagos_html = self.generate_products_html_page(
                page_products,
                self.forms,
                include_totals=is_last_page
            )
        
            # Calculate total only on the last page
            
            # Get additional fields for the last page
            note = "\n".join(self.invoice_data.get('observacion', '').replace('|', '.<br>') for _ in [1]) if is_last_page else ''
            note2 = "\n".join(self.invoice_data.get('nota', '').replace('|', '.<br>') for _ in [1]) if is_last_page else ''
            note4 = "\n".join(self.invoice_data.get('NotaPago', '').replace('|', '.<br>') for _ in [1]) if is_last_page else ''
            realizado = self.invoice_data.get('cajero') if is_last_page else ''
            codigoseguridad = self.invoice_data.get('codigoseguridad', '') if is_last_page else ''
            fechafirma = self.invoice_data.get('fechafirma', '') if is_last_page else ''
            url_qr = self.invoice_data.get('URLQR', '') if is_last_page else ''
            
            # Generate QR code only on the last page
            qr_image = self.generate_qr_code(url_qr) if is_last_page else ''
            
            # Generate page HTML - pass current_page and total_pages to header
            page_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; font-size: 5pt; margin: 20px; width=100%;">
                    {self.generate_header_html(current_page, total_pages)}
                    {self.generate_detail_html_page(products_html, pagos_html, total_descuento, is_last_page)}
                    {self.generate_footer_html(note, note2, note3,note4, realizado, qr_image, codigoseguridad, fechafirma, total_quantity, copy_label) if is_last_page else self.generate_page_footer(total_quantity)}
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
                        "copies": config.get("copies", 1),  # Default to 1 copy if not specified
                        "copy_labels": config.get("copy_labels", ['ORIGINAL - CLIENTE', 'COPIA - CAJA', 'COPIA - CONTABILIDAD', 'COPIA - ARCHIVO']),
                        "concodigo": config.get("concodigo", 0),  # Add default value here
                        "conunidad": config.get("conunidad", 0)
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                print("Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada.")
                return {"printer_name": None, "copies": 0, "concodigo": 0, "conunidad": 0}
                
        products_html = ""
        pagos_html = ""  # Inicializar pagos_html como una cadena vacía
        total_descuento = Decimal('0.00')
        total_quantity = 0
        tasa1 = self.invoice_data.get('Tasa')

        # Initialize note3 as an empty string or collect all notes
        all_notes = []

        # Call the local function without self
        config = load_printer_config()
        concodigo = config.get("concodigo", 0)  # This variable determines if the code column should be shown
        conunidad = config.get("conunidad", 0)

        for product in products:
            cantidad = Decimal(str(product['cantidad']))
            precio = Decimal(str(product['precio'])) / tasa1
            descuento = Decimal(str(product.get('descuento', 0))) / tasa1
            valor = Decimal(str(product.get('valor', 0))) / tasa1
            itbis = Decimal(str(product.get('itbis', 0))) / tasa1

            # Collect notes from all products
            if 'nota3' in product and product.get('nota3'):
                all_notes.append(product.get('nota3', ''))

            # Create the product row HTML based on concodigo value
            if concodigo == 1 and conunidad == 1:
                products_html += f"""
                    <tr>
                        <td style="padding: 0px; text-align: left; width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"> {cantidad:.2f} </td>
                        <td style="padding: 0px;text-align: left">{product['codigo']}</td>
                        <td style="padding: 0px;">{product['descripcion']}</td>
                        <td style="padding: 0px;">{product['unidad']}</td>
                        <td style="padding: 0px; text-align: right;">{precio:,.2f}</td>
                        <td style="padding: 0px; text-align: right;">{descuento:,.2f}</td>
                        <td style="padding: 0px; text-align: right;">{itbis:,.2f}</td>
                        <td style="padding: 0px; text-align: right;">{valor:,.2f}</td>
                    </tr>
                """
            elif concodigo == 0 and conunidad == 0:
                products_html += f"""
                    <tr>
                        <td style="padding: 0px; text-align: left; width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"> {cantidad:.2f} </td>
                        <td style="padding: 0px;">{product['descripcion']}</td>
                        <td style="padding: 0px; text-align: right;">{precio:,.2f}</td>
                        <td style="padding: 0px; text-align: right;">{descuento:,.2f}</td>
                        <td style="padding: 0px; text-align: right;">{itbis:,.2f}</td>
                        <td style="padding: 0px; text-align: right;">{valor:,.2f}</td>
                    </tr>
                """
            elif concodigo == 1 and conunidad == 0:
                products_html += f"""
                    <tr>
                        <td style="padding: 0px; text-align: left; width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"> {cantidad:.2f} </td>
                        <td style="padding: 0px;text-align: left">{product['codigo']}</td>
                        <td style="padding: 0px;">{product['descripcion']}</td>
                        <td style="padding: 0px; text-align: right;">{precio:,.2f}</td>
                        <td style="padding: 0px; text-align: right;">{descuento:,.2f}</td>
                        <td style="padding: 0px; text-align: right;">{itbis:,.2f}</td>
                        <td style="padding: 0px; text-align: right;">{valor:,.2f}</td>
                    </tr>
                """
            elif concodigo == 0 and conunidad == 1:
                products_html += f"""
                    <tr>
                        <td style="padding: 0px; text-align: right; width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"> {cantidad:.2f} </td>
                        <td style="padding: 0px;">{product['descripcion']}</td>
                        <td style="padding: 0px;">{product['unidad']}</td>
                        <td style="padding: 0px; text-align: right;">{precio:,.2f}</td>
                        <td style="padding: 0px; text-align: right;">{descuento:,.2f}</td>
                        <td style="padding: 0px; text-align: right;">{itbis:,.2f}</td>
                        <td style="padding: 0px; text-align: right;">{valor:,.2f}</td>
                    </tr>
                """

            # Always calculate quantity total for the current page
            total_quantity += cantidad

            if include_totals:
                total_descuento += descuento

        # Generar pagos_html
        if forms:
            for forma in forms:
                monto = Decimal(str(forma['MontoPago'])) / tasa1
                pagos_html += f"""
                    <tr>
                    <td style="text-align: right; font-size: 6pt; padding: 2px 4px">{forma['FormaPagoL']}</td>
                    <td style="text-align: right; font-size: 6pt; padding: 2px 4px">{monto:,.2f}</td>
                    </tr>
                """
        else:
            pagos_html = ''

        # Join notes with line breaks if there's a period in the text
        note3 = "\n".join(note.replace('|', '.<br>') for note in all_notes) if all_notes else ""

        return products_html, total_descuento, total_quantity, note3, pagos_html
        
    def generate_default_html(self, products_html, total_descuento, total, note, realizado, qr_image, codigoseguridad, fechafirma, total_quantity,pagos_html):
        # Generar cada sección por separado
        header_html = self.generate_header_html()
        detail_html = self.generate_detail_html(products_html, total_descuento,pagos_html, total)
        footer_html = self.generate_footer_html(note, realizado, qr_image, codigoseguridad, fechafirma, total_quantity)
# Supongamos que la fecha está en formato datetime
        fecha = self.invoice_data.get('fVencimientoNCF', '')

        if fecha:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                fecha_formateada = fecha.strftime('%d-%m-%Y')
            elif isinstance(fecha, str):
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                fecha_formateada = fecha.strftime('%d/%m/%Y')
            else:
                fecha_formateada = ''
            
            # Usar la fecha formateada

            
# Supongamos que la fecha está en formato datetime
        fecha2 = self.invoice_data.get('fecha', None)

        if fecha2:
            # Verifica si fecha es un objeto datetime
            if isinstance(fecha2, datetime):
                # Formatear la fecha en el formato deseado, por ejemplo 'DD/MM/YYYY'
                fecha_formateada2 = fecha2.strftime('%d-%m-%Y')
            else:
                # Si no es un objeto datetime, intenta convertirlo
                fecha_str = str(fecha)  # Convertir a cadena si es necesario
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                fecha_formateada2 = fecha.strftime('%d-%m-%Y')
            
            # Usar la fecha formateada
            print(f"VÁLIDO HASTA: {fecha_formateada2}")
        else:
            print("Fecha no disponible")
            
        # Obtener la fecha y hora actual
        fecha_hora_actual = datetime.now()

        # Formatear la fecha y hora como desees
        fecha_formateada3= fecha_hora_actual.strftime("%d-%m-%Y")
        
        tasa_html = f"<p style='margin: 0; padding: 0;'>TASA: {self.invoice_data.get('Tasa', ''):.2f}</p>" if self.invoice_data.get('Tasa', '') else ""
        '''valido_html = f"<p style='margin: 0; padding: 0;'>VÁLIDO HASTA: {fecha_formateada, ''}</p>" if {fecha_formateada} != '' else ""'''

        print("Fecha y hora actual:", fecha_formateada3)
        
        #valores formateados con la taza
        tasa1= self.invoice_data.get('Tasa')

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

    def generate_header_html(self, current_page=1, total_pages=1):
        """
        Generate HTML for the invoice header, including page numbers
        
        Args:
            current_page (int): Current page number (starting from 1)
            total_pages (int): Total number of pages
        
        Returns:
            str: HTML for the header section
        """
        config_path = "config/config_print.json"
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config = json.load(file)
                font_sizes = config.get("font_sizes", {})
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error: No se pudo cargar la configuración de los tamaños de fuente. Usando valores predeterminados.")
            font_sizes = {}

    # Default font sizes
        empresa_font = font_sizes.get("empresa", "7pt")
        cliente_font = font_sizes.get("cliente", "5pt")

        fecha = self.invoice_data.get('fVencimientoNCF', '')

        if fecha and fecha != ' ':
            if isinstance(fecha, datetime):
                # Si ya es un objeto datetime, formatea directamente
                fecha_formateada = fecha.strftime('%d-%m-%Y')
            elif isinstance(fecha, str) and fecha.strip():  # Verifica que no sea solo espacios en blanco
                try:
                    # Intenta convertir la cadena en un objeto datetime
                    fecha = datetime.strptime(fecha.strip(), '%Y-%m-%d')
                    fecha_formateada = fecha.strftime('%d/%m/%Y')
                except ValueError:
                    fecha_formateada = ''  # Si el formato es incorrecto, asigna cadena vacía
            else:
                fecha_formateada = ''
        else:
            fecha_formateada = ''

        valido_html = (
            f"<p style='margin: 0; padding: 0;'>VÁLIDO HASTA: {fecha_formateada}</p>"
            if fecha_formateada.strip() else ""
        )

        
        tasa1 = self.invoice_data.get('Tasa', '')
        
        tasa_html = (
            f"<p style='margin: 0; padding: 0;'>TASA: {tasa1:.2f}</p>"
            if tasa1 not in [0, 1, '0', '1', '', None]
            else ""
        )
        
        ncf_afectado = self.invoice_data.get('Ncf_Modificado', '')
        
        ncf_html = (
            f"<p style='margin: 0; padding: 0;'>NCF AFECTADO: {ncf_afectado}</p>"
            if ncf_afectado.strip() else ""
        )
        
        # Add page number information
        page_info = f"<p style='margin: 0; padding: 0;'><b>PÁGINA: {current_page} de {total_pages}</b></p>"
        
        return f"""
            <table width="100%" style="margin-bottom: 3px; padding: 0;">
                <tr>
                    <td style="text-align: left; vertical-align: top; padding: 0;">

                        <p style="margin: 0; padding: 0; font-size: {empresa_font};"><b>{self.company_data.get('nombre_empresa', '')}</b></p>

                        <p style="margin: 0; padding: 0;">
                            {self.company_data.get('direccion', '')}<br />
                            RNC: {self.company_data.get('rnc', '')} | Tel.: {self.company_data.get('telefono', '')}<br>&nbsp;
                        </p>
                        <p style="margin: 0; padding: 0;">

                            <b style="font-size: {cliente_font};">CLIENTE</b>: <span style="font-size: {cliente_font};">{self.invoice_data.get('cliente', '')} - {self.invoice_data.get('nombre_cliente', '')}</span><br />


                            <b>RNC</b>: {self.invoice_data.get('cedula', '')}<br />
                            <b>DIRECCION</b>: {self.invoice_data.get('direccion_cliente', '')}<br />
                            <b>TELEFONO</b>: {self.invoice_data.get('telefono_cliente', '')}<br />
                            <b>CORREO</b>:
                        </p>
                    </td>
                    <td style="text-align: right; vertical-align: top; padding: 0;">
                        <div style="text-align: left; display: inline-block;">
                            <p style="margin: 0; padding: 0;">&nbsp;</p>
                            <p style="margin: 0; padding: 0;"><b>{self.invoice_data.get("ncf_type", "")}</b></p>
                            <p style="margin: 0; padding: 0;"><b>e-NCF:</b> {self.invoice_data.get('ncf', '')}</p>
                            {ncf_html}
                            {valido_html}
                            <p style="margin: 0; padding: 0;">
                                <hr>
                            </p>
                            <p style="margin: 0; padding: 0;"><b>
                            #: {self.invoice_data.get('numero', '')}</b></p>
                            <p style="margin: 0; padding: 0;">FECHA FACT: {self.invoice_data.get('fecha', '').strftime('%d-%m-%Y')}</p>
                            <p style="margin: 0; padding: 0;">VENDEDOR: {self.invoice_data.get('vendedor', '')} - {self.invoice_data.get('nombre_vendedor', '')}</p>
                            <p style="margin: 0; padding: 0;">ALMACEN: {self.invoice_data.get('almacen', '')}</p>
                            <p style="margin: 0; padding: 0;">CONDICION: VENTA A {self.invoice_data.get('TipoPagoL', '')} {self.invoice_data.get('TerminoPago', '')}</p>
                            <p style="margin: 0; padding: 0;">Pedido NO.: {self.invoice_data.get('Pedido', '')}</p>
                            {tasa_html}
                            {page_info}
                            
                        </div>
                    </td>
                </tr>
            </table>
            <p style="margin: 0; padding: 0; text-align: center;"><b>EXPRESADO EN {self.invoice_data.get('moneda_type2', '')}</b></p>
        """

    def generate_detail_html_page(self, products_html,pagos_html, total_descuento, is_last_page):
        def load_printer_config():
            """Carga la configuración de la impresora desde un archivo JSON."""
            config_path = "config/config_print.json"
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    config = json.load(file)
                    return {
                        "printer_name": config.get("printer_name", None),
                        "copies": config.get("copies", 1),  # Default to 1 copy if not specified
                        "copy_labels": config.get("copy_labels", ['ORIGINAL - CLIENTE', 'COPIA - CAJA', 'COPIA - CONTABILIDAD', 'COPIA - ARCHIVO']),
                        "concodigo": config.get("concodigo", 0),  # Add default value here
                        "conunidad": config.get("conunidad", 0)
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                print("Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada.")
                return {"printer_name": None, "copies": 0, "concodigo": 0, "conunidad": 0}
                
        tasa1= self.invoice_data.get('Tasa')
        MONTOGRAVADO = self.invoice_data.get('Monto_gravado', '')
        MONTOEXENTO =self.invoice_data.get('Monto_exento', '')
        

        
        monto_total = self.invoice_data.get('Monto_total', 0.00)
        itbis_total = self.invoice_data.get('TotalITBIS', 0.00)
        
        subtotal =  (MONTOGRAVADO or 0) #+ total_descuento 
        
        subtotal_total_formateado = subtotal / tasa1
        monto_total_formateado = monto_total / tasa1
        itbis_total_formateado = itbis_total / tasa1
        
        
        
        
        
        # Call the local function without self
        config = load_printer_config()
        concodigo = config.get("concodigo", 0)
        conunidad = config.get("conunidad", 0)
        
        
        # Determine if code column should be shown
        tipo_pago = self.invoice_data.get('tipopago', 0)  # Obtener el tipo de pago, por defecto 0
        pagos_html1 = pagos_html if tipo_pago == 1 else ''
        
        """Generate detail HTML for a single page."""
        if concodigo == 1 and conunidad == 1:
            table_html = f"""
                <table width="100%" style="border-collapse: collapse; margin-top: 0px;">
                    <tr>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CANT.</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CÓDIGO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">DESCRIPCION</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">UNIDAD</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">PRECIO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">DESC.</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">ITBIS</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">VALOR</th>
                    </tr>
                    {products_html}
                </table>
            """
        elif concodigo == 0 and conunidad == 0:
            table_html = f"""
                <table width="100%" style="border-collapse: collapse; margin-top: 0px;">
                    <tr>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CANTIDAD</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">DESCRIPCION</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">PRECIO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">DESC.</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">ITBIS</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">VALOR</th>
                    </tr>
                    {products_html}
                </table>
            """
        elif concodigo == 1 and conunidad == 0:
            table_html = f"""
                <table width="100%" style="border-collapse: collapse; margin-top: 0px;">
                    <tr>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CANTIDAD</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CÓDIGO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">DESCRIPCION</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">PRECIO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">DESC.</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">ITBIS</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">VALOR</th>
                    </tr>
                    {products_html}
                </table>
            """
        elif concodigo == 0 and conunidad == 1:
            table_html = f"""
                <table width="100%" style="border-collapse: collapse; margin-top: 0px;">
                    <tr>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">CANTIDAD</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">DESCRIPCION</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: left;">UNIDAD</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">PRECIO</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">DESC.</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">ITBIS</th>
                        <th style="border-top: 1px solid black; border-bottom: 1px solid black; padding: 4px; text-align: right;">VALOR</th>
                    </tr>
                    {products_html}
                </table>
            """
        # Rest of the method remains the same
        if is_last_page:
            table_html += f"""
                <p colspan="3" style="text-align: center; font-weight: bold; margin-top: 0px;">*****ULTIMA LINEA*****</p>
                <table width="58%" style="border-collapse: collapse; margin-top: 0px; font-size: 5pt; padding: 10px; margin-right: 2px; text-align: right;">
                    <tr>
                        <td colspan="2" style="border-top: 1px solid black;"></td>
                    </tr>
                    <tr>
                        <td style="text-align: right; font-weight: bold; padding: 4px 8px;">Sub-Total {self.invoice_data.get('moneda_type', '')}:</td>
                        <td style="text-align: right; font-weight: bold; padding: 4px 8px;">{subtotal_total_formateado:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="text-align: right; font-weight: bold; padding: 4px 8px;">- DESCUENTO {self.invoice_data.get('moneda_type', '')}:</td>
                        <td style="text-align: right; padding: 4px 8px;">{total_descuento:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="text-align: right; font-weight: bold; padding: 4px 8px;">+ ITBIS {self.invoice_data.get('moneda_type', '')}:</td>
                        <td style="text-align: right; padding: 4px 8px;">{itbis_total_formateado:,.2f}</td>
                    </tr>
                    <tr>
                        <td colspan="2" style="border-top: 1px solid black;"></td>
                    </tr>
                    <tr>
                        <td style="text-align: right; font-weight: bold; font-size: 6pt; padding: 2px 4px;">TOTAL {self.invoice_data.get('moneda_type', '')}:</td>
                        <td style="text-align: right; font-weight: bold; font-size: 6pt; padding: 2px 4px;">{monto_total_formateado:,.2f}</td>
                        {pagos_html1}
                    </tr>
                </table>
            """
        
        return table_html
    
    def generate_page_footer(self, page_total_quantity):
        """Generate a simple footer for non-last pages."""
        fecha_hora_actual = datetime.now().strftime("%d-%m-%Y")
        
        return f"""
            <hr>
            <div style="font-family: Arial, sans-serif; font-size: 7px; border-top: 1px solid black; border-bottom: 1px solid black; padding: 5px 0; text-align: left; margin-top: 20px;">
                <span style="margin-right: 15px;">Cant. Total Página: {page_total_quantity:.2f}</span>
                <span>IMPRESO: {fecha_hora_actual}</span>
            </div>
        """

    def generate_footer_html(self, note, note2, note3,note4, realizado, qr_image, codigoseguridad, fechafirma, total_quantity, copy_label=None):
        
        def load_printer_config():
            """Carga la configuración de la impresora desde un archivo JSON."""
            config_path = "config/config_print.json"
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    config = json.load(file)
                    return {
                        "printer_name": config.get("printer_name", None),
                        "copies": config.get("copies", 1),  # Default to 1 copy if not specified
                        "copy_labels": config.get("copy_labels", ['ORIGINAL - CLIENTE', 'COPIA - CAJA', 'COPIA - CONTABILIDAD', 'COPIA - ARCHIVO']),
                        "concodigo": config.get("concodigo", 0),  # Add default value here
                        "show_copy_labels": config.get("show_copy_labels", True)  # Add default value for show_copy_labels
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                print("Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada.")
                return {"printer_name": None, "copies": 0, "concodigo": 0, "show_copy_labels": True}
                
        fecha_hora_actual = datetime.now().strftime("%d-%m-%Y")
        
        # Call the local function without self
        config = load_printer_config()
        show_copy_labels = config.get("show_copy_labels", True)
        copy_label_html = f'<div style="text-align: center; font-size: 5pt; font-weight: bold; margin-top: 2px;">{copy_label}</div>' if copy_label and show_copy_labels else ''
        
        return f"""
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
                        <p style="margin: 0; font-size: 10px;">{realizado if self.invoice_data.get('cajero') not in [None, '' ] and self.invoice_data.get('tipopago') == 1 else '&nbsp;'}</p>
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
            <p style="margin-top: 10px; font-size: 5pt;">{note}</p>
            <p style="margin-top: 10px; font-size: 5pt;">{note2}</p>
            <p style="margin-top: 10px; font-size: 5pt;">{note3}</p>
            <p style="margin-top: 10px; font-size: 5pt;">{note4}</p>
            <div style="text-align: left; margin-top: 20px;">
                <img src="{qr_image}" width="80" height="80" alt="QR Code"><br>
                <span style="font-size: 5pt;">Código de Seguridad: {codigoseguridad}</span><br>
                <span style="font-size: 5pt;">Fecha de Firma Digital: {fechafirma}</span>
            </div>
            <hr>
            <div style="font-family: Arial, sans-serif; font-size: 7px; border-top: 1px solid black; border-bottom: 1px solid black; padding: 5px 0; text-align: left;">
                <span style="margin-right: 15px;">Cant. Total: {total_quantity:.2f}</span>
                <span>IMPRESO: {fecha_hora_actual}</span>
            </div>
            {copy_label_html}
        """
        
    def generate_qr_code(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=7,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        # Convert the QR image to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = QtCore.QByteArray(buffer.getvalue()).toBase64().data().decode('utf-8')
        return f"data:image/png;base64,{img_str}"



    def load_custom_layout(self):
        try:
            with open("custom_layout_template.html", "r", encoding='utf-8') as f:
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
                    "copies": config.get("copies", 1),  # Default to 1 copy if not specified
                    "copy_labels": config.get("copy_labels", ['ORIGINAL - CLIENTE', 'COPIA - CAJA', 'COPIA - CONTABILIDAD', 'COPIA - ARCHIVO'])
                }
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error: No se pudo cargar la configuración de la impresora. Usando la predeterminada.")
            return {"printer_name": None, "copies": 0}


    def get_default_printer(self):
        """Obtiene la impresora predeterminada del sistema."""
        try:
            return win32print.GetDefaultPrinter()
        except win32print.error:
            print("Advertencia: No hay una impresora predeterminada configurada en el sistema.")
            return None

    def get_printer_name(self):
        """Determina la impresora a usar: Configurada en JSON o la predeterminada."""
        config = self.load_printer_config()
        printer_name = config["printer_name"] or self.get_default_printer()
        return printer_name, config["copies"], config["copy_labels"]
    
  
#_____________________________Factura_____________________________________________           

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
        available_printers = [printer_info.printerName() for printer_info in QPrinterInfo.availablePrinters()]

        # Obtener nombre de impresora, número de copias y etiquetas de copia
        printer_name, copies, copy_labels = self.get_printer_name()

        # Validar disponibilidad de la impresora
        if printer_name not in available_printers:
            print(f"Advertencia: La impresora '{printer_name}' no está disponible. Usando la predeterminada.")
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
            copy_label = copy_labels[i] if i < len(copy_labels) else f'COPIA {i+1}'
            print(f"Imprimiendo {copy_label}...")
            
            # Generate PDF with the copy_label parameter
            self.generate_pdf(printer, copy_label=copy_label)

        # Cerrar la aplicación Qt si no hay ventanas abiertas
        if app is not None and not QApplication.topLevelWidgets():
            app.quit()
