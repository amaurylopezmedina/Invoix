import os, sys, json
from urllib.parse import quote_plus
import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy import create_engine

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from src.common_audit import log_event
from src.common_config import load_cndb, save_cndb, make_conn_str

CONFIG_PATH = os.path.join(project_root, "config", "CNDB.json")

DEFAULT_CFG = {
    "DBMS": "ODBC Driver 17 for SQL Server",
    "Servidor": ".",
    "Puerto": 1433,
    "DB": "bscodeca01",
    "Usuario": "sistema",
    "Contrasena": "@@sistema",
    "AutenticacionUsuario": False,
    "UltimaConexionExitosa": None
}

def ensure_config():
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CFG, f, indent=2, ensure_ascii=False)

class PantallaConfig(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Configuración rápida — CNDB.json (perfil único)")
        self.geometry("660x520")
        self.resizable(False, False)
        ensure_config()
        self.original = load_cndb()
        self.state_cfg = dict(self.original)
        self._build_ui()
        self._load_to_form()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        frame = ttk.LabelFrame(self, text="Parámetros de conexión", padding=10)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        self.var_dbms = tk.StringVar()
        self.var_srv  = tk.StringVar()
        self.var_port = tk.StringVar()
        self.var_db   = tk.StringVar()
        self.var_user = tk.StringVar()
        self.var_pass = tk.StringVar()
        self.var_win  = tk.BooleanVar()
        self.var_last = tk.StringVar()

        ttk.Label(frame, text="DBMS").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.cmb_dbms = ttk.Combobox(frame, textvariable=self.var_dbms, state="readonly",
                                     values=["ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server"])
        self.cmb_dbms.grid(row=0, column=1, sticky="we", padx=6, pady=6)

        ttk.Label(frame, text="Servidor").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.var_srv).grid(row=1, column=1, sticky="we", padx=6, pady=6)

        ttk.Label(frame, text="Puerto").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.var_port).grid(row=2, column=1, sticky="we", padx=6, pady=6)

        ttk.Label(frame, text="Base de datos").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.var_db).grid(row=3, column=1, sticky="we", padx=6, pady=6)

        ttk.Label(frame, text="Usuario").grid(row=4, column=0, sticky="e", padx=6, pady=6)
        self.ent_user = ttk.Entry(frame, textvariable=self.var_user)
        self.ent_user.grid(row=4, column=1, sticky="we", padx=6, pady=6)

        ttk.Label(frame, text="Contraseña").grid(row=5, column=0, sticky="e", padx=6, pady=6)
        self.ent_pass = ttk.Entry(frame, textvariable=self.var_pass, show="*")
        self.ent_pass.grid(row=5, column=1, sticky="we", padx=6, pady=6)

        ttk.Checkbutton(frame, text="Autenticación de Windows (Trusted Connection)",
                        variable=self.var_win, command=self._toggle_windows_auth).grid(row=6, column=0, columnspan=2, sticky="w", padx=6, pady=6)

        frame.columnconfigure(1, weight=1)

        ttk.Label(self, textvariable=self.var_last, foreground="#666").pack(pady=(0,6))

        btns = ttk.Frame(self)
        btns.pack(pady=6)
        ttk.Button(btns, text="💾 Guardar", command=self._guardar).pack(side="left", padx=6)
        ttk.Button(btns, text="🔗 Probar conexión", command=self._probar_conexion).pack(side="left", padx=6)
        ttk.Button(btns, text="↩️ Volver", command=self._on_close).pack(side="left", padx=6)

    def _load_to_form(self):
        cfg = self.state_cfg
        self.var_dbms.set(cfg.get("DBMS", ""))
        self.var_srv.set(cfg.get("Servidor", ""))
        self.var_port.set(str(cfg.get("Puerto", "")))
        self.var_db.set(cfg.get("DB", ""))
        self.var_user.set(cfg.get("Usuario", ""))
        self.var_pass.set(cfg.get("Contrasena", ""))
        self.var_win.set(bool(cfg.get("AutenticacionUsuario", False)))
        last = cfg.get("UltimaConexionExitosa")
        self.var_last.set(f"Última conexión exitosa: {last if last else '— nunca —'}")
        self._toggle_windows_auth()

    def _form_to_state(self):
        try:
            port = int(self.var_port.get())
        except ValueError:
            messagebox.showerror("Error", "El puerto debe ser numérico (ej. 1433).")
            return None
        cfg = {
            "DBMS": self.var_dbms.get().strip(),
            "Servidor": self.var_srv.get().strip(),
            "Puerto": port,
            "DB": self.var_db.get().strip(),
            "Usuario": self.var_user.get().strip(),
            "Contrasena": self.var_pass.get(),
            "AutenticacionUsuario": bool(self.var_win.get()),
            "UltimaConexionExitosa": self.state_cfg.get("UltimaConexionExitosa", None)
        }
        return cfg

    def _toggle_windows_auth(self):
        if self.var_win.get():
            self.ent_user.configure(state="disabled")
            self.ent_pass.configure(state="disabled")
        else:
            self.ent_user.configure(state="normal")
            self.ent_pass.configure(state="normal")

    def _is_dirty(self):
        current = self._form_to_state()
        if current is None:
            return False
        import json
        return json.dumps(current, sort_keys=True) != json.dumps(self.original, sort_keys=True)

    def _guardar(self):
        cfg = self._form_to_state()
        if cfg is None:
            return
        try:
            save_cndb(cfg)
            self.original = dict(cfg)
            log_event("CNDB", "GUARDAR", "CNDB.json", "Guardado de configuración rápida")
            messagebox.showinfo("Guardado", "Configuración guardada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar CNDB.json:\n{e}")

    def _probar_conexion(self):
        cfg = self._form_to_state()
        if cfg is None:
            return
        from sqlalchemy import create_engine
        conn_str = make_conn_str(cfg)
        try:
            engine = create_engine(conn_str, fast_executemany=True)
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            from datetime import datetime
            cfg["UltimaConexionExitosa"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_cndb(cfg)
            self.original = dict(cfg)
            self.var_last.set(f"Última conexión exitosa: {cfg['UltimaConexionExitosa']}")
            log_event("CNDB", "TEST_CONEXION", "CNDB.json", "Conexión exitosa")
            messagebox.showinfo("Conexión exitosa", "✅ Se conectó correctamente al servidor.")
        except Exception as e:
            log_event("CNDB", "TEST_CONEXION_FAIL", "CNDB.json", str(e))
            messagebox.showerror("Error de conexión", f"❌ No se pudo conectar:\n{e}")

    def _on_close(self):
        if self._is_dirty():
            resp = messagebox.askyesnocancel("Cambios sin guardar", "Hay cambios sin guardar. ¿Desea guardarlos antes de salir?")
            if resp is None:
                return
            if resp:
                self._guardar()
        self.destroy()

if __name__ == "__main__":
    PantallaConfig().mainloop()