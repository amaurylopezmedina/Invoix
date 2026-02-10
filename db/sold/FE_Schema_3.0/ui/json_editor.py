
import os
import json
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

def _project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def open_json_editor(parent):
    win = tk.Toplevel(parent)
    win.title("Editor JSON (Tablas / Vistas / SP)")
    win.geometry("920x560")

    path_var = tk.StringVar(value="")

    top = tk.Frame(win)
    top.pack(fill="x", pady=6)

    tk.Button(top, text="Abrir JSON...", command=lambda: _open_file()).pack(side="left", padx=6)
    tk.Label(top, textvariable=path_var).pack(side="left", padx=6)

    text = ScrolledText(win, wrap="none")
    text.pack(expand=True, fill="both", padx=8, pady=8)

    def _open_file():
        fn = filedialog.askopenfilename(
            initialdir=_project_root(),
            filetypes=[("JSON", "*.json")],
            title="Selecciona un JSON"
        )
        if not fn:
            return
        path_var.set(fn)
        with open(fn, "r", encoding="utf-8") as f:
            text.delete("1.0", "end")
            text.insert("1.0", f.read())

    def save():
        fn = path_var.get()
        if not fn:
            messagebox.showwarning("Atención", "Primero abre un JSON.")
            return
        # Validar JSON
        try:
            obj = json.loads(text.get("1.0", "end"))
        except Exception as e:
            messagebox.showerror("JSON inválido", str(e))
            return
        with open(fn, "w", encoding="utf-8") as f:
            f.write(json.dumps(obj, indent=2, ensure_ascii=False))
        messagebox.showinfo("Guardado", "JSON guardado correctamente.")

    tk.Button(win, text="💾 Guardar", command=save).pack(pady=6)
