
import os
import json
from datetime import datetime

from db.uDB import ConectarDB

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "snapshots")

def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def create_snapshot(nombre_version: str, ambiente: str = "DEV"):
    """Toma un snapshot de esquema (solo estructura) y lo guarda en snapshots/<nombre>.json"""
    _ensure_dir(SNAPSHOT_DIR)
    cn = ConectarDB(ambiente)
    cur = cn.cursor

    # Tablas
    tables = []
    cur.execute("""
        SELECT t.name, s.name
        FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id
    """)
    for name, schema in cur.fetchall():
        tables.append({"table": name, "schema": schema})

    data = {
        "version": nombre_version,
        "created_at": datetime.utcnow().isoformat(),
        "ambiente": ambiente,
        "tables": tables,
    }

    file_path = os.path.join(SNAPSHOT_DIR, f"{nombre_version}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return file_path

def list_snapshots():
    _ensure_dir(SNAPSHOT_DIR)
    return [f for f in os.listdir(SNAPSHOT_DIR) if f.lower().endswith(".json")]

def load_snapshot(nombre_version: str):
    file_path = os.path.join(SNAPSHOT_DIR, f"{nombre_version}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def plan_rollback(current_version: str, target_version: str):
    """Devuelve un plan conceptual de rollback (no ejecuta cambios)."""
    return {
        "from": current_version,
        "to": target_version,
        "steps": [
            "Drop FKs en orden seguro",
            "Ajustar PK/Índices si difieren",
            "Aplicar cambios de columnas (ADD/DROP/ALTER)",
            "Recrear FKs",
        ],
    }

def execute_rollback(nombre_version: str, ambiente: str = "DEV", mode: str = "mixed"):
    """Punto de entrada para rollback. 'mode' puede ser: 'structure', 'data', 'mixed'.

    En este módulo sólo se implementa 'structure'; la parte de datos se deja para confirmación UI.
    """
    snapshot = load_snapshot(nombre_version)
    # Aquí se podría implementar la lógica avanzada; por ahora sólo validamos que el snapshot exista.
    return {
        "snapshot": snapshot.get("version"),
        "ambiente": ambiente,
        "mode": mode,
        "status": "planned",
    }
