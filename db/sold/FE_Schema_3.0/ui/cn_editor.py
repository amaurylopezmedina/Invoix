
import os
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

def _project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def open_cn_editor(parent):
    win = tk.Toplevel(parent)
    win.title("Editar cn_*.ini")
    win.geometry("820x520")

    frm = tk.Frame(win)
    frm.pack(fill="x", pady=6)

    env_var = tk.StringVar(value="cn_dev.ini")
    opts = ["cn_dev.ini", "cn_cert.ini", "cn_prd.ini"]
    tk.Label(frm, text="Archivo:").pack(side="left", padx=6)
    tk.OptionMenu(frm, env_var, *opts).pack(side="left")

    text = ScrolledText(win, wrap="none")
    text.pack(expand=True, fill="both", padx=8, pady=8)

    def load():
        path = os.path.join(_project_root(), "config", env_var.get())
        if not os.path.exists(path):
            messagebox.showerror("Error", f"No existe: {path}")
            return
        text.delete("1.0", "end")
        with open(path, "r", encoding="utf-8") as f:
            text.insert("1.0", f.read())

    def save():
        path = os.path.join(_project_root(), "config", env_var.get())
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.get("1.0", "end"))
        messagebox.showinfo("Guardado", "Archivo guardado correctamente.")

    tk.Button(frm, text="Cargar", command=load).pack(side="left", padx=6)
    tk.Button(frm, text="Guardar", command=save).pack(side="left", padx=6)

    load()
