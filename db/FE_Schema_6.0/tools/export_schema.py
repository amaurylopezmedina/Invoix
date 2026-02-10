
import os
import json
from db.uDB import ConectarDB

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TABLES_DIR = os.path.join(BASE_DIR, "tables")
VIEWS_DIR = os.path.join(BASE_DIR, "views")
PROCS_DIR = os.path.join(BASE_DIR, "procs")

def _ensure_dirs():
    os.makedirs(TABLES_DIR, exist_ok=True)
    os.makedirs(VIEWS_DIR, exist_ok=True)
    os.makedirs(PROCS_DIR, exist_ok=True)

def export_schema(ambiente: str = "DEV"):
    """Exporta el esquema actual SQL Server a JSON compatible con el Schema Manager."""
    _ensure_dirs()
    cn = ConectarDB(ambiente)
    cur = cn.cursor

    # Export tablas: por simplicidad, solo nombre + schema
    cur.execute("""
        SELECT t.name, s.name
        FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id
    """)
    for table, schema in cur.fetchall():
        j = {
            "table": table,
            "schema": schema,
            "description": f"Exportado desde {ambiente}",
            "fields": {}
        }
        # Columnas
        cur_cols = cn.connection.cursor()
        cur_cols.execute("""
            SELECT c.name, TYPE_NAME(c.user_type_id) AS type_name, c.max_length, c.precision, c.scale,
                   c.is_nullable, c.column_id
            FROM sys.columns c
            JOIN sys.tables t ON c.object_id = t.object_id
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE t.name = ? AND s.name = ?
            ORDER BY c.column_id
        """, (table, schema))
        for cname, tname, maxlen, prec, scale, is_null, colid in cur_cols.fetchall():
            # tipo simple
            if tname.lower() in ("varchar", "nvarchar", "char", "nchar", "binary", "varbinary"):
                if maxlen == -1:
                    tipo = f"{tname}(max)"
                else:
                    tipo = f"{tname}({maxlen})"
            elif tname.lower() in ("decimal", "numeric"):
                tipo = f"{tname}({prec},{scale})"
            else:
                tipo = tname
            j["fields"][cname] = {
                "type": tipo,
                "nullable": bool(is_null),
                "identity": False,
                "default": None,
                "description": f"Campo {cname} de {table}"
            }

        path = os.path.join(TABLES_DIR, f"{table}.table.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(j, f, indent=2, ensure_ascii=False)

    # Vistas y SP podrían añadirse aquí de forma similar.
    return True
