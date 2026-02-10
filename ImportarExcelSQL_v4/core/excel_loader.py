import pandas as pd
import numpy as np


def load_excel(path_excel: str) -> pd.DataFrame:
    """
    Lee el Excel y reemplaza:
    - celdas vacías -> None
    - '#e' / '#E' -> None
    - 'NULL' (texto en Excel) -> None
    - 'nan', 'NaN' -> None
    - Cualquier cadena que contenga solo espacios -> None
    para que lleguen como NULL reales a SQL Server.
    """
    df = pd.read_excel(path_excel, dtype=str, engine='openpyxl')

    # Limpia espacios en blanco y convierte a None valores especiales
    def clean_value(v):
        if not isinstance(v, str):
            return v
        v = v.strip()
        # Lista de valores que deben convertirse a None
        if v.lower() in ['#e', 'null', 'nan', 'none', ''] or v.startswith('#e'):
            return None
        return v
    
    # Usar map en lugar de applymap (deprecated)
    df = df.map(clean_value)

    # Convierte NaN → None (que se traducen a NULL en SQL Server)
    df = df.where(pd.notnull(df), None)

    return df
