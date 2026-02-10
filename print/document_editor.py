import base64
import os
import tempfile
from datetime import datetime
from decimal import Decimal
from io import BytesIO

import qrcode
import win32print
from PyQt5 import QtCore, QtGui, QtPrintSupport, QtWidgets
from PyQt5.QtCore import QRectF, QSizeF, Qt
from PyQt5.QtGui import QFont, QPainter, QTextDocument
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog
from PyQt5.QtWidgets import (QApplication, QComboBox, QFileDialog, QFormLayout,
                             QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QMessageBox, QPushButton, QSpinBox,
                             QTextEdit, QVBoxLayout, QWidget)


class DocumentEditor(QtWidgets.QMainWindow):
    def __init__(self, company_data, invoice_data, products):
        super().__init__()
        self.setWindowTitle("Editor de Formato de Documento")
        self.setGeometry(100, 100, 1200, 800)

        self.company_data = company_data
        self.invoice_data = invoice_data
        self.products = products

        # Editor principal de texto
        self.editor = QtWidgets.QTextEdit(self)
        self.setCentralWidget(self.editor)
        self.editor.setFont(QtGui.QFont("Arial", 12))
        self.editor.setAcceptRichText(True)

        # Inicializar valores predeterminados
        self.qr_image = self.generate_qr_image()

        # Cargar el contenido por defecto
        self.load_default_content()

        # Configurar la barra de herramientas
        self.create_toolbar()

    def create_toolbar(self):
        toolbar = self.addToolBar("Toolbar")

        # Botón Negrita
        bold_action = QtWidgets.QAction("Negrita", self)
        bold_action.triggered.connect(self.make_bold)
        toolbar.addAction(bold_action)

        # Botón Cursiva
        italic_action = QtWidgets.QAction("Cursiva", self)
        italic_action.triggered.connect(self.make_italic)
        toolbar.addAction(italic_action)

        # Botón Subrayado
        underline_action = QtWidgets.QAction("Subrayado", self)
        underline_action.triggered.connect(self.make_underline)
        toolbar.addAction(underline_action)

        # Combo box para tamaño de fuente
        self.font_size_box = QtWidgets.QComboBox(self)
        self.font_size_box.addItems([str(i) for i in range(8, 50, 2)])
        self.font_size_box.currentTextChanged.connect(self.change_font_size)
        toolbar.addWidget(self.font_size_box)

        # Selector de color
        color_action = QtWidgets.QAction("Cambiar Color", self)
        color_action.triggered.connect(self.change_color)
        toolbar.addAction(color_action)

        # Botón para alinear texto a la izquierda
        align_left_action = QtWidgets.QAction("Alinear Izquierda", self)
        align_left_action.triggered.connect(
            lambda: self.set_alignment(QtCore.Qt.AlignLeft)
        )
        toolbar.addAction(align_left_action)

        # Botón para centrar texto
        align_center_action = QtWidgets.QAction("Centrar", self)
        align_center_action.triggered.connect(
            lambda: self.set_alignment(QtCore.Qt.AlignCenter)
        )
        toolbar.addAction(align_center_action)

        # Botón para alinear texto a la derecha
        align_right_action = QtWidgets.QAction("Alinear Derecha", self)
        align_right_action.triggered.connect(
            lambda: self.set_alignment(QtCore.Qt.AlignRight)
        )
        toolbar.addAction(align_right_action)

        # Botón Deshacer
        undo_action = QtWidgets.QAction("Deshacer", self)
        undo_action.triggered.connect(self.editor.undo)
        toolbar.addAction(undo_action)

        # Botón Rehacer
        redo_action = QtWidgets.QAction("Rehacer", self)
        redo_action.triggered.connect(self.editor.redo)
        toolbar.addAction(redo_action)

        # Botón para copiar texto
        copy_action = QtWidgets.QAction("Copiar", self)
        copy_action.triggered.connect(self.editor.copy)
        toolbar.addAction(copy_action)

        # Botón para cortar texto
        cut_action = QtWidgets.QAction("Cortar", self)
        cut_action.triggered.connect(self.editor.cut)
        toolbar.addAction(cut_action)

        # Botón para pegar texto
        paste_action = QtWidgets.QAction("Pegar", self)
        paste_action.triggered.connect(self.editor.paste)
        toolbar.addAction(paste_action)

        # Agregar espaciador
        toolbar.addSeparator()

        # Botón para restablecer el formato
        clear_format_action = QtWidgets.QAction("Restablecer Formato", self)
        clear_format_action.triggered.connect(self.reseat_format)
        toolbar.addAction(clear_format_action)

        # Botón para cambiar al modo de vista previa

        # Botón Guardar
        save_action = QtWidgets.QAction("Guardar", self)
        save_action.triggered.connect(self.save_changes)
        toolbar.addAction(save_action)

    def generate_qr_image(self):
        urlqr = self.invoice_data.get("URLQR", "")
        if not urlqr:
            return ""

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=2,
            border=1,
        )
        qr.add_data(urlqr)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        buffer.close()
        return f"data:image/png;base64,{img_base64}"

    def load_default_content(self):
        """
        Carga el contenido inicial desde un archivo de plantilla.
        Si la plantilla contiene errores, muestra un mensaje y no intenta cargarla.
        """
        try:
            with open("print//template.html", "r", encoding="utf-8") as file:
                template_content = file.read()
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(
                self, "Error", "No se encontró el archivo de plantilla HTML."
            )
            return

        try:
            # Generar contenido dinámico
            products_html, subtotal, total_descuento, total_itbis = (
                self.generate_products_html()
            )
            total = subtotal - total_descuento + total_itbis

            # Reemplazar los marcadores
            content = template_content.format(
                company_name=self.company_data.get("nombre_empresa", ""),
                company_address=self.company_data.get("direccion", ""),
                company_rnc=self.company_data.get("rnc", ""),
                company_phone=self.company_data.get("telefono", ""),
                invoice_ncf=self.invoice_data.get("ncf", ""),
                invoice_ncf_type=self.invoice_data.get("ncf_type", ""),
                invoice_valid_until=self.invoice_data.get("fVencimientoNCF", ""),
                client_name=self.invoice_data.get("nombre_cliente", ""),
                client=self.invoice_data.get("cliente", ""),
                client_rnc=self.invoice_data.get("cedula", ""),
                client_phone=self.invoice_data.get("telefono_cliente", ""),
                client_address=self.invoice_data.get("direccion_cliente", ""),
                invoice_number=self.invoice_data.get("numero", ""),
                invoice_date=self.invoice_data.get("fecha", ""),
                seller_name=self.invoice_data.get("nombre_vendedor", ""),
                warehouse=self.invoice_data.get("almacen", ""),
                products_html=products_html,
                subtotal=subtotal,
                total_descuento=total_descuento,
                total_itbis=total_itbis,
                total=total,
                note=self.invoice_data.get("observacion", ""),
                realizado=self.invoice_data.get("usuario", ""),
                qr_image=self.qr_image,
                invoice_security_code=self.invoice_data.get("codigoseguridad", ""),
                invoice_signature_date=self.invoice_data.get("fechafirma", ""),
            )

            # Establecer contenido en el editor
            self.editor.setHtml(content)

        except KeyError as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                f"Clave faltante en la plantilla: {str(e)}. Verifique los marcadores.",
            )

    def generate_products_html(self):
        """
        Genera el contenido HTML para la lista de productos.
        """
        products_html = ""
        subtotal = 0
        total_descuento = 0
        total_itbis = 0

        for product in self.products:
            cantidad = float(product["cantidad"])
            precio = float(product["precio"])
            valor = cantidad * precio

            descuento = valor * (float(product.get("descuento", 0)) / 100)
            itbis = (valor - descuento) * (float(product.get("itbis", 0)) / 100)

            # Sumar valores numéricos para cálculos
            subtotal += valor
            total_descuento += descuento
            total_itbis += itbis

            # Formatear los valores como moneda para mostrar en el HTML
            cantidad_formateada = f"{cantidad:,.2f}"
            precio_formateado = f"{precio:,.2f}"
            descuento_formateado = f"{descuento:,.2f}"
            itbis_formateado = f"{itbis:,.2f}"
            valor_formateado = f"{valor:,.2f}"

            products_html += f"""
                <tr>
                    <td>{cantidad_formateada}</td>
                    <td style="word-wrap: break-word; white-space: normal;">{product['descripcion']}</td>
                    <td>{precio_formateado}</td>
                    <td>{descuento_formateado}</td>
                    <td>{itbis_formateado}</td>
                    <td>{valor_formateado}</td>
                </tr>
            """

        products_html += """
            <tr>
                ++
            </tr>
        """

        return products_html, subtotal, total_descuento, total_itbis



    def make_bold(self):
        fmt = QtGui.QTextCharFormat()
        fmt.setFontWeight(
            QtGui.QFont.Bold
            if self.editor.fontWeight() == QtGui.QFont.Normal
            else QtGui.QFont.Normal
        )
        self.merge_format_on_selection(fmt)

    def make_italic(self):
        fmt = QtGui.QTextCharFormat()
        fmt.setFontItalic(not self.editor.fontItalic())
        self.merge_format_on_selection(fmt)

    def make_underline(self):
        fmt = QtGui.QTextCharFormat()
        fmt.setFontUnderline(not self.editor.fontUnderline())
        self.merge_format_on_selection(fmt)

    def change_font_size(self, size):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            fmt = QtGui.QTextCharFormat()
            fmt.setFontPointSize(float(size))
            cursor.mergeCharFormat(fmt)
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Advertencia",
                "Seleccione texto para cambiar el tamaño de fuente.",
            )

    def set_alignment(self, alignment):
        cursor = self.editor.textCursor()
        block_format = QtGui.QTextBlockFormat()
        block_format.setAlignment(alignment)
        cursor.mergeBlockFormat(block_format)
        self.editor.setTextCursor(cursor)

    def merge_format_on_selection(self, fmt):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
            cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)

    def change_color(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            fmt = QtGui.QTextCharFormat()
            fmt.setForeground(QtGui.QBrush(color))
            self.merge_format_on_selection(fmt)

    def reseat_format(self):
        try:
            # Eliminar el archivo custom_layout_template.html
            if os.path.exists("custom_layout_template.html"):
                os.remove("custom_layout_template.html")

            # Recargar el contenido por defecto, lo que recargará la plantilla
            self.load_default_content()

            # Mostrar un mensaje de éxito
            QtWidgets.QMessageBox.information(
                self, "Éxito", "El archivo ha sido eliminado y la plantilla recargada."
            )

        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                f"Error al eliminar el archivo y recargar la plantilla: {str(e)}",
            )

    def save_changes(self):
        try:
            with open("custom_layout_template.html", "w", encoding="utf-8") as f:
                f.write(self.editor.toHtml())
            QtWidgets.QMessageBox.information(
                self, "Éxito", "El formato ha sido actualizado."
            )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Error", f"Error al guardar el formato: {str(e)}"
            )


class ReceiptEditor(QMainWindow):
    def __init__(self, company_data, invoice_data, products):
        super().__init__()
        self.company_data = company_data
        self.invoice_data = invoice_data
        self.products = products
        self.receipt_content = ""
        self.current_format = "Original Format"
        self.modified_content = ""

        # Path to template file
        self.template_path = "print//template.txt"
        self.qr_image = ""

        self.setWindowTitle("POS Receipt Editor")
        self.initUI()

    def initUI(self):
        main_widget = QWidget()
        self.layout = QVBoxLayout(main_widget)

        # Text Editor
        self.textEdit = QTextEdit()
        self.layout.addWidget(self.textEdit)

        # Paper Settings
        settings_layout = QGridLayout()
        settings_layout.addWidget(QLabel("Paper Width (mm)"), 0, 0)
        self.paperWidthInput = QLineEdit("135")
        settings_layout.addWidget(self.paperWidthInput, 0, 1)

        settings_layout.addWidget(QLabel("Paper Height (mm)"), 1, 0)
        self.paperHeightInput = QLineEdit("200")
        settings_layout.addWidget(self.paperHeightInput, 1, 1)

        settings_layout.addWidget(QLabel("Margins (mm)"), 2, 0)
        self.marginInput = QLineEdit("5")
        settings_layout.addWidget(self.marginInput, 2, 1)

        self.layout.addLayout(settings_layout)

        # Printer Selection
        self.layout.addWidget(QLabel("Select Printer"))
        self.printerSelect = QComboBox()
        self.printerSelect.addItems(self.get_available_printers())
        self.layout.addWidget(self.printerSelect)

        # Text style settings
        self.textSettingsLayout = QFormLayout()

        # Alignment selection
        self.alignmentSelect = QComboBox()
        self.alignmentSelect.addItems(["Left", "Center", "Right"])
        self.alignmentSelect.currentTextChanged.connect(self.update_alignment)
        self.textSettingsLayout.addRow("Text Alignment:", self.alignmentSelect)

        # Font selection
        self.fontSelect = QComboBox()
        self.fontSelect.addItems(
            [
                "Arial",
                "Times New Roman",
                "Courier New",
                "Helvetica",
                "Verdana",
                "Tahoma",
                "Georgia",
                "Calibri",
                "Sans Serif",
            ]
        )
        self.fontSelect.currentTextChanged.connect(self.update_font)
        self.textSettingsLayout.addRow("Font:", self.fontSelect)

        # Font size selection
        self.fontSizeSelect = QSpinBox()
        self.fontSizeSelect.setValue(12)
        self.fontSizeSelect.setRange(8, 40)
        self.fontSizeSelect.valueChanged.connect(self.update_font_size)
        self.textSettingsLayout.addRow("Font Size:", self.fontSizeSelect)

        # Line spacing selection
        self.lineSpacingSelect = QSpinBox()
        self.lineSpacingSelect.setValue(1)
        self.lineSpacingSelect.setRange(1, 3)
        self.lineSpacingSelect.valueChanged.connect(self.update_line_spacing)
        self.textSettingsLayout.addRow("Line Spacing:", self.lineSpacingSelect)

        self.layout.addLayout(self.textSettingsLayout)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.printButton = QPushButton("Print Receipt")
        self.printButton.clicked.connect(self.print_receipt)
        buttons_layout.addWidget(self.printButton)

        self.layout.addLayout(buttons_layout)

        # Format Selection
        self.setCentralWidget(main_widget)

        # Connect signals
        self.paperWidthInput.textChanged.connect(self.update_text_edit_size)
        self.paperHeightInput.textChanged.connect(self.update_text_edit_size)

        # Initialize content
        self.qr_image = self.generate_qr_code(self.invoice_data.get("ULRQR", ""))
        self.load_receipt_content()
        self.update_text_edit_size()

    def update_alignment(self):
        alignment = self.alignmentSelect.currentText()
        if alignment == "Left":
            self.textEdit.setAlignment(Qt.AlignLeft)
        elif alignment == "Center":
            self.textEdit.setAlignment(Qt.AlignCenter)
        elif alignment == "Right":
            self.textEdit.setAlignment(Qt.AlignRight)

    def update_font(self):
        font_family = self.fontSelect.currentText()
        if font_family == "Sans Serif":
            font_family = "Helvetica"  # "Sans Serif" is a generic font family, using Helvetica as a fallback
        font = QFont(font_family)
        self.textEdit.setCurrentFont(font)

    def update_font_size(self):
        font_size = self.fontSizeSelect.value()
        font = self.textEdit.currentFont()
        font.setPointSize(font_size)
        self.textEdit.setCurrentFont(font)

    def update_line_spacing(self):
        line_spacing = self.lineSpacingSelect.value()
        self.textEdit.setLineHeight(line_spacing * 1.5, 1)

    def generate_qr_code(self, url: str) -> str:
        if not url:
            return ""

        qr = qrcode.QRCode(
            version=5,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((190, 190))

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        buffer.close()

        return f"data:image/png;base64,{img_base64}"

    def get_available_printers(self) -> list:
        return [
            printer[2]
            for printer in win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
        ]

    def update_text_edit_size(self):
        try:
            width = int(float(self.paperWidthInput.text()) * 3)
            height = int(float(self.paperHeightInput.text()) * 3)
            self.textEdit.setFixedSize(width, height)
        except ValueError:
            pass

    def generate_products_section(self):
        products_lines = []
        subtotal = total_discount = total_itbis = Decimal("0.00")

        for product in self.products:
            value = Decimal(product["cantidad"]) * Decimal(product["precio"])
            discount = value * (Decimal(product.get("descuento", 0)) / Decimal("100"))
            itbis = (value - discount) * (
                Decimal(product.get("itbis", 0)) / Decimal("100")
            )

            subtotal += value
            total_discount += discount
            total_itbis += itbis

            products_lines.append(
                f"{product['cantidad']:>3}  {product['descripcion']:<15}  "
                f"{product['precio']:>7.2f}  {value:>7.2f}"
            )

        totals = {
            "subtotal": subtotal,
            "total_discount": total_discount,
            "total_itbis": total_itbis,
            "total": subtotal - total_discount + total_itbis,
        }

        return "\n".join(products_lines), totals

    def replace_placeholders(
        self, template: str, products_section: str, totals: dict
    ) -> str:
        replacements = {
            "{company_name}": self.company_data.get("nombre_empresa", ""),
            "{company_address}": self.company_data.get("direccion", ""),
            "{company_rnc}": self.company_data.get("rnc", ""),
            "{invoice_number}": self.invoice_data.get("ncf", ""),
            "{numero_telefono}": self.invoice_data.get("telefono", ""),
            "{tipo_ncf}": self.invoice_data.get("ncf_type", ""),
            "{fecha_vencimiento}": self.invoice_data.get("fVencimientoNCF", ""),
            "{fecha}": self.invoice_data.get("fecha", datetime.now()).strftime(
                "%Y-%m-%d %H:%M"
            ),
            "{client_name}": self.invoice_data.get("nombre_cliente", ""),
            "{client_address}": self.invoice_data.get("direccion_cliente", ""),
            "{client_rnc}": self.invoice_data.get("cedula", ""),
            "{client_contact_number}": self.invoice_data.get("telefono_cliente", ""),
            "{numero_telefono}": self.invoice_data.get("telefono", ""),
            "{numero_cliente}": self.invoice_data.get("numero", ""),
            "{vendedor}": self.invoice_data.get("nombre_vendedor", ""),
            "{almacen}": self.invoice_data.get("almacen", ""),
            "{nota}": self.invoice_data.get("observacion", ""),
            "{realizado_por}": self.invoice_data.get("usuario", ""),
            "{qr_image}": f'<div style="text-align: center;"><img src="{self.qr_image}" width="190" height="190"/></div>',
            "{security_code}": self.invoice_data.get("codigoseguridad", ""),
            "{products_section}": products_section,
            "{subtotal}": f"{totals['subtotal']:.2f}",
            "{total_discount}": f"{totals['total_discount']:.2f}",
            "{total_itbis}": f"{totals['total_itbis']:.2f}",
            "{total}": f"{totals['total']:.2f}",
        }
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, str(value))
        return template

    def load_receipt_content(self):
        try:
            if not os.path.exists(self.template_path):
                raise FileNotFoundError(
                    f"Template file '{self.template_path}' not found."
                )

            with open(self.template_path, "r", encoding="utf-8") as template_file:
                template_content = template_file.read()

            products_section, totals = self.generate_products_section()
            self.receipt_content = self.replace_placeholders(
                template_content, products_section, totals
            )
            self.textEdit.setHtml(self.receipt_content)
        except Exception as e:
            QMessageBox.warning(
                self, "Error", f"Failed to load receipt content: {str(e)}"
            )

    def print_receipt(self):
        selected_printer = self.printerSelect.currentText()
        if not selected_printer:
            QMessageBox.warning(self, "Error", "No printer selected.")
            return

        try:
            printer = QPrinter()
            printer.setPrinterName(selected_printer)
            printer.setPageSize(QPrinter.Custom)
            printer.setPaperSize(
                QSizeF(
                    float(self.paperWidthInput.text()),
                    float(self.paperHeightInput.text()),
                ),
                QPrinter.Millimeter,
            )

            painter = QPainter()
            if painter.begin(printer):
                self.textEdit.document().drawContents(painter)
                painter.end()
            else:
                QMessageBox.warning(
                    self, "Error", "Failed to start the printing process."
                )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Printing failed: {str(e)}")
