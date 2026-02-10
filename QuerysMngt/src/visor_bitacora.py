import os, sys, sqlite3, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

DATA_DIR = os.path.join(project_root, "data")
SQLITE_PATH = os.path.join(DATA_DIR, "procedimientos.db")
os.makedirs(DATA_DIR, exist_ok=True)

def ensure_table():
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Bitacora (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            actor TEXT,
            modulo TEXT,
            accion TEXT,
            objeto TEXT,
            detalle TEXT
        )
    """ )
    conn.commit(); conn.close()

ensure_table()

class VisorBitacora(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bitácora / Auditoría — v5.0")
        self.geometry("1280x720")

        self._build_ui()
        self._load()

    def _build_ui(self):
        top = ttk.LabelFrame(self, text="Filtros", padding=8); top.pack(fill="x", padx=10, pady=8)
        self.e_desde = ttk.Entry(top, width=18); self.e_hasta = ttk.Entry(top, width=18)
        self.e_mod = ttk.Entry(top, width=14); self.e_acc = ttk.Entry(top, width=14); self.e_obj = ttk.Entry(top, width=18)
        ttk.Label(top, text="Desde (YYYY-MM-DD)").pack(side="left"); self.e_desde.pack(side="left", padx=6)
        ttk.Label(top, text="Hasta").pack(side="left", padx=(12,0)); self.e_hasta.pack(side="left", padx=6)
        ttk.Label(top, text="Módulo").pack(side="left", padx=(12,0)); self.e_mod.pack(side="left", padx=6)
        ttk.Label(top, text="Acción").pack(side="left", padx=(12,0)); self.e_acc.pack(side="left", padx=6)
        ttk.Label(top, text="Objeto").pack(side="left", padx=(12,0)); self.e_obj.pack(side="left", padx=6)
        ttk.Button(top, text="Buscar", command=self._load).pack(side="left", padx=10)
        ttk.Button(top, text="Exportar TXT", command=self._export).pack(side="left", padx=10)

        frame = ttk.LabelFrame(self, text="Eventos", padding=8); frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.tree = ttk.Treeview(frame, show="headings")
        self.tree.pack(fill="both", expand=True, side="left")
        for c,w in [("id",80),("ts",160),("actor",100),("modulo",120),("accion",140),("objeto",260),("detalle",800)]:
            self.tree["columns"] = (*self.tree["columns"], c) if self.tree["columns"] else (c,)
            self.tree.heading(c, text=c.upper()); self.tree.column(c, width=w, anchor="w", minwidth=60)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview); vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview); hsb.pack(side="bottom", fill="x")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    def _load(self):
        conn = sqlite3.connect(SQLITE_PATH); cur = conn.cursor()
        q = "SELECT id, ts, actor, modulo, accion, objeto, detalle FROM Bitacora WHERE 1=1"
        params = []
        if self.e_desde.get().strip():
            q += " AND ts >= ?"; params.append(self.e_desde.get().strip()+" 00:00:00")
        if self.e_hasta.get().strip():
            q += " AND ts <= ?"; params.append(self.e_hasta.get().strip()+" 23:59:59")
        if self.e_mod.get().strip():
            q += " AND modulo LIKE ?"; params.append("%"+self.e_mod.get().strip()+"%")
        if self.e_acc.get().strip():
            q += " AND accion LIKE ?"; params.append("%"+self.e_acc.get().strip()+"%")
        if self.e_obj.get().strip():
            q += " AND objeto LIKE ?"; params.append("%"+self.e_obj.get().strip()+"%")
        q += " ORDER BY id DESC LIMIT 5000"
        rows = cur.execute(q, params).fetchall()
        conn.close()
        self.tree.delete(*self.tree.get_children())
        for r in rows: self.tree.insert("", "end", values=r)

    def _export(self):
        ruta = filedialog.asksaveasfilename(title="Guardar TXT", defaultextension=".txt", filetypes=[("Texto","*.txt")],
                                            initialfile=f"bitacora_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        if not ruta: return
        lines = []
        for iid in self.tree.get_children():
            vals = self.tree.item(iid)["values"]
            lines.append("\t".join([str(v) for v in vals]))
        with open(ruta, "w", encoding="utf-8") as f: f.write("\n".join(lines))
        messagebox.showinfo("Exportado", f"TXT guardado en:\n{ruta}")

if __name__ == "__main__":
    VisorBitacora().mainloop()