import pandas as pd
import json
import sys
import traceback
from typing import Dict, Any, Tuple


class CSVImportMapper:
    def __init__(self, mapping_file: str):
        """
        Initialize the mapper with the JSON mapping file.

        Args:
            mapping_file (str): Path to the JSON mapping file
        """
        self.mapping = self._load_mapping(mapping_file)
        self.encabezado_columns = list(self.mapping["csv"]["FEENCABEZADO"].keys())
        self.detalle_columns = list(self.mapping["csv"]["FEDETALLE"].keys())

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
            raise Exception(
                f"Error loading mapping file: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
            )

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
                # Check if the first character is 'E' or 'D'
                return not (first_line.startswith("E,") or first_line.startswith("D,"))
        except Exception as e:
            raise Exception(
                f"Error detecting header: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
            )

    def process_csv(self, csv_file: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Process the CSV file and split it into encabezado and detalle DataFrames.

        Args:
            csv_file (str): Path to the CSV file

        Returns:
            Tuple containing (encabezado_df, detalle_df)
        """
        try:
            has_header = self._detect_header(csv_file)

            # Read CSV file
            df = pd.read_csv(
                csv_file,
                header=0 if has_header else None,
                dtype=str,  # Read all columns as string initially
            )

            # If no header, assign column names based on the maximum columns needed
            if not has_header:
                max_columns = max(
                    len(self.encabezado_columns), len(self.detalle_columns)
                )
                df.columns = [f"col_{i}" for i in range(max_columns)]

            # Split data based on first column
            encabezado_mask = df.iloc[:, 0] == "E"
            detalle_mask = df.iloc[:, 0] == "D"

            # Create separate DataFrames
            encabezado_df = df[encabezado_mask].copy()
            detalle_df = df[detalle_mask].copy()

            # Apply mappings and convert data types
            encabezado_df = self._apply_mapping(encabezado_df, "FEENCABEZADO")
            detalle_df = self._apply_mapping(detalle_df, "FEDETALLE")

            return encabezado_df, detalle_df

        except Exception as e:
            raise Exception(
                f"Error processing CSV file: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
            )

    def _apply_mapping(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Apply the mapping configuration to the DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame
            table_name (str): Name of the table mapping to apply

        Returns:
            pd.DataFrame: Processed DataFrame with applied mappings
        """
        mapping = self.mapping["csv"][table_name]
        result_df = pd.DataFrame()

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

                result_df[col_name] = data

            except Exception as e:
                print(
                    f"Warning: Error processing column {col_name}: {str(e)}:{ traceback.extract_tb(sys.exc_info()[2])}"
                )
                result_df[col_name] = None

        return result_df


def main():
    """
    Example usage of the CSVImportMapper class.
    """
    # Example usage
    mapper = CSVImportMapper("fm/datadefCarga.json")
    encabezado_df, detalle_df = mapper.process_csv("C:/XMLValidar/AR/E320000000002.csv")

    # Save to new CSV files
    encabezado_df.to_csv("encabezado_output.csv", index=False)
    detalle_df.to_csv("detalle_output.csv", index=False)


if __name__ == "__main__":
    main()
