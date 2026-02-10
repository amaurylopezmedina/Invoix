
import os
import sys
import tkinter as tk
from tkinter import messagebox, filedialog

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import schema_manager
from ui.cn_editor import open_cn_editor
from ui.json_manager_ui import JsonManagerUI
from ui.log_window import LogWindow, attach_ui_logger

class MainUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Administrador de Esquema FE (DGII)")
        self.geometry("520x360")
        self.resizable(False, False)

        self.ambiente_var = tk.StringVar(value="DEV")
        self.dry_run_var = tk.BooleanVar(value=False)

        self.log_win = None

        self._build()

    def _build(self):
        tk.Label(self, text="Administrador de Esquema FE", font=("Segoe UI", 14, "bold")).pack(pady=12)

        frm = tk.Frame(self)
        frm.pack(pady=5)
        tk.Label(frm, text="Ambiente: ").pack(side="left")
        tk.OptionMenu(frm, self.ambiente_var, "DEV", "CERT", "PRD").pack(side="left")

        tk.Checkbutton(self, text="🧪 Dry-Run (simulación: NO ejecuta SQL)", variable=self.dry_run_var).pack(pady=8)

        tk.Button(self, text="🗄️ Editar cn_*.ini", width=40, command=self.edit_cn).pack(pady=5)
        tk.Button(self, text="🧾 Editar JSON (tablas/vistas/SP)", width=40, command=self.edit_json).pack(pady=5)
        tk.Button(self, text="📜 Ver logs en tiempo real", width=40, command=self.open_logs).pack(pady=5)
        tk.Button(self, text="⚙️ Crear / Actualizar estructura", width=40, command=self.apply_schema).pack(pady=12)
        tk.Button(self, text="❌ Salir", width=40, command=self.destroy).pack(pady=5)

        tk.Label(self, text="Tip: En dry-run verás el SQL en la ventana de logs.").pack(pady=5)

    def open_logs(self):
        if self.log_win and self.log_win.winfo_exists():
            self.log_win.lift()
            return
        self.log_win = LogWindow(self)
        attach_ui_logger(self.log_win.append)

    def edit_cn(self):
        open_cn_editor(self)

    def edit_json(self):
        JsonManagerUI(self)

    def apply_schema(self):
        try:
            self.open_logs()
            schema_manager.run_install(
                ambiente=self.ambiente_var.get(),
                dry_run=self.dry_run_var.get(),
                base_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            )
            messagebox.showinfo("Éxito", "Estructura aplicada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    MainUI().mainloop()
