import traceback
import pandas as pd
import json
from typing import Dict, Any, Tuple
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

import time

import pyodbc
from sqlalchemy import Column, MetaData, String, Table, create_engine, select, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from db.uDB import *
from glib.Servicios import *

from glib.ufe import *


class CSVImportMapper:
    def __init__(self, mapping_file: str, db_connection: "ConectarDB"):
        """
        Initialize the mapper with the JSON mapping file and database connection.

        Args:
            mapping_file (str): Path to the JSON mapping file
            db_connection (ConectarDB): Instance of ConectarDB class
        """
        self.mapping = self._load_mapping(mapping_file)
        self.encabezado_columns = list(self.mapping["csv"]["FEENCABEZADO"].keys())
        self.detalle_columns = list(self.mapping["csv"]["FEDETALLE"].keys())
        self.db = db_connection

    def _load_mapping(self, mapping_file: str) -> Dict[str, Any]:
        """
        Load and parse the JSON mapping file.
        """
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise Exception(
                f"Error loading mapping file: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
            )

    def _detect_header(self, csv_file: str) -> bool:
        """
        Detect if the CSV file has a header.
        """
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                return not (first_line.startswith("E,") or first_line.startswith("D,"))
        except Exception as e:
            raise Exception(
                f"Error detecting header: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
            )

    def _create_tables(self):
        """
        Create database tables if they don't exist based on the mapping.
        """
        try:
            # Create FEENCABEZADO table
            encabezado_columns = []
            for col_name, (_, dtype) in self.mapping["csv"]["FEENCABEZADO"].items():
                sql_type = self._get_sql_type(dtype)
                encabezado_columns.append(f"{col_name} {sql_type}")

            create_encabezado = f"""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'FEENCABEZADO')
            CREATE TABLE FEENCABEZADO (
                {', '.join(encabezado_columns)}
            )
            """

            # Create FEDETALLE table
            detalle_columns = []
            for col_name, (_, dtype) in self.mapping["csv"]["FEDETALLE"].items():
                sql_type = self._get_sql_type(dtype)
                detalle_columns.append(f"{col_name} {sql_type}")

            create_detalle = f"""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'FEDETALLE')
            CREATE TABLE FEDETALLE (
                {', '.join(detalle_columns)}
            )
            """

            session = self.db.Session()
            try:
                session.execute(text(create_encabezado))
                session.execute(text(create_detalle))
                session.commit()
            finally:
                session.close()

        except Exception as e:
            raise Exception(
                f"Error creating database tables: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
            )

    def _get_sql_type(self, dtype: str) -> str:
        """
        Convert mapping data types to SQL Server data types.
        """
        type_mapping = {
            "char": "VARCHAR(255)",
            "numeric": "DECIMAL(18,2)",
            "int": "INT",
            "bit": "BIT",
            "date": "DATE",
            "datetime": "DATETIME",
        }
        return type_mapping.get(dtype, "VARCHAR(255)")

    def process_and_insert(
        self, csv_file: str, batch_size: int = 1000
    ) -> Tuple[int, int]:
        """
        Process the CSV file and insert data into database tables.
        """
        try:
            # Ensure tables exist
            self._create_tables()

            # Process CSV file
            has_header = self._detect_header(csv_file)
            df = pd.read_csv(csv_file, header=0 if has_header else None, dtype=str)

            if not has_header:
                # Asignar nombres de columna numéricos
                df.columns = [f"col_{i}" for i in range(len(df.columns))]

            # Split and process data
            encabezado_mask = df.iloc[:, 0] == "E"
            detalle_mask = df.iloc[:, 0] == "D"

            # Procesar FEENCABEZADO
            encabezado_df = self._apply_mapping(
                df[encabezado_mask].copy(), "FEENCABEZADO"
            )

            # Procesar FEDETALLE, asegurando que tenemos las columnas correctas
            detalle_df = df[detalle_mask].copy()
            detalle_df = self._apply_mapping(detalle_df, "FEDETALLE")

            # Insert data in batches
            encabezado_count = self._batch_insert(
                encabezado_df, "FEENCABEZADO", batch_size
            )
            detalle_count = self._batch_insert(detalle_df, "FEDETALLE", batch_size)

            return encabezado_count, detalle_count

        except Exception as e:
            raise Exception(
                f"Error processing and inserting data: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
            )

    def _batch_insert(self, df: pd.DataFrame, table_name: str, batch_size: int) -> int:
        """
        Insert DataFrame into database table in batches using SQL Server bulk insert.
        Includes proper handling of null values.
        """
        total_rows = 0
        try:
            for start in range(0, len(df), batch_size):
                end = start + batch_size
                batch_df = df.iloc[
                    start:end
                ].copy()  # Create a copy to avoid modifying original data

                session = self.db.Session()
                try:
                    # Manejar valores nulos según el tipo de datos de cada columna
                    for column in batch_df.columns:
                        dtype = self.mapping["csv"][table_name][column][1]

                        if dtype == "char":
                            batch_df[column] = (
                                batch_df[column].astype(str).replace("nan", "")
                            )
                        elif dtype in ["numeric", "int", "bit"]:
                            batch_df[column] = pd.to_numeric(
                                batch_df[column], errors="coerce"
                            )
                        elif dtype in ["date", "datetime"]:
                            batch_df[column] = pd.to_datetime(
                                batch_df[column], errors="coerce"
                            )

                    # Convertir a tipos de datos compatibles con SQL Server
                    dtype_map = {
                        "char": "str",
                        "numeric": "float",
                        "int": "Int64",
                        "bit": "Int64",
                        "date": "datetime64[ns]",
                        "datetime": "datetime64[ns]",
                    }

                    sql_dtypes = {
                        col: dtype_map[self.mapping["csv"][table_name][col][1]]
                        for col in batch_df.columns
                    }

                    batch_df = batch_df.astype(sql_dtypes)

                    # Insertar en la base de datos
                    batch_df.to_sql(
                        table_name,
                        self.db.engine,
                        if_exists="append",
                        index=False,
                        method="multi",
                        chunksize=batch_size,
                    )

                    session.commit()
                    total_rows += len(batch_df)

                except Exception as e:
                    session.rollback()
                    raise e
                finally:
                    session.close()

            return total_rows

        except Exception as e:
            raise Exception(
                f"Error inserting batch into {table_name}: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
            )

    def _apply_mapping(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Apply the mapping configuration to the DataFrame with special handling for FEDETALLE.
        """
        mapping = self.mapping["csv"][table_name]
        processed_columns = {}

        for col_name, (source_col, dtype) in mapping.items():
            try:
                # Manejo especial para FEDETALLE
                data = (
                    df[source_col]
                    if source_col in df.columns
                    else pd.Series(None, index=df.index)
                )

                # Convertir data type con manejo apropiado de nulos
                if dtype == "numeric":
                    data = pd.to_numeric(data, errors="coerce")
                elif dtype == "int":
                    data = pd.to_numeric(data, errors="coerce")
                    data = data.astype("Int64")
                elif dtype == "bit":
                    data = data.map(
                        {"true": 1, "false": 0, "1": 1, "0": 0, True: 1, False: 0}
                    ).astype("Int64")
                elif dtype == "date":
                    data = pd.to_datetime(data, errors="coerce").dt.date
                elif dtype == "datetime":
                    data = pd.to_datetime(data, errors="coerce")
                elif dtype == "char":
                    data = data.fillna("").astype(str)

                processed_columns[col_name] = data

            except Exception as e:
                print(f"Warning: Error processing column {col_name}: {str(e)}")
                if dtype in ["numeric", "int", "bit"]:
                    processed_columns[col_name] = pd.Series(
                        None, index=df.index, dtype="Int64"
                    )
                elif dtype in ["date", "datetime"]:
                    processed_columns[col_name] = pd.Series(
                        None, index=df.index, dtype="datetime64[ns]"
                    )
                else:
                    processed_columns[col_name] = pd.Series(
                        "", index=df.index, dtype="str"
                    )

        result_df = pd.concat(processed_columns, axis=1)

        return result_df
