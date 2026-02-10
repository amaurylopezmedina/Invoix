import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QStackedWidget,
    QMessageBox,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt
import sqlite3
import os

DB_FILE = "pos.db"


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Productos
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        )
    """
    )

    # Tickets
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT (datetime('now')),
            total REAL NOT NULL
        )
    """
    )

    # Items del ticket
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ticket_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            qty INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY(ticket_id) REFERENCES tickets(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """
    )
    conn.commit()
    conn.close()


class ProductsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.txt_code = QLineEdit()
        self.txt_name = QLineEdit()
        self.sp_price = QDoubleSpinBox()
        self.sp_price.setMaximum(9999999)
        self.sp_price.setDecimals(2)
        self.sp_stock = QSpinBox()
        self.sp_stock.setMaximum(999999)

        form.addRow("Código:", self.txt_code)
        form.addRow("Nombre:", self.txt_name)
        form.addRow("Precio:", self.sp_price)
        form.addRow("Existencia:", self.sp_stock)

        btns = QHBoxLayout()
        self.btn_new = QPushButton("Nuevo")
        self.btn_save = QPushButton("Guardar")
        self.btn_delete = QPushButton("Eliminar")
        btns.addWidget(self.btn_new)
        btns.addWidget(self.btn_save)
        btns.addWidget(self.btn_delete)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Código", "Nombre", "Precio", "Existencia"]
        )
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addLayout(form)
        layout.addLayout(btns)
        layout.addWidget(self.table)

        self.btn_new.clicked.connect(self.on_new)
        self.btn_save.clicked.connect(self.on_save)
        self.btn_delete.clicked.connect(self.on_delete)
        self.table.cellClicked.connect(self.on_row_clicked)

    def on_new(self):
        self.txt_code.clear()
        self.txt_name.clear()
        self.sp_price.setValue(0)
        self.sp_stock.setValue(0)
        self.table.clearSelection()

    def on_save(self):
        code = self.txt_code.text().strip()
        name = self.txt_name.text().strip()
        price = float(self.sp_price.value())
        stock = int(self.sp_stock.value())

        if not code or not name:
            QMessageBox.warning(self, "Validación", "Código y nombre son obligatorios.")
            return

        conn = get_connection()
        cur = conn.cursor()

        selected = self.table.currentRow()
        try:
            if selected >= 0:
                product_id = int(self.table.item(selected, 0).text())
                cur.execute(
                    """
                    UPDATE products
                    SET code = ?, name = ?, price = ?, stock = ?
                    WHERE id = ?
                """,
                    (code, name, price, stock, product_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO products (code, name, price, stock)
                    VALUES (?, ?, ?, ?)
                """,
                    (code, name, price, stock),
                )
            conn.commit()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Ya existe un producto con ese código.")
        finally:
            conn.close()

        self.load_products()
        self.on_new()

    def on_delete(self):
        selected = self.table.currentRow()
        if selected < 0:
            return
        product_id = int(self.table.item(selected, 0).text())
        if (
            QMessageBox.question(self, "Confirmar", "¿Eliminar producto seleccionado?")
            != QMessageBox.Yes
        ):
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()
        self.load_products()
        self.on_new()

    def on_row_clicked(self, row, col):
        self.txt_code.setText(self.table.item(row, 1).text())
        self.txt_name.setText(self.table.item(row, 2).text())
        self.sp_price.setValue(float(self.table.item(row, 3).text()))
        self.sp_stock.setValue(int(self.table.item(row, 4).text()))

    def load_products(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, code, name, price, stock FROM products ORDER BY name")
        rows = cur.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setData(Qt.UserRole, value)
                self.table.setItem(row, col, item)


class SalesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cart = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        input_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Código o nombre del producto...")
        self.btn_add = QPushButton("Agregar")
        input_layout.addWidget(self.txt_search)
        input_layout.addWidget(self.btn_add)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Producto", "Cantidad", "Precio", "Subtotal"]
        )
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        bottom = QHBoxLayout()
        self.lbl_total = QLabel("Total: 0.00")
        self.lbl_total.setStyleSheet("font-size: 18px; font-weight: bold;")
        bottom.addWidget(self.lbl_total)
        bottom.addStretch()
        self.btn_charge = QPushButton("Cobrar (F12)")
        self.btn_cancel = QPushButton("Cancelar")
        bottom.addWidget(self.btn_cancel)
        bottom.addWidget(self.btn_charge)

        layout.addLayout(input_layout)
        layout.addWidget(self.table)
        layout.addLayout(bottom)

        self.btn_add.clicked.connect(self.add_product)
        self.btn_charge.clicked.connect(self.charge_sale)
        self.btn_cancel.clicked.connect(self.cancel_sale)

    def add_product(self):
        text = self.txt_search.text().strip()
        if not text:
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name, price, stock
            FROM products
            WHERE code = ? OR name LIKE ?
        """,
            (text, f"%{text}%"),
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            QMessageBox.warning(self, "No encontrado", "Producto no encontrado.")
            return

        product_id, name, price, stock = row

        # Por simplicidad, siempre cantidad 1 y sin controlar stock
        qty = 1

        self.cart.append(
            {"product_id": product_id, "name": name, "price": price, "qty": qty}
        )
        self.refresh_cart()
        self.txt_search.clear()
        self.txt_search.setFocus()

    def refresh_cart(self):
        self.table.setRowCount(0)
        total = 0.0
        for line in self.cart:
            subtotal = line["qty"] * line["price"]
            total += subtotal
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(line["product_id"])))
            self.table.setItem(row, 1, QTableWidgetItem(line["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(line["qty"])))
            self.table.setItem(row, 3, QTableWidgetItem(f"{line['price']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{subtotal:.2f}"))
        self.lbl_total.setText(f"Total: {total:.2f}")

    def cancel_sale(self):
        if not self.cart:
            return
        if (
            QMessageBox.question(self, "Cancelar", "¿Cancelar la venta actual?")
            != QMessageBox.Yes
        ):
            return
        self.cart.clear()
        self.refresh_cart()

    def charge_sale(self):
        if not self.cart:
            QMessageBox.information(self, "Venta", "No hay productos en el carrito.")
            return
        total = sum(line["qty"] * line["price"] for line in self.cart)

        # En POS real pedirías forma de pago, efectivo, cambio, etc.
        if (
            QMessageBox.question(self, "Cobrar", f"Confirmar cobro de {total:.2f}?")
            != QMessageBox.Yes
        ):
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO tickets (total) VALUES (?)", (total,))
        ticket_id = cur.lastrowid

        for line in self.cart:
            cur.execute(
                """
                INSERT INTO ticket_items (ticket_id, product_id, qty, price)
                VALUES (?, ?, ?, ?)
            """,
                (ticket_id, line["product_id"], line["qty"], line["price"]),
            )
            # Descontar del stock
            cur.execute(
                """
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
            """,
                (line["qty"], line["product_id"]),
            )
        conn.commit()
        conn.close()

        QMessageBox.information(
            self, "Venta registrada", f"Venta #{ticket_id} registrada correctamente."
        )
        self.cart.clear()
        self.refresh_cart()


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.lbl_info = QLabel(
            "Aquí irían los reportes de ventas, cierres de caja, etc."
        )
        layout.addWidget(self.lbl_info)
        layout.addStretch()


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.lbl_info = QLabel(
            "Configuración del sistema (impresora, empresa, usuarios, etc.)"
        )
        layout.addWidget(self.lbl_info)
        layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("POS Python / PyQt - Esquema básico tipo Tina POS")
        self.resize(1024, 600)

        central = QWidget()
        main_layout = QHBoxLayout(central)

        # Menú lateral
        side = QVBoxLayout()
        self.btn_sales = QPushButton("Ventas")
        self.btn_products = QPushButton("Productos")
        self.btn_reports = QPushButton("Reportes")
        self.btn_settings = QPushButton("Configuración")
        for b in (
            self.btn_sales,
            self.btn_products,
            self.btn_reports,
            self.btn_settings,
        ):
            b.setMinimumHeight(40)
            side.addWidget(b)
        side.addStretch()

        # Páginas
        self.pages = QStackedWidget()
        self.sales_page = SalesPage()
        self.products_page = ProductsPage()
        self.reports_page = ReportsPage()
        self.settings_page = SettingsPage()

        self.pages.addWidget(self.sales_page)
        self.pages.addWidget(self.products_page)
        self.pages.addWidget(self.reports_page)
        self.pages.addWidget(self.settings_page)

        main_layout.addLayout(side, 1)
        main_layout.addWidget(self.pages, 4)

        self.setCentralWidget(central)

        self.btn_sales.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.sales_page)
        )
        self.btn_products.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.products_page)
        )
        self.btn_reports.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.reports_page)
        )
        self.btn_settings.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.settings_page)
        )

        self.pages.setCurrentWidget(self.sales_page)


def main():
    init_db()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
