import os
import sys
import json
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ============================================================================
# 📂 CONFIGURAR RUTA DEL PROYECTO
# ============================================================================
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)


# ============================================================================
# 🔧 CARGAR CONFIGURACIÓN DESDE config/CNDB.json
# ============================================================================
def cargar_configuracion():
    ruta_config = os.path.join(project_root, "config", "CNDB.json")
    if not os.path.exists(ruta_config):
        raise FileNotFoundError(
            f"No se encontró el archivo de configuración: {ruta_config}"
        )
    with open(ruta_config, "r", encoding="utf-8") as f:
        return json.load(f)


config = cargar_configuracion()

# ============================================================================
# ⚙️ CONSTRUIR CADENA DE CONEXIÓN SQLALCHEMY
# ============================================================================
if config.get("AutenticacionUsuario", False):
    conn_str = (
        f"mssql+pyodbc://@{config['Servidor']},{config['Puerto']}/{config['DB']}?"
        f"driver={quote_plus(config['DBMS'])}&trusted_connection=yes"
    )
else:
    usuario = quote_plus(config["Usuario"])
    contrasena = quote_plus(config["Contrasena"])
    conn_str = (
        f"mssql+pyodbc://{usuario}:{contrasena}@{config['Servidor']},{config['Puerto']}/"
        f"{config['DB']}?driver={quote_plus(config['DBMS'])}"
    )

engine = create_engine(conn_str, fast_executemany=True)


# ============================================================================
# 🧩 FUNCIÓN PARA EJECUTAR PROCEDIMIENTOS
# ============================================================================
def ejecutar_sp(nombre_sp, parametros):
    """
    Ejecuta el procedimiento almacenado con los parámetros dados.
    Devuelve un DataFrame con los resultados y la cadena SQL usada.
    """
    query_text = f"""
EXEC {nombre_sp}
    @RNCEmisor = {repr(parametros['rnc']) if parametros['rnc'] else 'NULL'},
    @ENCF = {repr(parametros['encf']) if parametros['encf'] else 'NULL'},
    @Numero = {repr(parametros['numero']) if parametros['numero'] else 'NULL'},
    @Tipo = {repr(parametros['tipo']) if parametros['tipo'] else 'NULL'},
    @Desde = {repr(parametros['desde']) if parametros['desde'] else 'NULL'},
    @Hasta = {repr(parametros['hasta']) if parametros['hasta'] else 'NULL'}
""".strip()

    try:
        with engine.connect() as conn:
            query = text(
                """
                EXEC {0}
                    @RNCEmisor = :rnc,
                    @ENCF = :encf,
                    @Numero = :numero,
                    @Tipo = :tipo,
                    @Desde = :desde,
                    @Hasta = :hasta
            """.format(
                    nombre_sp
                )
            )
            df = pd.read_sql(query, conn, params=parametros)
            return df, query_text
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error ejecutando {nombre_sp}:\n{e}")
        return pd.DataFrame(), query_text


# ============================================================================
# 🖥️ INTERFAZ PRINCIPAL
# ============================================================================
class VentanaFacturas(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Consulta de Facturas Electrónicas ECF")
        self.geometry("1300x780")

        self.df_todo = pd.DataFrame()

        # ------------------ PARÁMETROS ------------------
        frame_param = ttk.LabelFrame(self, text="Filtros de búsqueda", padding=10)
        frame_param.pack(fill="x", padx=10, pady=10)

        etiquetas = [
            ("RNC Emisor", 15),
            ("ENCF", 20),
            ("Número", 12),
            ("Tipo", 5),
            ("Desde (YYYY-MM-DD)", 15),
            ("Hasta (YYYY-MM-DD)", 15),
        ]

        self.campos = {}
        for i, (etq, ancho) in enumerate(etiquetas):
            ttk.Label(frame_param, text=etq).grid(row=0, column=i, padx=5, pady=5)
            entry = ttk.Entry(frame_param, width=ancho)
            entry.grid(row=1, column=i, padx=5, pady=5)
            self.campos[etq] = entry

        # Botones
        ttk.Button(frame_param, text="🔍 Consultar", command=self.consultar).grid(
            row=1, column=len(etiquetas), padx=10
        )
        ttk.Button(
            frame_param, text="💾 Exportar a Excel", command=self.exportar_excel
        ).grid(row=1, column=len(etiquetas) + 1, padx=5)

        # ------------------ SENTENCIA SQL ------------------
        frame_sql = ttk.LabelFrame(self, text="Sentencia SQL ejecutada", padding=8)
        frame_sql.pack(fill="x", padx=10, pady=(0, 10))

        self.text_sql = tk.Text(frame_sql, height=5, wrap="word", bg="#f7f7f7")
        self.text_sql.pack(fill="x", expand=True)

        # ------------------ TABLA DE RESULTADOS ------------------
        frame_result = ttk.LabelFrame(self, text="Resultados", padding=10)
        frame_result.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(frame_result, show="headings")
        self.tree.pack(fill="both", expand=True, side="left")

        # Scrollbars
        vsb = ttk.Scrollbar(frame_result, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")

        hsb = ttk.Scrollbar(frame_result, orient="horizontal", command=self.tree.xview)
        hsb.pack(side="bottom", fill="x")

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    # ------------------------------------------------------------------
    def consultar(self):
        params = {
            "rnc": self.campos["RNC Emisor"].get() or None,
            "encf": self.campos["ENCF"].get() or None,
            "numero": self.campos["Número"].get() or None,
            "tipo": self.campos["Tipo"].get() or None,
            "desde": self.campos["Desde (YYYY-MM-DD)"].get() or None,
            "hasta": self.campos["Hasta (YYYY-MM-DD)"].get() or None,
        }

        df_contado, sql1 = ejecutar_sp("sp_FEVentaContadoRD", params)
        df_credito, sql2 = ejecutar_sp("sp_FEVentaCreditoRD", params)

        self.df_todo = pd.concat([df_contado, df_credito], ignore_index=True)

        # Mostrar SQL ejecutado
        self.text_sql.delete("1.0", "end")
        self.text_sql.insert("1.0", f"{sql1}\n\n{sql2}")

        if self.df_todo.empty:
            messagebox.showinfo(
                "Sin resultados",
                "No se encontraron facturas con los filtros indicados.",
            )
            self.tree.delete(*self.tree.get_children())
            return

        self.mostrar_df(self.df_todo)
        messagebox.showinfo(
            "Éxito",
            f"Consulta completada. Se encontraron {len(self.df_todo)} registros.",
        )

    # ------------------------------------------------------------------
    def mostrar_df(self, df):
        self.tree.delete(*self.tree.get_children())
        if df.empty:
            return

        cols = list(df.columns)
        self.tree["columns"] = cols

        muestra = df.head(100)
        for c in cols:
            max_len = max(
                [len(str(x)) for x in muestra[c].astype(str).tolist()] + [len(c)]
            )
            ancho = min(max(80, max_len * 7), 400)
            self.tree.heading(c, text=c)
            self.tree.column(c, width=ancho, minwidth=80, anchor="w")

        for _, row in df.iterrows():
            valores = [str(x) if pd.notnull(x) else "" for x in row.tolist()]
            self.tree.insert("", "end", values=valores)

    # ------------------------------------------------------------------
    def exportar_excel(self):
        if self.df_todo.empty:
            messagebox.showwarning("Sin datos", "No hay datos para exportar.")
            return

        ruta_predeterminada = os.path.join(project_root, "reportes")
        os.makedirs(ruta_predeterminada, exist_ok=True)

        archivo = filedialog.asksaveasfilename(
            initialdir=ruta_predeterminada,
            title="Guardar archivo Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=f"Facturas_ECF_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )

        if not archivo:
            return

        try:
            with pd.ExcelWriter(archivo, engine="xlsxwriter") as writer:
                self.df_todo.to_excel(writer, sheet_name="Facturas", index=False)
            messagebox.showinfo(
                "Exportación exitosa", f"Archivo guardado en:\n{archivo}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error al exportar", f"No se pudo guardar el archivo:\n{e}"
            )


# ============================================================================
# 🚀 EJECUCIÓN
# ============================================================================
if __name__ == "__main__":
    app = VentanaFacturas()
    app.mainloop()
