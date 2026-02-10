import glob
import json
import os
import re
import traceback
import uuid
from configparser import ConfigParser
from datetime import datetime

import pyodbc

# Hook opcional para UI
try:
    from ui.log_window import ui_log  # type: ignore
except Exception:
    ui_log = None

# ------------------------------------------------------------
#  Flags globales
# ------------------------------------------------------------
DRY_RUN = False
AMBIENTE = "DEV"  # se setea desde UI/CLI
AMBiente = AMBIENTE  # compat
SCHEMA_VERSION = 1  # incrementa cuando cambies el paquete de esquema
RUN_ID = str(uuid.uuid4())  # agrupa eventos de una misma ejecución


# ------------------------------------------------------------
#  Logger simple (stdout). Si tienes glib.logG, se usa.
# ------------------------------------------------------------
try:
    from glib.log_g import log_event, setup_logger  # type: ignore

    _logger = setup_logger("schema_manager.log")

    def _log(level: str, msg: str):
        log_event(_logger, level, msg)
        if ui_log:
            ui_log(f"[{level.upper()}] {msg}")

except Exception:
    _logger = None

    def _log(level: str, msg: str):
        line = f"[{level.upper()}] {msg}"
        print(line)
        if ui_log:
            ui_log(line)


# ------------------------------------------------------------
#  Auditoría (tabla) - se crea automáticamente
# ------------------------------------------------------------
AUDIT_TABLE = "dbo.SchemaAudit"


def ensure_audit_table(cursor):
    # Crea la tabla si no existe y asegura columnas nuevas (versionado + usuario/host/app)
    sql_create = f"""
IF OBJECT_ID('{AUDIT_TABLE}', 'U') IS NULL
BEGIN
    CREATE TABLE {AUDIT_TABLE}(
        Id              INT IDENTITY(1,1) PRIMARY KEY,
        run_id          UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
        schema_version  INT NOT NULL DEFAULT (1),
        applied_at      DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        ambiente        VARCHAR(10)  NULL,
        object_type     VARCHAR(20)  NOT NULL,
        object_name     NVARCHAR(256) NOT NULL,
        action          VARCHAR(30)  NOT NULL,
        status          VARCHAR(10)  NOT NULL,
        sql_text        NVARCHAR(MAX) NULL,
        old_def         NVARCHAR(MAX) NULL,
        new_def         NVARCHAR(MAX) NULL,
        error_text      NVARCHAR(MAX) NULL,
        sql_user        NVARCHAR(128) NULL DEFAULT ORIGINAL_LOGIN(),
        host_name       NVARCHAR(128) NULL DEFAULT HOST_NAME(),
        app_name        NVARCHAR(128) NULL DEFAULT PROGRAM_NAME()
    );
END
"""
    _exec(
        cursor,
        sql_create,
        object_type="system",
        object_name=AUDIT_TABLE,
        action="ensure_audit_table",
    )

    # Asegurar columnas si la tabla ya existía de versiones anteriores
    col_sql = f"""
IF COL_LENGTH('{AUDIT_TABLE}', 'run_id') IS NULL
    ALTER TABLE {AUDIT_TABLE} ADD run_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_SchemaAudit_run_id DEFAULT NEWID();
IF COL_LENGTH('{AUDIT_TABLE}', 'schema_version') IS NULL
    ALTER TABLE {AUDIT_TABLE} ADD schema_version INT NOT NULL CONSTRAINT DF_SchemaAudit_schema_version DEFAULT (1);
IF COL_LENGTH('{AUDIT_TABLE}', 'sql_user') IS NULL
    ALTER TABLE {AUDIT_TABLE} ADD sql_user NVARCHAR(128) NULL CONSTRAINT DF_SchemaAudit_sql_user DEFAULT ORIGINAL_LOGIN();
IF COL_LENGTH('{AUDIT_TABLE}', 'host_name') IS NULL
    ALTER TABLE {AUDIT_TABLE} ADD host_name NVARCHAR(128) NULL CONSTRAINT DF_SchemaAudit_host_name DEFAULT HOST_NAME();
IF COL_LENGTH('{AUDIT_TABLE}', 'app_name') IS NULL
    ALTER TABLE {AUDIT_TABLE} ADD app_name NVARCHAR(128) NULL CONSTRAINT DF_SchemaAudit_app_name DEFAULT PROGRAM_NAME();
"""
    _exec(
        cursor,
        col_sql,
        object_type="system",
        object_name=AUDIT_TABLE,
        action="ensure_audit_columns",
    )


def audit(
    cursor,
    object_type: str,
    object_name: str,
    action: str,
    status: str,
    sql_text: str | None = None,
    old_def: str | None = None,
    new_def: str | None = None,
    error_text: str | None = None,
):
    """
    Registra auditoría en dbo.SchemaAudit.
    Incluye: run_id (agrupa una ejecución), schema_version, ambiente, y defaults SQL para user/host/app.
    """
    if DRY_RUN:
        _log(
            "info", f"[DRY-RUN][AUDIT] {object_type} {object_name} {action} ({status})"
        )
        return

    try:
        cursor.execute(
            f"INSERT INTO {AUDIT_TABLE}(run_id, schema_version, ambiente, object_type, object_name, action, status, sql_text, old_def, new_def, error_text) "
            f"VALUES (CONVERT(uniqueidentifier, ?), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                RUN_ID,
                SCHEMA_VERSION,
                AMBIENTE,
                object_type,
                object_name,
                action,
                status,
                sql_text,
                old_def,
                new_def,
                error_text,
            ),
        )
    except Exception as e:
        # No romper instalación si la auditoría falla
        _log("error", f"[AUDIT FAIL] {e}")


# ------------------------------------------------------------
#  Helpers para conexión / cn_*.ini
# ------------------------------------------------------------
def _project_root() -> str:
    # schema_manager.py está en la raíz del proyecto de schema
    return os.path.dirname(os.path.abspath(__file__))


def load_connection_string(ambiente: str) -> str:
    cfg = ConfigParser()
    fname = f"cn_{ambiente.lower()}.ini"
    path = os.path.join(_project_root(), "config", fname)
    if not os.path.exists(path):
        raise FileNotFoundError(f"No existe {path}")
    cfg.read(path, encoding="utf-8")
    conn = cfg.get("database", "connection_string", fallback=None)
    if not conn:
        raise ValueError(f"No se encontró connection_string en {path}")
    return conn


def _get_database_name(conn_str: str) -> str | None:
    # soporta "Database=XXX" o "Initial Catalog=XXX"
    m = re.search(r"(?:Database|Initial Catalog)\s*=\s*([^;]+)", conn_str, re.I)
    return m.group(1).strip() if m else None


def _set_database_name(conn_str: str, dbname: str) -> str:
    # reemplaza Database= o Initial Catalog=; si no existe, agrega Database=
    if re.search(r"(Database|Initial Catalog)\s*=", conn_str, re.I):
        conn_str = re.sub(
            r"(Database|Initial Catalog)\s*=\s*[^;]+",
            f"Database={dbname}",
            conn_str,
            flags=re.I,
        )
    else:
        if not conn_str.endswith(";"):
            conn_str += ";"
        conn_str += f"Database={dbname};"
    return conn_str


def ensure_database_exists(conn_str: str):
    dbname = _get_database_name(conn_str)
    if not dbname:
        raise ValueError(
            "El connection_string no incluye Database=... o Initial Catalog=..."
        )
    master_conn = _set_database_name(conn_str, "master")
    cn = pyodbc.connect(master_conn, autocommit=True, timeout=5)
    cur = cn.cursor()
    ensure_audit_table(cur)
    sql = f"IF DB_ID(N'{dbname}') IS NULL CREATE DATABASE [{dbname}];"
    _log("info", f"Asegurando base de datos: {dbname}")
    _exec(
        cur, sql, object_type="database", object_name=dbname, action="create_if_missing"
    )
    cur.close()
    cn.close()


def connect(ambiente: str):
    """
    Conecta a SQL Server.
    Si existe db.uDB.ConectarDB en tu repo, lo usa; si no, usa pyodbc directo.
    """
    global AMBiente
    AMBIENTE = ambiente
    AMBiente = AMBIENTE.upper()

    conn_str = load_connection_string(AMBiente)
    ensure_database_exists(conn_str)

    # Preferir tu clase ConectarDB si está disponible (ASESYS)
    try:
        from db.uDB import ConectarDB as AseConectarDB  # type: ignore

        db = (
            AseConectarDB(AMBiente)
            if "ambiente" in AseConectarDB.__init__.__code__.co_varnames
            else AseConectarDB()
        )
        return db.connection, db.cursor
    except Exception:
        cn = pyodbc.connect(conn_str, autocommit=True, timeout=5)
        cur = cn.cursor()
        return cn, cur


# ------------------------------------------------------------
#  Comparador inteligente vs sys.columns
# ------------------------------------------------------------
def _norm_type(sql_type: str) -> str:
    return sql_type.strip().lower()


def _expected_sql_type(meta: dict) -> str:
    t = meta["type"].strip().lower()
    if t in ("varchar", "nvarchar", "char", "nchar", "binary", "varbinary"):
        length = meta.get("length")
        if length is None:
            raise ValueError(f"Tipo {t} requiere length")
        if isinstance(length, str) and length.lower() == "max":
            return f"{t}(max)"
        return f"{t}({int(length)})"
    if t in ("decimal", "numeric"):
        p = meta.get("precision")
        s = meta.get("scale")
        if p is None or s is None:
            raise ValueError("decimal/numeric requiere precision y scale")
        return f"{t}({int(p)},{int(s)})"
    if t in ("datetime2",):
        prec = meta.get("scale")
        return f"datetime2({int(prec)})" if prec is not None else "datetime2"
    # int, bit, date, datetime, text, etc.
    return t


def _get_existing_columns(cursor, schema: str, table: str) -> dict:
    sql = """
SELECT
    c.name AS col_name,
    t.name AS type_name,
    c.max_length,
    c.precision,
    c.scale,
    c.is_nullable,
    c.is_identity,
    dc.definition AS default_definition
FROM sys.columns c
JOIN sys.types t ON c.user_type_id = t.user_type_id
LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
WHERE c.object_id = OBJECT_ID(?, 'U')
"""
    cursor.execute(sql, (f"{schema}.{table}",))
    rows = cursor.fetchall()
    cols = {}
    for r in rows:
        cols[r.col_name] = {
            "type_name": r.type_name,
            "max_length": r.max_length,
            "precision": r.precision,
            "scale": r.scale,
            "is_nullable": bool(r.is_nullable),
            "is_identity": bool(r.is_identity),
            "default_definition": r.default_definition,
        }
    return cols


def _render_existing_type(ex: dict) -> str:
    t = ex["type_name"].lower()
    if t in ("varchar", "nvarchar", "char", "nchar", "binary", "varbinary"):
        ml = ex["max_length"]
        # nvarchar/nchar stores bytes => divide by 2
        if t in ("nvarchar", "nchar") and ml not in (-1, None):
            ml = int(ml) // 2
        if ml == -1:
            return f"{t}(max)"
        return f"{t}({int(ml)})"
    if t in ("decimal", "numeric"):
        return f"{t}({int(ex['precision'])},{int(ex['scale'])})"
    return t


def compare_column(
    cursor, schema: str, table: str, col: str, meta: dict
) -> tuple[bool, str | None, str | None, str | None]:
    """
    Returns: (needs_change, action, old_def, new_def)
    action: 'add' | 'alter' | 'skip'
    """
    existing = _get_existing_columns(cursor, schema, table)
    if col not in existing:
        new_type = _expected_sql_type(meta)
        null_sql = "NULL" if meta.get("nullable", True) else "NOT NULL"
        return True, "add", None, f"{new_type} {null_sql}"
    ex = existing[col]
    old_type = _render_existing_type(ex)
    new_type = _expected_sql_type(meta)

    old_null = "NULL" if ex["is_nullable"] else "NOT NULL"
    new_null = "NULL" if meta.get("nullable", True) else "NOT NULL"

    # identidad no puede alterarse fácilmente
    if ex["is_identity"] != bool(meta.get("identity", False)):
        return (
            False,
            "skip",
            f"{old_type} {old_null} IDENTITY={ex['is_identity']}",
            f"{new_type} {new_null} IDENTITY={meta.get('identity', False)}",
        )

    if _norm_type(old_type) != _norm_type(new_type) or old_null != new_null:
        return True, "alter", f"{old_type} {old_null}", f"{new_type} {new_null}"

    return False, "skip", f"{old_type} {old_null}", f"{new_type} {new_null}"


# ------------------------------------------------------------
#  Exec wrapper (con auditoría y dry-run)
# ------------------------------------------------------------
def _exec(
    cursor,
    sql: str,
    object_type: str,
    object_name: str,
    action: str,
    old_def: str | None = None,
    new_def: str | None = None,
):
    sql_clean = sql.strip()
    if not sql_clean:
        return
    if DRY_RUN:
        _log("info", f"[DRY-RUN] {action} {object_type} {object_name}\n{sql_clean}\n")
        return
    try:
        cursor.execute(sql_clean)
        # limpiar resultsets por seguridad
        try:
            while cursor.nextset():
                pass
        except Exception:
            pass
        audit(
            cursor,
            object_type,
            object_name,
            action,
            "OK",
            sql_clean,
            old_def,
            new_def,
            None,
        )
        _log("info", f"OK: {action} {object_type} {object_name}")
    except Exception as e:
        err = f"{e}\n{traceback.format_exc()}"
        try:
            audit(
                cursor,
                object_type,
                object_name,
                action,
                "FAIL",
                sql_clean,
                old_def,
                new_def,
                err,
            )
        except Exception:
            pass
        _log("error", f"FAIL: {action} {object_type} {object_name} -> {e}")
        raise


# ------------------------------------------------------------
#  JSON Validators (básico, extendible)
# ------------------------------------------------------------
def validate_table_json(cfg: dict) -> list[str]:
    errors = []
    if cfg.get("table") is None:
        errors.append("Falta 'table'")
    fields = cfg.get("fields")
    if not isinstance(fields, dict) or not fields:
        errors.append("Falta 'fields' o está vacío")
        return errors

    for col, meta in fields.items():
        if "type" not in meta:
            errors.append(f"{col}: falta 'type'")
            continue
        t = meta["type"].lower()
        if (
            t in ("varchar", "nvarchar", "char", "nchar", "binary", "varbinary")
            and meta.get("length") is None
        ):
            errors.append(f"{col}: {t} requiere 'length'")
        if t in ("decimal", "numeric") and (
            meta.get("precision") is None or meta.get("scale") is None
        ):
            errors.append(f"{col}: {t} requiere 'precision' y 'scale'")
    return errors


def validate_ddl_json(cfg: dict) -> list[str]:
    errors = []
    if cfg.get("ddl") is None:
        errors.append("Falta 'ddl'")
    if cfg.get("name") is None:
        errors.append("Falta 'name'")
    if cfg.get("type") not in ("view", "proc", "function", "ddl"):
        errors.append("type inválido (esperado: view/proc/function/ddl)")
    return errors


# ------------------------------------------------------------
#  Apply: Tables / Views / Procs
# ------------------------------------------------------------
def ensure_table_exists(cursor, schema: str, table: str, cfg: dict):
    sql = f"IF OBJECT_ID('{schema}.{table}', 'U') IS NULL SELECT 0 ELSE SELECT 1"
    cursor.execute(sql)
    exists = cursor.fetchone()[0] == 1
    if exists:
        return

    # Crear tabla completa (sin PK/constraints avanzadas por ahora)
    cols_sql = []
    for col, meta in cfg["fields"].items():
        col_type = _expected_sql_type(meta)
        # Si la columna es IDENTITY, forzamos NOT NULL (SQL Server no permite IDENTITY NULL)
        if meta.get("identity", False):
            null_sql = "NOT NULL"
        else:
            null_sql = "NULL" if meta.get("nullable", True) else "NOT NULL"
        identity = " IDENTITY(1,1)" if meta.get("identity", False) else ""
        cols_sql.append(f"[{col}] {col_type}{identity} {null_sql}")
    create_sql = (
        f"CREATE TABLE [{schema}].[{table}] (\n  " + ",\n  ".join(cols_sql) + "\n);"
    )
    _exec(
        cursor,
        create_sql,
        object_type="table",
        object_name=f"{schema}.{table}",
        action="create",
    )


def apply_table(cursor, cfg: dict):
    schema = cfg.get("schema", "dbo")
    table = cfg["table"]

    errs = validate_table_json(cfg)
    if errs:
        raise ValueError(
            f"JSON inválido para tabla {schema}.{table}:\n- " + "\n- ".join(errs)
        )

    ensure_table_exists(cursor, schema, table, cfg)

    # Comparar vs sys.columns (inteligente)
    for col, meta in cfg["fields"].items():
        needs, action, old_def, new_def = compare_column(
            cursor, schema, table, col, meta
        )
        if not needs:
            if (
                action == "skip"
                and old_def
                and new_def
                and "IDENTITY" in (old_def + new_def)
            ):
                _log(
                    "warning",
                    f"Saltando cambio de IDENTITY en {schema}.{table}.{col}. Requiere rebuild de columna.",
                )
            continue

        if action == "add":
            sql = f"ALTER TABLE [{schema}].[{table}] ADD [{col}] {new_def};"
            _exec(
                cursor,
                sql,
                object_type="column",
                object_name=f"{schema}.{table}.{col}",
                action="add_column",
                old_def=old_def,
                new_def=new_def,
            )
        elif action == "alter":
            # Nota: cambiar NULL/NOT NULL puede fallar si hay datos incompatibles.
            sql = f"ALTER TABLE [{schema}].[{table}] ALTER COLUMN [{col}] {new_def};"
            _exec(
                cursor,
                sql,
                object_type="column",
                object_name=f"{schema}.{table}.{col}",
                action="alter_column",
                old_def=old_def,
                new_def=new_def,
            )


def apply_ddl(cursor, cfg: dict):
    errs = validate_ddl_json(cfg)
    if errs:
        raise ValueError(
            f"JSON DDL inválido ({cfg.get('name','(sin nombre)')}):\n- "
            + "\n- ".join(errs)
        )

    obj_type = cfg["type"]
    schema = cfg.get("schema", "dbo")
    name = cfg["name"]
    ddl = cfg["ddl"].strip()

    # replace => drop + create (vistas/SP)
    exec_mode = cfg.get("execution", "replace").lower()
    full_name = f"{schema}.{name}"

    if exec_mode == "replace":
        if obj_type == "view":
            drop = (
                f"IF OBJECT_ID('{full_name}', 'V') IS NOT NULL DROP VIEW {full_name};"
            )
        elif obj_type == "proc":
            drop = f"IF OBJECT_ID('{full_name}', 'P') IS NOT NULL DROP PROCEDURE {full_name};"
        elif obj_type == "function":
            drop = f"IF OBJECT_ID('{full_name}', 'FN') IS NOT NULL DROP FUNCTION {full_name};"
        else:
            drop = ""
        if drop:
            _exec(
                cursor,
                drop,
                object_type=obj_type,
                object_name=full_name,
                action="drop_if_exists",
            )
    _exec(
        cursor,
        ddl,
        object_type=obj_type,
        object_name=full_name,
        action="create_or_replace",
    )


def apply_folder(cursor, folder: str, pattern: str, applier):
    files = sorted(glob.glob(os.path.join(folder, pattern)))
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
        applier(cursor, cfg)


def run_install(
    ambiente: str = "DEV", dry_run: bool = False, base_dir: str | None = None
):
    global DRY_RUN
    DRY_RUN = bool(dry_run)

    cn, cur = connect(ambiente)

    # Importante: aseguramos tabla de auditoría dentro de la BD destino
    ensure_audit_table(cur)

    # Ejecutar en orden
    root = base_dir or _project_root()
    apply_folder(cur, os.path.join(root, "tables"), "*.table.json", apply_table)
    apply_folder(cur, os.path.join(root, "views"), "*.view.json", apply_ddl)
    apply_folder(cur, os.path.join(root, "procs"), "*.proc.json", apply_ddl)

    # cerrar
    try:
        cur.close()
    except Exception:
        pass
    try:
        cn.close()
    except Exception:
        pass

    _log("info", "Instalación completada.")
