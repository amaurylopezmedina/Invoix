import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd
from sqlalchemy import text

# Tus imports originales
from APIFE.api import logger
from db.uDB import ConectarDB
from glib.uGlobalLib import GConfig


class CSVImportMapper:
    def __init__(self, mapping_file: str, db_connection):
        self.mapping = self._load_mapping(mapping_file)
        self.db = db_connection  # Ahora es un ConectarDB
        self.conn = db_connection.connection
        self.cursor = self.conn.cursor()

    def _load_mapping(self, mapping_file: str) -> Dict[str, Any]:
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                mapping_data = json.load(f)
            return self._convert_keys_to_lowercase(mapping_data)
        except Exception as e:
            raise Exception(f"Error loading mapping file: {str(e)}")

    def _convert_keys_to_lowercase(self, data):
        if isinstance(data, dict):
            new_dict = {}
            for key, value in data.items():
                new_key = key.lower()
                if isinstance(value, dict):
                    new_dict[new_key] = self._convert_keys_to_lowercase(value)
                elif (
                    isinstance(value, list)
                    and len(value) > 0
                    and isinstance(value[0], str)
                ):
                    new_value = value.copy()
                    new_value[0] = value[0].lower()
                    new_dict[new_key] = new_value
                else:
                    new_dict[new_key] = value
            return new_dict
        elif isinstance(data, list):
            return [
                (
                    self._convert_keys_to_lowercase(item)
                    if isinstance(item, (dict, list))
                    else item
                )
                for item in data
            ]
        else:
            return data

    def _detect_encoding(self, file_path: str) -> str:
        encodings = ["utf-8", "latin-1", "windows-1252", "iso-8859-1"]
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    f.read()
                return encoding
            except UnicodeDecodeError:
                continue
        return "latin-1"

    def _detect_header(self, csv_file: str) -> bool:
        try:
            encoding = self._detect_encoding(csv_file)
            with open(csv_file, "r", encoding=encoding) as f:
                first_line = f.readline().strip()
                return not (first_line.startswith("E,") or first_line.startswith("D,"))
        except Exception:
            return True

    def _get_case_insensitive_table_name(self, table_name: str) -> str:
        try:
            query = "SELECT name FROM sys.tables WHERE LOWER(name) = ?"
            row = self.db.fetch_query(query, (table_name.lower(),))
            if row:
                return row[0][0]
            return table_name
        except Exception as e:
            logger.error(f"Error buscando tabla {table_name}: {e}")
            return table_name

    def _get_table_columns(self, table_name: str):
        try:
            query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ?
            """
            rows = self.db.fetch_query(query, (table_name,))
            return {r[0].lower(): r[0] for r in rows}
        except Exception as e:
            logger.error(f"Error obteniendo columnas de {table_name}: {e}")
            return {}

    def _get_sql_type(self, dtype: str) -> str:
        return {
            "char": "VARCHAR(255)",
            "numeric": "DECIMAL(18,6)",
            "int": "INT",
            "bit": "BIT",
            "date": "DATE",
            "datetime": "DATETIME",
        }.get(dtype.lower(), "VARCHAR(255)")

    def process_and_insert(
        self, csv_file: str, batch_size: int = 1000
    ) -> Tuple[int, int]:
        try:
            encoding = self._detect_encoding(csv_file)
            logger.info(f"Detected encoding: {encoding}")
            has_header = self._detect_header(csv_file)

            df = pd.read_csv(
                csv_file,
                header=0 if has_header else None,
                dtype=str,
                encoding=encoding,
                on_bad_lines="warn",
            )
            if not has_header:
                df.columns = [f"col_{i}" for i in range(len(df.columns))]
            df.columns = [col.lower() for col in df.columns]

            encabezado_mask = df.iloc[:, 0].str.strip().str.upper() == "E"
            detalle_mask = df.iloc[:, 0].str.strip().str.upper() == "D"

            encabezado_df = self._apply_mapping(
                df[encabezado_mask].copy(), "feencabezado", csv_file
            )
            detalle_df = self._apply_mapping(
                df[detalle_mask].copy(), "fedetalle", csv_file
            )

            enc_table = self._get_case_insensitive_table_name("FEEncabezado")
            det_table = self._get_case_insensitive_table_name("FEDetalle")

            encabezado_count = self._batch_insert(encabezado_df, enc_table, batch_size)
            detalle_count = self._batch_insert(detalle_df, det_table, batch_size)

            return encabezado_count, detalle_count
        except Exception as e:
            logger.error(f"Error general en process_and_insert: {e}")
            import traceback

            traceback.print_exc()
            raise

    def _apply_mapping(
        self, df: pd.DataFrame, table_name: str, csv_file: Optional[str] = None
    ) -> pd.DataFrame:
        mapping = self.mapping["csv"][table_name]
        processed = {}
        df_cols = {col.lower(): col for col in df.columns}

        for col_name, (src, dtype) in mapping.items():
            src_lower = src.lower()
            data = (
                df[df_cols.get(src_lower)]
                if df_cols.get(src_lower)
                else pd.Series(None, index=df.index)
            )

            if dtype.lower() in ["numeric", "int", "bit"]:
                # Limpieza ultra agresiva para República Dominicana (comas, puntos, espacios, símbolos)
                data = data.astype(str).str.replace(
                    r"[^\d,.-]", "", regex=True
                )  # quita letras y símbolos ros
                data = data.str.replace(",", ".")  # coma decimal → punto
                data = data.str.strip()
                data = pd.to_numeric(data, errors="coerce")

                if dtype.lower() == "int":
                    data = data.astype("Int64")
                if dtype.lower() == "bit":
                    data = data.notna().astype(int)

                data = data.replace({pd.NA: None, float("nan"): None})

            elif dtype.lower() in ["date", "datetime"]:
                data = pd.to_datetime(data, errors="coerce", dayfirst=True)
                data = data.apply(
                    lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else None
                )

            elif dtype.lower() == "char":
                data = data.fillna("").astype(str)

            processed[col_name] = data

        return pd.DataFrame(processed)

    def _batch_insert(self, df: pd.DataFrame, table_name: str, batch_size: int) -> int:

        if df.empty:
            logger.info(f"No hay datos para {table_name}")
            return 0

        total = 0
        db_cols = self._get_table_columns(table_name)

        # Renombrar columnas si es necesario
        if db_cols:
            rename = {
                c: db_cols[c.lower()]
                for c in df.columns
                if c.lower() in db_cols and c != db_cols[c.lower()]
            }
            if rename:
                df = df.rename(columns=rename)

        columnas = list(df.columns)
        placeholders = ", ".join(["?"] * len(columnas))
        columnas_sql = ", ".join(columnas)

        insert_sql = (
            f"INSERT INTO {table_name} ({columnas_sql}) VALUES ({placeholders})"
        )

        for idx, row in df.iterrows():
            try:
                self.cursor.execute(insert_sql, tuple(row.values))
                total += 1
            except Exception as e:
                logger.error(f"Error insertando fila {idx+1} en {table_name}: {e}")
                self.conn.rollback()
                continue

        self.conn.commit()
        return total


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================
def organize_files(source_dir):
    try:
        GConfig.cargar(1)
        cn1 = ConectarDB()
        mapper = CSVImportMapper("fm/datadefCarga.json", cn1)

        for ext in ["csv"]:
            Path(source_dir, f"Procesados/{ext}").mkdir(parents=True, exist_ok=True)
        Path(source_dir, "NoProcesados").mkdir(exist_ok=True)
        Path(source_dir, "Logs").mkdir(exist_ok=True)

        files = [
            f
            for f in os.listdir(source_dir)
            if os.path.isfile(os.path.join(source_dir, f))
        ]
        logger.info(f"{len(files)} archivos encontrados")

        for file in files:
            path = os.path.join(source_dir, file)
            if file.lower().endswith(".csv"):
                try:
                    logger.info(f"\n{'='*70}\nPROCESANDO: {file}\n{'='*70}")
                    enc, det = mapper.process_and_insert(path)
                    logger.info(f"¡ÉXITO! → Encabezados: {enc} | Detalles: {det}")
                    dest = os.path.join(source_dir, "Procesados/csv", file)
                except Exception as e:
                    logger.error(f"¡FALLÓ! → {file} | Error: {e}")
                    dest = os.path.join(source_dir, "NoProcesados", file)
            else:
                dest = os.path.join(source_dir, "NoProcesados", file)

            shutil.move(path, dest)

    except Exception as e:
        logger.error(f"Error global: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import sys

    dir_path = sys.argv[1] if len(sys.argv) > 1 else "."
    organize_files(dir_path)
