import os, sys, subprocess, tkinter as tk
from tkinter import ttk, messagebox

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Centro de Control DGII — v5.0")
        self.geometry("860x560")
        self.configure(bg="#f4f6f9")
        ttk.Style().configure("TButton", padding=10)

        ttk.Label(self, text="Centro de Control DGII", font=("Segoe UI", 22, "bold"), background="#f4f6f9").pack(pady=20)

        btns = [
            ("🧾 Ejecutar procedimientos DGII", "pantalla_facturas_ecf.py"),
            ("🛠️ Gestor de procedimientos SQL", "gestor_procedimientos_sql.py"),
            ("📄 Gestor de vistas SQL", "gestor_vistas_sql.py"),
            ("👥 Perfiles de conexión (múltiples)", "gestor_perfiles_bd.py"),
            ("⚙️ Config rápida CNDB.json", "pantalla_configuracion_bd.py"),
            ("📜 Visor de Bitácora/Auditoría", "visor_bitacora.py"),
        ]
        for text, script in btns:
            ttk.Button(self, text=text, width=56, command=lambda s=script: self._run_py(s)).pack(pady=6)

        ttk.Label(self, text="ASESYS SRL • Facturación Electrónica", background="#f4f6f9").pack(side="bottom", pady=18)

    def _run_py(self, relpath):
        ruta = os.path.join(project_root, "src", relpath)
        if not os.path.exists(ruta):
            messagebox.showerror("Error", f"No se encontró el archivo:\n{ruta}")
            return
        subprocess.Popen([sys.executable, ruta])

if __name__ == "__main__":
    VentanaPrincipal().mainloop()