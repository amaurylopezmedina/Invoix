
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from ui.json_editor_ui import abrir_editor_json
from ui.json_templates import templates as _templates

def _project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _folders():
    root = _project_root()
    return {
        "TABLE": os.path.join(root, "tables"),
        "VIEW":  os.path.join(root, "views"),
        "PROC":  os.path.join(root, "procs"),
    }

def _ext(tipo: str) -> str:
    return {
        "TABLE": ".table.json",
        "VIEW":  ".view.json",
        "PROC":  ".proc.json",
    }[tipo]

def _display_name(tipo: str, data: dict) -> str:
    if tipo == "TABLE":
        return data.get("table","(sin table)")
    return data.get("name","(sin name)")

class JsonManagerUI(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Administrador de JSON (Grid)")
        self.geometry("920x480")

        self.tree = ttk.Treeview(self, columns=("tipo","nombre","archivo"), show="headings")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("archivo", text="Archivo")
        self.tree.column("tipo", width=90, anchor="center")
        self.tree.column("nombre", width=280)
        self.tree.column("archivo", width=520)
        self.tree.pack(expand=True, fill="both", padx=8, pady=8)

        btns = tk.Frame(self)
        btns.pack(fill="x", padx=8, pady=6)
        tk.Button(btns, text="➕ Crear", width=12, command=self.crear).pack(side="left")
        tk.Button(btns, text="✏️ Editar", width=12, command=self.editar).pack(side="left", padx=6)
        tk.Button(btns, text="🗑️ Borrar", width=12, command=self.borrar).pack(side="left")
        tk.Button(btns, text="🔄 Recargar", width=12, command=self.cargar).pack(side="left", padx=6)
        tk.Button(btns, text="Cerrar", width=12, command=self.destroy).pack(side="right")

        self.cargar()

    def cargar(self):
        self.tree.delete(*self.tree.get_children())
        folders = _folders()
        for tipo, folder in folders.items():
            os.makedirs(folder, exist_ok=True)
            for fn in sorted(os.listdir(folder)):
                if not fn.endswith(_ext(tipo)):
                    continue
                path = os.path.join(folder, fn)
                try:
                    data = json.load(open(path, "r", encoding="utf-8"))
                except Exception:
                    data = {}
                nombre = _display_name(tipo, data)
                self.tree.insert("", "end", values=(tipo, nombre, fn), tags=(tipo,))
        # color tags
        self.tree.tag_configure("TABLE", background="")
        self.tree.tag_configure("VIEW",  background="")
        self.tree.tag_configure("PROC",  background="")

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0])["values"]  # [tipo, nombre, archivo]

    def crear(self):
        tipo = simpledialog.askstring("Crear", "Tipo (TABLE/VIEW/PROC):", initialvalue="TABLE")
        if not tipo:
            return
        tipo = tipo.strip().upper()
        if tipo not in ("TABLE","VIEW","PROC"):
            messagebox.showerror("Error", "Tipo inválido.")
            return

        base_name = simpledialog.askstring("Nombre", "Nombre del archivo (sin extensión):", initialvalue="nuevo")
        if not base_name:
            return

        folder = _folders()[tipo]
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, base_name + _ext(tipo))

        if os.path.exists(path):
            messagebox.showerror("Error", "Ya existe ese archivo.")
            return

        tpl = _templates()[tipo]
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(tpl, indent=2, ensure_ascii=False))

        abrir_editor_json(self, path, on_saved=self.cargar)

    def editar(self):
        row = self._selected()
        if not row:
            messagebox.showwarning("Atención", "Selecciona un JSON.")
            return
        tipo, _, archivo = row
        path = os.path.join(_folders()[tipo], archivo)
        abrir_editor_json(self, path, on_saved=self.cargar)

    def borrar(self):
        row = self._selected()
        if not row:
            messagebox.showwarning("Atención", "Selecciona un JSON.")
            return
        tipo, nombre, archivo = row
        if not messagebox.askyesno("Confirmar", f"¿Borrar {tipo} '{nombre}'?\nArchivo: {archivo}"):
            return
        path = os.path.join(_folders()[tipo], archivo)
        try:
            os.remove(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self.cargar()
