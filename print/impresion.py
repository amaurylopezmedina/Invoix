import datetime
import io
import json  # Add this import for JSON handling
import os  # Add this import for directory operations
import platform
from datetime import datetime
from decimal import Decimal

import qrcode
import win32print
import win32ui
from PIL import Image, ImageWin
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Add reportlab imports for PDF generation
from reportlab.pdfgen import canvas
from win32.lib import win32con

# --------------------------------------------------------------------
# Función para cargar la configuración de la impresora
# --------------------------------------------------------------------


def load_printer_config():
    """Carga la configuración de la impresora desde un archivo JSON."""
    config_path = "config/config_print.json"
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
        return {
            "caja": config.get("caja", None),
            "printer_name": config.get("printer_name", None),
            "printer_name2": config.get("printer_name2", None),
            "imprimir_sin_caja": config.get("imprimir_sin_caja", False),
            "copies": config.get("copies", 1),
            "copies2": config.get("copies2", 1),
            "copy_labels": config.get(
                "copy_labels",
                [
                    "ORIGINAL - CLIENTE",
                    "COPIA - CAJA",
                    "COPIA - CONTABILIDAD",
                    "COPIA - ARCHIVO",
                ],
            ),
            "copy_labels2": config.get(
                "copy_labels2",
                ["COPIA - CAJA", "COPIA - CONTABILIDAD", "COPIA - ARCHIVO"],
            ),
            "concodigo": config.get("concodigo", 0),
            "conunidad": config.get("conunidad", 0),
            "show_copy_labels": config.get("show_copy_labels", True),
            "Impresion_grande": config.get("Impresion_grande", 0),
            "impresion_pdv": config.get("impresion_pdv", 0),
            "sinpdf": config.get("sinpdf", 0),  # Added this line
            "tipo_pago_grande": config.get("tipo_pago_grande", "CRCO"),
            "tipo_pago_pdv": config.get("tipo_pago_pdv", "CRCO"),  # Added this line
            "conpantalla": config.get("conpantalla", 0),  # Added this line
            "config_path1": config.get("config_path1", "config/config_print.json"),
            "tiponotap": config.get("tiponotap", 0),  # Added this line
            "numcolum": config.get("numcolum", 0),  # Added this line
            "tipodeespacio": config.get(
                "tipodeespacio", "sinespacio"
            ),  # Added this line
            "formatopv": config.get("formatopv", 1),  # Added this line
            "connotantesproducto": config.get(
                "connotantesproducto", 0
            ),  # Added this line
            "EquipoImpresion": config.get("EquipoImpresion", None),  # Added this line
            "montodevolver": config.get("montodevolver", 0),  # Added this line
            "controlportipo": config.get("controlportipo", 0),  # Added this line
            "numerodeimpresionesportipo": config.get("numerodeimpresionesportipo", {}),
            "numerodeimpresionesportipop": config.get(
                "numerodeimpresionesportipop", {}
            ),
            "estadosimpresion": config.get("estadosimpresion", []),
            "ruta_ri": config.get("ruta_ri", "C:\\xmlvalidar\\ri"),
            "check_interval": config.get("check_interval", 5),
        }
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default configuration if file not found or invalid
        return {
            "caja": None,
            "imprimir_sin_caja": False,
            "printer_name": None,
            "printer_name2": None,
            "copies": 1,
            "copies2": 1,
            "copy_labels": [
                "ORIGINAL - CLIENTE",
                "COPIA - CAJA",
                "COPIA - CONTABILIDAD",
                "COPIA - ARCHIVO",
            ],
            "copy_labels2": ["COPIA - CAJA", "COPIA - CONTABILIDAD", "COPIA - ARCHIVO"],
            "concodigo": 0,
            "show_copy_labels": True,
            "Impresion_grande": 0,
            "impresion_pdv": 0,
            "sinpdf": 0,  # Added this line
            "tipo_pago_grande": "CRCO",
            "tipo_pago_pdv": "CRCO",
            "conpantalla": 0,
            "tiponotap": 0,  # Added this line
            "tipodeespacio": "sinespacio",
            "formatopv": 1,  # Added this line
            "connotantesproducto": 0,  # Added this line
            "EquipoImpresion": None,  # Added this line
            "numcolum": 0,  # Added this line
            "montodevolver": 0,  # Added this line
            "controlportipo": 0,  # Added this line
            "numerodeimpresionesportipo": {},
            "numerodeimpresionesportipop": {},
            "estadosimpresion": [],
            "ruta_ri": "C:\\xmlvalidar\\ri",
            "check_interval": 5,
        }


# --------------------------------------------------------------------
# Clases de configuración y datos (tal como las tienes)
# --------------------------------------------------------------------


class Impresora:
    def __init__(self, invoice_data, printer_name2=None, config=None):
        # If no config provided, try to load from file
        if config is None:
            config = load_printer_config()

        # Use config if provided, otherwise use defaults
        if config:
            controlportipo = config.get("controlportipo", 0)
            tipoecf = invoice_data.get("tipoecf", "")
            tipopago = invoice_data.get("tipopago", "")
            self.printer_name2 = (
                config.get("printer_name2") or self.get_default_printer()
            )
            if controlportipo == 1:
                numerodeimpresionesportipo = config.get(
                    "numerodeimpresionesportipo", {}
                )
                numerodeimpresionesportipop = config.get(
                    "numerodeimpresionesportipop", {}
                )

                # Busca por tipoecf primero
                if str(tipoecf) in numerodeimpresionesportipo:
                    self.copias = numerodeimpresionesportipo.get(str(tipoecf))
                # Si no existe, busca por tipopago
                elif str(tipopago) in numerodeimpresionesportipop:
                    self.copias = numerodeimpresionesportipop.get(str(tipopago))
                # Si tampoco existe, usa el default
                else:
                    self.copias = config.get("copies2", 1)
            elif controlportipo == 0:
                self.copias = config.get("copies2", 1)
            self.espacios_encabezado = 2
            self.comentarios_factura = config.get("show_copy_labels", True)
            self.comentarios = config.get(
                "copy_labels2",
                [
                    "",
                    "Copia para el Cliente",
                    "Copia para Contabilidad",
                ],
            )
            self.caja = config.get("caja", "A")
            self.concodigo = config.get("concodigo", 0)
        else:
            self.printer_name2 = printer_name2 or self.get_default_printer()
            self.copias = 1
            self.espacios_encabezado = 2
            self.comentarios_factura = True
            self.comentarios = [
                "",
                "Copia para el Cliente",
                "Copia para Contabilidad",
            ]
            self.caja = "A"
            self.concodigo = 0

        self.columnas = config.get("numcolum", 0) or 47

    def get_default_printer(self):
        system = platform.system()
        if system == "Windows":
            import win32print

            return win32print.GetDefaultPrinter()
        elif system in ["Linux", "Darwin"]:
            import cups

            conn = cups.Connection()
            return conn.getDefault()
        else:
            raise OSError("Sistema no soportado para obtener impresoras")

    def get_printer_width(self):

        return 47

    def set_printer_name(self, printer_name2):
        self.printer_name2 = printer_name2


class GConfigPrinter:
    def __init__(self, impresora):
        self.impresora = impresora


# --------------------------------------------------------------------
# Función para ajustar y centrar texto
# --------------------------------------------------------------------


def print_centered(text, width):
    return text.center(width)


def print_left(text, width):
    return text.ljust(width)


def print_right(text, width):
    return text.rjust(width)


def adjust_text(text, width):
    lines = []
    while len(text) > width:
        lines.append(text[:width])
        text = text[width:]
    lines.append(text)
    return lines


def print_bold(text):
    # Uses ESC/P commands to make text bold
    return f"\x1b\x21\x08{text}\x1b\x21\x00"


def print_reverse(text):
    # Uses ESC/P commands for reverse printing (white text on black background)
    return f"\x1b\x34\x01{text}\x1b\x34\x00"


def print_bold_taller(text):
    # ESC ! 16 -> solo doble altura (bit 4 activado)
    return f"\x1b\x21\x10{text}\x1b\x21\x00"


# --------------------------------------------------------------------
# Función para generar el texto de la factura (tal como la tienes)
# --------------------------------------------------------------------


def factura_pequena(
    company_data, invoice_data, products, forms, descuento_recargo, gconfig, config=None
):
    impresora = gconfig.impresora
    output = io.StringIO()
    columnas = impresora.columnas
    raya = "-" * columnas

    if config is None:
        config = load_printer_config()

    notaantesp = config.get("connotantesproducto", 0)

    for copia in range(impresora.copias):
        output.write("\n" * impresora.espacios_encabezado)

        tipo_espacio = config.get("tipodeespacio", "sinespacio")
        formatopv = config.get("formatopv", 1)

        if tipo_espacio == "sinespacio":
            espacio_medio = ""
            espacio_arriba = ""
            espacio_abajo = ""
        elif tipo_espacio == "medio":
            espacio_medio = "\n" * 10
            espacio_arriba = ""
            espacio_abajo = ""
        elif tipo_espacio == "arriba":
            espacio_medio = ""
            espacio_arriba = "\n" * 10
            espacio_abajo = ""
        elif tipo_espacio == "abajo":
            espacio_medio = ""
            espacio_arriba = ""
            espacio_abajo = "\n" * 10

        # Cabecera
        # Try alternative ESC/P commands for bold text
        output.write(espacio_arriba)

        EI = invoice_data.get("EI", "")
        if str(EI).strip() == "3":
            output.write(
                print_bold(
                    print_centered("****REIMPRESION****", impresora.columnas) + "\n"
                )
            )
        output.write(
            print_bold(
                print_centered(
                    company_data["nombre_empresa"].strip(), impresora.columnas
                )
                + "\n"
            )
        )
        output.write(
            print_centered(company_data["direccion"].strip(), impresora.columnas) + "\n"
        )
        tel_line = f"Tel: {company_data['telefono'].strip()}"
        rnc_line = f"RNC: {company_data['rnc'].strip()}"
        # Calculate padding to align RNC with telephone
        tel_start = (impresora.columnas - len(tel_line)) // 2
        output.write(" " * tel_start + tel_line + "\n")
        output.write(" " * tel_start + rnc_line + "\n")
        output.write("\n")

        # Información de factura
        output.write(print_bold(f"{invoice_data['ncf_type'].strip()}\n"))
        output.write(f"e-NCF......: {invoice_data['ncf']}\n")
        # Only show expiration date if it's not empty
        if invoice_data.get("fVencimientoNCF") != "":
            output.write(f"VALIDO HASTA: {invoice_data['fVencimientoNCF']}\n")

        ncf_modficado = invoice_data.get("Ncf_Modificado")
        if ncf_modficado.strip() != "":
            output.write(f"e-NCF MODIFICADO: {invoice_data['Ncf_Modificado']}\n")

        output.write(raya + "\n")
        if invoice_data.get("tipoecf") == "34":
            output.write(
                print_bold(
                    print_centered(
                        f"DEVOLUCION DE {invoice_data['TipoPagoL']}", impresora.columnas
                    )
                )
                + "\n"
            )
        else:
            output.write(
                print_bold(
                    print_centered(
                        f"FACTURA DE {invoice_data['TipoPagoL']}", impresora.columnas
                    )
                )
                + "\n"
            )
        output.write(raya + "\n")

        output.write(print_bold(f"FACTURA..:") + f" {invoice_data['numero']}\n")
        output.write(
            print_bold(f"FECHA....:")
            + f" {invoice_data['fecha'].strftime('%d-%m-%Y')}\n"
        )
        output.write(
            print_bold(f"CONDICION:")
            + f" VENTA A{invoice_data['TipoPagoL']} {invoice_data['TerminoPago']}\n"
        )
        output.write(
            print_bold(f"CLIENTE..: {invoice_data['nombre_cliente'].strip()}\n")
        )
        output.write(print_bold(f"RNC......:") + f" {invoice_data['cedula']}\n")
        output.write(
            print_bold(f"VENDEDOR.:") + f" {invoice_data['nombre_vendedor']}\n"
        )

        tasar = invoice_data.get("Tasa")

        if tasar != 1 and tasar != 0:
            output.write(print_bold(f"TASA.....:") + f" {tasar:.2f}\n")

        # output.write(print_bold(f"CAJERO...:") + f" {invoice_data['usuario']}\n")
        tasad = invoice_data.get("Tasa")
        notaantesp2 = invoice_data.get("NotaAntesProducto").strip()
        if notaantesp == 1 and notaantesp2 != "":
            output.write(raya + "\n")
            output.write(
                print_bold_taller(f" {invoice_data['NotaAntesProducto'].strip()}\n")
            )
        elif notaantesp == 0:
            output.write("\n")

        if formatopv == 1:
            output.write(raya + "\n")

            # Configuración de anchos según el ancho total disponible
            if columnas <= 40:  # Impresora muy estrecha
                # Formato compacto
                output.write(print_bold("CODIGO\n"))
                output.write(print_bold("CANT  DESCRIPCION\n"))
                output.write(print_bold("PRECIO    ITBIS  VALOR\n"))
                output.write(raya + "\n")
                for producto in products:
                    codigo = producto.get("codigo", "")
                    cantidad = producto.get("cantidad", 0.0)
                    descripcion = producto.get("descripcion", "")
                    precio_unitario = producto.get("precio", 0.0) / tasad
                    itbis = producto.get("itbis", 0.0) / tasad
                    importe = producto.get("valor", 0.0) / tasad

                    # Línea 1: Código
                    output.write(f"{codigo[:columnas]}\n")

                    # Línea 2: Cantidad y Descripción
                    desc_max_len = columnas - 6
                    desc_str = descripcion[:desc_max_len].strip()
                    output.write(f"{cantidad:4.2f} {desc_str}\n")

                    # Línea 3: Precio, ITBIS, Valor
                    precio_str = f"{precio_unitario:,.2f}"
                    itbis_str = f"{itbis:,.2f}"
                    valor_str = f"{importe:,.2f}"

                    total_width = len(precio_str) + len(itbis_str) + len(valor_str) + 2
                    if total_width > columnas:
                        output.write(f"P:{precio_str} I:{itbis_str} V:{valor_str}\n")
                    else:
                        espacio = (columnas - total_width) // 2
                        output.write(
                            f"{precio_str}{' ' * espacio}{itbis_str}{' ' * espacio}{valor_str}\n"
                        )

                    output.write("\n")

            elif columnas <= 58:  # Impresora de ancho medio
                # Formato semi-completo con ITBIS
                output.write(print_bold("CODIGO\n"))
                output.write(print_bold("CANT  DESCRIPCION\n"))
                output.write(print_bold("PRECIO       ITBIS                   VALOR\n"))
                output.write(raya + "\n")
                for producto in products:
                    codigo = producto.get("codigo", "")
                    cantidad = producto.get("cantidad", 0.0)
                    descripcion = producto.get("descripcion", "")
                    precio_unitario = producto.get("precio", 0.0) / tasad
                    itbis = producto.get("itbis", 0.0) / tasad
                    importe = producto.get("valor", 0.0) / tasad

                    # Línea 1: Código
                    output.write(f"{codigo[:columnas]}\n")

                    # Línea 2: Cantidad y Descripción
                    cant_str = f"{cantidad:4.2f}".ljust(6)
                    desc_max_len = columnas - len(cant_str)
                    desc_str = descripcion[:desc_max_len].strip()
                    output.write(f"{cant_str}{desc_str}\n")

                    # Línea 3: Precio, ITBIS, Valor
                    precio_str = f"{precio_unitario:,.2f}"
                    itbis_str = f"{itbis:,.2f}"
                    valor_str = f"{importe:,.2f}"

                    field_width = (columnas - 2) // 3
                    output.write(
                        f"{precio_str.ljust(field_width)}{itbis_str.ljust(field_width)}{valor_str.rjust(16)}\n"
                    )
                    output.write("\n")

            else:  # Impresora ancha
                # Formato completo con ITBIS
                output.write(print_bold("CODIGO\n"))
                output.write(print_bold("CANT  DESCRIPCION\n"))
                output.write(print_bold("PRECIO       ITBIS                   VALOR\n"))
                output.write(raya + "\n")

                for producto in products:
                    codigo = producto.get("codigo", "")
                    cantidad = producto.get("cantidad", 0.0)
                    descripcion = producto.get("descripcion", "")
                    precio_unitario = producto.get("precio", 0.0) / tasad
                    itbis = producto.get("itbis", 0.0) / tasad
                    importe = producto.get("valor", 0.0) / tasad
                    # Línea 1: Código
                    output.write(f"{codigo}\n")

                    # Línea 2: Cantidad y Descripción
                    cantidad_str = f"{cantidad:.2f}".ljust(6)
                    output.write(f"{cantidad_str}{descripcion}\n")

                    # Línea 3: Precio, ITBIS, Valor
                    precio_str = f"{precio_unitario:,.2f}".ljust(12)
                    itbis_str = f"{itbis:,.2f}".ljust(10)
                    importe_str = f"{importe:,.2f}".rjust(12)
                    output.write(f"{precio_str}{itbis_str}{importe_str}\n")
                    output.write("\n")

            output.write(raya + "\n")
        elif formatopv == 2:
            # Detalle de productos con referencia adaptado al ancho de la impresora
            output.write(raya + "\n")

            # --- Cálculo de anchos para Encabezados y Detalles ---

            if columnas <= 40:  # Impresora muy estrecha
                ref_header_width = columnas
                desc_header_width = columnas - 7
                unidad_header_width = 7

                # Anchos base para datos y encabezados (ajusta estos para tus necesidades)
                cant_data_width_base = 6
                valor_data_width_base = 10  # Ancho para el dato de Valor

                # Ancho deseado para el texto del encabezado "Precio" y su alineación
                desired_precio_header_display_width = 10

                # Encabezados
                output.write(print_bold(f"{'Referencia'.ljust(ref_header_width)}\n"))
                output.write(
                    print_bold(
                        f"{'Descripcion'.ljust(desc_header_width)}{'Unidad'.rjust(unidad_header_width)}\n"
                    )
                )

                occupied_by_cant_valor_headers = (
                    cant_data_width_base + valor_data_width_base
                )
                remaining_space_for_precio_header = (
                    columnas - occupied_by_cant_valor_headers
                )

                padding_around_precio_header = max(
                    0,
                    remaining_space_for_precio_header
                    - desired_precio_header_display_width,
                )
                padding_left_of_precio_header = padding_around_precio_header // 2
                padding_right_of_precio_header = (
                    padding_around_precio_header - padding_left_of_precio_header
                )

                output.write(
                    print_bold(
                        f"{'Cantidad'.ljust(cant_data_width_base)}"
                        f"{' ' * padding_left_of_precio_header}"
                        f"{'Precio'.ljust(desired_precio_header_display_width)}"
                        f"{' ' * padding_right_of_precio_header}"
                        f"{'Valor'.rjust(valor_data_width_base)}\n"
                    )
                )
                output.write(raya + "\n")

                for producto in products:
                    cantidad = producto.get("cantidad", 0.0)
                    codigo = producto.get("codigo", "")
                    unidad = producto.get("unidad", "")
                    descripcion = producto.get("descripcion", "")
                    precio_unitario = producto.get("precio", 0.0) / tasad
                    importe = producto.get("valor", 0.0) / tasad

                    # Línea 1: Referencia
                    output.write(f"{codigo.ljust(columnas)[:columnas]}\n")

                    # Línea 2: Descripción y Unidad
                    unidad_str = unidad.strip()
                    desc_str = descripcion.strip()

                    space_for_desc = columnas - len(unidad_str) - 2
                    desc_printed = desc_str[:space_for_desc].ljust(space_for_desc)

                    output.write(
                        f"{desc_printed}{unidad_str.rjust(columnas - len(desc_printed))}\n"
                    )

                    # Línea 3: Cantidad, Precio y Valor (AJUSTE CLAVE AQUÍ)
                    cantidad_str = f"{cantidad:.2f}"
                    precio_str = f"{precio_unitario:,.2f}"
                    importe_str = f"{importe:,.2f}"

                    # Ancho fijo para la sección de cantidad
                    cant_section_width = cant_data_width_base  # Usamos el ancho base para la columna de cantidad
                    cant_padded = cantidad_str.ljust(cant_section_width)

                    # Calcular el espacio restante en la línea después de la cantidad y el valor
                    remaining_line_after_cant_valor = (
                        columnas - len(cant_padded) - len(importe_str)
                    )

                    # Ancho deseado para el campo de Precio (ajusta este valor si necesitas más/menos espacio para el número)
                    desired_precio_data_display_width = max(
                        len(precio_str), 8
                    )  # Mínimo 8 o el largo real

                    # Espacio libre alrededor del precio
                    padding_around_precio_data = max(
                        0,
                        remaining_line_after_cant_valor
                        - desired_precio_data_display_width,
                    )
                    padding_left_of_precio_data = padding_around_precio_data // 2
                    padding_right_of_precio_data = (
                        padding_around_precio_data - padding_left_of_precio_data
                    )

                    output.write(
                        f"{cant_padded}"
                        f"{' ' * padding_left_of_precio_data}"  # Espacio antes de Precio
                        f"{precio_str.ljust(desired_precio_data_display_width)}"  # Precio con su ancho deseado
                        f"{' ' * padding_right_of_precio_data}"  # Espacio después de Precio
                        f"{importe_str}\n"  # Valor al final (se alineará a la derecha por el padding previo)
                    )
                    output.write("\n")  # Línea en blanco entre productos

            elif columnas <= 58:  # Impresora de ancho medio
                ref_header_width = columnas

                desc_header_width = int(columnas * 0.7)
                unidad_header_width = columnas - desc_header_width

                cant_data_width_base = 10
                valor_data_width_base = 12

                desired_precio_header_display_width = 10

                # Encabezados
                output.write(print_bold(f"{'Referencia'.ljust(ref_header_width)}\n"))
                output.write(
                    print_bold(
                        f"{'Descripcion'.ljust(desc_header_width)}{'Unidad'.rjust(unidad_header_width)}\n"
                    )
                )

                occupied_by_cant_valor_headers = (
                    cant_data_width_base + valor_data_width_base
                )
                remaining_space_for_precio_header = (
                    columnas - occupied_by_cant_valor_headers
                )

                padding_around_precio_header = max(
                    0,
                    remaining_space_for_precio_header
                    - desired_precio_header_display_width,
                )
                padding_left_of_precio_header = padding_around_precio_header // 2
                padding_right_of_precio_header = (
                    padding_around_precio_header - padding_left_of_precio_header
                )

                output.write(
                    print_bold(
                        f"{'Cantidad'.ljust(cant_data_width_base)}"
                        f"{' ' * padding_left_of_precio_header}"
                        f"{'Precio'.ljust(desired_precio_header_display_width)}"
                        f"{' ' * padding_right_of_precio_header}"
                        f"{'Valor'.rjust(valor_data_width_base)}\n"
                    )
                )
                output.write(raya + "\n")

                for producto in products:
                    cantidad = producto.get("cantidad", 0.0)
                    codigo = producto.get("codigo", "")
                    unidad = producto.get("unidad", "")
                    descripcion = producto.get("descripcion", "")
                    precio_unitario = producto.get("precio", 0.0) / tasad
                    importe = producto.get("valor", 0.0) / tasad

                    # Línea 1: Referencia
                    output.write(f"{codigo.ljust(columnas)[:columnas]}\n")

                    # Línea 2: Descripción y Unidad
                    unidad_str = unidad.strip()
                    desc_str = descripcion.strip()

                    space_for_desc = columnas - len(unidad_str) - 2
                    desc_printed = desc_str[:space_for_desc].ljust(space_for_desc)

                    output.write(
                        f"{desc_printed}{unidad_str.rjust(columnas - len(desc_printed))}\n"
                    )

                    # Línea 3: Cantidad, Precio y Valor (AJUSTE CLAVE AQUÍ)
                    cantidad_str = f"{cantidad:.2f}"
                    precio_str = f"{precio_unitario:,.2f}"
                    importe_str = f"{importe:,.2f}"

                    cant_section_width = cant_data_width_base
                    cant_padded = cantidad_str.ljust(cant_section_width)

                    remaining_line_after_cant_valor = (
                        columnas - len(cant_padded) - len(importe_str)
                    )

                    desired_precio_data_display_width = max(
                        len(precio_str), 12
                    )  # Mínimo 12 o el largo real

                    padding_around_precio_data = max(
                        0,
                        remaining_line_after_cant_valor
                        - desired_precio_data_display_width,
                    )
                    padding_left_of_precio_data = padding_around_precio_data // 2
                    padding_right_of_precio_data = (
                        padding_around_precio_data - padding_left_of_precio_data
                    )

                    output.write(
                        f"{cant_padded}"
                        f"{' ' * padding_left_of_precio_data}"
                        f"{precio_str.ljust(desired_precio_data_display_width)}"
                        f"{' ' * padding_right_of_precio_data}"
                        f"{importe_str}\n"
                    )
                    output.write("\n")  # Línea en blanco entre productos

            else:  # Impresora ancha (columnas > 58)
                ref_header_width = columnas

                unidad_width = 15
                desc_header_width = columnas - unidad_width

                cant_data_width_base = 16
                valor_data_width_base = 16

                desired_precio_header_display_width = 16

                # Encabezados
                output.write(print_bold(f"{'Referencia'.ljust(ref_header_width)}\n"))
                output.write(
                    print_bold(
                        f"{'Descripcion'.ljust(desc_header_width)}{'Unidad'.rjust(unidad_width)}\n"
                    )
                )

                occupied_by_cant_valor_headers = (
                    cant_data_width_base + valor_data_width_base
                )
                remaining_space_for_precio_header = (
                    columnas - occupied_by_cant_valor_headers
                )

                padding_around_precio_header = max(
                    0,
                    remaining_space_for_precio_header
                    - desired_precio_header_display_width,
                )
                padding_left_of_precio_header = padding_around_precio_header // 2
                padding_right_of_precio_header = (
                    padding_around_precio_header - padding_left_of_precio_header
                )

                output.write(
                    print_bold(
                        f"{'Cantidad'.ljust(cant_data_width_base)}"
                        f"{' ' * padding_left_of_precio_header}"
                        f"{'Precio'.ljust(desired_precio_header_display_width)}"
                        f"{' ' * padding_right_of_precio_header}"
                        f"{'Valor'.rjust(valor_data_width_base)}\n"
                    )
                )
                output.write(raya + "\n")

                for producto in products:
                    cantidad = producto.get("cantidad", 0.0)
                    codigo = producto.get("codigo", "")
                    unidad = producto.get("unidad", "")
                    descripcion = producto.get("descripcion", "")
                    precio_unitario = producto.get("precio", 0.0) / tasad
                    importe = producto.get("valor", 0.0) / tasad

                    # Línea 1: Referencia
                    output.write(f"{codigo.ljust(columnas)[:columnas]}\n")

                    # Línea 2: Descripción y Unidad
                    unidad_str = unidad.strip()
                    desc_str = descripcion.strip()

                    space_for_desc = columnas - len(unidad_str) - 2
                    desc_printed = desc_str[:space_for_desc].ljust(space_for_desc)

                    output.write(
                        f"{desc_printed}{unidad_str.rjust(columnas - len(desc_printed))}\n"
                    )

                    # Línea 3: Cantidad, Precio y Valor (AJUSTE CLAVE AQUÍ)
                    cantidad_str = f"{cantidad:.2f}"
                    precio_str = f"{precio_unitario:,.2f}"
                    importe_str = f"{importe:,.2f}"

                    cant_section_width = cant_data_width_base
                    cant_padded = cantidad_str.ljust(cant_section_width)

                    remaining_line_after_cant_valor = (
                        columnas - len(cant_padded) - len(importe_str)
                    )

                    desired_precio_data_display_width = max(
                        len(precio_str), 15
                    )  # Mínimo 15 o el largo real

                    padding_around_precio_data = max(
                        0,
                        remaining_line_after_cant_valor
                        - desired_precio_data_display_width,
                    )
                    padding_left_of_precio_data = padding_around_precio_data // 2
                    padding_right_of_precio_data = (
                        padding_around_precio_data - padding_left_of_precio_data
                    )

                    output.write(
                        f"{cant_padded}"
                        f"{' ' * padding_left_of_precio_data}"
                        f"{precio_str.ljust(desired_precio_data_display_width)}"
                        f"{' ' * padding_right_of_precio_data}"
                        f"{importe_str}\n"
                    )
                    output.write("\n")  # Línea en blanco entre productos

            output.write(raya + "\n")
        elif formatopv == 2:
            # Detalle de productos con referencia adaptado al ancho de la impresora
            output.write(raya + "\n")

            # --- Cálculo de anchos para Encabezados y Detalles ---

            if columnas <= 40:  # Impresora muy estrecha
                ref_header_width = columnas
                desc_header_width = columnas - 7
                unidad_header_width = 7

                # Anchos base para datos y encabezados (ajusta estos para tus necesidades)
                cant_data_width_base = 6
                valor_data_width_base = 10  # Ancho para el dato de Valor

                # Ancho deseado para el texto del encabezado "Precio" y su alineación
                desired_precio_header_display_width = 10

                # Encabezados
                output.write(print_bold(f"{'Referencia'.ljust(ref_header_width)}\n"))
                output.write(
                    print_bold(
                        f"{'Descripcion'.ljust(desc_header_width)}{'Unidad'.rjust(unidad_header_width)}\n"
                    )
                )

                occupied_by_cant_valor_headers = (
                    cant_data_width_base + valor_data_width_base
                )
                remaining_space_for_precio_header = (
                    columnas - occupied_by_cant_valor_headers
                )

                padding_around_precio_header = max(
                    0,
                    remaining_space_for_precio_header
                    - desired_precio_header_display_width,
                )
                padding_left_of_precio_header = padding_around_precio_header // 2
                padding_right_of_precio_header = (
                    padding_around_precio_header - padding_left_of_precio_header
                )

                output.write(
                    print_bold(
                        f"{'Cantidad'.ljust(cant_data_width_base)}"
                        f"{' ' * padding_left_of_precio_header}"
                        f"{'Precio'.ljust(desired_precio_header_display_width)}"
                        f"{' ' * padding_right_of_precio_header}"
                        f"{'Valor'.rjust(valor_data_width_base)}\n"
                    )
                )
                output.write(raya + "\n")

                for producto in products:
                    cantidad = producto.get("cantidad", 0.0)
                    codigo = producto.get("codigo", "")
                    unidad = producto.get("unidad", "")
                    descripcion = producto.get("descripcion", "")
                    precio_unitario = producto.get("precio", 0.0) / tasad
                    importe = producto.get("valor", 0.0) / tasad

                    # Línea 1: Referencia
                    output.write(f"{codigo.ljust(columnas)[:columnas]}\n")

                    # Línea 2: Descripción y Unidad
                    unidad_str = unidad.strip()
                    desc_str = descripcion.strip()

                    space_for_desc = columnas - len(unidad_str) - 2
                    desc_printed = desc_str[:space_for_desc].ljust(space_for_desc)

                    output.write(
                        f"{desc_printed}{unidad_str.rjust(columnas - len(desc_printed))}\n"
                    )

                    # Línea 3: Cantidad, Precio y Valor (AJUSTE CLAVE AQUÍ)
                    cantidad_str = f"{cantidad:.2f}"
                    precio_str = f"{precio_unitario:,.2f}"
                    importe_str = f"{importe:,.2f}"

                    # Ancho fijo para la sección de cantidad
                    cant_section_width = cant_data_width_base  # Usamos el ancho base para la columna de cantidad
                    cant_padded = cantidad_str.ljust(cant_section_width)

                    # Calcular el espacio restante en la línea después de la cantidad y el valor
                    remaining_line_after_cant_valor = (
                        columnas - len(cant_padded) - len(importe_str)
                    )

                    # Ancho deseado para el campo de Precio (ajusta este valor si necesitas más/menos espacio para el número)
                    desired_precio_data_display_width = max(
                        len(precio_str), 8
                    )  # Mínimo 8 o el largo real

                    # Espacio libre alrededor del precio
                    padding_around_precio_data = max(
                        0,
                        remaining_line_after_cant_valor
                        - desired_precio_data_display_width,
                    )
                    padding_left_of_precio_data = padding_around_precio_data // 2
                    padding_right_of_precio_data = (
                        padding_around_precio_data - padding_left_of_precio_data
                    )

                    output.write(
                        f"{cant_padded}"
                        f"{' ' * padding_left_of_precio_data}"  # Espacio antes de Precio
                        f"{precio_str.ljust(desired_precio_data_display_width)}"  # Precio con su ancho deseado
                        f"{' ' * padding_right_of_precio_data}"  # Espacio después de Precio
                        f"{importe_str}\n"  # Valor al final (se alineará a la derecha por el padding previo)
                    )
                    output.write("\n")  # Línea en blanco entre productos

            elif columnas <= 58:  # Impresora de ancho medio
                ref_header_width = columnas

                desc_header_width = int(columnas * 0.7)
                unidad_header_width = columnas - desc_header_width

                cant_data_width_base = 10
                valor_data_width_base = 12

                desired_precio_header_display_width = 10

                # Encabezados
                output.write(print_bold(f"{'Referencia'.ljust(ref_header_width)}\n"))
                output.write(
                    print_bold(
                        f"{'Descripcion'.ljust(desc_header_width)}{'Unidad'.rjust(unidad_header_width)}\n"
                    )
                )

                occupied_by_cant_valor_headers = (
                    cant_data_width_base + valor_data_width_base
                )
                remaining_space_for_precio_header = (
                    columnas - occupied_by_cant_valor_headers
                )

                padding_around_precio_header = max(
                    0,
                    remaining_space_for_precio_header
                    - desired_precio_header_display_width,
                )
                padding_left_of_precio_header = padding_around_precio_header // 2
                padding_right_of_precio_header = (
                    padding_around_precio_header - padding_left_of_precio_header
                )

                output.write(
                    print_bold(
                        f"{'Cantidad'.ljust(cant_data_width_base)}"
                        f"{' ' * padding_left_of_precio_header}"
                        f"{'Precio'.ljust(desired_precio_header_display_width)}"
                        f"{' ' * padding_right_of_precio_header}"
                        f"{'Valor'.rjust(valor_data_width_base)}\n"
                    )
                )
                output.write(raya + "\n")

                for producto in products:
                    cantidad = producto.get("cantidad", 0.0)
                    codigo = producto.get("codigo", "")
                    unidad = producto.get("unidad", "")
                    descripcion = producto.get("descripcion", "")
                    precio_unitario = producto.get("precio", 0.0) / tasad
                    importe = producto.get("valor", 0.0) / tasad

                    # Línea 1: Referencia
                    output.write(f"{codigo.ljust(columnas)[:columnas]}\n")

                    # Línea 2: Descripción y Unidad
                    unidad_str = unidad.strip()
                    desc_str = descripcion.strip()

                    space_for_desc = columnas - len(unidad_str) - 2
                    desc_printed = desc_str[:space_for_desc].ljust(space_for_desc)

                    output.write(
                        f"{desc_printed}{unidad_str.rjust(columnas - len(desc_printed))}\n"
                    )

                    # Línea 3: Cantidad, Precio y Valor (AJUSTE CLAVE AQUÍ)
                    cantidad_str = f"{cantidad:.2f}"
                    precio_str = f"{precio_unitario:,.2f}"
                    importe_str = f"{importe:,.2f}"

                    cant_section_width = cant_data_width_base
                    cant_padded = cantidad_str.ljust(cant_section_width)

                    remaining_line_after_cant_valor = (
                        columnas - len(cant_padded) - len(importe_str)
                    )

                    desired_precio_data_display_width = max(
                        len(precio_str), 12
                    )  # Mínimo 12 o el largo real

                    padding_around_precio_data = max(
                        0,
                        remaining_line_after_cant_valor
                        - desired_precio_data_display_width,
                    )
                    padding_left_of_precio_data = padding_around_precio_data // 2
                    padding_right_of_precio_data = (
                        padding_around_precio_data - padding_left_of_precio_data
                    )

                    output.write(
                        f"{cant_padded}"
                        f"{' ' * padding_left_of_precio_data}"
                        f"{precio_str.ljust(desired_precio_data_display_width)}"
                        f"{' ' * padding_right_of_precio_data}"
                        f"{importe_str}\n"
                    )
                    output.write("\n")  # Línea en blanco entre productos

            else:  # Impresora ancha (columnas > 58)
                ref_header_width = columnas

                unidad_width = 15
                desc_header_width = columnas - unidad_width

                cant_data_width_base = 16
                valor_data_width_base = 16

                desired_precio_header_display_width = 16

                # Encabezados
                output.write(print_bold(f"{'Referencia'.ljust(ref_header_width)}\n"))
                output.write(
                    print_bold(
                        f"{'Descripcion'.ljust(desc_header_width)}{'Unidad'.rjust(unidad_width)}\n"
                    )
                )

                occupied_by_cant_valor_headers = (
                    cant_data_width_base + valor_data_width_base
                )
                remaining_space_for_precio_header = (
                    columnas - occupied_by_cant_valor_headers
                )

                padding_around_precio_header = max(
                    0,
                    remaining_space_for_precio_header
                    - desired_precio_header_display_width,
                )
                padding_left_of_precio_header = padding_around_precio_header // 2
                padding_right_of_precio_header = (
                    padding_around_precio_header - padding_left_of_precio_header
                )

                output.write(
                    print_bold(
                        f"{'Cantidad'.ljust(cant_data_width_base)}"
                        f"{' ' * padding_left_of_precio_header}"
                        f"{'Precio'.ljust(desired_precio_header_display_width)}"
                        f"{' ' * padding_right_of_precio_header}"
                        f"{'Valor'.rjust(valor_data_width_base)}\n"
                    )
                )
                output.write(raya + "\n")

                for producto in products:
                    cantidad = producto.get("cantidad", 0.0)
                    codigo = producto.get("codigo", "")
                    unidad = producto.get("unidad", "")
                    descripcion = producto.get("descripcion", "")
                    precio_unitario = producto.get("precio", 0.0) / tasad
                    importe = producto.get("valor", 0.0) / tasad

                    # Línea 1: Referencia
                    output.write(f"{codigo.ljust(columnas)[:columnas]}\n")

                    # Línea 2: Descripción y Unidad
                    unidad_str = unidad.strip()
                    desc_str = descripcion.strip()

                    space_for_desc = columnas - len(unidad_str) - 2
                    desc_printed = desc_str[:space_for_desc].ljust(space_for_desc)

                    output.write(
                        f"{desc_printed}{unidad_str.rjust(columnas - len(desc_printed))}\n"
                    )

                    # Línea 3: Cantidad, Precio y Valor (AJUSTE CLAVE AQUÍ)
                    cantidad_str = f"{cantidad:.2f}"
                    precio_str = f"{precio_unitario:,.2f}"
                    importe_str = f"{importe:,.2f}"

                    cant_section_width = cant_data_width_base
                    cant_padded = cantidad_str.ljust(cant_section_width)

                    remaining_line_after_cant_valor = (
                        columnas - len(cant_padded) - len(importe_str)
                    )

                    desired_precio_data_display_width = max(
                        len(precio_str), 15
                    )  # Mínimo 15 o el largo real

                    padding_around_precio_data = max(
                        0,
                        remaining_line_after_cant_valor
                        - desired_precio_data_display_width,
                    )
                    padding_left_of_precio_data = padding_around_precio_data // 2
                    padding_right_of_precio_data = (
                        padding_around_precio_data - padding_left_of_precio_data
                    )

                    output.write(
                        f"{cant_padded}"
                        f"{' ' * padding_left_of_precio_data}"
                        f"{precio_str.ljust(desired_precio_data_display_width)}"
                        f"{' ' * padding_right_of_precio_data}"
                        f"{importe_str}\n"
                    )
                    output.write("\n")  # Línea en blanco entre productos

            output.write(raya + "\n")

        # Totales
        tasa1 = invoice_data.get("Tasa")
        monto_total = invoice_data.get("Monto_total", 0.00)
        itbis_total = invoice_data.get("TotalITBIS", 0.00)
        MONTOGRAVADO = invoice_data.get("Monto_gravado", "")
        MONTOEXENTO = invoice_data.get("Monto_exento", "")
        IndicadorMontoGravado = invoice_data.get("IndicadorMontoGravado", "")
        descuentoglobal = descuento_recargo.get("monto", 0.00)

        itbis_total = sum(p["itbis"] for p in products)
        total_descuento = sum(p["descuento"] for p in products)
        monto_total = invoice_data["Monto_total"]
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

        # Calculate the width needed for the largest amount
        max_amount = max(subtotal, itbis_total, monto_total)
        amount_width = len(f"{max_amount:,.2f}")

        subtotal_total_formateado = subtotal / tasa1
        monto_total_formateado = monto_total / tasa1
        itbis_total_formateado = itbis_total / tasa1
        total_descuento_formateado = total_descuento1 / tasa1

        # Format the totals with right alignment matching the last column
        subtotal_str = f"{subtotal_total_formateado:,.2f}".rjust(17)
        itbis_str = f"{itbis_total_formateado:,.2f}".rjust(17)
        total_descuento_str = f"{total_descuento_formateado:,.2f}".rjust(17)
        total_str = f"{monto_total_formateado:,.2f}".rjust(17)

        # Write the totals with consistent alignment
        # Instead of using print_right for the entire line, we'll construct the line manually
        # to ensure the values align with the product values column
        label_subtotal = print_bold(f"SUB-TOTAL {invoice_data['moneda_type']}:")
        label_itbis = print_bold(f"ITBIS {invoice_data['moneda_type']}:")
        label_descuento = print_bold(f"DESCUENTO {invoice_data['moneda_type']}:")
        label_total = print_bold(f"NETO A {invoice_data['moneda_type']}:")

        # Calculate padding to align values with the product values
        # Add extra padding to move totals more to the right
        extra_padding = 6  # Adjust this value to move further right
        padding = (
            impresora.columnas - len(label_subtotal) - len(subtotal_str) + extra_padding
        )
        output.write(f"{' ' * padding}{label_subtotal}{subtotal_str}\n")

        padding = impresora.columnas - len(label_itbis) - len(itbis_str) + extra_padding
        output.write(f"{' ' * padding}{label_itbis}{itbis_str}\n")

        padding = (
            impresora.columnas
            - len(label_descuento)
            - len(total_descuento_str)
            + extra_padding
        )
        output.write(f"{' ' * padding}{label_descuento}{total_descuento_str}\n")

        padding = impresora.columnas - len(label_total) - len(total_str) + extra_padding
        output.write(f"{' ' * padding}{label_total}{total_str}\n")
        monto_totalc = invoice_data.get("Monto_total", 0.00)
        monto_pagoc = invoice_data.get("Monto_pago", 0.00)
        # monto_devolver = monto_pagoc - monto_totalc
        tipopago = invoice_data.get("tipopago", "")
        if invoice_data.get("tipoecf") != "34" and tipopago == 1:
            output.write(raya + "\n")
            output.write(print_left("DESGLOSE DE PAGOS", impresora.columnas) + "\n")

            # Primero, imprime todas las formas de pago que NO sean "Devuelta"
            for forma in forms:
                FormaPagoL = forma.get("FormaPagoL", "")
                if FormaPagoL.strip().lower() != "devuelta":
                    MontoPago = forma.get("MontoPago", 0.0)
                    FormaPagoL_str = f"{FormaPagoL}".ljust(16)
                    MontoPago_str = f"{MontoPago:,.2f}".rjust(10)
                    output.write(f"{FormaPagoL_str}{MontoPago_str}\n")

            # Luego, imprime el total pagado
            output.write(f"{'TOTAL PAGADO:'.ljust(16)}{monto_totalc:>10,.2f}\n")

            # Finalmente, imprime las líneas de "Devuelta"
            for forma in forms:
                FormaPagoL = forma.get("FormaPagoL", "")
                if FormaPagoL.strip().lower() == "devuelta":
                    MontoPago = forma.get("MontoPago", 0.0)
                    FormaPagoL_str = f"{FormaPagoL}".ljust(16)
                    MontoPago_str = f"{MontoPago:,.2f}".rjust(10)
                    output.write(f"{FormaPagoL_str}{MontoPago_str}\n")

        # Display the total aligned with amount column
        # tnp = tiponotapermanente

        num_articulos = len(products)
        output.write(raya + "\n")
        output.write(
            print_centered(
                f"EL NUMERO DE ARTICULOS ES :{num_articulos}", impresora.columnas
            )
            + "\n"
        )
        output.write(raya + "\n")

        tipopago = invoice_data.get("tipopago", "")
        tiponotap = config.get("tiponotap", 0)

        if tipopago == 2:
            output.write("\n\n")
            output.write(print_centered("_________________", impresora.columnas) + "\n")
            output.write(print_centered("RECIBIDO POR", impresora.columnas) + "\n")

        if tiponotap == 1 and tipopago == 1:
            nota_text = invoice_data["nota"].strip().replace("|", "")
            nota = output.write(f"{nota_text}\n")
        elif tiponotap == 2 and tipopago == 2:
            nota_text = invoice_data["nota"].strip().replace("|", "")
            nota = output.write(f"{nota_text}\n")
        elif tiponotap == 3:
            nota_text = invoice_data["nota"].strip().replace("|", "")
            nota = output.write(f"{nota_text}\n")
        else:
            nota = ""

        # Comentarios
        if impresora.comentarios_factura and copia < len(impresora.comentarios):
            comentario_actual = impresora.comentarios[copia]
            output.write("\n")
            output.write(print_centered(comentario_actual, impresora.columnas) + "\n")
            output.write(espacio_medio)

        output.write(f"{(invoice_data['observacion'] or "").strip()}\n")
        output.write(f"{nota}\n")

        for producto in products:
            nota3 = producto.get("nota3", "")

            nota3_str = f"{nota3}".strip()
        output.write(f"{nota3_str}\n")
        output.write(espacio_medio)

        output.write("\n" + raya + "\n")
    return output.getvalue()


# --------------------------------------------------------------------
# Función para generar un código QR y guardarlo como imagen PNG
# --------------------------------------------------------------------


def generar_qr_png(data, filename="qr.png"):
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    return filename


# --------------------------------------------------------------------
# Función para imprimir la factura (texto) y, al final, el QR (imagen)
# usando la API GDI de Windows.
# --------------------------------------------------------------------


def imprimir_factura_con_qr(
    factura_text,
    qr_data,
    printer_name2=None,
    security_code="",
    fecha_firma="",
    print_date=None,
):
    if printer_name2 is None:
        printer_name2 = win32print.GetDefaultPrinter()

    if print_date is None:
        print_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    config = load_printer_config()
    tipo_espacio = config.get("tipodeespacio", "sinespacio")

    # Imprimir texto en modo RAW
    hPrinter = win32print.OpenPrinter(printer_name2)
    try:
        hJob = win32print.StartDocPrinter(hPrinter, 1, ("Factura", None, "RAW"))
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, factura_text.encode("utf-8"))
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
    finally:
        win32print.ClosePrinter(hPrinter)

    # Imprimir QR como imagen usando GDI
    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name2)
    hDC.StartDoc("QR Factura")
    hDC.StartPage()

    # Generar el QR y abrir la imagen
    qr_path = generar_qr_png(qr_data, "qr.png")
    img = Image.open(qr_path)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Escalar el QR para adaptarlo a la impresión
    qr_size = 300  # Tamaño fijo del QR en píxeles
    img = img.resize((qr_size, qr_size))
    dib = ImageWin.Dib(img)

    # Dibujar el QR en la página
    x_qr = 120  # Margen izquierdo
    y_qr = 100  # Posición vertical después del texto impreso
    dib.draw(hDC.GetHandleOutput(), (x_qr, y_qr, x_qr + qr_size, y_qr + qr_size))

    # Agregar el texto "Código de seguridad" en un tamaño más grande justo debajo del QR
    font = win32ui.CreateFont(
        {
            "name": "Courier New",
            "height": 25,  # Tamaño más grande
            "weight": win32con.FW_BOLD,
        }
    )
    hDC.SelectObject(font)
    y_qr += qr_size + 5  # Menos espacio entre QR y texto
    hDC.TextOut(x_qr, y_qr, f"Codigo de seguridad: {security_code}")
    y_qr += 30
    hDC.TextOut(25, y_qr, f"Fecha de firma: {fecha_firma}")  # Mostrar fecha de firma
    y_qr += 30
    hDC.TextOut(
        25, 70, f"Fecha de impresion: {print_date}"
    )  # Mostrar fecha de impresión
    hDC.EndPage()
    hDC.EndDoc()
    hDC.DeleteDC()


# --------------------------------------------------------------------
# Función opcional: impresión vía RAW (texto plano) (si solo quieres texto)
# --------------------------------------------------------------------


def print_to_printer(data, printer_name2=None):
    system = platform.system()
    if system == "Windows":
        import win32print

        printer_name2 = printer_name2 or win32print.GetDefaultPrinter()
        hPrinter = win32print.OpenPrinter(printer_name2)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Factura", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)
            win32print.WritePrinter(hPrinter, data.encode("utf-8"))
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
    elif system in ["Linux", "Darwin"]:
        import cups

        conn = cups.Connection()
        printer_name2 = printer_name2 or conn.getDefault()
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp.write(data.encode("utf-8"))
            tmp_path = tmp.name
        conn.printFile(printer_name2, tmp_path, "Factura", {})
    else:
        raise OSError("Sistema no soportado para impresión")


# --------------------------------------------------------------------
# Programa principal
# --------------------------------------------------------------------


class Impresion:
    def __init__(
        self,
        company_data,
        invoice_data,
        products,
        forms,
        descuento_recargo,
        config=None,
        pdf_directory=os.path.join(os.path.abspath(os.sep), "xmlvalidar", "ri"),
    ):
        self.company_data = company_data
        self.invoice_data = invoice_data
        self.products = products
        self.forms = forms
        self.descuento_recargo = descuento_recargo
        self.impresora = Impresora(invoice_data=invoice_data, config=config)
        self.gconfig = GConfigPrinter(self.impresora)
        self.pdf_directory = (
            pdf_directory  # Default PDF directory set to your specified path
        )

        # Ensure required fields exist in company_data
        if "nombre_empresa" not in self.company_data:
            self.company_data["nombre_empresa"] = "Empresa"
        if "direccion" not in self.company_data:
            self.company_data["direccion"] = ""
        if "rnc" not in self.company_data:
            self.company_data["rnc"] = ""
        if "telefono" not in self.company_data:
            self.company_data["telefono"] = ""

        # Ensure required fields exist in invoice_data
        default_fields = {
            "ncf": "",
            "ncf_type": "",
            "numero": "",
            "fecha": datetime.now(),
            "nombre_cliente": "",
            "cedula": "",
            "nombre_vendedor": "",
            "usuario": "",
            "almacen": "",
            "Monto_total": 0.0,
            "URLQR": f"https://dgii.gov.do/consultas/{self.company_data.get('rnc', '')}/{self.invoice_data.get('ncf', '')}",
        }

        for key, value in default_fields.items():
            if key not in self.invoice_data:
                self.invoice_data[key] = value

    def abrir_cajon(self):
        """
        Abre el cajón de dinero enviando un comando directo a la impresora.
        """
        try:
            # Nombre de la impresora de la instancia de Impresora
            printer_name = self.impresora.printer_name2

            # Comando para abrir el cajón (Comando ESC/POS estándar)
            comando_bytes = b"\x1b\x70\x00\x32\xfa"

            # Mostrar información de depuración
            hex_str = " ".join([f"{b:02X}" for b in comando_bytes])
            print(f"Abriendo cajón en impresora: {printer_name}")
            print(f"Comando utilizado: {hex_str}")

            # Enviar comando a la impresora
            handle = win32print.OpenPrinter(printer_name)
            try:
                trabajo = win32print.StartDocPrinter(
                    handle, 1, ("Abrir Cajón", None, "RAW")
                )
                try:
                    win32print.StartPagePrinter(handle)
                    win32print.WritePrinter(handle, comando_bytes)
                    win32print.EndPagePrinter(handle)
                finally:
                    win32print.EndDocPrinter(handle)
            finally:
                win32print.ClosePrinter(handle)

            print("Cajón abierto con éxito")
            return True
        except Exception as e:
            print(f"Error al abrir el cajón: {e}")
            return False

    # impresion con pdf
    def imprimir_factura(self, output_directory, file_name):
        # Ensure directory exists
        os.makedirs(output_directory, exist_ok=True)

        # If PDF directory is specified, ensure it exists
        if self.pdf_directory:
            os.makedirs(self.pdf_directory, exist_ok=True)

        # Save the original number of copies
        copias_originales = self.impresora.copias

        # Temporarily set copies to 1 to generate one copy at a time
        self.impresora.copias = 1

        # For each copy
        for copia in range(copias_originales):
            # Set the current copy label
            if copia < len(self.impresora.comentarios):
                comentario_actual = self.impresora.comentarios[copia]
                # Create a temporary list with just the current comment
                comentarios_originales = self.impresora.comentarios
                self.impresora.comentarios = [comentario_actual]

            # Generate text content for this copy
            factura_text = factura_pequena(
                self.company_data,
                self.invoice_data,
                self.products,
                self.forms,
                self.descuento_recargo,
                self.gconfig,
            )

            # Get QR data from invoice
            datos_qr = self.invoice_data.get("URLQR", "")
            security_code = self.invoice_data.get("codigoseguridad", "")
            print_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            fecha_firma = self.invoice_data.get("fechafirma", "")

            # Print this copy with its QR code
            imprimir_factura_con_qr(
                factura_text,
                datos_qr,
                self.impresora.printer_name2,
                security_code,
                fecha_firma,
                print_date,
            )

            # If this is the first copy, save it to the specified file
            if copia == 0:
                with open(
                    os.path.join(output_directory, file_name), "w", encoding="utf-8"
                ) as f:
                    f.write(factura_text)

                # Generate PDF for the first copy
                pdf_file_name = os.path.splitext(file_name)[0] + ".pdf"
                pdf_path = os.path.join(self.pdf_directory, pdf_file_name)
                generar_pdf_factura(
                    factura_text, datos_qr, pdf_path, security_code, print_date
                )

            # Restore original comments
            if copia < len(self.impresora.comentarios):
                self.impresora.comentarios = comentarios_originales

        # Restore original number of copies - FIXED INDENTATION HERE
        self.impresora.copias = copias_originales
        self.abrir_cajon()

        return True

    # impresion sin pdf
    def imprimir_facturaspdf(self, output_directory, file_name):
        # Ensure directory exists
        os.makedirs(output_directory, exist_ok=True)

        # Save the original number of copies
        copias_originales = self.impresora.copias

        # Temporarily set copies to 1 to generate one copy at a time
        self.impresora.copias = 1

        # For each copy
        for copia in range(copias_originales):
            # Set the current copy label
            if copia < len(self.impresora.comentarios):
                comentario_actual = self.impresora.comentarios[copia]
                # Create a temporary list with just the current comment
                comentarios_originales = self.impresora.comentarios
                self.impresora.comentarios = [comentario_actual]

            # Generate text content for this copy
            factura_text = factura_pequena(
                self.company_data,
                self.invoice_data,
                self.products,
                self.forms,
                self.gconfig,
            )

            # Get QR data from invoice
            datos_qr = self.invoice_data.get("URLQR", "")
            security_code = self.invoice_data.get("codigoseguridad", "")
            print_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            fecha_firma = self.invoice_data.get("fechafirma", "")

            imprimir_factura_con_qr(
                factura_text,
                datos_qr,
                self.impresora.printer_name2,
                security_code,
                fecha_firma,
                print_date,
            )

            # If this is the first copy, save it to the specified file
            if copia == 0:
                with open(
                    os.path.join(output_directory, file_name), "w", encoding="utf-8"
                ) as f:
                    f.write(factura_text)

            # Restore original comments
            if copia < len(self.impresora.comentarios):
                self.impresora.comentarios = comentarios_originales

        # Restore original number of copies
        self.impresora.copias = copias_originales

        return True

    # nota de credito
    def imprimir_nota_credito(self, output_directory, file_name):
        # Ensure directory exists
        os.makedirs(output_directory, exist_ok=True)

        # If PDF directory is specified, ensure it exists
        if self.pdf_directory:
            os.makedirs(self.pdf_directory, exist_ok=True)

        # Save the original number of copies
        copias_originales = self.impresora.copias

        # Temporarily set copies to 1 to generate one copy at a time
        self.impresora.copias = 1

        # For each copy
        for copia in range(copias_originales):
            # Set the current copy label
            if copia < len(self.impresora.comentarios):
                comentario_actual = self.impresora.comentarios[copia]
                # Create a temporary list with just the current comment
                comentarios_originales = self.impresora.comentarios
                self.impresora.comentarios = [comentario_actual]

            # Generate text content for this copy
            factura_text = nota_credito_pequena(
                self.company_data, self.invoice_data, self.products, self.gconfig
            )

            # Get QR data from invoice
            datos_qr = self.invoice_data.get("URLQR", "")
            security_code = self.invoice_data.get("codigoseguridad", "")
            print_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            fecha_firma = self.invoice_data.get("fechafirma", "")

            # Print this copy with its QR code
            imprimir_factura_con_qr(
                factura_text,
                datos_qr,
                self.impresora.printer_name2,
                security_code,
                fecha_firma,
                print_date,
            )

            # If this is the first copy, save it to the specified file
            if copia == 0:
                with open(
                    os.path.join(output_directory, file_name), "w", encoding="utf-8"
                ) as f:
                    f.write(factura_text)

                # Generate PDF for the first copy
                pdf_file_name = os.path.splitext(file_name)[0] + ".pdf"
                pdf_path = os.path.join(self.pdf_directory, pdf_file_name)
                generar_pdf_factura(
                    factura_text,
                    datos_qr,
                    pdf_path,
                    security_code,
                    print_date,
                    fecha_firma,
                )

            # Restore original comments
            if copia < len(self.impresora.comentarios):
                self.impresora.comentarios = comentarios_originales

        # Restore original number of copies
        self.impresora.copias = copias_originales

        return True

    # nota de credito sin pdf
    def imprimir_nota_creditospdf(self, output_directory, file_name):
        # Ensure directory exists
        os.makedirs(output_directory, exist_ok=True)

        # Save the original number of copies
        copias_originales = self.impresora.copias

        # Temporarily set copies to 1 to generate one copy at a time
        self.impresora.copias = 1

        # For each copy
        for copia in range(copias_originales):
            # Set the current copy label
            if copia < len(self.impresora.comentarios):
                comentario_actual = self.impresora.comentarios[copia]
                # Create a temporary list with just the current comment
                comentarios_originales = self.impresora.comentarios
                self.impresora.comentarios = [comentario_actual]

            # Generate text content for this copy
            factura_text = nota_credito_pequena(
                self.company_data, self.invoice_data, self.products, self.gconfig
            )

            # Get QR data from invoice
            datos_qr = self.invoice_data.get("URLQR", "")
            security_code = self.invoice_data.get("codigoseguridad", "")
            print_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            fecha_firma = self.invoice_data.get("fechafirma", "")

            # Print this copy with its QR code
            imprimir_factura_con_qr(
                factura_text,
                datos_qr,
                self.impresora.printer_name2,
                security_code,
                fecha_firma,
                print_date,
            )

            # If this is the first copy, save it to the specified file
            if copia == 0:
                with open(
                    os.path.join(output_directory, file_name), "w", encoding="utf-8"
                ) as f:
                    f.write(factura_text)

            # Restore original comments
            if copia < len(self.impresora.comentarios):
                self.impresora.comentarios = comentarios_originales

        # Restore original number of copies
        self.impresora.copias = copias_originales

        return True

    # nota de debito
    def imprimir_nota_debito(self, output_directory, file_name):
        # Ensure directory exists
        os.makedirs(output_directory, exist_ok=True)

        # If PDF directory is specified, ensure it exists
        if self.pdf_directory:
            os.makedirs(self.pdf_directory, exist_ok=True)

        # Save the original number of copies
        copias_originales = self.impresora.copias

        # Temporarily set copies to 1 to generate one copy at a time
        self.impresora.copias = 1

        # For each copy
        for copia in range(copias_originales):
            # Set the current copy label
            if copia < len(self.impresora.comentarios):
                comentario_actual = self.impresora.comentarios[copia]
                # Create a temporary list with just the current comment
                comentarios_originales = self.impresora.comentarios
                self.impresora.comentarios = [comentario_actual]

            # Generate text content for this copy
            factura_text = nota_debito_pequena(
                self.company_data, self.invoice_data, self.products, self.gconfig
            )

            # Get QR data from invoice
            datos_qr = self.invoice_data.get("URLQR", "")
            security_code = self.invoice_data.get("codigoseguridad", "")
            print_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            fecha_firma = self.invoice_data.get("fechafirma", "")
            # Obtener fecha de firma

            # Print this copy with its QR code
            imprimir_factura_con_qr(
                factura_text,
                datos_qr,
                self.impresora.printer_name2,
                security_code,
                fecha_firma,
                print_date,
            )

            # If this is the first copy, save it to the specified file
            if copia == 0:
                with open(
                    os.path.join(output_directory, file_name), "w", encoding="utf-8"
                ) as f:
                    f.write(factura_text)

                # Generate PDF for the first copy
                pdf_file_name = os.path.splitext(file_name)[0] + ".pdf"
                pdf_path = os.path.join(self.pdf_directory, pdf_file_name)
                generar_pdf_factura(
                    factura_text,
                    datos_qr,
                    pdf_path,
                    security_code,
                    print_date,
                    fecha_firma,
                )

            # Restore original comments
            if copia < len(self.impresora.comentarios):
                self.impresora.comentarios = comentarios_originales

        # Restore original number of copies
        self.impresora.copias = copias_originales

        return True

    # nota de debito sin pdf
    def imprimir_nota_debitospf(self, output_directory, file_name):
        # Ensure directory exists
        os.makedirs(output_directory, exist_ok=True)

        # Save the original number of copies
        copias_originales = self.impresora.copias

        # Temporarily set copies to 1 to generate one copy at a time
        self.impresora.copias = 1

        # For each copy
        for copia in range(copias_originales):
            # Set the current copy label
            if copia < len(self.impresora.comentarios):
                comentario_actual = self.impresora.comentarios[copia]
                # Create a temporary list with just the current comment
                comentarios_originales = self.impresora.comentarios
                self.impresora.comentarios = [comentario_actual]

            # Generate text content for this copy
            factura_text = nota_debito_pequena(
                self.company_data, self.invoice_data, self.products, self.gconfig
            )

            # Get QR data from invoice
            datos_qr = self.invoice_data.get("URLQR", "")
            security_code = self.invoice_data.get("codigoseguridad", "")
            print_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            fecha_firma = self.invoice_data.get("fechafirma", "")

            # Print this copy with its QR code
            imprimir_factura_con_qr(
                factura_text,
                datos_qr,
                self.impresora.printer_name2,
                security_code,
                fecha_firma,
                print_date,
            )

            # If this is the first copy, save it to the specified file

            if copia == 0:
                with open(
                    os.path.join(output_directory, file_name), "w", encoding="utf-8"
                ) as f:
                    f.write(factura_text)

            # Restore original comments
            if copia < len(self.impresora.comentarios):
                self.impresora.comentarios = comentarios_originales

        # Restore original number of copies
        self.impresora.copias = copias_originales

        return True

    # caja chica
    def imprimir_caja_chica(self, output_directory, file_name):
        # Ensure directory exists
        os.makedirs(output_directory, exist_ok=True)

        # If PDF directory is specified, ensure it exists
        if self.pdf_directory:
            os.makedirs(self.pdf_directory, exist_ok=True)

        # Save the original number of copies
        copias_originales = self.impresora.copias

        # Temporarily set copies to 1 to generate one copy at a time
        self.impresora.copias = 1

        # For each copy
        for copia in range(copias_originales):
            # Set the current copy label
            if copia < len(self.impresora.comentarios):
                comentario_actual = self.impresora.comentarios[copia]
                # Create a temporary list with just the current comment
                comentarios_originales = self.impresora.comentarios
                self.impresora.comentarios = [comentario_actual]

            # Generate text content for this copy
            factura_text = caja_chica_pequena(
                self.company_data, self.invoice_data, self.products, self.gconfig
            )

            # Get QR data from invoice
            datos_qr = self.invoice_data.get("URLQR", "")
            security_code = self.invoice_data.get("codigoseguridad", "")
            print_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            fecha_firma = self.invoice_data.get("fechafirma", "")

            # Print this copy with its QR code
            imprimir_factura_con_qr(
                factura_text,
                datos_qr,
                self.impresora.printer_name2,
                security_code,
                fecha_firma,
                print_date,
            )

            # If this is the first copy, save it to the specified file
            if copia == 0:
                with open(
                    os.path.join(output_directory, file_name), "w", encoding="utf-8"
                ) as f:
                    f.write(factura_text)

                # Generate PDF for the first copy
                pdf_file_name = os.path.splitext(file_name)[0] + ".pdf"
                pdf_path = os.path.join(self.pdf_directory, pdf_file_name)
                generar_pdf_factura(
                    factura_text,
                    datos_qr,
                    pdf_path,
                    security_code,
                    print_date,
                    fecha_firma,
                )

            # Restore original comments
            if copia < len(self.impresora.comentarios):
                self.impresora.comentarios = comentarios_originales

        # Restore original number of copies
        self.impresora.copias = copias_originales

        return True

    # caja chica sin pdf
    def imprimir_caja_chicaspdf(self, output_directory, file_name):
        # Ensure directory exists
        os.makedirs(output_directory, exist_ok=True)

        # Save the original number of copies
        copias_originales = self.impresora.copias

        # Temporarily set copies to 1 to generate one copy at a time
        self.impresora.copias = 1

        # For each copy
        for copia in range(copias_originales):
            # Set the current copy label
            if copia < len(self.impresora.comentarios):
                comentario_actual = self.impresora.comentarios[copia]
                # Create a temporary list with just the current comment
                comentarios_originales = self.impresora.comentarios
                self.impresora.comentarios = [comentario_actual]

            # Generate text content for this copy
            factura_text = caja_chica_pequena(
                self.company_data, self.invoice_data, self.products, self.gconfig
            )

            # Get QR data from invoice
            datos_qr = self.invoice_data.get("URLQR", "")
            security_code = self.invoice_data.get("codigoseguridad", "")
            print_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

            # Print this copy with its QR code
            imprimir_factura_con_qr(
                factura_text,
                datos_qr,
                self.impresora.printer_name2,
                security_code,
                print_date,
            )

            # If this is the first copy, save it to the specified file
            if copia == 0:
                with open(
                    os.path.join(output_directory, file_name), "w", encoding="utf-8"
                ) as f:
                    f.write(factura_text)

            # Restore original comments
            if copia < len(self.impresora.comentarios):
                self.impresora.comentarios = comentarios_originales

        # Restore original number of copies
        self.impresora.copias = copias_originales

        return True


# --------------------------------------------------------------------
# Función para generar un PDF con el mismo formato que la impresión
# --------------------------------------------------------------------


def generar_pdf_factura(
    factura_text, qr_data, pdf_path, security_code="", print_date=None, fecha_firma=None
):
    """Genera un PDF con el mismo formato que la impresión térmica."""
    if print_date is None:
        print_date = datetime.now().strftime("%y-%m-%d %H:%M:%S")

    # Register a monospaced font for the receipt
    try:
        pdfmetrics.registerFont(TTFont("Courier", "C:/Windows/Fonts/cour.ttf"))
    except:
        # If Courier font not available, use a default
        pass

    # Create custom page size to match thermal receipt (width x height)
    receipt_width = 3.15 * inch

    # More aggressive cleaning of the text
    import re

    # First, convert any non-standard encoding to standard ASCII
    # This helps with characters that might be in a different encoding
    try:
        cleaned_text = factura_text.encode("ascii", "ignore").decode("ascii")
    except:
        cleaned_text = factura_text

    # Then remove any remaining non-ASCII characters
    cleaned_text = re.sub(r"[^\x00-\x7F]+", "", cleaned_text)

    # Explicitly remove problematic characters
    for char in ["□", "■", "◽", "◻", "!", ""]:
        cleaned_text = cleaned_text.replace(char, "")

    # Remove any character that's not alphanumeric, space, or basic punctuation
    cleaned_text = re.sub(r"[^\w\s.,;:$%&()\-+=\[\]{}\'\"]+", "", cleaned_text)

    # Calculate the height based on content
    lines = cleaned_text.split("\n")
    line_height = 10  # points
    content_height = (
        len(lines) * line_height + 2.5 * inch
    )  # Add space for QR and footer
    receipt_height = max(content_height, 6 * inch)  # Minimum height

    # Create the PDF with custom page size
    c = canvas.Canvas(pdf_path, pagesize=(receipt_width, receipt_height))
    c.setFont("Courier", 7)  # Smaller font to fit thermal paper width

    # Start position (top of page with margin)
    y = receipt_height - 0.3 * inch
    x = 0.1 * inch  # Small left margin

    # Calculate character width that fits on the page
    char_width = 5.5  # Average width of a character in points for Courier font
    max_chars = int((receipt_width - 0.2 * inch) / (char_width * 0.7))

    # Draw each line of text, wrapping if necessary
    for line in lines:
        # Additional cleaning for each line
        line = re.sub(r"[^\x00-\x7F]+", "", line)
        line = re.sub(r"[^\w\s.,;:$%&()\-+=\[\]{}\'\"]+", "", line)

        # Truncate or wrap lines that are too long
        if len(line) > max_chars:
            wrapped_lines = [
                line[i : i + max_chars] for i in range(0, len(line), max_chars)
            ]
            for wrapped_line in wrapped_lines:
                c.drawString(x, y, wrapped_line)
                y -= line_height
                if y < 1 * inch:
                    c.showPage()
                    c.setFont("Courier", 7)
                    y = receipt_height - 0.3 * inch
        else:
            c.drawString(x, y, line)
            y -= line_height

        # If we're near the bottom of the page, start a new page
        if y < 1 * inch:
            c.showPage()
            c.setFont("Courier", 7)
            y = receipt_height - 0.3 * inch

    # Generate QR code and add it to the PDF
    qr_path = generar_qr_png(qr_data, "qr_temp.png")

    # Position the QR code
    qr_width = 1.2 * inch
    qr_height = 1.2 * inch
    qr_x = (receipt_width - qr_width) / 2  # Center the QR code
    qr_y = y - qr_height - 0.2 * inch

    # Add the QR code to the PDF
    c.drawImage(qr_path, qr_x, qr_y, width=qr_width, height=qr_height)

    # Add security code text - also clean any unwanted characters
    c.setFont("Courier", 7)
    security_text = f"Codigo de seguridad: {security_code}"
    security_text = re.sub(r"[^\x00-\x7F]+", "", security_text)
    security_text = security_text.replace("□!□", "").replace("□", "").replace("!", "")
    if len(security_text) > max_chars:
        security_text = security_text[:max_chars]
    c.drawString(0.1 * inch, qr_y - 0.3 * inch, security_text)

    # Add fecha de firma
    if fecha_firma:
        c.drawString(0.1 * inch, qr_y - 0.4 * inch, f"Fecha de firma: {fecha_firma}")
    # Add print date
    current_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    date_text = f"Fecha de impresion: {current_date}"
    c.drawString(0.1 * inch, qr_y - 0.5 * inch, date_text)

    # Save the PDF
    c.save()

    # Clean up temporary QR file
    try:
        os.remove("qr_temp.png")
    except:
        pass

    return pdf_path


def nota_credito_pequena(company_data, invoice_data, products, gconfig):
    impresora = gconfig.impresora
    output = io.StringIO()
    raya = "-" * impresora.columnas

    for copia in range(impresora.copias):
        output.write("\n" * impresora.espacios_encabezado)

        # Cabecera
        output.write(
            print_centered(company_data["nombre_empresa"], impresora.columnas) + "\n"
        )
        output.write(
            print_centered(company_data["direccion"].strip(), impresora.columnas) + "\n"
        )
        tel_line = f"Tel: {company_data['telefono'].strip()}"
        rnc_line = f"RNC: {company_data['rnc'].strip()}"
        # Calculate padding to align RNC with telephone
        tel_start = (impresora.columnas - len(tel_line)) // 2
        output.write(" " * tel_start + tel_line + "\n")
        output.write(" " * tel_start + rnc_line + "\n")
        output.write("\n")

        # Información de nota de crédito
        output.write(f"{invoice_data['ncf_type'].strip()}\n")
        output.write(f"e-NCF......: {invoice_data['ncf']}\n")
        # Only show expiration date if it's not empty
        if invoice_data.get("fVencimientoNCF") != "":
            output.write(f"VALIDO HASTA: {invoice_data['fVencimientoNCF']}\n")
        output.write(raya + "\n")

        output.write(print_centered("NOTA DE CREDITO", impresora.columnas) + "\n")
        output.write(raya + "\n")

        output.write(f"DOCUMENTO: {invoice_data['numero']}\n")
        output.write(f"FECHA....: {invoice_data['fecha'].strftime('%d-%m-%Y')}\n")
        output.write(f"CLIENTE..: {invoice_data['nombre_cliente'].strip()}\n")
        output.write(f"RNC......: {invoice_data['cedula']}\n")
        output.write(f"VENDEDOR.: {invoice_data['nombre_vendedor']}\n")
        output.write(f"CAJERO...: {invoice_data['usuario']}\n")
        output.write(raya + "\n")

        # Detalle de productos
        # Define header format for invoice details
        # Define column widths for alignment
        col_widths = {
            "factura": 14,  # Increased width for factura
            "fecha": 12,  # Increased width for fecha
            "monto": 12,
            "balance": 12,
            "abono": 12,
            "desc": 12,
            "pendiente": 12,
        }

        # Create header format with fixed widths
        header1 = (
            "FACTURA".ljust(col_widths["factura"])
            + "FECHA".ljust(col_widths["fecha"])
            + "MONTO".ljust(col_widths["monto"])
            + "BALANCE".ljust(col_widths["balance"])
        )
        header2 = (
            "ABONO".ljust(col_widths["abono"])
            + "DESC.".ljust(col_widths["desc"])
            + "PENDIENTE".ljust(col_widths["pendiente"])
        )

        output.write(print_bold(header1 + "\n"))
        output.write(print_bold(header2 + "\n"))
        output.write(raya + "\n")

        # Extract basic invoice information
        invoice_details = {
            "factura": invoice_data.get("NumeroDocumentoNCFModificado", "").strip(),
            "fecha": invoice_data.get("FechaNCFModificado", datetime.now()).strftime(
                "%d-%m-%Y"
            ),
            "tasa": Decimal(
                str(invoice_data.get("Tasa", 1))
            ),  # Convert to string first for safety
        }
        invoice_details.update(
            {
                "monto": Decimal(str(invoice_data.get("MontoNCFModificado", 0)))
                / invoice_details["tasa"],
                "balance": Decimal(str(invoice_data.get("MontoNCFModificado", 0)))
                / invoice_details["tasa"],
                "abono": Decimal(str(invoice_data.get("AbonoNCFModificado", 0)))
                / invoice_details["tasa"],
                "descuento": Decimal(str(invoice_data.get("DescuentoNCFModificado", 0)))
                / invoice_details["tasa"],
                "pendiente": Decimal(str(invoice_data.get("PendienteNCFModificado", 0)))
                / invoice_details["tasa"],
            }
        )

        # Format detail line with fixed column widths and added spacing
        detail_line1 = (
            f"{invoice_details['factura']}".ljust(col_widths["factura"])
            + f"{invoice_details['fecha']}".ljust(col_widths["fecha"])
            + f"{invoice_details['monto']:.2f}".ljust(col_widths["monto"])
            + f"{invoice_details['balance']:.2f}".ljust(col_widths["balance"])
        )
        detail_line2 = (
            f"{invoice_details['abono']:.2f}".ljust(col_widths["abono"])
            + f"{invoice_details['descuento']:.2f}".ljust(col_widths["desc"])
            + f"{invoice_details['pendiente']:.2f}".ljust(col_widths["pendiente"])
        )

        output.write(detail_line1 + "\n")
        output.write(detail_line2 + "\n")
        # Finalizar sección de detalle
        output.write(raya + "\n")
        output.write(
            print_centered("*****ULTIMA LINEA*****", impresora.columnas) + "\n"
        )
        output.write(raya + "\n")
        # Totales
        subtotal = sum(float(p.get("valor", 0)) for p in products)
        itbis_total = sum(float(p.get("itbis", 0)) for p in products)
        monto_total = float(invoice_data.get("Monto_total", 0))

        output.write(
            print_right(f"SUB-TOTAL RD$: {subtotal:.2f}\n", impresora.columnas)
        )
        output.write(print_right(f"ITBIS RD$: {itbis_total:.2f}\n", impresora.columnas))
        output.write(
            print_right(f"NETO A PAGAR RD$: {monto_total:.2f}\n", impresora.columnas)
        )

        # Comentarios
        if impresora.comentarios_factura and copia < len(impresora.comentarios):
            comentario_actual = impresora.comentarios[copia]
            output.write("\n")
            output.write(print_centered(comentario_actual, impresora.columnas) + "\n")

        output.write("\n" + raya + "\n")
    return output.getvalue()


def nota_debito_pequena(company_data, invoice_data, products, gconfig):
    impresora = gconfig.impresora
    output = io.StringIO()
    raya = "-" * impresora.columnas

    for copia in range(impresora.copias):
        output.write("\n" * impresora.espacios_encabezado)

        # Cabecera
        output.write(
            print_centered(company_data["nombre_empresa"], impresora.columnas) + "\n"
        )
        output.write(
            print_centered(company_data["direccion"].strip(), impresora.columnas) + "\n"
        )
        tel_line = f"Tel: {company_data['telefono'].strip()}"
        rnc_line = f"RNC: {company_data['rnc'].strip()}"
        # Calculate padding to align RNC with telephone
        tel_start = (impresora.columnas - len(tel_line)) // 2
        output.write(" " * tel_start + tel_line + "\n")
        output.write(" " * tel_start + rnc_line + "\n")
        output.write("\n")

        # Información de nota de débito
        output.write(f"{invoice_data['ncf_type'].strip()}\n")
        output.write(f"e-NCF......: {invoice_data['ncf']}\n")
        output.write(f"VALIDO HASTA: {invoice_data['fVencimientoNCF']}\n")
        output.write(raya + "\n")

        output.write(print_centered("NOTA DE DÉBITO", impresora.columnas) + "\n")
        output.write(raya + "\n")

        output.write(f"DOCUMENTO: {invoice_data['numero']}\n")
        output.write(f"FECHA....: {invoice_data['fecha'].strftime('%d-%m-%Y')}\n")
        output.write(f"CLIENTE..: {invoice_data['nombre_cliente'].strip()}\n")
        output.write(f"RNC......: {invoice_data['cedula']}\n")
        output.write(f"VENDEDOR.: {invoice_data['nombre_vendedor']}\n")
        output.write(f"CAJERO...: {invoice_data['usuario']}\n")

        # Detalle de productos
        output.write(raya + "\n")
        output.write("Cantidad      Descripcion\n")
        output.write("Precio        ITBIS            Valor\n")
        output.write(raya + "\n")  # Línea separadora

        for producto in products:
            cantidad = producto.get("cantidad", 0.0)
            descripcion = producto.get("descripcion", "")
            precio_unitario = producto.get("precio", 0.0)
            itbis = producto.get("itbis", 0.0)
            importe = producto.get("valor", 0.0)

            # Primera línea: Cantidad, Descripción
            cantidad_str = f"{cantidad:.2f}".ljust(14)
            descripcion_str = descripcion.ljust(28)[:28]
            output.write(f"{cantidad_str}{descripcion_str}\n")

            # Segunda línea: Precio, ITBIS, Valor
            precio_str = f"{precio_unitario:,.2f}".ljust(14)
            itbis_str = f"{itbis:,.2f}".ljust(16)
            importe_str = f"{importe:,.2f}".ljust(10)
            output.write(f"{precio_str}{itbis_str}{importe_str}\n")

            output.write("\n")

        output.write(raya + "\n")

        # Totales
        subtotal = sum(p["valor"] for p in products)
        itbis_total = sum(p["itbis"] for p in products)
        monto_total = invoice_data["Monto_total"]

        output.write(
            print_right(f"SUB-TOTAL RD$: {subtotal:.2f}\n", impresora.columnas)
        )
        output.write(print_right(f"ITBIS RD$: {itbis_total:.2f}\n", impresora.columnas))
        output.write(
            print_right(f"NETO A PAGAR RD$: {monto_total:.2f}\n", impresora.columnas)
        )

        # Comentarios
        if impresora.comentarios_factura and copia < len(impresora.comentarios):
            comentario_actual = impresora.comentarios[copia]
            output.write("\n")
            output.write(print_centered(comentario_actual, impresora.columnas) + "\n")

        output.write("\n" + raya + "\n")
    return output.getvalue()


def caja_chica_pequena(company_data, invoice_data, products, gconfig):
    impresora = gconfig.impresora
    output = io.StringIO()
    raya = "-" * impresora.columnas

    for copia in range(impresora.copias):
        output.write("\n" * impresora.espacios_encabezado)

        # Cabecera
        output.write(
            print_centered(company_data["nombre_empresa"], impresora.columnas) + "\n"
        )
        output.write(
            print_centered(company_data["direccion"].strip(), impresora.columnas) + "\n"
        )
        tel_line = f"Tel: {company_data['telefono'].strip()}"
        rnc_line = f"RNC: {company_data['rnc'].strip()}"
        # Calculate padding to align RNC with telephone
        tel_start = (impresora.columnas - len(tel_line)) // 2
        output.write(" " * tel_start + tel_line + "\n")
        output.write(" " * tel_start + rnc_line + "\n")
        output.write("\n")

        # Información de caja chica
        output.write(raya + "\n")
        output.write(
            print_centered("COMPROBANTE DE CAJA CHICA", impresora.columnas) + "\n"
        )
        output.write(raya + "\n")

        output.write(f"DOCUMENTO: {invoice_data['numero']}\n")
        output.write(f"FECHA....: {invoice_data['fecha']}\n")
        output.write(f"BENEFICIARIO: {invoice_data['nombre_cliente'].strip()}\n")
        output.write(f"CONCEPTO: {invoice_data.get('concepto', 'Pago de gastos')}\n")
        output.write(f"AUTORIZADO POR: {invoice_data.get('autorizado_por', '')}\n")

        # Detalle de productos/gastos
        output.write(raya + "\n")
        output.write("Cantidad      Descripcion\n")
        output.write("Precio                      Valor\n")
        output.write(raya + "\n")  # Línea separadora

        for producto in products:
            cantidad = producto.get("cantidad", 0.0)
            descripcion = producto.get("descripcion", "")
            precio_unitario = producto.get("precio", 0.0)
            importe = producto.get("valor", 0.0)

            # Primera línea: Cantidad, Descripción
            cantidad_str = f"{cantidad:.2f}".ljust(14)
            descripcion_str = descripcion.ljust(28)[:28]
            output.write(f"{cantidad_str}{descripcion_str}\n")

            # Segunda línea: Precio, Valor
            precio_str = f"{precio_unitario:,.2f}".ljust(26)
            importe_str = f"{importe:,.2f}".ljust(10)
            output.write(f"{precio_str}{importe_str}\n")

            output.write("\n")

        output.write(raya + "\n")

        # Totales
        monto_total = invoice_data["Monto_total"]
        output.write(print_right(f"TOTAL RD$: {monto_total:.2f}\n", impresora.columnas))

        # Comentarios
        if impresora.comentarios_factura and copia < len(impresora.comentarios):
            comentario_actual = impresora.comentarios[copia]
            output.write("\n")
            output.write(print_centered(comentario_actual, impresora.columnas) + "\n")

        output.write("\n" + raya + "\n")

        # Firmas
        output.write("\n\n")
        output.write(
            print_centered(
                "_________________     _________________", impresora.columnas
            )
            + "\n"
        )
        output.write(
            print_centered(
                "    RECIBIDO             AUTORIZADO    ", impresora.columnas
            )
            + "\n"
        )

    return output.getvalue()
