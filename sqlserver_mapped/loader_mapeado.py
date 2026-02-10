# -*- coding: utf-8 -*-
import json, re, argparse
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

def sql_name(s):
    import re
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:120] if s else "col"

def build_conn_url(conn_cfg: dict)->str:
    # Build a SQLAlchemy URL for mssql+pyodbc
    # Supports trusted_connection or user/pass
    from urllib.parse import quote_plus
    driver = conn_cfg.get("driver", "ODBC Driver 17 for SQL Server")
    if conn_cfg.get("trusted_connection"):
        params = f"Driver={driver};Server={conn_cfg['server']};Database={conn_cfg['database']};Trusted_Connection=yes;"
    else:
        params = f"Driver={driver};Server={conn_cfg['server']};Database={conn_cfg['database']};UID={conn_cfg['username']};PWD={conn_cfg['password']};"
    if conn_cfg.get("query"):
        # append extra options
        for k,v in conn_cfg["query"].items():
            params += f"{k}={v};"
    return f"mssql+pyodbc:///?odbc_connect={quote_plus(params)}"

def load_mapping(path: Path):
    m = json.loads(path.read_text(encoding="utf-8"))
    return m["csv"]["FEEncabezado"], m["csv"]["FEDetalle"]

def normalize_header(df: pd.DataFrame, hdr_map: dict)->pd.DataFrame:
    # hdr_map: {dbcol: [source_name, type]}
    out = pd.DataFrame()
    for dbcol, (src, _) in hdr_map.items():
        colname = "ENCF" if dbcol.lower()=="encf" or src.lower()=="encf" else dbcol
        if src in df.columns:
            out[colname] = df[src]
        else:
            # If not found, try a few relaxed matches
            candidates = [c for c in df.columns if c.lower() == src.lower()]
            if candidates:
                out[colname] = df[candidates[0]]
            else:
                out[colname] = None
    # ENCF is required
    if "ENCF" not in out.columns:
        raise ValueError("No se encontró ENCF en cabecera tras el mapeo.")
    return out

def find_wide_variants(df_columns, base):
    """Return a dict index->column_name for patterns base_{i}, base.i, base-i, base{i} up to 62"""
    cols = list(map(str, df_columns))
    variants = {}
    for i in range(1, 63):
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

def build_detail(df: pd.DataFrame, det_map: dict, hdr_df: pd.DataFrame)->pd.DataFrame:
    # det_map: {dbcol: [source_name, type]}
    # We expect NumeroLinea present in det_map
    if "NumeroLinea" not in det_map:
        raise ValueError("det_map requiere 'NumeroLinea'.")
    # ENCF must come from header
    if "ENCF" not in hdr_df.columns:
        raise ValueError("Cabecera no contiene ENCF.")

    # For each db field in det_map, try to locate wide variants across 1..62
    located = {}
    for dbcol, (src, _) in det_map.items():
        if dbcol in ("ENCF","NumeroLinea"):
            continue
        located[dbcol] = find_wide_variants(df.columns, src)

    rows = []
    for ridx, row in df.iterrows():
        encf = row.get("ENCF", None) or row.get("eNCF", None)
        if pd.isna(encf):
            # try mapped header version
            encf = hdr_df.iloc[ridx]["ENCF"] if ridx < len(hdr_df) else None
        # Determine which line numbers exist: union of indices found across all fields
        indices = set()
        for _, varmap in located.items():
            indices.update(varmap.keys())
        # If NumeroLinea_* pattern exists, prefer those
        numline_variants = find_wide_variants(df.columns, det_map["NumeroLinea"][0])
        if numline_variants:
            indices.update(numline_variants.keys())
        # Build row per index
        for i in sorted([x for x in indices if 1 <= x <= 62]):
            rec = {"ENCF": encf, "NumeroLinea": i}
            # assign fields
            for dbcol, varmap in located.items():
                col = varmap.get(i)
                if col:
                    rec[dbcol] = row[col]
                else:
                    rec[dbcol] = None
            # NumeroLinea explicit column variant? overwrite with value if present
            if i in numline_variants:
                rec["NumeroLinea"] = row[numline_variants[i]]
            rows.append(rec)
    return pd.DataFrame(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", required=True)
    ap.add_argument("--sheet", default="ECF")
    ap.add_argument("--conn-json", required=True)       # path to conn_sqlserver.json
    ap.add_argument("--map-json", required=True)        # path to datadefCarga.json
    ap.add_argument("--ddl", required=False)            # optional DDL to run
    args = ap.parse_args()

    hdr_map, det_map = load_mapping(Path(args.map_json))
    conn_cfg = json.loads(Path(args.conn_json).read_text(encoding="utf-8"))
    url = build_conn_url(conn_cfg)

    xls = pd.ExcelFile(args.excel)
    df = xls.parse(args.sheet)
    hdr_df = normalize_header(df, hdr_map)
    det_df = build_detail(df, det_map, hdr_df)

    from sqlalchemy import create_engine
    engine = create_engine(url, fast_executemany=True)

    with engine.begin() as conn:
        if args.ddl:
            sql = Path(args.ddl).read_text(encoding="utf-8")
            # naive split; SQL Server tolerates batched executes via text()
            for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
                conn.execute(text(stmt))
        # load
        hdr_df.to_sql("FEEncabezado", con=conn, schema="dbo", if_exists="append", index=False)
        det_df.to_sql("FEDetalle", con=conn, schema="dbo", if_exists="append", index=False)

if __name__ == "__main__":
    main()
