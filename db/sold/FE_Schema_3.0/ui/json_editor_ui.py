
import json
import os
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

def abrir_editor_json(parent, filepath: str, on_saved=None):
    win = tk.Toplevel(parent)
    win.title(f"Editor JSON - {os.path.basename(filepath)}")
    win.geometry("980x620")

    text = ScrolledText(win, wrap="none")
    text.pack(expand=True, fill="both", padx=8, pady=8)

    def cargar():
        with open(filepath, "r", encoding="utf-8") as f:
            text.delete("1.0", "end")
            text.insert("1.0", f.read())

    def guardar():
        raw = text.get("1.0", "end")
        try:
            obj = json.loads(raw)
        except Exception as e:
            messagebox.showerror("JSON inválido", str(e))
            return
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json.dumps(obj, indent=2, ensure_ascii=False))
        messagebox.showinfo("Guardado", "JSON guardado correctamente.")
        if on_saved:
            try:
                on_saved()
            except Exception:
                pass

    btns = tk.Frame(win)
    btns.pack(fill="x", padx=8, pady=6)
    tk.Button(btns, text="💾 Guardar", command=guardar).pack(side="left")
    tk.Button(btns, text="↩️ Recargar", command=cargar).pack(side="left", padx=6)
    tk.Button(btns, text="Cerrar", command=win.destroy).pack(side="right")

    cargar()
