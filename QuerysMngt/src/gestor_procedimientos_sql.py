import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import difflib
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

DATA_DIR = os.path.join(project_root, "data")
BACKUP_DIR = os.path.join(project_root, "backups")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

from src.common_config import get_effective_config, make_conn_str
from src.common_audit import log_event

def load_config(profile: str | None = None):
    return get_effective_config(profile)

def make_engine(profile: str | None = None):
    cfg = load_config(profile)
    return create_engine(make_conn_str(cfg), fast_executemany=True)

def quotename(name: str) -> str:
    return f"[{str(name).replace(']', ']]')}]"

def strip_go(sql_text: str) -> str:
    lines = []
    for line in sql_text.splitlines():
        if line.strip().upper() == "GO":
            continue
        lines.append(line)
    return "\n".join(lines)

def show_diff_window(parent, a_text, b_text, title="Diff (A: izquierda | B: derecha)"):
    a_lines = a_text.splitlines(keepends=True)
    b_lines = b_text.splitlines(keepends=True)
    diff = difflib.unified_diff(a_lines, b_lines, fromfile="SQLite", tofile="SQL Server", lineterm="")
    win = tk.Toplevel(parent)
    win.title(title)
    win.geometry("1100x700")
    text = tk.Text(win, wrap="none", font=("Consolas", 10))
    text.pack(fill="both", expand=True)
    sx = ttk.Scrollbar(win, orient="horizontal", command=text.xview)
    sy = ttk.Scrollbar(win, orient="vertical", command=text.yview)
    text.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
    sy.pack(side="right", fill="y")
    sx.pack(side="bottom", fill="x")
    text.insert("1.0", "".join(diff) or "-- No hay diferencias --")
    text.configure(state="disabled")

def backup_server_code(folder, filename_hint, code_text):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_full = os.path.join(BACKUP_DIR, folder)
    os.makedirs(folder_full, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename_hint)
    path = os.path.join(folder_full, f"{ts}_{safe_name}.sql")
    with open(path, "w", encoding="utf-8") as f:
        f.write(code_text or "")
    return path

class FindReplaceMixin:
    def _bind_editor_shortcuts(self, widget_text):
        widget_text.bind("<Control-f>", lambda e: (self._find_dialog(), "break"))
        widget_text.bind("<Control-h>", lambda e: (self._replace_dialog(), "break"))
        widget_text.bind("<Control-g>", lambda e: (self._goto_line(), "break"))
        self.bind_all("<Control-s>", lambda e: self._shortcut_save())
        self.bind_all("<F5>", lambda e: self._shortcut_apply())
        self.bind_all("<F9>", lambda e: self._shortcut_dryrun())

    def _shortcut_save(self): pass
    def _shortcut_apply(self): pass
    def _shortcut_dryrun(self): pass

    def _find_dialog(self):
        term = simpledialog.askstring("Buscar", "Texto a buscar:", parent=self)
        if not term:
            return
        text = self.text_sql
        start = text.index(tk.INSERT)
        idx = text.search(term, start, stopindex="end", nocase=True)
        if not idx:
            idx = text.search(term, "1.0", stopindex="end", nocase=True)
        if idx:
            end = f"{idx}+{len(term)}c"
            text.tag_remove("sel", "1.0", "end")
            text.tag_add("sel", idx, end)
            text.mark_set(tk.INSERT, end)
            text.see(idx)

    def _replace_dialog(self):
        term = simpledialog.askstring("Reemplazar", "Texto a buscar:", parent=self)
        if term is None:
            return
        rep = simpledialog.askstring("Reemplazar por", "Nuevo texto:", parent=self)
        if rep is None:
            return
        text = self.text_sql
        content = text.get("1.0", "end")
        new_content = content.replace(term, rep)
        text.delete("1.0", "end")
        text.insert("1.0", new_content)

    def _goto_line(self):
        try:
            ln = simpledialog.askinteger("Ir a línea", "Número de línea:", parent=self, minvalue=1, maxvalue=999999)
            if not ln:
                return
            index = f"{ln}.0"
            self.text_sql.mark_set(tk.INSERT, index)
            self.text_sql.see(index)
        except Exception:
            pass

import sqlite3

SQLITE_PATH = os.path.join(DATA_DIR, "procedimientos.db")

def ensure_sqlite():
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Procedimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            descripcion TEXT,
            codigo TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ProcedimientoHistorial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            procedimiento_nombre TEXT,
            version INTEGER,
            fecha TEXT,
            codigo TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Bitacora (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, actor TEXT, modulo TEXT, accion TEXT, objeto TEXT, detalle TEXT
        )
    """)
    conn.commit()
    conn.close()

ensure_sqlite()

class GestorProcedimientos(tk.Tk, FindReplaceMixin):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Procedimientos SQL (SQL Server + SQLite) — v5.0")
        self.geometry("1580x980")

        self.sqlite_conn = sqlite3.connect(SQLITE_PATH)

        self._build_ui()
        self._load_list_sqlite()
        self._reload_server_list()

    def _build_ui(self):
        top = ttk.Frame(self); top.pack(fill="both", expand=True, padx=10, pady=8)

        left = ttk.LabelFrame(top, text="Procedimientos guardados (SQLite)", padding=8)
        left.pack(side="left", fill="both", expand=True, padx=(0,6))

        self.tree_local = ttk.Treeview(left, columns=("id","nombre","descripcion"), show="headings", height=14)
        for c,w in [("id",70),("nombre",480),("descripcion",560)]:
            self.tree_local.heading(c, text=c.capitalize()); self.tree_local.column(c, width=w)
        self.tree_local.pack(side="left", fill="both", expand=True)
        vsb_l = ttk.Scrollbar(left, orient="vertical", command=self.tree_local.yview); vsb_l.pack(side="right", fill="y")
        self.tree_local.configure(yscrollcommand=vsb_l.set)
        self.tree_local.bind("<<TreeviewSelect>>", self._on_select_local)

        right = ttk.LabelFrame(top, text="Procedimientos en SQL Server", padding=8)
        right.pack(side="left", fill="both", expand=True, padx=(6,0))

        filt = ttk.Frame(right); filt.pack(fill="x", pady=(0,6))
        ttk.Label(filt, text="Perfil (opcional):").pack(side="left")
        self.var_profile = tk.StringVar(); ttk.Entry(filt, textvariable=self.var_profile, width=18).pack(side="left", padx=6)
        ttk.Button(filt, text="🔄 Recargar", command=self._reload_server_list).pack(side="left", padx=6)
        ttk.Label(filt, text="Buscar:").pack(side="left", padx=(12,2))
        self.var_filter = tk.StringVar(); ttk.Entry(filt, textvariable=self.var_filter, width=30).pack(side="left", padx=4)
        ttk.Button(filt, text="🔎 Filtrar", command=self._apply_filter).pack(side="left", padx=4)
        ttk.Button(filt, text="📥 Cargar al editor", command=self._load_selected_server_to_editor).pack(side="left", padx=6)
        ttk.Button(filt, text="💾 Importar a SQLite", command=self._import_selected_to_sqlite).pack(side="left", padx=6)
        ttk.Button(filt, text="📦 Importar TODOS", command=self._import_all_to_sqlite).pack(side="left", padx=6)
        ttk.Button(filt, text="🔍 Diff", command=self._diff_selected).pack(side="left", padx=6)

        self.tree_srv = ttk.Treeview(right, columns=("schema","name","create","modify"), show="headings", height=14)
        for c,w in [("schema",180),("name",420),("create",200),("modify",200)]:
            self.tree_srv.heading(c, text=c.capitalize()); self.tree_srv.column(c, width=w)
        self.tree_srv.pack(side="left", fill="both", expand=True)
        vsb_r = ttk.Scrollbar(right, orient="vertical", command=self.tree_srv.yview); vsb_r.pack(side="right", fill="y")
        self.tree_srv.configure(yscrollcommand=vsb_r.set)

        editor = ttk.LabelFrame(self, text="Editor de código SQL", padding=8); editor.pack(fill="both", expand=True, padx=10, pady=(6,10))
        self.text_sql = tk.Text(editor, wrap="none", font=("Consolas", 10), undo=True); self.text_sql.pack(fill="both", expand=True)
        sx = ttk.Scrollbar(editor, orient="horizontal", command=self.text_sql.xview); sy = ttk.Scrollbar(editor, orient="vertical", command=self.text_sql.yview)
        self.text_sql.configure(xscrollcommand=sx.set, yscrollcommand=sy.set); sy.pack(side="right", fill="y"); sx.pack(side="bottom", fill="x")

        btns = ttk.Frame(self); btns.pack(pady=6)
        ttk.Button(btns, text="➕ Nuevo", command=self._new_proc).pack(side="left", padx=6)
        ttk.Button(btns, text="📂 Importar .sql", command=self._import_sql_file).pack(side="left", padx=6)
        ttk.Button(btns, text="💾 Guardar SQLite", command=self._save_sqlite).pack(side="left", padx=6)
        ttk.Button(btns, text="⬆️ Aplicar en SQL Server", command=self._apply_sqlserver).pack(side="left", padx=6)
        ttk.Button(btns, text="🗑️ Eliminar en SQL Server", command=self._drop_sqlserver).pack(side="left", padx=6)
        ttk.Button(btns, text="☁️ Sincronizar SQLite → SQL Server (todos)", command=self._sync_sqlite_to_sqlserver).pack(side="left", padx=12)
        ttk.Button(btns, text="🧪 Dry‑run", command=self._simulate_sync_sqlite_to_sqlserver).pack(side="left", padx=12)

        self._bind_editor_shortcuts(self.text_sql)

    def _shortcut_save(self): self._save_sqlite()
    def _shortcut_apply(self): self._apply_sqlserver()
    def _shortcut_dryrun(self): self._simulate_sync_sqlite_to_sqlserver()

    def _load_list_sqlite(self):
        for r in self.tree_local.get_children(): self.tree_local.delete(r)
        cur = self.sqlite_conn.cursor(); cur.execute("SELECT id,nombre,descripcion FROM Procedimientos ORDER BY nombre")
        for row in cur.fetchall(): self.tree_local.insert("", "end", values=row)

    def _reload_server_list(self):
        profile = (self.var_profile.get() or None)
        self.server_rows = []
        engine = make_engine(profile)
        try:
            with engine.connect() as conn:
                rs = conn.execute(text('''
                    SELECT s.name AS SchemaName, p.name AS ProcedureName,
                           CONVERT(varchar(19), p.create_date, 120) AS create_date,
                           CONVERT(varchar(19), p.modify_date, 120) AS modify_date
                    FROM sys.procedures p
                    INNER JOIN sys.schemas s ON p.schema_id = s.schema_id
                    WHERE p.is_ms_shipped = 0
                    ORDER BY s.name, p.name
                '''))
                self.server_rows = rs.fetchall()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer la lista de procedimientos:\n{e}")
            return
        self._refresh_server_tree(self.server_rows)

    def _refresh_server_tree(self, rows):
        for r in self.tree_srv.get_children(): self.tree_srv.delete(r)
        for schema, name, create, modify in rows:
            self.tree_srv.insert("", "end", values=(schema, name, create, modify))

    def _apply_filter(self):
        q = (self.var_filter.get() or "").strip().lower()
        if not q: self._refresh_server_tree(self.server_rows); return
        filtered = [r for r in self.server_rows if q in (r[0] or '').lower() or q in (r[1] or '').lower()]
        self._refresh_server_tree(filtered)

    def _on_select_local(self, event=None):
        sel = self.tree_local.selection()
        if not sel: return
        item = self.tree_local.item(sel[0]); proc_id = item["values"][0]
        cur = self.sqlite_conn.cursor(); cur.execute("SELECT codigo FROM Procedimientos WHERE id=?", (proc_id,))
        row = cur.fetchone()
        if row: self.text_sql.delete("1.0", "end"); self.text_sql.insert("1.0", row[0])

    def _load_selected_server_to_editor(self):
        sel = self.tree_srv.selection()
        if not sel: messagebox.showwarning("Atención", "Seleccione un procedimiento del servidor."); return
        item = self.tree_srv.item(sel[0]); schema, name = item["values"][0], item["values"][1]
        engine = make_engine(None)
        try:
            with engine.connect() as conn:
                rs = conn.execute(text("SELECT sm.definition FROM sys.sql_modules sm INNER JOIN sys.objects so ON sm.object_id = so.object_id WHERE so.type IN ('P','PC') AND so.name = :n"),
                                  {"n": name})
                row = rs.fetchone()
                if row and row[0]:
                    self.text_sql.delete("1.0", "end"); self.text_sql.insert("1.0", row[0])
                    messagebox.showinfo("Importado", f"Procedimiento '{schema}.{name}' cargado en el editor.")
                else:
                    messagebox.showwarning("No encontrado", f"No se encontró el código de '{schema}.{name}'.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el procedimiento:\n{e}")

    def _new_proc(self):
        schema = simpledialog.askstring("Esquema", "Esquema (ej. dbo):") or "dbo"
        name = simpledialog.askstring("Nombre", "Nombre del procedimiento:") or "NuevoProcedimiento"
        plantilla = (
            f"CREATE OR ALTER PROCEDURE {quotename(schema)}.{quotename(name)}\n"
            "AS\nBEGIN\n    SET NOCOUNT ON;\n    -- TODO\nEND\n"
        )
        self.text_sql.delete("1.0", "end"); self.text_sql.insert("1.0", plantilla)

    def _import_sql_file(self):
        path = filedialog.askopenfilename(title="Seleccionar archivo .sql", filetypes=[("SQL", "*.sql"), ("Todos", "*.*")])
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f: sql_code = f.read()
            self.text_sql.delete("1.0", "end"); self.text_sql.insert("1.0", sql_code)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")

    def _save_sqlite(self):
        codigo = self.text_sql.get("1.0", "end").strip()
        if not codigo: messagebox.showwarning("Aviso", "El código SQL está vacío."); return
        nombre = simpledialog.askstring("Nombre", "Nombre del procedimiento (schema.name):")
        if not nombre: return
        descripcion = simpledialog.askstring("Descripción", "Descripción (opcional):") or ""
        try:
            cur = self.sqlite_conn.cursor()
            cur.execute("INSERT OR REPLACE INTO Procedimientos (id, nombre, descripcion, codigo) VALUES ((SELECT id FROM Procedimientos WHERE nombre=?), ?, ?, ?)",
                        (nombre, nombre, descripcion, codigo))
            cur.execute("SELECT COALESCE(MAX(version),0) FROM ProcedimientoHistorial WHERE procedimiento_nombre=?", (nombre,))
            next_ver = (cur.fetchone()[0] or 0) + 1
            cur.execute("INSERT INTO ProcedimientoHistorial (procedimiento_nombre, version, fecha, codigo) VALUES (?,?,?,?)",
                        (nombre, next_ver, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), codigo))
            self.sqlite_conn.commit()
            log_event("PROC","SAVE_SQLITE",nombre,"Guardado en SQLite")
            messagebox.showinfo("Guardado", f"'{nombre}' guardado (v{next_ver}).")
            self._load_list_sqlite()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar en SQLite:\n{e}")

    def _backup_current_server(self, schema, name):
        engine = make_engine(None)
        try:
            with engine.connect() as conn:
                rs = conn.execute(text("SELECT sm.definition FROM sys.sql_modules sm INNER JOIN sys.objects so ON sm.object_id = so.object_id INNER JOIN sys.schemas s ON s.schema_id=so.schema_id WHERE so.type IN ('P','PC') AND so.name = :n AND s.name=:s"),
                                  {"n": name, "s": schema})
                row = rs.fetchone()
                if row and row[0]:
                    path = backup_server_code("procedimientos", f"{schema}.{name}", row[0])
                    return path
        except Exception: pass
        return None

    def _apply_sqlserver(self):
        codigo = self.text_sql.get("1.0", "end").strip()
        if not codigo: messagebox.showwarning("Aviso", "El código SQL está vacío."); return
        sel = self.tree_srv.selection()
        if sel:
            item = self.tree_srv.item(sel[0]); schema, name = item["values"][0], item["values"][1]
            path = self._backup_current_server(schema, name)
            if path: messagebox.showinfo("Backup", f"Respaldo:\n{path}")
        engine = make_engine(None)
        try:
            sql_to_run = strip_go(codigo)
            with engine.connect() as conn: conn.exec_driver_sql(sql_to_run)
            log_event("PROC","APPLY_SQLSERVER","", "Aplicado en servidor")
            messagebox.showinfo("Éxito", "Procedimiento creado/actualizado en SQL Server.")
            self._reload_server_list()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo aplicar:\n{e}")

    def _drop_sqlserver(self):
        sel = self.tree_srv.selection()
        if not sel: messagebox.showwarning("Atención", "Seleccione un procedimiento para eliminar."); return
        item = self.tree_srv.item(sel[0]); schema, name = item["values"][0], item["values"][1]
        if not messagebox.askyesno("Confirmar", f"¿Eliminar {schema}.{name}?"): return
        engine = make_engine(None); full = f"{schema}.{name}".replace("'", "''")
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql(f"""
IF OBJECT_ID(N'{full}', N'P') IS NOT NULL
    DROP PROCEDURE {quotename(schema)}.{quotename(name)};
""" )
            log_event("PROC","DROP_SQLSERVER",f"{schema}.{name}","Eliminado")
            messagebox.showinfo("Eliminado", f"{schema}.{name} eliminado (si existía).")
            self._reload_server_list()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar:\n{e}")

    def _diff_selected(self):
        sel = self.tree_srv.selection()
        if not sel: messagebox.showwarning("Atención", "Seleccione en la lista del servidor para comparar."); return
        item = self.tree_srv.item(sel[0]); schema, name = item["values"][0], item["values"][1]
        engine = make_engine(None)
        server_code = ""
        try:
            with engine.connect() as conn:
                rs = conn.execute(text("SELECT sm.definition FROM sys.sql_modules sm INNER JOIN sys.objects so ON sm.object_id = so.object_id WHERE so.type IN ('P','PC') AND so.name = :n"),
                                  {"n": name})
                row = rs.fetchone(); server_code = row[0] if row and row[0] else ""
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer del servidor:\n{e}"); return
        cur = self.sqlite_conn.cursor(); cur.execute("SELECT codigo FROM Procedimientos WHERE nombre=?", (f"{schema}.{name}",))
        row = cur.fetchone(); sqlite_code = row[0] if row and row[0] else ""
        if not sqlite_code: messagebox.showwarning("Aviso", "No existe en SQLite para comparar."); return
        show_diff_window(self, sqlite_code, server_code, title=f"Diff — {schema}.{name}")

    def _import_selected_to_sqlite(self):
        sel = self.tree_srv.selection()
        if not sel: messagebox.showwarning("Atención", "Seleccione un procedimiento."); return
        item = self.tree_srv.item(sel[0]); schema, name = item["values"][0], item["values"][1]
        engine = make_engine(None)
        try:
            with engine.connect() as conn:
                rs = conn.execute(text("SELECT sm.definition FROM sys.sql_modules sm INNER JOIN sys.objects so ON sm.object_id = so.object_id WHERE so.type IN ('P','PC') AND so.name = :n"),
                                  {"n": name})
                row = rs.fetchone()
                if not (row and row[0]): messagebox.showwarning("No encontrado", "Sin definición"); return
                codigo = row[0]
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener el código:\n{e}"); return
        cur = self.sqlite_conn.cursor()
        try:
            cur.execute("INSERT OR REPLACE INTO Procedimientos (id, nombre, descripcion, codigo) VALUES ((SELECT id FROM Procedimientos WHERE nombre=?), ?, ?, ?)",
                        (f"{schema}.{name}", f"{schema}.{name}", "", codigo))
            cur.execute("SELECT COALESCE(MAX(version),0) FROM ProcedimientoHistorial WHERE procedimiento_nombre=?", (f"{schema}.{name}",))
            next_ver = (cur.fetchone()[0] or 0) + 1
            cur.execute("INSERT INTO ProcedimientoHistorial (procedimiento_nombre, version, fecha, codigo) VALUES (?,?,?,?)",
                        (f"{schema}.{name}", next_ver, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), codigo))
            self.sqlite_conn.commit()
            log_event("PROC","IMPORT_ONE",f"{schema}.{name}","Importado a SQLite")
            messagebox.showinfo("Importado", f"{schema}.{name} importado (v{next_ver}).")
            self._load_list_sqlite()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar en SQLite:\n{e}")

    def _import_all_to_sqlite(self):
        if not messagebox.askyesno("Confirmar", "¿Importar TODOS los procedimientos a SQLite?"): return
        engine = make_engine(None)
        total=ok=fail=0
        try:
            with engine.connect() as conn:
                rs = conn.execute(text('''
                    SELECT s.name AS schema_name, p.name AS proc_name
                    FROM sys.procedures p
                    INNER JOIN sys.schemas s ON p.schema_id=s.schema_id
                    WHERE p.is_ms_shipped=0
                    ORDER BY s.name, p.name
                '''))
                procs = rs.fetchall(); total = len(procs)
                cur = self.sqlite_conn.cursor()
                for schema, name in procs:
                    try:
                        rs2 = conn.execute(text("SELECT sm.definition FROM sys.sql_modules sm INNER JOIN sys.objects so ON sm.object_id=so.object_id WHERE so.type IN ('P','PC') AND so.name=:n"),
                                           {"n": name})
                        row = rs2.fetchone(); code = row[0] if row and row[0] else ""
                        cur.execute("INSERT OR REPLACE INTO Procedimientos (id, nombre, descripcion, codigo) VALUES ((SELECT id FROM Procedimientos WHERE nombre=?), ?, ?, ?)",
                                    (f"{schema}.{name}", f"{schema}.{name}", "", code))
                        cur.execute("SELECT COALESCE(MAX(version),0) FROM ProcedimientoHistorial WHERE procedimiento_nombre=?", (f"{schema}.{name}",))
                        next_ver = (cur.fetchone()[0] or 0) + 1
                        cur.execute("INSERT INTO ProcedimientoHistorial (procedimiento_nombre, version, fecha, codigo) VALUES (?,?,?,?)",
                                    (f"{schema}.{name}", next_ver, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), code))
                        ok += 1
                    except Exception:
                        fail += 1
                self.sqlite_conn.commit()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar:\n{e}"); return
        log_event("PROC","IMPORT_ALL","", f"OK={ok} FAIL={fail} TOTAL={total}")
        messagebox.showinfo("Importación", f"Total: {total}\nOK: {ok}\nFallidos: {fail}")

    def _simulate_sync_sqlite_to_sqlserver(self):
        if not messagebox.askyesno("Simulación", "Validar sintaxis (SET NOEXEC ON) de TODOS los procedimientos. ¿Continuar?"): return
        from tkinter import simpledialog
        stop_first = messagebox.askyesno("Detener en primer error", "¿Detener en primer error?")
        n_preview = simpledialog.askinteger("Vista previa", "Primeras líneas por error:", initialvalue=40, minvalue=5, maxvalue=500) or 40
        ruta = os.path.join(DATA_DIR, f"dryrun_procedimientos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        engine = make_engine(None)
        cur = self.sqlite_conn.cursor(); cur.execute("SELECT nombre, codigo FROM Procedimientos ORDER BY nombre")
        rows = cur.fetchall()
        total = len(rows); ok = 0; fail = 0; lines = []
        try:
            with engine.connect() as conn:
                for nombre, codigo in rows:
                    if not codigo: continue
                    sql_clean = strip_go(codigo)
                    try:
                        conn.exec_driver_sql("SET NOEXEC ON; " + sql_clean + "; SET NOEXEC OFF;")
                        ok += 1; lines.append(f"[OK] {nombre}")
                    except Exception as ex:
                        fail += 1
                        preview = "\n".join(sql_clean.splitlines()[:n_preview])
                        lines.append(f"[ERROR] {nombre} :: {ex}\n--- Preview ---\n{preview}\n--- Fin ---")
                        try: conn.exec_driver_sql("SET NOEXEC OFF;")
                        except Exception: pass
                        if stop_first: break
        except Exception as e:
            lines.append(f"[FATAL] {e}")
        finally:
            lines.append(f"Resumen => OK:{ok} FAIL:{fail} TOTAL:{total}")
            with open(ruta, "w", encoding="utf-8") as f: f.write("\n".join(lines))
        log_event("PROC","DRYRUN","", f"OK={ok} FAIL={fail} TOTAL={total} REP={ruta}")
        messagebox.showinfo("Simulación", f"OK:{ok} FAIL:{fail} TOTAL:{total}\nReporte:\n{ruta}")

    def _sync_sqlite_to_sqlserver(self):
        if not messagebox.askyesno("Sincronizar", "Aplicar TODOS los procedimientos de SQLite en SQL Server (ejecutará scripts). ¿Continuar?"):
            return
        engine = make_engine(None)
        cur = self.sqlite_conn.cursor(); cur.execute("SELECT nombre, codigo FROM Procedimientos ORDER BY nombre")
        rows = cur.fetchall(); ok=0; fail=0
        try:
            with engine.connect() as conn:
                for nombre, codigo in rows:
                    if not codigo: continue
                    sql_clean = strip_go(codigo)
                    try:
                        conn.exec_driver_sql(sql_clean); ok+=1
                    except Exception as ex:
                        fail+=1
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        log_event("PROC","SYNC_APPLY","", f"OK={ok} FAIL={fail} TOTAL={len(rows)}")
        messagebox.showinfo("Sincronización", f"Aplicados OK:{ok} — Fallidos:{fail} — Total:{len(rows)}")

if __name__ == "__main__":
    GestorProcedimientos().mainloop()
