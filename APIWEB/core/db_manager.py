"""
Database Manager Module - ImportarDGII
Gestión de conexión, esquema y operaciones con SQL Server para Facturación Electrónica DGII
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

# Configurar la salida estándar para manejar UTF-8 en Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def safe_print(msg: str) -> None:
    """Imprime mensajes usando logger en lugar de print para evitar recursión."""
    # Limpiar emojis para compatibilidad
    replacements = {
        "[DEL]": "[DEL]",
        "[OK]": "[OK]",
        "[WARN]": "[WARN]",
        "[ERROR]": "[ERROR]",
        "[INFO]": "[INFO]",
        "[PROC]": "[PROC]",
        "[ADD]": "[ADD]",
        "[INFO]": "[INFO]",
    }
    for emoji, ascii_text in replacements.items():
        msg = msg.replace(emoji, ascii_text)
    
    # Usar logger en lugar de print
    logger.info(msg)


# Obtener rutas de configuración relativas a este archivo
def get_config_path(filename: str) -> Path:
    """Obtiene la ruta de un archivo de configuración"""
    return Path(__file__).resolve().parents[1] / "config" / filename


SETTINGS_PATH = get_config_path("settings.json")
MAX_COLS_PER_TABLE = 80  # Columnas de detalle por tabla (más ENCF y RNCEmisor)


def load_settings() -> Dict[str, str]:
    """Carga configuración desde config/settings.json"""
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(cfg: dict) -> None:
    """Guarda configuración en config/settings.json"""
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def load_detalle_columns() -> Dict[str, dict]:
    """Carga las definiciones de columnas de detalle desde el JSON."""
    detalle_path = get_config_path("detalle_columns.json")
    with open(detalle_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_encabezado_columns() -> Dict[str, dict]:
    """Carga las definiciones de columnas de encabezado desde el JSON."""
    encabezado_path = get_config_path("encabezado_columns.json")
    with open(encabezado_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_engine(cfg: dict, database_name: str):
    """Construye engine de SQLAlchemy para la base de datos especificada"""
    connection_url = URL.create(
        "mssql+pyodbc",
        username=cfg["user"],
        password=cfg["password"],
        host=cfg["server"],
        database=database_name,
        query={"driver": cfg.get("driver", "ODBC Driver 17 for SQL Server")},
    )
    return create_engine(connection_url, fast_executemany=True)


def _build_master_engine(cfg: dict):
    """Construye engine conectado a la base de datos master"""
    return _build_engine(cfg, "master")


def _build_db_engine(cfg: dict):
    """Construye engine conectado a la base de datos configurada"""
    return _build_engine(cfg, cfg["database"])


def ensure_database_exists() -> None:
    """Crea la base si no existe usando AUTOCOMMIT para evitar error 226."""
    cfg = load_settings()
    dbname = cfg["database"]

    eng_master = _build_master_engine(cfg)
    with eng_master.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sys.databases WHERE name = :dbname"),
            {"dbname": dbname},
        ).fetchone()

    if not result:
        with eng_master.execution_options(isolation_level="AUTOCOMMIT").connect() as conn2:
            conn2.execute(text(f"CREATE DATABASE [{dbname}]"))
            safe_print(f"[OK] Base de datos [{dbname}] creada exitosamente")
    else:
        safe_print(f"[INFO] Base de datos [{dbname}] ya existe")


def _normalize_col(col: str) -> str:
    """Normaliza nombre de columna agregando corchetes"""
    safe = col.strip().replace("]", "").replace("[", "")
    return f"[{safe}]"


def _table_exists(conn, table_name: str) -> bool:
    """Verifica si una tabla existe en la base de datos"""
    row = conn.execute(
        text("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = :t"),
        {"t": table_name},
    ).fetchone()
    return bool(row)


def sync_table_with_json(conn, table_name: str, json_path: str, drop_if_exists: bool = False) -> None:
    """Alinea la tabla de SQL Server con la definición JSON."""
    import re
    
    with open(json_path, "r", encoding="utf-8") as f:
        columns = json.load(f)

    result = conn.execute(
        text(
            f"""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME = '{table_name}'
    """
        )
    ).scalar()

    dropped = False
    if result > 0 and drop_if_exists:
        safe_print(f"[DEL] Eliminando tabla existente {table_name} para recrearla con esquema actualizado...")
        try:
            conn.execute(text(f"DROP TABLE IF EXISTS [{table_name}]"))
            dropped = True
            result = 0
            safe_print(f"[OK] Tabla {table_name} eliminada.")
        except Exception as exc:
            safe_print(f"[WARN] No se pudo eliminar {table_name}: {exc}")

    if result == 0:
        safe_print(f"[PROC] Creando tabla {table_name} según definición JSON...")
        sql_cols = []
        for col, meta in columns.items():
            # Normalizar nombre de columna: FormaPago[1] → FormaPago1
            normalized_col = re.sub(r'\[(\d+)\]', r'\1', col)
            # Eliminar espacios al inicio y final
            normalized_col = normalized_col.strip()
            col_type = meta["type"].upper()
            if col_type == "NVARCHAR":
                length = meta.get("length", 255)
                if str(length).upper() == "MAX":
                    sql_cols.append(f"[{normalized_col}] NVARCHAR(MAX)")
                else:
                    sql_cols.append(f"[{normalized_col}] NVARCHAR({length})")
            elif col_type == "DECIMAL":
                precision = meta.get("precision", 18)
                scale = meta.get("scale", 4)
                sql_cols.append(f"[{normalized_col}] DECIMAL({precision},{scale})")
            else:
                sql_cols.append(f"[{normalized_col}] {col_type}")

            if not meta.get("nullable", True):
                sql_cols[-1] += " NOT NULL"

        sql_cols.append("PRIMARY KEY (eNCF, RNCEmisor)")
        create_sql = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(sql_cols) + "\n)"

        try:
            conn.execute(text(create_sql))
            safe_print(f"[OK] Tabla {table_name} creada correctamente con PK compuesta (eNCF, RNCEmisor).")
        except Exception as exc:
            safe_print(f"[ERROR] Error al crear la tabla {table_name}: {exc}")
        return

    if not dropped:
        safe_print(f"[INFO] Verificando columnas existentes en {table_name}...")
        existing = conn.execute(
            text(
                f"""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table_name}'
        """
            )
        ).fetchall()

        existing_cols = {r.COLUMN_NAME: r for r in existing}
        altered = 0
        added = 0

        for col, meta in columns.items():
            # Normalizar nombre de columna
            normalized_col = re.sub(r'\[(\d+)\]', r'\1', col)
            # Eliminar espacios al inicio y final
            normalized_col = normalized_col.strip()
            
            col_type = meta["type"].upper()
            if col_type == "NVARCHAR":
                length = meta.get("length", 255)
                sql_def = (
                    f"NVARCHAR({length})"
                    if str(length).upper() != "MAX"
                    else "NVARCHAR(MAX)"
                )
            elif col_type == "DECIMAL":
                precision = meta.get("precision", 18)
                scale = meta.get("scale", 4)
                sql_def = f"DECIMAL({precision},{scale})"
            else:
                sql_def = col_type

            if normalized_col in existing_cols:
                row = existing_cols[normalized_col]
                db_type = row.DATA_TYPE.upper()

                mismatch = False
                if db_type != col_type:
                    mismatch = True
                elif col_type == "NVARCHAR":
                    if str(row.CHARACTER_MAXIMUM_LENGTH) != str(meta.get("length", 255)):
                        mismatch = True
                elif col_type == "DECIMAL":
                    if (
                        row.NUMERIC_PRECISION != meta.get("precision", 18)
                        or row.NUMERIC_SCALE != meta.get("scale", 4)
                    ):
                        mismatch = True

                if mismatch:
                    try:
                        conn.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN [{normalized_col}] {sql_def}"))
                        altered += 1
                        safe_print(f"[WARN] Tipo ajustado: {normalized_col} -> {sql_def}")
                    except Exception as exc:
                        safe_print(f"[ERROR] Error ajustando columna {normalized_col}: {exc}")
            else:
                try:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD [{normalized_col}] {sql_def}"))
                    added += 1
                    safe_print(f"[ADD] Columna agregada: {normalized_col} ({sql_def})")
                except Exception as exc:
                    safe_print(f"[ERROR] Error agregando columna {normalized_col}: {exc}")
        
        safe_print(
            f"[OK] Sincronizacion completada para {table_name}. Columnas nuevas: {added}, ajustadas: {altered}"
        )
def _create_table(
    conn,
    table_name: str,
    columns: List[str],
    primary_key: str | None = None,
    pk_len: int = 20,
) -> None:
    """Crea una tabla con las columnas especificadas"""
    parts = []
    for col in columns:
        col_sql = _normalize_col(col)
        if primary_key and col == primary_key:
            parts.append(f"{col_sql} NVARCHAR({pk_len}) NOT NULL PRIMARY KEY")
        elif col == "eNCF" or col == "RNCEmisor":
            parts.append(f"{col_sql} NVARCHAR({pk_len}) NULL")
        else:
            # Usar VARCHAR en lugar de NVARCHAR(MAX) para mejor rendimiento
            parts.append(f"{col_sql} VARCHAR(500) NULL")

    create_sql = f"CREATE TABLE [{table_name}] (\n    " + ",\n    ".join(parts) + "\n);"
    conn.execute(text(create_sql))


def ensure_tables_exist(df: pd.DataFrame, recreate_mode: bool = False) -> List[str]:
    """Garantiza que las tablas estén listas. En modo recreate elimina datos previos, en modo append los preserva.
    
    Args:
        df: DataFrame con los datos a importar
        recreate_mode: Si True, elimina y recrea tablas. Si False, agrega a tablas existentes.
    
    Returns:
        Lista de nombres de tablas creadas/validadas
    """
    cfg = load_settings()
    table_head = cfg["table_encabezado"]
    detalle_prefix = cfg["table_detalle_prefix"]

    eng_db = _build_db_engine(cfg)

    json_path = get_config_path("encabezado_columns.json")

    with eng_db.connect() as conn:
        if recreate_mode:
            # Modo RECREAR: eliminar tabla de encabezado y todas las de detalle
            safe_print("[RECREATE] Modo RECREAR: eliminando tablas existentes...")
            sync_table_with_json(conn, table_head, str(json_path), drop_if_exists=True)
            
            # Eliminar todas las tablas de detalle
            result = conn.execute(
                text(
                    f"""
                    SELECT TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_NAME LIKE '{detalle_prefix}%'
                    """
                )
            ).fetchall()

            for row in result:
                table_name = row[0]
                safe_print(f"[DEL] Eliminando tabla de detalle {table_name}...")
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS [{table_name}]"))
                except Exception as exc:
                    safe_print(f"[WARN] Error al eliminar tabla {table_name}: {exc}")
        else:
            # Modo AGREGAR: solo sincronizar estructura sin eliminar datos
            safe_print("[ADD] Modo AGREGAR: sincronizando estructura de tablas...")
            sync_table_with_json(conn, table_head, str(json_path), drop_if_exists=False)
            
            # Verificar que tabla de detalle exista
            detalle_table = f"{detalle_prefix}"
            if not _table_exists(conn, detalle_table):
                safe_print(f"[INFO] Tabla de detalle {detalle_table} no existe, sera creada al insertar datos")

    return []


def _convert_column_type(df: pd.DataFrame, col: str, col_meta: dict) -> pd.Series:
    """Convierte una columna al tipo definido en el JSON manteniendo valores nulos."""
    col_type = col_meta["type"].upper()
    series = df[col].copy()

    def clean_special_values(val):
        if val is None or pd.isna(val):
            return None
        if isinstance(val, str):
            val_lower = val.strip().lower()
            if val_lower in {"", "nan", "none", "null", "#e"} or val_lower.startswith("#e"):
                return None
            return val.strip()
        return val

    series = series.apply(clean_special_values)
    series = series.where(pd.notnull(series), None)

    if col_type == "NVARCHAR":
        return series.apply(lambda x: str(x) if x is not None else None)
    if col_type == "DECIMAL":
        result = pd.to_numeric(series, errors="coerce")
        return result.where(pd.notnull(result), None)
    if col_type == "DATE":
        def convert_date(val):
            if val is None or pd.isna(val):
                return None
            try:
                dt_val = pd.to_datetime(val, errors="coerce")
                if pd.isna(dt_val):
                    return None
                return dt_val
            except Exception:
                return None

        return series.apply(convert_date)
    if col_type == "INT":
        result = pd.to_numeric(series, errors="coerce")
        return result.where(pd.notnull(result), None).astype("Int64")
    return series.apply(lambda x: str(x) if x is not None else None)


def split_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Divide el DataFrame original en encabezado y tablas de detalle, filtrando solo columnas definidas en JSON."""
    cfg = load_settings()
    detalle_prefix = cfg["table_detalle_prefix"]

    # Cargar definiciones de columnas desde JSON
    import re
    header_cols_meta = load_encabezado_columns()
    detalle_cols_meta = load_detalle_columns()

    # Mapeo de aliases: nombre en Excel -> nombre esperado en JSON/BD
    column_aliases = {
        'ENCF': 'eNCF',      # Excel usa ENCF, JSON/BD usa eNCF
        'TipoeCF': 'TipoECF',  # Excel usa TipoeCF, JSON/BD usa TipoECF
        'Version': 'Version',  # Puede estar en minúsculas
        'CasoPrueba': 'CasoPrueba'
    }
    
    # Renombrar columnas del DataFrame según aliases
    df_renamed_cols = {}
    for col in df.columns:
        if col in column_aliases:
            df_renamed_cols[col] = column_aliases[col]
    
    if df_renamed_cols:
        safe_print(f"[INFO] Renombrando columnas: {df_renamed_cols}")
        df = df.rename(columns=df_renamed_cols)

    # Obtener lista de columnas válidas de encabezado (con nombres normalizados)
    # Crear mapeo de ambos formatos: con y sin corchetes
    valid_encabezado_cols = set()
    for col_name in header_cols_meta.keys():
        valid_encabezado_cols.add(col_name)  # FormaPago[1]
        normalized = re.sub(r'\[(\d+)\]', r'\1', col_name)  # FormaPago1
        valid_encabezado_cols.add(normalized)
    
    # Obtener lista de columnas base válidas de detalle (sin índices)
    # Por ejemplo: "NumeroLinea[1]" → "NumeroLinea"
    valid_detalle_base_cols = set()
    for col_name in detalle_cols_meta.keys():
        if '[' in col_name:
            base_name = col_name.split('[')[0]
            valid_detalle_base_cols.add(base_name)
        else:
            valid_detalle_base_cols.add(col_name)
    
    safe_print(f"[TABLA] Columnas válidas de encabezado en JSON: {len(header_cols_meta)}")
    safe_print(f"[TABLA] Columnas base válidas de detalle en JSON: {len(valid_detalle_base_cols)}")
    
    # Separar y filtrar columnas del Excel según definiciones JSON
    cols_det_all = []
    cols_head_all = []
    cols_ignoradas = []
    
    for col in df.columns:
        # Verificar primero si está en encabezado (match exacto)
        if col in valid_encabezado_cols:
            cols_head_all.append(col)
        # Si tiene índice [X], verificar si su base está en detalle
        elif '[' in col and ']' in col:
            base_name = col.split('[')[0]
            if base_name in valid_detalle_base_cols:
                cols_det_all.append(col)
            else:
                cols_ignoradas.append(col)
        else:
            # Columna no definida en ningún JSON
            cols_ignoradas.append(col)
    
    safe_print(f"[DATA] Columnas de detalle a importar: {len(cols_det_all)}")
    safe_print(f"[DATA] Columnas de encabezado a importar: {len(cols_head_all)}")
    safe_print(f"[DATA] Columnas ignoradas (no en JSON): {len(cols_ignoradas)}")
    safe_print(f"[DATA] Total columnas en Excel: {len(df.columns)}")
    
    if cols_ignoradas:
        safe_print(f"[WARN] Columnas ignoradas: {cols_ignoradas[:10]}{'...' if len(cols_ignoradas) > 10 else ''}")
    
    # Procesar encabezado
    df_head = df[cols_head_all].copy()
    
    # Convertir tipos solo para columnas definidas en el JSON
    for col in df_head.columns:
        if col in header_cols_meta:
            df_head[col] = _convert_column_type(df_head, col, header_cols_meta[col])
    
    # Si el encabezado tiene más de 1020 columnas, particionarlo
    # (SQL Server soporta hasta 1024, dejamos margen de seguridad)
    MAX_COLS_ENCABEZADO = 1020
    head_extra_tables = {}
    
    if len(cols_head_all) > MAX_COLS_ENCABEZADO:
        safe_print(f"[WARN] Encabezado tiene {len(cols_head_all)} columnas, se particionará en múltiples tablas")
        # Asegurar que eNCF y RNCEmisor estén en la primera partición
        priority_cols = ['eNCF', 'RNCEmisor']
        priority_existing = [c for c in priority_cols if c in cols_head_all]
        other_head_cols = [c for c in cols_head_all if c not in priority_cols]
        
        # Primera tabla con columnas prioritarias + hasta MAX_COLS_ENCABEZADO
        first_chunk_size = MAX_COLS_ENCABEZADO - len(priority_existing)
        cols_head_first = priority_existing + other_head_cols[:first_chunk_size]
        cols_head_remaining = other_head_cols[first_chunk_size:]
        
        # Recrear df_head solo con las columnas de la primera partición
        df_head = df[cols_head_first].copy()
        for col in df_head.columns:
            if col in header_cols_meta:
                df_head[col] = _convert_column_type(df_head, col, header_cols_meta[col])
        
        # Crear tablas adicionales de encabezado
        table_num = 2
        for i in range(0, len(cols_head_remaining), MAX_COLS_ENCABEZADO - 2):
            chunk_cols = cols_head_remaining[i : i + (MAX_COLS_ENCABEZADO - 2)]
            # Incluir ENCF y RNCEmisor en cada tabla adicional
            chunk_with_keys = priority_existing + chunk_cols
            df_chunk = df[chunk_with_keys].copy()
            head_extra_tables[f"{cfg['table_encabezado']}{table_num}"] = df_chunk
            table_num += 1
        
        safe_print(f"[TABLA] Encabezado particionado en {1 + len(head_extra_tables)} tablas")
    
    def clean_and_convert(val):
        if val is None or pd.isna(val):
            return None
        if isinstance(val, str):
            stripped = val.strip()
            lowered = stripped.lower()
            if lowered in {"", "nan", "null", "none", "#e"} or lowered.startswith("#e"):
                return None
            return stripped
        return str(val)

    # Transponer columnas de detalle: convertir NumeroLinea[1], NumeroLinea[2]... en filas
    safe_print(f"[DATA] Transponiendo {len(cols_det_all)} columnas de detalle a formato vertical...")
    
    # Identificar todos los índices únicos [1], [2], [3]...
    indices_detalle = set()
    for col in cols_det_all:
        if '[' in col and ']' in col:
            # Extraer el índice entre corchetes
            try:
                idx_str = col.split('[')[1].split(']')[0]
                indices_detalle.add(int(idx_str))
            except (IndexError, ValueError):
                pass
    
    indices_detalle = sorted(indices_detalle)
    safe_print(f"[TABLA] Encontrados {len(indices_detalle)} ítems de detalle (índices: {min(indices_detalle) if indices_detalle else 0} a {max(indices_detalle) if indices_detalle else 0})")
    
    # Usar solo los nombres base definidos en JSON
    base_names_detalle = sorted(valid_detalle_base_cols)
    safe_print(f"[TABLA] Campos por ítem (definidos en JSON): {len(base_names_detalle)}")
    safe_print(f"[TABLA] Filas esperadas: {len(df)} facturas × {len(indices_detalle)} ítems = {len(df) * len(indices_detalle)} filas")
    
    # Crear tabla de detalle transpuesta
    detalle_rows = []
    
    for fila_idx in range(len(df)):
        # Usar eNCF para detalle (no ENCF como en encabezado)
        encf_val = df_head['eNCF'].iloc[fila_idx] if 'eNCF' in df_head.columns else ""
        rnc_val = df_head['RNCEmisor'].iloc[fila_idx] if 'RNCEmisor' in df_head.columns else ""
        tipo_ecf = df_head['TipoECF'].iloc[fila_idx] if 'TipoECF' in df_head.columns else None
        
        for item_idx in indices_detalle:
            row_data = {
                'eNCF': encf_val,
                'RNCEmisor': rnc_val,
                'TipoECF': tipo_ecf,
                'NumeroLinea': item_idx  # La tabla usa NumeroLinea, no NumeroItem
            }
            
            # Agregar cada campo del detalle para este índice
            for base_name in base_names_detalle:
                col_name = f"{base_name}[{item_idx}]"
                if col_name in df.columns:
                    val = df[col_name].iloc[fila_idx]
                    row_data[base_name] = clean_and_convert(val)
                else:
                    row_data[base_name] = None
            
            detalle_rows.append(row_data)
    
    # Crear DataFrame de detalle transpuesto
    df_detalle = pd.DataFrame(detalle_rows)
    
    # Filtrar filas donde CantidadItem está vacío o NULL
    # NOTA: NumeroLinea siempre se preserva independientemente de su valor
    filas_antes = len(df_detalle)
    
    def es_valor_valido(val):
        """Verifica si un valor es válido (no None, no vacío, no 'NULL')"""
        if val is None or pd.isna(val):
            return False
        if isinstance(val, str):
            val_lower = val.strip().lower()
            return val_lower not in {'', 'null'}
        return True
    
    # Solo filtrar por CantidadItem
    df_detalle = df_detalle[df_detalle['CantidadItem'].apply(es_valor_valido)]
    filas_despues = len(df_detalle)
    filas_eliminadas = filas_antes - filas_despues
    
    safe_print(f"[OK] Detalle transpuesto: {filas_despues} filas con CantidadItem válida ({filas_eliminadas} filas sin cantidad eliminadas)")
    
    # Crear diccionario con una sola tabla de detalle
    det_tables: Dict[str, pd.DataFrame] = {
        f"{detalle_prefix}": df_detalle
    }
    
    # Combinar tablas de encabezado extra con tabla de detalle
    all_tables = {**head_extra_tables, **det_tables}
    
    if head_extra_tables:
        safe_print(f"[OK] {len(head_extra_tables)} tablas de encabezado adicionales preparadas.")
    
    return df_head, all_tables


def _filter_duplicates(df: pd.DataFrame, table_name: str, engine) -> pd.DataFrame:
    """Filtra registros que ya existen en la tabla basándose en eNCF y RNCEmisor."""
    # Verificar columnas (puede ser eNCF o ENCF dependiendo del momento)
    encf_col = 'eNCF' if 'eNCF' in df.columns else ('ENCF' if 'ENCF' in df.columns else None)
    if encf_col is None or 'RNCEmisor' not in df.columns:
        safe_print("[WARN] No se puede validar duplicados: faltan columnas eNCF/ENCF o RNCEmisor")
        return df
    
    try:
        with engine.connect() as conn:
            # Verificar si la tabla existe
            if not _table_exists(conn, table_name):
                safe_print(f"[INFO] Tabla {table_name} no existe, no hay duplicados que validar")
                return df
            
            # Obtener pares eNCF+RNCEmisor únicos del DataFrame
            unique_pairs = df[[encf_col, 'RNCEmisor']].drop_duplicates()
            total_original = len(df)
            
            # Crear lista de condiciones para buscar en la BD (usar eNCF como nombre de columna)
            conditions = []
            for _, row in unique_pairs.iterrows():
                encf = str(row[encf_col]).replace("'", "''")
                rnc = str(row['RNCEmisor']).replace("'", "''")
                conditions.append(f"(eNCF = '{encf}' AND RNCEmisor = '{rnc}')")
            
            if not conditions:
                return df
            
            # Buscar registros existentes
            where_clause = " OR ".join(conditions)
            query = f"""
                SELECT eNCF, RNCEmisor 
                FROM [{table_name}] 
                WHERE {where_clause}
            """
            
            existing = pd.read_sql(query, conn)
            
            if len(existing) == 0:
                safe_print("[OK] No se encontraron duplicados")
                return df
            
            # Crear una columna combinada para hacer el merge
            df['_key'] = df[encf_col].astype(str) + '|' + df['RNCEmisor'].astype(str)
            existing['_key'] = existing['eNCF'].astype(str) + '|' + existing['RNCEmisor'].astype(str)
            
            # Filtrar registros que NO están en la tabla existente
            df_filtered = df[~df['_key'].isin(existing['_key'])].copy()
            df_filtered.drop(columns=['_key'], inplace=True)
            
            duplicates_count = total_original - len(df_filtered)
            if duplicates_count > 0:
                safe_print(f"[WARN] Se encontraron {duplicates_count} registros duplicados que serán omitidos")
                safe_print(f"[OK] Se insertarán {len(df_filtered)} registros nuevos")
            
            return df_filtered
            
    except Exception as e:
        safe_print(f"[WARN] Error al validar duplicados: {e}")
        safe_print("[INFO] Continuando sin validación de duplicados...")
        return df


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas removiendo corchetes y espacios: FormaPago[1] → FormaPago1"""
    import re
    normalized_cols = {}
    for col in df.columns:
        # Reemplazar [X] por X: FormaPago[1] → FormaPago1
        normalized = re.sub(r'\[(\d+)\]', r'\1', col)
        # Eliminar espacios al inicio y final
        normalized = normalized.strip()
        normalized_cols[col] = normalized
    
    # Renombrar columnas
    df_renamed = df.rename(columns=normalized_cols)
    
    # Convertir columnas según los tipos esperados en SQL Server
    # Basado en la estructura real de la tabla FEEncabezado
    
    # Columnas tipo INT
    int_columns = ['TipoECF', 'TipoPago']
    for col in int_columns:
        if col in df_renamed.columns:
            df_renamed[col] = pd.to_numeric(df_renamed[col], errors='coerce')
            df_renamed[col] = df_renamed[col].where(pd.notna(df_renamed[col]), None)
    
    # Columnas tipo BIT (booleano)
    bit_columns = ['IndicadorNotaCredito', 'IndicadorEnvioDiferido', 'IndicadorMontoGravado']
    for col in bit_columns:
        if col in df_renamed.columns:
            # Convertir a booleano: '0' -> False, '1' -> True, None -> None
            df_renamed[col] = df_renamed[col].apply(lambda x: 
                True if str(x).strip() == '1' else 
                False if str(x).strip() == '0' else 
                None if x is None or pd.isna(x) else None
            )
    
    # Columnas tipo DATE
    date_columns = ['FechaVencimientoSecuencia', 'FechaLimitePago', 'FechaEmision', 
                    'FechaEntrega', 'FechaOrdenCompra', 'FechaEmbarque', 'FechaNCFModificado']
    for col in date_columns:
        if col in df_renamed.columns:
            # Convertir fechas en formato DD-MM-YYYY a datetime
            df_renamed[col] = pd.to_datetime(df_renamed[col], format='%d-%m-%Y', errors='coerce')
            df_renamed[col] = df_renamed[col].where(pd.notna(df_renamed[col]), None)
    
    # Para el resto de columnas, asegurar que sean object y reemplazar NaN con None
    for col in df_renamed.columns:
        if col not in int_columns and col not in bit_columns and col not in date_columns:
            df_renamed[col] = df_renamed[col].astype('object')
            df_renamed[col] = df_renamed[col].where(pd.notna(df_renamed[col]), None)
    
    return df_renamed


def insert_dataframes(
    df_head: pd.DataFrame, det_tables: Dict[str, pd.DataFrame]
) -> Tuple[int, Dict[str, int]]:
    """Inserta los dataframes de encabezado y detalle en SQL Server, agregando a tablas existentes."""
    cfg = load_settings()
    eng_db = _build_db_engine(cfg)
    inserted_details: Dict[str, int] = {}
    validate_duplicates = cfg.get("validate_duplicates", True)

    # DEBUG: Verificar columnas críticas ANTES de normalizar
    if 'eNCF' in df_head.columns:
        safe_print(f"[DEBUG] eNCF antes de normalizar - muestra: {df_head['eNCF'].head(3).tolist()}")
    if 'TipoECF' in df_head.columns:
        safe_print(f"[DEBUG] TipoECF antes de normalizar - muestra: {df_head['TipoECF'].head(3).tolist()}")
    
    # Normalizar nombres de columnas del encabezado (remover corchetes)
    safe_print("[EMOJI] Normalizando nombres de columnas...")
    df_head = _normalize_column_names(df_head)

    # DEBUG: Verificar columnas críticas DESPUÉS de normalizar
    if 'eNCF' in df_head.columns:
        safe_print(f"[DEBUG] eNCF después de normalizar - muestra: {df_head['eNCF'].head(3).tolist()}")
    if 'TipoECF' in df_head.columns:
        safe_print(f"[DEBUG] TipoECF después de normalizar - muestra: {df_head['TipoECF'].head(3).tolist()}")

    # Validar duplicados si está habilitado (verificar eNCF o ENCF)
    has_encf = 'eNCF' in df_head.columns or 'ENCF' in df_head.columns
    if validate_duplicates and has_encf and 'RNCEmisor' in df_head.columns:
        safe_print("[INFO] Validando duplicados antes de insertar...")
        df_head = _filter_duplicates(df_head, cfg["table_encabezado"], eng_db)
        if len(df_head) == 0:
            safe_print("[WARN] Todos los registros ya existen en la base de datos. No se insertará nada.")
            return 0, {}

    # Agregar columnas requeridas por la tabla que no vienen en el Excel
    from datetime import datetime
    
    # fechacreacion: columna NOT NULL tipo datetime
    if 'fechacreacion' not in df_head.columns:
        df_head['fechacreacion'] = datetime.now()
    
    # Modificado: columna NOT NULL tipo datetime (fecha de última modificación)
    if 'Modificado' not in df_head.columns:
        df_head['Modificado'] = datetime.now()
    
    # DEBUG: Verificar columnas críticas ANTES de insertar en BD
    if 'eNCF' in df_head.columns:
        safe_print(f"[DEBUG] eNCF antes de to_sql - muestra: {df_head['eNCF'].head(3).tolist()}")
    if 'TipoECF' in df_head.columns:
        safe_print(f"[DEBUG] TipoECF antes de to_sql - muestra: {df_head['TipoECF'].head(3).tolist()}")
    safe_print(f"[DEBUG] Columnas en df_head antes de insertar: {list(df_head.columns)[:10]}...")
    
    # Insertar encabezado principal (siempre en modo append)
    try:
        # No especificar dtype cuando la tabla ya existe - esto permite que pandas
        # use los tipos de columna existentes en la tabla de SQL Server
        df_head.to_sql(
            cfg["table_encabezado"],
            eng_db,
            if_exists="append",  # Siempre agregar, nunca reemplazar
            index=False,
            method=None,
            chunksize=1000,
        )
        head_count = len(df_head.index)
        safe_print(f"[OK] Encabezado: {head_count} filas insertadas (agregadas a tabla existente).")
    except Exception as exc:
        print(f"Error detallado al insertar encabezado: {exc}")
        print(f"Columnas en df_head: {list(df_head.columns)}")
        print(f"Número de columnas: {len(df_head.columns)}")
        primer_registro = df_head.iloc[0].to_dict() if len(df_head) > 0 else "Sin datos"
        print(f"Primera fila de datos: {primer_registro}")
        raise

    # Filtrar tablas de detalle para incluir solo los registros cuyo encabezado se insertó
    if validate_duplicates and len(df_head) > 0 and 'eNCF' in df_head.columns and 'RNCEmisor' in df_head.columns:
        safe_print("[INFO] Filtrando detalles para que coincidan con encabezados insertados...")
        # Crear clave combinada de los encabezados que se insertaron (usar eNCF)
        df_head['_key'] = df_head['eNCF'].astype(str) + '|' + df_head['RNCEmisor'].astype(str)
        valid_keys = set(df_head['_key'].unique())
        
        # Filtrar cada tabla de detalle
        for table_name in list(det_tables.keys()):
            df_det = det_tables[table_name]
            if 'eNCF' in df_det.columns and 'RNCEmisor' in df_det.columns:
                df_det['_key'] = df_det['eNCF'].astype(str) + '|' + df_det['RNCEmisor'].astype(str)
                original_count = len(df_det)
                df_det_filtered = df_det[df_det['_key'].isin(valid_keys)].copy()
                df_det_filtered.drop(columns=['_key'], inplace=True)
                det_tables[table_name] = df_det_filtered
                filtered_count = original_count - len(df_det_filtered)
                if filtered_count > 0:
                    safe_print(f"   [INFO] {table_name}: {filtered_count} filas filtradas, {len(df_det_filtered)} filas a insertar")
        
        # Limpiar columna auxiliar
        df_head.drop(columns=['_key'], inplace=True, errors='ignore')

    # Normalizar nombres de columnas de las tablas de detalle
    for table_name in det_tables:
        det_tables[table_name] = _normalize_column_names(det_tables[table_name])
        # Convertir tipos específicos para tabla de detalle
        df_det = det_tables[table_name]
        
        # Columnas INT en FEDetalle
        int_cols_det = ['NumeroLinea', 'TipoECF', 'IndicadorFacturacion', 'IndicadorAgenteRetencionoPercepcion',
                        'IndicadorBienoServicio', 'CodigoSubcantidad1', 'CodigoSubcantidad2', 
                        'CodigoSubcantidad3', 'CodigoSubcantidad4', 'CodigoSubcantidad5',
                        'TipoAfiliacion', 'Liquidacion', 'TipoImpuesto1', 'TipoImpuesto2']
        for col in int_cols_det:
            if col in df_det.columns:
                df_det[col] = pd.to_numeric(df_det[col], errors='coerce')
                df_det[col] = df_det[col].where(pd.notna(df_det[col]), None)
        
        # Columnas DECIMAL en FEDetalle
        decimal_cols_det = ['MontoITBISRetenido', 'MontoISRRetenido', 'CantidadItem', 'CantidadReferencia',
                           'Subcantidad1', 'Subcantidad2', 'Subcantidad3', 'Subcantidad4', 'Subcantidad5',
                           'GradosAlcohol', 'PrecioUnitarioReferencia', 'PesoNetoKilogramo', 'PesoNetoMineria',
                           'PrecioUnitarioItem', 'DescuentoMonto', 'SubDescuentoPorcentaje1', 'MontoSubDescuento1',
                           'SubDescuentoPorcentaje2', 'MontoSubDescuento2', 'SubDescuentoPorcentaje3', 'MontoSubDescuento3',
                           'SubDescuentoPorcentaje4', 'MontoSubDescuento4', 'SubDescuentoPorcentaje5', 'MontoSubDescuento5',
                           'MontoRecargo', 'SubRecargoPorcentaje1', 'MontoSubRecargo1', 'SubRecargoPorcentaje2',
                           'MontoSubRecargo2', 'SubRecargoPorcentaje3', 'MontoSubRecargo3', 'SubRecargoPorcentaje4',
                           'MontoSubRecargo4', 'SubRecargoPorcentaje5', 'MontoSubRecargo5', 'PrecioOtraMoneda',
                           'DescuentoOtraMoneda', 'RecargoOtraMoneda', 'MontoItemOtraMoneda', 'MontoItem']
        for col in decimal_cols_det:
            if col in df_det.columns:
                df_det[col] = pd.to_numeric(df_det[col], errors='coerce')
                df_det[col] = df_det[col].where(pd.notna(df_det[col]), None)
        
        # Columnas DATETIME en FEDetalle
        datetime_cols_det = ['FechaElaboracion', 'FechaVencimientoItem']
        for col in datetime_cols_det:
            if col in df_det.columns:
                df_det[col] = pd.to_datetime(df_det[col], format='%d-%m-%Y', errors='coerce')
                df_det[col] = df_det[col].where(pd.notna(df_det[col]), None)
        
        det_tables[table_name] = df_det

    # Crear todas las tablas (detalle y encabezado adicionales) primero
    safe_print(f"[PROC] Creando {len(det_tables)} tablas...")
    with eng_db.connect() as conn:
        for table_name, df_det in det_tables.items():
            if not _table_exists(conn, table_name):
                _create_table(conn, table_name, list(df_det.columns))
    safe_print(f"[OK] Todas las tablas creadas.")

    # Insertar datos en todas las tablas
    safe_print(f"[INSERT] Insertando datos en {len(det_tables)} tablas...")
    table_count = 0
    
    for table_name, df_det in det_tables.items():
        if len(df_det) == 0:
            safe_print(f"   [INFO] {table_name}: Sin datos para insertar (todos filtrados)")
            inserted_details[table_name] = 0
            continue
            
        try:
            # No especificar dtype - permite que pandas use los tipos de la tabla existente
            df_det.to_sql(
                table_name,
                eng_db,
                if_exists="append",
                index=False,
                method=None,
                chunksize=1000,
            )
            inserted_details[table_name] = len(df_det.index)
            table_count += 1
            if table_count % 10 == 0:
                safe_print(f"   [DATA] Progreso: {table_count}/{len(det_tables)} tablas insertadas...")
        except Exception as exc:
            print(f"Error al insertar en {table_name}: {exc}")
            print(f"Columnas: {list(df_det.columns)}")
            print(f"Número de columnas: {len(df_det.columns)}")
            raise
    
    safe_print(f"[OK] Todas las tablas insertadas.")
    return head_count, inserted_details


def test_connection() -> Tuple[bool, str]:
    """Prueba la conexión a SQL Server.
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje de error si falló)
    """
    try:
        cfg = load_settings()
        eng = _build_master_engine(cfg)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, ""
    except Exception as e:
        return False, str(e)


def get_server_info() -> Tuple[str, str]:
    """Obtiene información del servidor SQL Server"""
    cfg = load_settings()
    eng = _build_master_engine(cfg)
    with eng.connect() as conn:
        result = conn.execute(text("SELECT @@VERSION")).scalar()
    return result, cfg.get("driver", "")
