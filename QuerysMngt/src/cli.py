import os, sys, argparse, csv
from datetime import datetime
from sqlalchemy import create_engine, text

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from src.common_config import get_effective_config, make_conn_str
from src.common_audit import log_event

def make_engine(profile: str | None):
    cfg = get_effective_config(profile)
    return create_engine(make_conn_str(cfg), fast_executemany=True)

def cmd_test_conn(args):
    try:
        engine = make_engine(args.profile)
        with engine.connect() as conn: conn.exec_driver_sql("SELECT 1")
        log_event("CLI","TEST_CONN", args.profile or "default", "OK")
        print("OK: conexión exitosa")
    except Exception as e:
        log_event("CLI","TEST_CONN_FAIL", args.profile or "default", str(e))
        print("ERROR:", e); sys.exit(1)

def cmd_list_procs(args):
    engine = make_engine(args.profile)
    with engine.connect() as conn:
        rs = conn.execute(text("""
            SELECT s.name AS SchemaName, p.name AS ProcedureName
            FROM sys.procedures p
            INNER JOIN sys.schemas s ON p.schema_id = s.schema_id
            WHERE p.is_ms_shipped=0
            ORDER BY s.name, p.name
        """))
        for sname, pname in rs.fetchall():
            print(f"{sname}.{pname}")

def cmd_list_views(args):
    engine = make_engine(args.profile)
    with engine.connect() as conn:
        rs = conn.execute(text("""
            SELECT s.name AS SchemaName, v.name AS ViewName
            FROM sys.views v
            INNER JOIN sys.schemas s ON v.schema_id = s.schema_id
            ORDER BY s.name, v.name
        """))
        for sname, vname in rs.fetchall():
            print(f"{sname}.{vname}")

def cmd_exec_sp(args):
    engine = make_engine(args.profile)
    stmt = text(f"""
        EXEC {args.sp}
            @RNCEmisor = :rnc,
            @ENCF = :encf,
            @Numero = :numero,
            @Tipo = :tipo,
            @Desde = :desde,
            @Hasta = :hasta
    """ )
    params = {
        "rnc": args.rnc, "encf": args.encf, "numero": args.numero, "tipo": args.tipo,
        "desde": args.desde, "hasta": args.hasta
    }
    with engine.connect() as conn:
        rs = conn.execute(stmt, params)
        rows = rs.fetchall(); cols = list(rs.keys())
    log_event("CLI","EXEC_SP", args.sp, f"rows={len(rows)} params={params}")
    if args.out:
        out = args.out
        if out.lower().endswith(".xlsx"):
            import xlsxwriter
            wb = xlsxwriter.Workbook(out); ws = wb.add_worksheet("Resultados")
            for j,c in enumerate(cols): ws.write(0,j,c)
            for i,row in enumerate(rows, start=1):
                for j,val in enumerate(row): ws.write(i,j, "" if val is None else str(val))
            wb.close()
        else:
            with open(out, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f); writer.writerow(cols)
                for r in rows: writer.writerow([("" if v is None else str(v)) for v in r])
        print(f"Archivo exportado: {out}")
    else:
        print(",".join(cols))
        for r in rows: print(",".join([("" if v is None else str(v)) for v in r]))

def cmd_import_procs(args):
    import sqlite3
    DATA_DIR = os.path.join(project_root, "data"); os.makedirs(DATA_DIR, exist_ok=True)
    SQLITE_PATH = os.path.join(DATA_DIR, "procedimientos.db")
    conn_sqlite = sqlite3.connect(SQLITE_PATH); cur = conn_sqlite.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Procedimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            descripcion TEXT,
            codigo TEXT
        )
    """) ; cur.execute("""
        CREATE TABLE IF NOT EXISTS ProcedimientoHistorial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            procedimiento_nombre TEXT,
            version INTEGER,
            fecha TEXT,
            codigo TEXT
        )
    """ )
    engine = make_engine(args.profile)
    total=ok=fail=0
    with engine.connect() as conn:
        if args.all:
            rs = conn.execute(text("""
                SELECT s.name AS schema_name, p.name AS proc_name
                FROM sys.procedures p
                INNER JOIN sys.schemas s ON p.schema_id=s.schema_id
                WHERE p.is_ms_shipped=0
                ORDER BY s.name, p.name
            """))
            procs = rs.fetchall()
        else:
            if not args.name: print("--name es requerido si no usa --all"); sys.exit(2)
            schema, name = (args.name.split(".",1)+[""])[:2]
            if not name: print("Nombre debe ser schema.name"); sys.exit(2)
            procs = [(schema, name)]
        total = len(procs)
        for schema, name in procs:
            try:
                rs2 = conn.execute(text("SELECT sm.definition FROM sys.sql_modules sm INNER JOIN sys.objects so ON sm.object_id=so.object_id INNER JOIN sys.schemas s ON s.schema_id=so.schema_id WHERE so.type IN ('P','PC') AND so.name=:n AND s.name=:s"),
                                   {"n": name, "s": schema})
                row = rs2.fetchone(); code = row[0] if row and row[0] else ""
                cur.execute("INSERT OR REPLACE INTO Procedimientos (id, nombre, descripcion, codigo) VALUES ((SELECT id FROM Procedimientos WHERE nombre=?), ?, ?, ?)",
                            (f"{schema}.{name}", f"{schema}.{name}", "", code))
                cur.execute("SELECT COALESCE(MAX(version),0) FROM ProcedimientoHistorial WHERE procedimiento_nombre=?", (f"{schema}.{name}",))
                next_ver = (cur.fetchone()[0] or 0) + 1
                cur.execute("INSERT INTO ProcedimientoHistorial (procedimiento_nombre, version, fecha, codigo) VALUES (?,?,?,?)",
                            (f"{schema}.{name}", next_ver, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), code))
                ok += 1
            except Exception as e:
                fail += 1
    conn_sqlite.commit(); conn_sqlite.close()
    log_event("CLI","IMPORT_PROCS","", f"OK={ok} FAIL={fail} TOTAL={total}")
    print(f"Total: {total} OK:{ok} FAIL:{fail}")

def cmd_sync_procs(args):
    import sqlite3
    DATA_DIR = os.path.join(project_root, "data"); SQLITE_PATH = os.path.join(DATA_DIR, "procedimientos.db")
    conn_sqlite = sqlite3.connect(SQLITE_PATH); cur = conn_sqlite.cursor()
    engine = make_engine(args.profile)
    ok=0; fail=0; total=0
    with engine.connect() as conn:
        cur.execute("SELECT nombre, codigo FROM Procedimientos ORDER BY nombre"); rows = cur.fetchall(); total=len(rows)
        for nombre, codigo in rows:
            if not codigo: continue
            sql = codigo
            try:
                if args.dry_run:
                    conn.exec_driver_sql("SET NOEXEC ON; " + sql + "; SET NOEXEC OFF;")
                else:
                    conn.exec_driver_sql(sql)
                ok+=1
            except Exception as e:
                fail+=1
                if args.dry_run:
                    try: conn.exec_driver_sql("SET NOEXEC OFF;")
                    except Exception: pass
                if args.stop_first:
                    break
    conn_sqlite.close()
    log_event("CLI","SYNC_PROCS", "apply" if not args.dry_run else "dry-run", f"OK={ok} FAIL={fail} TOTAL={total}")
    print(f"OK:{ok} FAIL:{fail} TOTAL:{total}")

def main():
    ap = argparse.ArgumentParser(description="DGII Toolkit CLI (v5.0)")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("test-conn"); p.add_argument("--profile"); p.set_defaults(func=cmd_test_conn)
    p = sub.add_parser("list-procs"); p.add_argument("--profile"); p.set_defaults(func=cmd_list_procs)
    p = sub.add_parser("list-views"); p.add_argument("--profile"); p.set_defaults(func=cmd_list_views)

    p = sub.add_parser("exec-sp")
    p.add_argument("--profile"); p.add_argument("--sp", required=True)
    p.add_argument("--rnc"); p.add_argument("--encf"); p.add_argument("--numero"); p.add_argument("--tipo")
    p.add_argument("--desde"); p.add_argument("--hasta")
    p.add_argument("--out", help="ruta de salida .csv o .xlsx")
    p.set_defaults(func=cmd_exec_sp)

    p = sub.add_parser("import-procs")
    p.add_argument("--profile"); g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true"); g.add_argument("--name")
    p.set_defaults(func=cmd_import_procs)

    p = sub.add_parser("sync-procs")
    p.add_argument("--profile"); p.add_argument("--dry-run", action="store_true"); p.add_argument("--stop-first", action="store_true")
    p.set_defaults(func=cmd_sync_procs)

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help(); sys.exit(0)
    args.func(args)

if __name__ == "__main__":
    main()