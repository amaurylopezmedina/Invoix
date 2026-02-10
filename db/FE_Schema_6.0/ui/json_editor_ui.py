
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText

def abrir_editor_json(parent, filepath: str, on_saved=None):
    data = {}
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    tipo = "TABLE" if filepath.endswith(".table.json") else ("VIEW" if filepath.endswith(".view.json") else "PROC")

    win = tk.Toplevel(parent)
    win.title(f"Editor JSON ({tipo}) - {os.path.basename(filepath)}")
    win.geometry("1100x650")

    # Header
    header = tk.Frame(win)
    header.pack(fill="x", padx=10, pady=6)
    tk.Label(header, text=f"Tipo: {tipo}", font=("Segoe UI", 11, "bold")).pack(side="left")
    tk.Label(header, text=f"Archivo: {os.path.basename(filepath)}", fg="#555").pack(side="right")

    body = tk.PanedWindow(win, orient=tk.HORIZONTAL)
    body.pack(expand=True, fill="both", padx=10, pady=6)

    # LEFT: Grid for TABLE fields (or DDL info for VIEW/PROC)
    left = tk.Frame(body)
    body.add(left, minsize=520)

    # RIGHT: Raw JSON editor (advanced)
    right = tk.Frame(body)
    body.add(right, minsize=520)

    # ---------- RIGHT (Raw JSON) ----------
    raw = ScrolledText(right, wrap="none")
    raw.pack(expand=True, fill="both")
    raw.insert("1.0", json.dumps(data, indent=2, ensure_ascii=False))

    # ---------- LEFT ----------
    if tipo == "TABLE":
        tk.Label(left, text="Campos de la Tabla", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        cols = ("campo","type","nullable","identity","description")
        tree = ttk.Treeview(left, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120 if c!="description" else 260)
        tree.pack(expand=True, fill="both", pady=6)

        def refresh_grid():
            tree.delete(*tree.get_children())
            fields = data.get("fields", {})
            for k,v in fields.items():
                tree.insert("", "end", values=(
                    k,
                    v.get("type",""),
                    v.get("nullable", True),
                    v.get("identity", False),
                    v.get("description","")
                ))

        def add_field():
            name = simpledialog.askstring("Campo","Nombre del campo:")
            if not name: return
            if name in data.get("fields", {}):
                messagebox.showerror("Error","El campo ya existe")
                return
            ftype = simpledialog.askstring("Tipo","Tipo SQL (ej: varchar(100), int, decimal(18,2)):")
            if not ftype: return
            nullable = messagebox.askyesno("Nullable","¿Permite NULL?")
            identity = messagebox.askyesno("Identity","¿Es IDENTITY?")
            desc = simpledialog.askstring("Descripción","Descripción del campo:", initialvalue="")
            data.setdefault("fields", {})[name] = {
                "type": ftype,
                "nullable": nullable,
                "identity": identity,
                "description": desc or ""
            }
            refresh_grid()

        def edit_field():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Atención","Selecciona un campo")
                return
            campo, ftype, nullable, identity, desc = tree.item(sel[0])["values"]
            ftype2 = simpledialog.askstring("Tipo","Tipo SQL:", initialvalue=ftype)
            if not ftype2: return
            nullable2 = messagebox.askyesno("Nullable","¿Permite NULL?")
            identity2 = messagebox.askyesno("Identity","¿Es IDENTITY?")
            desc2 = simpledialog.askstring("Descripción","Descripción:", initialvalue=desc)
            data["fields"][campo].update({
                "type": ftype2,
                "nullable": nullable2,
                "identity": identity2,
                "description": desc2 or ""
            })
            refresh_grid()

        def del_field():
            sel = tree.selection()
            if not sel:
                return
            campo = tree.item(sel[0])["values"][0]
            if not messagebox.askyesno("Confirmar", f"¿Eliminar campo '{campo}'?"):
                return
            data["fields"].pop(campo, None)
            refresh_grid()

        btns = tk.Frame(left)
        btns.pack(fill="x", pady=4)
        tk.Button(btns, text="➕ Agregar", command=add_field).pack(side="left")
        tk.Button(btns, text="✏️ Editar", command=edit_field).pack(side="left", padx=6)
        tk.Button(btns, text="🗑️ Borrar", command=del_field).pack(side="left")

        refresh_grid()
    else:
        tk.Label(left, text="Definición DDL", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ddl = ScrolledText(left, wrap="none")
        ddl.pack(expand=True, fill="both", pady=6)
        ddl.insert("1.0", data.get("ddl",""))

    # ---------- Bottom actions ----------
    def guardar():
        try:
            # sync raw editor if user edited there
            raw_obj = json.loads(raw.get("1.0","end"))
            data.clear()
            data.update(raw_obj)
        except Exception:
            pass

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False))
        messagebox.showinfo("Guardado","JSON guardado correctamente")
        if on_saved:
            try: on_saved()
            except: pass

    actions = tk.Frame(win)
    actions.pack(fill="x", padx=10, pady=6)
    tk.Button(actions, text="💾 Guardar", command=guardar).pack(side="left")
    tk.Button(actions, text="Cerrar", command=win.destroy).pack(side="right")
