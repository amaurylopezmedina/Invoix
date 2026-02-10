# -*- coding: utf-8 -*-
import json, re, threading, traceback, datetime, os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd
from sqlalchemy import create_engine, text

DEFAULT_MAX_LINES = 62

TYPE_MAP_SQL = {
    "char": "NVARCHAR(MAX)",
    "int": "INT",
    "numeric": "DECIMAL(38,10)",
    "date": "DATE",
    "bit": "BIT"
}

def sql_name(s):
    import re
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:120] if s else "col"

def build_conn_url(conn_cfg: dict)->str:
    from urllib.parse import quote_plus
    driver = conn_cfg.get("driver", "ODBC Driver 17 for SQL Server")
    if conn_cfg.get("trusted_connection"):
        params = f"Driver={driver};Server={conn_cfg['server']};Database={conn_cfg['database']};Trusted_Connection=yes;"
    else:
        params = f"Driver={driver};Server={conn_cfg['server']};Database={conn_cfg['database']};UID={conn_cfg['username']};PWD={conn_cfg['password']};"
    if conn_cfg.get("query"):
        for k,v in conn_cfg["query"].items():
            params += f"{k}={v};"
    return f"mssql+pyodbc:///?odbc_connect={quote_plus(params)}"

def load_mapping(path: Path):
    m = json.loads(path.read_text(encoding="utf-8"))
    return m["csv"]["FEEncabezado"], m["csv"]["FEDetalle"]

def normalize_header(df: pd.DataFrame, hdr_map: dict, issues:list)->pd.DataFrame:
    out = pd.DataFrame()
    for dbcol, (src, _) in hdr_map.items():
        colname = "ENCF" if dbcol.lower()=="encf" or src.lower()=="encf" else dbcol
        if src in df.columns:
            out[colname] = df[src]
        else:
            candidates = [c for c in df.columns if c.lower() == src.lower()]
            if candidates:
                out[colname] = df[candidates[0]]
                if src != candidates[0]:
                    issues.append({"Nivel":"Header","Campo":colname,"Tipo":"AliasUsado","Detalle":f"{src}→{candidates[0]}"})
            else:
                out[colname] = None
                issues.append({"Nivel":"Header","Campo":colname,"Tipo":"NoEncontrado","Detalle":src})
    if "ENCF" not in out.columns:
        raise ValueError("No se encontró ENCF en cabecera tras el mapeo.")
    return out

def find_wide_variants(df_columns, base, max_lines):
    cols = list(map(str, df_columns))
    variants = {}
    for i in range(1, max_lines+1):
        patterns = [
            rf"^{re.escape(base)}_{i}$", rf"^{re.escape(base)}\.{i}$",
            rf"^{re.escape(base)}-{i}$", rf"^{re.escape(base)}{i}$",
            rf"^{re.escape(base)}_{i}_.+$", rf"^{re.escape(base)}\.{i}\..+$",
            rf"^{re.escape(base)}-{i}-.+$"
        ]
        match = None
        for p in patterns:
            m = [c for c in cols if re.fullmatch(p, c)]
            if m:
                match = m[0]
                break
        if match:
            variants[i] = match
    return variants

def autodetect_max_lines(df: pd.DataFrame, det_map: dict, hard_cap=200):
    """Scan all base names from mapping (including NumeroLinea) to find the highest index present."""
    max_found = 0
    bases = [src for (src_type) in det_map.values() for src in [src_type[0]]]
    bases = list(set(bases))
    cols = list(map(str, df.columns))
    for c in cols:
        m = re.search(r"(?:_|\.|-)(\d{1,3})(?:_|\.|-|$)", c)
        if m:
            idx = int(m.group(1))
            if 1 <= idx <= hard_cap:
                max_found = max(max_found, idx)
    # Also ensure we don't go below defaults
    return max(max_found, DEFAULT_MAX_LINES)

def build_detail(df: pd.DataFrame, det_map: dict, hdr_df: pd.DataFrame, issues:list, max_lines:int)->pd.DataFrame:
    if "NumeroLinea" not in det_map:
        raise ValueError("det_map requiere 'NumeroLinea'.")
    if "ENCF" not in hdr_df.columns:
        raise ValueError("Cabecera no contiene ENCF.")
    located = {}
    for dbcol, (src, _) in det_map.items():
        if dbcol in ("ENCF","NumeroLinea"):
            continue
        varmap = find_wide_variants(df.columns, src, max_lines)
        if not varmap:
            issues.append({"Nivel":"Detalle","Campo":dbcol,"Tipo":"NoEncontrado","Detalle":f"Base={src} (1..{max_lines})"})
        located[dbcol] = varmap

    rows = []
    for ridx, row in df.iterrows():
        encf = row.get("ENCF", None) or row.get("eNCF", None)
        if pd.isna(encf) if hasattr(pd, "isna") else encf is None:
            encf = hdr_df.iloc[ridx]["ENCF"] if ridx < len(hdr_df) else None

        indices = set()
        for _, varmap in located.items():
            indices.update(varmap.keys())
        numline_variants = find_wide_variants(df.columns, det_map["NumeroLinea"][0], max_lines)
        if numline_variants:
            indices.update(numline_variants.keys())

        for i in sorted([x for x in indices if 1 <= x <= max_lines]):
            rec = {"ENCF": encf, "NumeroLinea": i}
            for dbcol, varmap in located.items():
                col = varmap.get(i)
                rec[dbcol] = row[col] if col else None
            if i in numline_variants:
                rec["NumeroLinea"] = row[numline_variants[i]]
            rows.append(rec)
    return pd.DataFrame(rows)

def cast_series(s: pd.Series, t: str, issues: list, nivel:str):
    if t.lower() == "char":
        return s.astype(object)
    if t.lower() == "int":
        out = pd.to_numeric(s, errors="coerce").astype("Int64")
        mask = s.notna() & out.isna()
        for _, val in s[mask].items():
            issues.append({"Nivel":nivel,"Campo":s.name,"Tipo":"ParseInt","Detalle":str(val)})
        return out
    if t.lower() == "numeric":
        out = pd.to_numeric(s, errors="coerce")
        mask = s.notna() & out.isna()
        for _, val in s[mask].items():
            issues.append({"Nivel":nivel,"Campo":s.name,"Tipo":"ParseNumeric","Detalle":str(val)})
        return out
    if t.lower() == "date":
        out = pd.to_datetime(s, errors="coerce", dayfirst=True, infer_datetime_format=True)
        mask = s.notna() & out.isna()
        if mask.any():
            out2 = pd.to_datetime(s[mask], errors="coerce", dayfirst=False, infer_datetime_format=True)
            out.loc[mask] = out2
            mask = s.notna() & out.isna()
        for _, val in s[mask].items():
            issues.append({"Nivel":nivel,"Campo":s.name,"Tipo":"ParseDate","Detalle":str(val)})
        return out.dt.date
    if t.lower() == "bit":
        true_set = {"1","true","t","y","yes","si","sí","x"}
        false_set = {"0","false","f","n","no"}
        def to_bit(v):
            if pd.isna(v):
                return None
            s = str(v).strip().lower()
            if s in true_set: return 1
            if s in false_set: return 0
            try:
                return 1 if float(s)!=0 else 0
            except:
                issues.append({"Nivel":nivel,"Campo":s.name if hasattr(s,'name') else 'bit',"Tipo":"ParseBit","Detalle":str(v)})
                return None
        return s.apply(to_bit)
    return s

def cast_dataframe(df: pd.DataFrame, mapping: dict, nivel:str, issues:list)->pd.DataFrame:
    out = df.copy()
    for dbcol, (src, t) in mapping.items():
        colname = dbcol if dbcol in out.columns else ("ENCF" if dbcol.lower()=="encf" else None)
        if colname is None or colname not in out.columns:
            continue
        out[colname] = cast_series(out[colname], t, issues, nivel)
    return out

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ECF Loader – SQL Server (Auto-detect + Logs)")
        self.geometry("980x760")
        self.resizable(True, True)

        self.var_excel = tk.StringVar()
        self.var_conn = tk.StringVar()
        self.var_map = tk.StringVar()
        self.var_ddl = tk.StringVar()
        self.var_sheet = tk.StringVar(value="ECF")

        self.var_autodetect = tk.BooleanVar(value=True)
        self.var_maxlines = tk.IntVar(value=DEFAULT_MAX_LINES)

        top = ttk.Notebook(self)
        self.tab_main = ttk.Frame(top)
        self.tab_logs = ttk.Frame(top)

        top.add(self.tab_main, text="Cargar")
        top.add(self.tab_logs, text="Logs")
        top.pack(fill=tk.BOTH, expand=True)

        # --- Tab main ---
        frm = ttk.Frame(self.tab_main, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        # Row 0
        ttk.Label(frm, text="Archivo Excel:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_excel, width=80).grid(row=0, column=1, sticky="ew")
        ttk.Button(frm, text="...", command=self.pick_excel).grid(row=0, column=2, padx=4)

        # Row 1
        ttk.Label(frm, text="Hoja:").grid(row=1, column=0, sticky="w")
        self.cmb_sheet = ttk.Combobox(frm, textvariable=self.var_sheet, values=["ECF"], state="readonly", width=30)
        self.cmb_sheet.grid(row=1, column=1, sticky="w")

        # Row 2
        ttk.Label(frm, text="Conexión (JSON):").grid(row=2, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_conn, width=80).grid(row=2, column=1, sticky="ew")
        ttk.Button(frm, text="...", command=self.pick_conn).grid(row=2, column=2, padx=4)

        # Row 3
        ttk.Label(frm, text="Mapeo (JSON):").grid(row=3, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_map, width=80).grid(row=3, column=1, sticky="ew")
        ttk.Button(frm, text="...", command=self.pick_map).grid(row=3, column=2, padx=4)

        # Row 4
        ttk.Label(frm, text="DDL (SQL opcional):").grid(row=4, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_ddl, width=80).grid(row=4, column=1, sticky="ew")
        ttk.Button(frm, text="...", command=self.pick_ddl).grid(row=4, column=2, padx=4)

        # Row 5: autodetect
        autodet_frame = ttk.Frame(frm)
        autodet_frame.grid(row=5, column=0, columnspan=3, sticky="w", pady=4)
        ttk.Checkbutton(autodet_frame, text="Auto-detectar máximo de líneas de detalle", variable=self.var_autodetect).pack(side=tk.LEFT)
        ttk.Label(autodet_frame, text="Máximo manual:").pack(side=tk.LEFT, padx=(12,4))
        ttk.Spinbox(autodet_frame, from_=1, to=200, textvariable=self.var_maxlines, width=6).pack(side=tk.LEFT)

        # Row 6: buttons
        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=3, sticky="ew", pady=8)
        ttk.Button(btns, text="Cargar a SQL Server", command=self.run_loader_thread).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Salir", command=self.destroy).pack(side=tk.LEFT, padx=4)

        # Row 7: console
        self.txt = tk.Text(frm, height=18)
        self.txt.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=6)
        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(7, weight=1)

        # --- Tab logs ---
        lfrm = ttk.Frame(self.tab_logs, padding=8)
        lfrm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(lfrm, text="Quality issues").pack(anchor="w")
        self.tree_issues = ttk.Treeview(lfrm, columns=("Nivel","Campo","Tipo","Detalle"), show="headings", height=10)
        for c in ("Nivel","Campo","Tipo","Detalle"):
            self.tree_issues.heading(c, text=c)
            self.tree_issues.column(c, width=160 if c!="Detalle" else 400, stretch=True)
        self.tree_issues.pack(fill=tk.BOTH, expand=True, pady=(0,8))

        ttk.Label(lfrm, text="Unmapped fields").pack(anchor="w")
        self.tree_unmapped = ttk.Treeview(lfrm, columns=("Nivel","Campo"), show="headings", height=6)
        for c in ("Nivel","Campo"):
            self.tree_unmapped.heading(c, text=c)
            self.tree_unmapped.column(c, width=180, stretch=True)
        self.tree_unmapped.pack(fill=tk.BOTH, expand=True)

    def log(self, msg):
        self.txt.insert(tk.END, msg + "\n")
        self.txt.see(tk.END)
        self.update_idletasks()

    def pick_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files","*.xlsx;*.xls")])
        if not path:
            return
        self.var_excel.set(path)
        try:
            xls = pd.ExcelFile(path)
            sheets = xls.sheet_names
            self.cmb_sheet.configure(values=sheets)
            if "ECF" in sheets:
                self.var_sheet.set("ECF")
            elif sheets:
                self.var_sheet.set(sheets[0])
        except Exception as ex:
            messagebox.showerror("Error", f"No pude leer las hojas del Excel:\n{ex}")

    def pick_conn(self):
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if path:
            self.var_conn.set(path)

    def pick_map(self):
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if path:
            self.var_map.set(path)

    def pick_ddl(self):
        path = filedialog.askopenfilename(filetypes=[("SQL","*.sql"),("All","*.*")])
        if path:
            self.var_ddl.set(path)

    def run_loader_thread(self):
        t = threading.Thread(target=self.run_loader, daemon=True)
        t.start()

    def run_loader(self):
        issues = []
        unmapped_rows = []
        try:
            excel = self.var_excel.get().strip()
            sheet = self.var_sheet.get().strip()
            conn_json = self.var_conn.get().strip()
            map_json = self.var_map.get().strip()
            ddl = self.var_ddl.get().strip() or None
            autodetect = self.var_autodetect.get()
            maxlines = int(self.var_maxlines.get() or DEFAULT_MAX_LINES)

            if not (excel and conn_json and map_json and sheet):
                messagebox.showwarning("Faltan datos","Selecciona Excel, hoja, JSON de conexión y JSON de mapeo.")
                return

            self.log("Leyendo configuración de mapeo...")
            hdr_map, det_map = load_mapping(Path(map_json))
            self.log("Leyendo conexión...")
            conn_cfg = json.loads(Path(conn_json).read_text(encoding="utf-8"))
            url = build_conn_url(conn_cfg)

            self.log("Cargando Excel...")
            xls = pd.ExcelFile(excel)
            df = xls.parse(sheet)

            # Autodetect lines if requested
            if autodetect:
                auto_max = autodetect_max_lines(df, det_map, hard_cap=200)
                self.log(f"Auto-detectado máximo de líneas: {auto_max}")
                maxlines = auto_max
            else:
                self.log(f"Máximo de líneas (manual): {maxlines}")

            self.log("Normalizando cabecera...")
            hdr_df = normalize_header(df, hdr_map, issues)
            self.log(f"Cabecera columnas: {list(hdr_df.columns)}  filas={len(hdr_df)}")

            self.log("Construyendo detalle...")
            det_df = build_detail(df, det_map, hdr_df, issues, max_lines=maxlines)
            self.log(f"Detalle columnas: {list(det_df.columns)}  filas={len(det_df)}")

            # Cast/typing
            self.log("Tipificando cabecera...")
            hdr_df = cast_dataframe(hdr_df, hdr_map, "Header", issues)
            self.log("Tipificando detalle...")
            det_df = cast_dataframe(det_df, det_map, "Detalle", issues)

            # Logs
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = Path(excel).parent if os.path.isdir(Path(excel).parent) else Path.cwd()
            log_dir = log_dir / f"logs_ecf_{ts}"
            log_dir.mkdir(exist_ok=True, parents=True)

            if issues:
                issues_df = pd.DataFrame(issues)
                issues_path = log_dir / "quality_issues.csv"
                issues_df.to_csv(issues_path, index=False, encoding="utf-8-sig")
                self.log(f"⚠️ Quality issues: {issues_path} ({len(issues_df)} registros)")
            else:
                self.log("✅ Sin issues de calidad detectados en tipificación.")

            def unmapped(mapping, df_final):
                keys = set(df_final.columns)
                miss = []
                for dbcol in mapping.keys():
                    if dbcol.lower()=="encf":
                        continue
                    if dbcol not in keys:
                        miss.append(dbcol)
                return miss

            unmapped_hdr = unmapped(hdr_map, hdr_df)
            unmapped_det = unmapped(det_map, det_df)
            if unmapped_hdr or unmapped_det:
                unmapped_df = pd.DataFrame(
                    [{"Nivel":"Header","Campo":c} for c in unmapped_hdr] +
                    [{"Nivel":"Detalle","Campo":c} for c in unmapped_det]
                )
                unmapped_path = log_dir / "unmapped_fields.csv"
                unmapped_df.to_csv(unmapped_path, index=False, encoding="utf-8-sig")
                self.log(f"ℹ️ Campos no mapeados: {unmapped_path} ({len(unmapped_df)})")
            else:
                unmapped_df = pd.DataFrame(columns=["Nivel","Campo"])
                self.log("✅ Todos los campos del mapping están presentes tras la normalización.")

            # Populate Logs tab
            self.populate_logs_tab(issues_df if issues else pd.DataFrame(columns=["Nivel","Campo","Tipo","Detalle"]),
                                   unmapped_df)

            # Load to SQL Server
            self.log("Conectando a SQL Server...")
            engine = create_engine(url, fast_executemany=True)

            with engine.begin() as conn:
                if ddl:
                    self.log("Ejecutando DDL...")
                    sql = Path(ddl).read_text(encoding="utf-8")
                    for stmt in [s.strip() for s in sql.split(';') if s.strip()]:
                        conn.execute(text(stmt))

                self.log("Insertando dbo.FEEncabezado...")
                hdr_df.to_sql("FEEncabezado", con=conn, schema="dbo", if_exists="append", index=False)
                self.log("Insertando dbo.FEDetalle...")
                det_df.to_sql("FEDetalle", con=conn, schema="dbo", if_exists="append", index=False)

            self.log("✅ Carga completada.")
            messagebox.showinfo("Éxito", "Carga completada correctamente.\nRevisa la pestaña 'Logs' para ver los detalles.")

        except Exception as ex:
            err = traceback.format_exc()
            self.log("❌ Error:\n" + err)
            messagebox.showerror("Error", str(ex))

    def populate_logs_tab(self, issues_df: pd.DataFrame, unmapped_df: pd.DataFrame):
        # Clear current
        for i in self.tree_issues.get_children():
            self.tree_issues.delete(i)
        for i in self.tree_unmapped.get_children():
            self.tree_unmapped.delete(i)
        # Insert rows
        if not issues_df.empty:
            for _, r in issues_df.iterrows():
                self.tree_issues.insert("", tk.END, values=(r.get("Nivel",""), r.get("Campo",""), r.get("Tipo",""), r.get("Detalle","")))
        if not unmapped_df.empty:
            for _, r in unmapped_df.iterrows():
                self.tree_unmapped.insert("", tk.END, values=(r.get("Nivel",""), r.get("Campo","")))

def autodetect_max_lines(df: pd.DataFrame, det_map: dict, hard_cap=200):
    max_found = 0
    cols = list(map(str, df.columns))
    for c in cols:
        m = re.search(r"(?:_|\.|-)(\d{1,3})(?:_|\.|-|$)", c)
        if m:
            idx = int(m.group(1))
            if 1 <= idx <= hard_cap:
                max_found = max(max_found, idx)
    return max_found if max_found>0 else DEFAULT_MAX_LINES

def cast_dataframe(df: pd.DataFrame, mapping: dict, nivel:str, issues:list)->pd.DataFrame:
    out = df.copy()
    for dbcol, (src, t) in mapping.items():
        colname = dbcol if dbcol in out.columns else ("ENCF" if dbcol.lower()=="encf" else None)
        if colname is None or colname not in out.columns:
            continue
        out[colname] = cast_series(out[colname], t, issues, nivel)
    return out

def cast_series(s: pd.Series, t: str, issues: list, nivel:str):
    if t.lower() == "char":
        return s.astype(object)
    if t.lower() == "int":
        out = pd.to_numeric(s, errors="coerce").astype("Int64")
        mask = s.notna() & out.isna()
        for _, val in s[mask].items():
            issues.append({"Nivel":nivel,"Campo":s.name,"Tipo":"ParseInt","Detalle":str(val)})
        return out
    if t.lower() == "numeric":
        out = pd.to_numeric(s, errors="coerce")
        mask = s.notna() & out.isna()
        for _, val in s[mask].items():
            issues.append({"Nivel":nivel,"Campo":s.name,"Tipo":"ParseNumeric","Detalle":str(val)})
        return out
    if t.lower() == "date":
        out = pd.to_datetime(s, errors="coerce", dayfirst=True, infer_datetime_format=True)
        mask = s.notna() & out.isna()
        if mask.any():
            out2 = pd.to_datetime(s[mask], errors="coerce", dayfirst=False, infer_datetime_format=True)
            out.loc[mask] = out2
            mask = s.notna() & out.isna()
        for _, val in s[mask].items():
            issues.append({"Nivel":nivel,"Campo":s.name,"Tipo":"ParseDate","Detalle":str(val)})
        return out.dt.date
    if t.lower() == "bit":
        true_set = {"1","true","t","y","yes","si","sí","x"}
        false_set = {"0","false","f","n","no"}
        def to_bit(v):
            if pd.isna(v):
                return None
            s = str(v).strip().lower()
            if s in true_set: return 1
            if s in false_set: return 0
            try:
                return 1 if float(s)!=0 else 0
            except:
                issues.append({"Nivel":nivel,"Campo":s.name if hasattr(s,'name') else 'bit',"Tipo":"ParseBit","Detalle":str(v)})
                return None
        return s.apply(to_bit)
    return s

if __name__ == "__main__":
    App().mainloop()
