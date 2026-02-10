import sys
import json
import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, 
                            QSpinBox, QCheckBox, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QWidget, QComboBox, QListWidget,
                            QListWidgetItem, QMessageBox, QGroupBox, QFormLayout,
                            QInputDialog, QMenu, QAction)
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt
# Add win32print import for printer detection
import win32print

class PrintConfigScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración de Impresión")
        self.setGeometry(300, 300, 650, 550)
        
        # Set emerald theme
        self.apply_emerald_theme()
        
        # Path to the config file
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                        "config", "config_print.json")
        
        # Load current configuration
        self.load_config()
        
        # Setup UI
        self.init_ui()
    
    def apply_emerald_theme(self):
        # Define emerald colors
        emerald = QColor(46, 139, 87)  # Sea Green / Emerald
        light_emerald = QColor(152, 251, 152)  # Pale Green
        dark_emerald = QColor(0, 100, 0)  # Dark Green
        
        # Create a palette
        palette = QPalette()
        
        # Set window background
        palette.setColor(QPalette.Window, QColor(240, 255, 240))  # Honeydew
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        
        # Set button colors
        palette.setColor(QPalette.Button, emerald)
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        
        # Set highlight colors
        palette.setColor(QPalette.Highlight, emerald)
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Set base colors
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(220, 255, 220))
        
        # Apply the palette
        self.setPalette(palette)
        
        # Set stylesheet for more detailed control
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0FFF0;
            }
            QGroupBox {
                border: 1px solid #2E8B57;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
                color: #006400;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #2E8B57;
                color: white;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3CB371;
            }
            QPushButton:pressed {
                background-color: #006400;
            }
            QLineEdit, QSpinBox, QComboBox, QListWidget {
                border: 1px solid #2E8B57;
                border-radius: 3px;
                padding: 2px;
            }
            QLabel {
                color: #006400;
            }
            QCheckBox {
                color: #006400;
            }
        """)
        
    def load_config(self):
        try:
            with open(self.config_path, 'r') as file:
                self.config = json.load(file)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar la configuración: {str(e)}")
            self.config = {
                "caja": "A",
                "printer_name": "",
                "copies": 1,
                "copy_labels": ["ORIGINAL - CLIENTE"],
                "show_copy_labels": False,
                "concodigo": 1
            }
    
    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # General settings group
        general_group = QGroupBox("Configuración General")
        general_layout = QFormLayout()
        
        # Caja
        self.caja_input = QLineEdit(self.config.get("caja", "A"))
        general_layout.addRow("Caja:", self.caja_input)
        
        # Printer name - allow direct input instead of just combo selection
        printer_layout = QHBoxLayout()
        self.printer_input = QLineEdit(self.config.get("printer_name", ""))
        self.printer_combo = QComboBox()
        
        # Get available printers
        printers = self.get_available_printers()
        self.printer_combo.addItems(["-- Seleccionar impresora --"] + printers)
        
        # Connect combo box to update line edit
        self.printer_combo.currentIndexChanged.connect(self.update_printer_name)
        
        printer_layout.addWidget(self.printer_input, 2)
        printer_layout.addWidget(self.printer_combo, 1)
        general_layout.addRow("Impresora:", printer_layout)
        
        # Copies
        self.copies_spin = QSpinBox()
        self.copies_spin.setMinimum(1)
        self.copies_spin.setMaximum(10)
        self.copies_spin.setValue(self.config.get("copies", 1))
        general_layout.addRow("Número de copias:", self.copies_spin)
        
        # Concodigo
        self.concodigo_spin = QSpinBox()
        self.concodigo_spin.setMinimum(0)
        self.concodigo_spin.setMaximum(1)
        self.concodigo_spin.setValue(self.config.get("concodigo", 1))
        general_layout.addRow("Con código:", self.concodigo_spin)
        
        general_group.setLayout(general_layout)
        main_layout.addWidget(general_group)
        
        # Copy labels group
        labels_group = QGroupBox("Etiquetas de Copias")
        labels_layout = QVBoxLayout()
        
        # Show copy labels
        self.show_labels_check = QCheckBox("Mostrar etiquetas en las copias")
        self.show_labels_check.setChecked(self.config.get("show_copy_labels", False))
        labels_layout.addWidget(self.show_labels_check)
        
        # Copy labels list with context menu for editing
        self.labels_list = QListWidget()
        self.labels_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.labels_list.customContextMenuRequested.connect(self.show_label_context_menu)
        
        for label in self.config.get("copy_labels", []):
            self.labels_list.addItem(label)
        labels_layout.addWidget(self.labels_list)
        
        # Add/Edit/Remove label buttons
        labels_buttons_layout = QHBoxLayout()
        
        self.add_label_button = QPushButton("Agregar")
        self.edit_label_button = QPushButton("Editar")
        self.remove_label_button = QPushButton("Eliminar")
        
        self.add_label_button.clicked.connect(self.add_label)
        self.edit_label_button.clicked.connect(self.edit_selected_label)
        self.remove_label_button.clicked.connect(self.remove_label)
        
        labels_buttons_layout.addWidget(self.add_label_button)
        labels_buttons_layout.addWidget(self.edit_label_button)
        labels_buttons_layout.addWidget(self.remove_label_button)
        
        labels_layout.addLayout(labels_buttons_layout)
        labels_group.setLayout(labels_layout)
        main_layout.addWidget(labels_group)
        
        # Save and Cancel buttons
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Guardar Configuración")
        self.cancel_button = QPushButton("Cancelar")
        
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        
        self.save_button.clicked.connect(self.save_config)
        self.cancel_button.clicked.connect(self.close)
        
        main_layout.addLayout(buttons_layout)
        
        # Set the main layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def show_label_context_menu(self, position):
        # Create context menu for the labels list
        menu = QMenu()
        edit_action = QAction("Editar", self)
        remove_action = QAction("Eliminar", self)
        
        # Only enable actions if an item is selected
        if self.labels_list.currentItem():
            edit_action.triggered.connect(self.edit_selected_label)
            remove_action.triggered.connect(self.remove_label)
            menu.addAction(edit_action)
            menu.addAction(remove_action)
            menu.exec_(self.labels_list.mapToGlobal(position))
    
    def edit_selected_label(self):
        # Edit the currently selected label
        current_item = self.labels_list.currentItem()
        if current_item:
            current_text = current_item.text()
            new_text, ok = QInputDialog.getText(
                self, 
                "Editar etiqueta", 
                "Modificar etiqueta:", 
                QLineEdit.Normal, 
                current_text
            )
            if ok and new_text:
                current_item.setText(new_text)
    
    def add_label(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Agregar etiqueta", "Ingrese la etiqueta:")
        if ok and text:
            self.labels_list.addItem(text)
    
    def remove_label(self):
        selected_items = self.labels_list.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            self.labels_list.takeItem(self.labels_list.row(item))
    
    def save_config(self):
        try:
            # Update config with UI values
            self.config["caja"] = self.caja_input.text()
            self.config["printer_name"] = self.printer_input.text()
            self.config["copies"] = self.copies_spin.value()
            
            # Get labels from list widget
            labels = []
            for i in range(self.labels_list.count()):
                labels.append(self.labels_list.item(i).text())
            self.config["copy_labels"] = labels
            
            self.config["show_copy_labels"] = self.show_labels_check.isChecked()
            self.config["concodigo"] = self.concodigo_spin.value()
            
            # Save to file
            with open(self.config_path, 'w') as file:
                json.dump(self.config, file, indent=4)
            
            QMessageBox.information(self, "Éxito", "Configuración guardada correctamente.")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar la configuración: {str(e)}")

    def get_available_printers(self):
        """Get a list of available printers on the system using win32print."""
        printers = []
        try:
            # Enumerate all printers on the system
            for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | 
                                                 win32print.PRINTER_ENUM_CONNECTIONS):
                printers.append(printer[2])  # printer[2] contains the printer name
            
            # Get the default printer name
            default_printer = win32print.GetDefaultPrinter()
            if default_printer and default_printer not in printers:
                printers.append(default_printer)
                
            # Sort the printer list alphabetically
            printers.sort()
            
            return printers
        except Exception as e:
            # If there's an error, log it and return a default list
            print(f"Error getting printers: {e}")
            return ["Microsoft Print to PDF", "Microsoft XPS Document Writer"]
    
    def update_printer_name(self, index):
        if index > 0:  # Skip the first item which is the placeholder
            self.printer_input.setText(self.printer_combo.currentText())
            
def main():
    app = QApplication(sys.argv)
    window = PrintConfigScreen()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()