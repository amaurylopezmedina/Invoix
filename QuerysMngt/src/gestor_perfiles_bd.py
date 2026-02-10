import os, sys, json, tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy import create_engine
from urllib.parse import quote_plus

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from src.common_config import load_profiles, save_profiles, make_conn_str, DEFAULT_PROFILE_NAME
from src.common_audit import log_event

class GestorPerfiles(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Perfiles de Conexión (profiles.json)")
        self.geometry("860x560")

        self.data = load_profiles()
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.Frame(top)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="Perfiles").pack(anchor="w")
        self.listbox = tk.Listbox(left, width=28, height=20)
        self.listbox.pack(fill="y", expand=False)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._load_selected())
        ttk.Button(left, text="➕ Agregar", command=self._add).pack(fill="x", pady=4)
        ttk.Button(left, text="🗑️ Eliminar", command=self._delete).pack(fill="x", pady=4)
        ttk.Button(left, text="⭐ Marcar por defecto", command=self._set_default).pack(fill="x", pady=4)
        ttk.Button(left, text="🔗 Probar conexión", command=self._test_conn).pack(fill="x", pady=12)

        right = ttk.LabelFrame(top, text="Detalle del perfil", padding=8)
        right.pack(side="left", fill="both", expand=True, padx=10)

        self.vars = {k: tk.StringVar() for k in ["DBMS","Servidor","Puerto","DB","Usuario","Contrasena"]}
        self.var_win = tk.BooleanVar()

        row=0
        for label, key in [("DBMS","DBMS"),("Servidor","Servidor"),("Puerto","Puerto"),("Base de datos","DB"),("Usuario","Usuario"),("Contraseña","Contrasena")]:
            ttk.Label(right, text=label).grid(row=row, column=0, sticky="e", padx=6, pady=6)
            ttk.Entry(right, textvariable=self.vars[key]).grid(row=row, column=1, sticky="we", padx=6, pady=6)
            row+=1
        ttk.Checkbutton(right, text="Autenticación de Windows", variable=self.var_win).grid(row=row, column=0, columnspan=2, sticky="w", padx=6, pady=6)
        row+=1
        right.columnconfigure(1, weight=1)

        btns = ttk.Frame(self)
        btns.pack(pady=10)
        ttk.Button(btns, text="💾 Guardar cambios", command=self._save).pack(side="left", padx=6)
        ttk.Button(btns, text="↩️ Cerrar", command=self.destroy).pack(side="left", padx=6)

    def _refresh_list(self):
        self.listbox.delete(0, "end")
        self.names = sorted(list(self.data.get("profiles", {}).keys()))
        for n in self.names:
            star = " (default)" if self.data.get("default")==n else ""
            self.listbox.insert("end", n + star)

    def _get_selected_name(self):
        if not self.listbox.curselection():
            return None
        idx = self.listbox.curselection()[0]
        # strip (default)
        raw = self.listbox.get(idx)
        name = raw.replace(" (default)", "")
        return name

    def _load_selected(self):
        name = self._get_selected_name()
        if not name: return
        prof = self.data["profiles"].get(name, {})
        self.vars["DBMS"].set(prof.get("DBMS","ODBC Driver 17 for SQL Server"))
        self.vars["Servidor"].set(prof.get("Servidor","."))
        self.vars["Puerto"].set(str(prof.get("Puerto",1433)))
        self.vars["DB"].set(prof.get("DB","bscodeca01"))
        self.vars["Usuario"].set(prof.get("Usuario","sistema"))
        self.vars["Contrasena"].set(prof.get("Contrasena","@@sistema"))
        self.var_win.set(bool(prof.get("AutenticacionUsuario", False)))

    def _add(self):
        name = tk.simpledialog.askstring("Nombre del perfil", "Nombre único del perfil (ej. prod, qa, dev):")
        if not name: return
        if "profiles" not in self.data: self.data["profiles"] = {}
        if name in self.data["profiles"]:
            messagebox.showerror("Error","Ya existe un perfil con ese nombre.")
            return
        self.data["profiles"][name] = {
            "DBMS":"ODBC Driver 17 for SQL Server",
            "Servidor":".","Puerto":1433,"DB":"bscodeca01","Usuario":"sistema","Contrasena":"@@sistema",
            "AutenticacionUsuario": False, "UltimaConexionExitosa": None
        }
        save_profiles(self.data)
        log_event("PERFILES","CREAR",name,"Perfil creado")
        self._refresh_list()

    def _delete(self):
        name = self._get_selected_name()
        if not name: return
        if not messagebox.askyesno("Confirmar", f"¿Eliminar el perfil '{name}'?"): return
        if name==self.data.get("default"):
            messagebox.showerror("Error","No se puede eliminar el perfil por defecto.")
            return
        self.data["profiles"].pop(name, None)
        save_profiles(self.data)
        log_event("PERFILES","ELIMINAR",name,"Perfil eliminado")
        self._refresh_list()

    def _set_default(self):
        name = self._get_selected_name()
        if not name: return
        self.data["default"] = name
        save_profiles(self.data)
        log_event("PERFILES","DEFAULT",name,"Marcado como predeterminado")
        self._refresh_list()

    def _save(self):
        name = self._get_selected_name()
        if not name: return
        try:
            port = int(self.vars["Puerto"].get())
        except ValueError:
            messagebox.showerror("Error","Puerto debe ser numérico.")
            return
        self.data["profiles"][name] = {
            "DBMS": self.vars["DBMS"].get().strip(),
            "Servidor": self.vars["Servidor"].get().strip(),
            "Puerto": port,
            "DB": self.vars["DB"].get().strip(),
            "Usuario": self.vars["Usuario"].get().strip(),
            "Contrasena": self.vars["Contrasena"].get(),
            "AutenticacionUsuario": bool(self.var_win.get()),
            "UltimaConexionExitosa": None
        }
        save_profiles(self.data)
        log_event("PERFILES","GUARDAR",name,"Perfil actualizado")
        messagebox.showinfo("Guardado","Cambios guardados.")

    def _test_conn(self):
        from src.common_config import make_conn_str
        name = self._get_selected_name()
        if not name: return
        cfg = self.data["profiles"][name]
        conn_str = make_conn_str(cfg)
        try:
            engine = create_engine(conn_str, fast_executemany=True)
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            self.data["profiles"][name]["UltimaConexionExitosa"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_profiles(self.data)
            log_event("PERFILES","TEST_CONEXION",name,"Conexión exitosa")
            messagebox.showinfo("OK","Conexión exitosa.")
        except Exception as e:
            log_event("PERFILES","TEST_CONEXION_FAIL",name,str(e))
            messagebox.showerror("Error", f"No se pudo conectar:\n{e}")

if __name__ == "__main__":
    GestorPerfiles().mainloop()