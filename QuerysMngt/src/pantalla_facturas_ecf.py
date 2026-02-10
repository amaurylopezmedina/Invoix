import os, sys, json, webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from sqlalchemy import create_engine, text

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from src.common_config import get_effective_config, make_conn_str
from src.common_audit import log_event

def get_engine(profile: str | None = None):
    cfg = get_effective_config(profile)
    return create_engine(make_conn_str(cfg), fast_executemany=True)

def ejecutar_sp(engine, nombre_sp: str, params: dict):
    sql_mostrado = f"""
EXEC {nombre_sp}
    @RNCEmisor = {repr(params.get('rnc')) if params.get('rnc') else 'NULL'},
    @ENCF      = {repr(params.get('encf')) if params.get('encf') else 'NULL'},
    @Numero    = {repr(params.get('numero')) if params.get('numero') else 'NULL'},
    @Tipo      = {repr(params.get('tipo')) if params.get('tipo') else 'NULL'},
    @Desde     = {repr(params.get('desde')) if params.get('desde') else 'NULL'},
    @Hasta     = {repr(params.get('hasta')) if params.get('hasta') else 'NULL'}
""".strip()

    stmt = text(f"""
        EXEC {nombre_sp}
            @RNCEmisor = :rnc,
            @ENCF = :encf,
            @Numero = :numero,
            @Tipo = :tipo,
            @Desde = :desde,
            @Hasta = :hasta
    """)
    with engine.connect() as conn:
        result = conn.execute(stmt, {
            "rnc": params.get("rnc"),
            "encf": params.get("encf"),
            "numero": params.get("numero"),
            "tipo": params.get("tipo"),
            "desde": params.get("desde"),
            "hasta": params.get("hasta"),
        })
        rows = result.fetchall()
        cols = list(result.keys())
        return cols, rows, sql_mostrado

def ajustar_columnas(tree, cols, rows, max_rows=120):
    tree["columns"] = cols
    for c in cols:
        tree.heading(c, text=c)
    muestra = rows[:max_rows]
    for i, c in enumerate(cols):
        max_len = len(c)
        for r in muestra:
            v = "" if r[i] is None else str(r[i])
            if len(v) > max_len: max_len = len(v)
        width_px = min(max(80, max_len * 7), 480)
        tree.column(c, width=width_px, minwidth=80, anchor="w")

def llenar_tree(tree, cols, rows):
    tree.delete(*tree.get_children())
    for r in rows:
        tree.insert("", "end", values=[("" if v is None else str(v)) for v in r])

class VentanaEjecucion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Consulta de Facturas ECF — v5.0 (SQLAlchemy puro)")
        self.geometry("1360x840")

        self.cols = []; self.rows = []

        frame_top = ttk.Frame(self); frame_top.pack(fill="x", padx=10, pady=8)
        ttk.Label(frame_top, text="Perfil (opcional)").pack(side="left")
        self.var_profile = tk.StringVar()
        ttk.Entry(frame_top, textvariable=self.var_profile, width=18).pack(side="left", padx=6)
        ttk.Button(frame_top, text="Usar perfil", command=self._recrear_engine).pack(side="left", padx=4)

        self.engine = get_engine(None)

        frame_param = ttk.LabelFrame(self, text="Filtros de búsqueda", padding=10)
        frame_param.pack(fill="x", padx=10, pady=10)
        campos = [
            ("RNC Emisor", 15),
            ("ENCF", 20),
            ("Número", 12),
            ("Tipo", 6),
            ("Desde (YYYY-MM-DD)", 16),
            ("Hasta (YYYY-MM-DD)", 16),
        ]
        self.inputs = {}
        for i, (label, width) in enumerate(campos):
            ttk.Label(frame_param, text=label).grid(row=0, column=i, padx=4, pady=4)
            ent = ttk.Entry(frame_param, width=width)
            ent.grid(row=1, column=i, padx=4, pady=4)
            self.inputs[label] = ent
        ttk.Button(frame_param, text="Consultar", command=self.consultar).grid(row=1, column=len(campos), padx=8)
        ttk.Button(frame_param, text="Exportar a Excel", command=self.exportar_excel).grid(row=1, column=len(campos)+1, padx=6)

        frame_sql = ttk.LabelFrame(self, text="Sentencias SQL ejecutadas", padding=8)
        frame_sql.pack(fill="x", padx=10, pady=(0,10))
        self.text_sql = tk.Text(frame_sql, height=5, wrap="word", bg="#f7f7f7")
        self.text_sql.pack(fill="x", expand=True)
        ttk.Button(frame_sql, text="Copiar SQL", command=self._copiar_sql).pack(anchor="e", pady=4)

        frame_result = ttk.LabelFrame(self, text="Resultados", padding=10)
        frame_result.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree = ttk.Treeview(frame_result, show="headings")
        self.tree.pack(fill="both", expand=True, side="left")
        vsb = ttk.Scrollbar(frame_result, orient="vertical", command=self.tree.yview); vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(frame_result, orient="horizontal", command=self.tree.xview); hsb.pack(side="bottom", fill="x")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.bind("<Button-3>", self._context_menu)

    def _recrear_engine(self):
        name = self.var_profile.get().strip() or None
        try:
            self.engine = get_engine(name)
            messagebox.showinfo("OK", f"Se cargó el perfil: {name or 'default'}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid: return
        self.tree.selection_set(iid)
        menu = tk.Menu(self, tearoff=0)
        if "URLQR" in self.cols:
            menu.add_command(label="Abrir URLQR en navegador", command=self._abrir_url_qr)
        menu.post(event.x_root, event.y_root)

    def _abrir_url_qr(self):
        if "URLQR" not in self.cols: return
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0]); values = item.get("values", [])
        try:
            idx = self.cols.index("URLQR"); url = values[idx]
            if url: webbrowser.open(url)
        except Exception: pass

    def _copiar_sql(self):
        sql = self.text_sql.get("1.0", "end").strip()
        if not sql: return
        self.clipboard_clear(); self.clipboard_append(sql)
        messagebox.showinfo("Copiado", "SQL copiada al portapapeles.")

    def _read_params(self):
        return {
            "rnc": self.inputs["RNC Emisor"].get() or None,
            "encf": self.inputs["ENCF"].get() or None,
            "numero": self.inputs["Número"].get() or None,
            "tipo": self.inputs["Tipo"].get() or None,
            "desde": self.inputs["Desde (YYYY-MM-DD)"].get() or None,
            "hasta": self.inputs["Hasta (YYYY-MM-DD)"].get() or None,
        }

    def consultar(self):
        params = self._read_params()
        cols1, rows1, sql1 = ejecutar_sp(self.engine, "sp_FEVentaContadoRD", params)
        cols2, rows2, sql2 = ejecutar_sp(self.engine, "sp_FEVentaCreditoRD", params)
        self.cols = cols1 if len(cols1) >= len(cols2) else cols2
        self.rows = list(rows1) + list(rows2)
        self.text_sql.delete("1.0", "end"); self.text_sql.insert("1.0", f"{sql1}\n\n{sql2}")
        self.tree["columns"] = self.cols
        for c in self.cols: self.tree.heading(c, text=c)
        ajustar_columnas(self.tree, self.cols, self.rows, max_rows=140); llenar_tree(self.tree, self.cols, self.rows)
        log_event("ECF","EXEC_SP","sp_FEVentaContadoRD+Credito", f"rows={len(self.rows)} params={params}")
        messagebox.showinfo("Consulta lista", f"Se recuperaron {len(self.rows)} registros.")

    def exportar_excel(self):
        if not self.cols or not self.rows:
            messagebox.showwarning("Sin datos", "No hay datos para exportar."); return
        import xlsxwriter
        ruta_dir = os.path.join(project_root, "reportes"); os.makedirs(ruta_dir, exist_ok=True)
        ruta = filedialog.asksaveasfilename(
            initialdir=ruta_dir, title="Guardar Excel", defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=f"Facturas_ECF_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )
        if not ruta: return
        try:
            wb = xlsxwriter.Workbook(ruta); ws = wb.add_worksheet("Facturas")
            for j, c in enumerate(self.cols): ws.write(0, j, c)
            for i, row in enumerate(self.rows, start=1):
                for j, val in enumerate(row): ws.write(i, j, "" if val is None else str(val))
            wb.close()
            log_event("ECF","EXPORT_XLSX", os.path.basename(ruta), f"cols={len(self.cols)} rows={len(self.rows)}")
            messagebox.showinfo("Exportado", f"Archivo guardado en:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

if __name__ == "__main__":
    VentanaEjecucion().mainloop()