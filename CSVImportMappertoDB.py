import traceback
import pandas as pd
import json
import sys
from typing import Dict, Any, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
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
    def __init__(self, mapping_file: str, cn1):
        """
        Initialize the mapper with the JSON mapping file and database connection.

        Args:
            mapping_file (str): Path to the JSON mapping file
            db_connection_string (str): SQLAlchemy database connection string
        """
        self.mapping = self._load_mapping(mapping_file)
        self.encabezado_columns = list(self.mapping["csv"]["FEENCABEZADO"].keys())
        self.detalle_columns = list(self.mapping["csv"]["FEDETALLE"].keys())
        self.engine = cn1

    def _load_mapping(self, mapping_file: str) -> Dict[str, Any]:
        """
        Load and parse the JSON mapping file.

        Args:
            mapping_file (str): Path to the JSON mapping file

        Returns:
            Dict containing the mapping configuration
        """
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Error loading mapping file: {str(e)}")

    def _detect_header(self, csv_file: str) -> bool:
        """
        Detect if the CSV file has a header by checking the first column of the first row.

        Args:
            csv_file (str): Path to the CSV file

        Returns:
            bool: True if header is detected, False otherwise
        """
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                return not (first_line.startswith("E,") or first_line.startswith("D,"))
        except Exception as e:
            raise Exception(f"Error detecting header: {str(e)}")

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
            CREATE TABLE IF NOT EXISTS FEENCABEZADO (
                {', '.join(encabezado_columns)}
            )
            """

            # Create FEDETALLE table
            detalle_columns = []
            for col_name, (_, dtype) in self.mapping["csv"]["FEDETALLE"].items():
                sql_type = self._get_sql_type(dtype)
                detalle_columns.append(f"{col_name} {sql_type}")

            create_detalle = f"""
            CREATE TABLE IF NOT EXISTS FEDETALLE (
                {', '.join(detalle_columns)}
            )
            """

            with self.engine.connect() as conn:
                conn.execute(text(create_encabezado))
                conn.execute(text(create_detalle))
                conn.commit()

        except Exception as e:
            raise Exception(f"Error creating database tables: {str(e)}")

    def _get_sql_type(self, dtype: str) -> str:
        """
        Convert mapping data types to SQL data types.

        Args:
            dtype (str): Data type from mapping

        Returns:
            str: Corresponding SQL data type
        """
        type_mapping = {
            "char": "VARCHAR(255)",
            "numeric": "DECIMAL(18,2)",
            "int": "INTEGER",
            "bit": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP",
        }
        return type_mapping.get(dtype, "VARCHAR(255)")

    def process_and_insert(
        self, csv_file: str, batch_size: int = 1000
    ) -> Tuple[int, int]:
        """
        Process the CSV file and insert data into database tables.

        Args:
            csv_file (str): Path to the CSV file
            batch_size (int): Number of records to insert in each batch

        Returns:
            Tuple containing (encabezado_count, detalle_count)
        """
        try:
            # Ensure tables exist
            # self._create_tables()

            # Process CSV file
            has_header = self._detect_header(csv_file)
            df = pd.read_csv(csv_file, header=0 if has_header else None, dtype=str)

            if not has_header:
                max_columns = max(
                    len(self.encabezado_columns), len(self.detalle_columns)
                )
                df.columns = [f"col_{i}" for i in range(max_columns)]

            # Split and process data
            encabezado_mask = df.iloc[:, 0] == "E"
            detalle_mask = df.iloc[:, 0] == "D"

            encabezado_df = self._apply_mapping(
                df[encabezado_mask].copy(), "FEENCABEZADO"
            )
            detalle_df = self._apply_mapping(df[detalle_mask].copy(), "FEDETALLE")

            # Insert data in batches
            encabezado_count = self._batch_insert(
                encabezado_df, "FEENCABEZADO", batch_size
            )
            detalle_count = self._batch_insert(detalle_df, "FEDETALLE", batch_size)

            return encabezado_count, detalle_count

        except Exception as e:
            raise Exception(f"Error processing and inserting data: {str(e)}")

    def _batch_insert(self, df: pd.DataFrame, table_name: str, batch_size: int) -> int:
        """
        Insert DataFrame into database table in batches.

        Args:
            df (pd.DataFrame): DataFrame to insert
            table_name (str): Target table name
            batch_size (int): Number of records per batch

        Returns:
            int: Number of records inserted
        """
        total_rows = 0
        try:
            for start in range(0, len(df), batch_size):
                end = start + batch_size
                batch_df = df.iloc[start:end]

                with self.engine as conn:
                    batch_df.to_sql(
                        table_name,
                        conn,
                        if_exists="append",
                        index=False,
                        method="multi",
                    )
                total_rows += len(batch_df)

            return total_rows

        except Exception as e:
            raise Exception(f"Error inserting batch into {table_name}: {str(e)}")

    def _apply_mapping(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Apply the mapping configuration to the DataFrame using optimized construction.

        Args:
            df (pd.DataFrame): Input DataFrame
            table_name (str): Name of the table mapping to apply

        Returns:
            pd.DataFrame: Processed DataFrame with applied mappings
        """
        mapping = self.mapping["csv"][table_name]
        processed_columns = {}

        for col_name, (source_col, dtype) in mapping.items():
            try:
                # Get the source column from the DataFrame
                if source_col in df.columns:
                    data = df[source_col]
                else:
                    # If column doesn't exist, create empty column
                    data = pd.Series(index=df.index)

                # Convert data type
                if dtype == "numeric":
                    data = pd.to_numeric(data, errors="coerce")
                elif dtype == "int":
                    data = pd.to_numeric(data, errors="coerce").astype("Int64")
                elif dtype == "bit":
                    data = pd.to_numeric(data, errors="coerce").astype("Int64")
                elif dtype == "date":
                    data = pd.to_datetime(data, errors="coerce").dt.date
                elif dtype == "datetime":
                    data = pd.to_datetime(data, errors="coerce")

                processed_columns[col_name] = data

            except Exception as e:
                print(f"Warning: Error processing column {col_name}: {str(e)}")
                processed_columns[col_name] = pd.Series(index=df.index)

        # Crear el DataFrame final usando pd.concat para mejor rendimiento
        return pd.concat(processed_columns, axis=1)
