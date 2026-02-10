import os, sqlite3, json, datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(project_root, "data")
os.makedirs(DATA_DIR, exist_ok=True)

SQLITE_PATH = os.path.join(DATA_DIR, "procedimientos.db")

def ensure_audit():
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Bitacora (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            actor TEXT,
            modulo TEXT,
            accion TEXT,
            objeto TEXT,
            detalle TEXT
        )
    """)
    conn.commit()
    conn.close()

ensure_audit()

def log_event(modulo: str, accion: str, objeto: str = "", detalle: str = "", actor: str = "local"):
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Bitacora (ts, actor, modulo, accion, objeto, detalle) VALUES (?,?,?,?,?,?)",
            (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), actor, modulo, accion, objeto, detalle[:2000])
        )
        conn.commit()
        conn.close()
    except Exception:
        # No romper el flujo por errores de auditoría
        pass