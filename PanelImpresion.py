import os
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import QPoint, QRect, QSize, Qt

from db.database import fetch_invoice_data
from print.document_editor import DocumentEditor, ReceiptEditor
from print.invoice_app import InvoiceApp
from print.pdf_generator import PDFGenerator


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = InvoiceApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
