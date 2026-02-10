import sys
from PyQt6 import QtWidgets
from ui.main_window import MainWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setOrganizationName("ASESYS")
    app.setApplicationName("Importador DGII SQL")

    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
