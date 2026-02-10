import os, sys, json
from urllib.parse import quote_plus

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

CONFIG_DIR = os.path.join(project_root, "config")
CNDB_PATH = os.path.join(CONFIG_DIR, "CNDB.json")
PROFILES_PATH = os.path.join(CONFIG_DIR, "profiles.json")

DEFAULT_PROFILE_NAME = "default"

def ensure_dirs():
    os.makedirs(CONFIG_DIR, exist_ok=True)

def load_cndb():
    ensure_dirs()
    if not os.path.exists(CNDB_PATH):
        raise FileNotFoundError(f"No se encontró CNDB.json en {CNDB_PATH}")
    with open(CNDB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cndb(cfg: dict):
    ensure_dirs()
    with open(CNDB_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def load_profiles():
    ensure_dirs()
    if not os.path.exists(PROFILES_PATH):
        # construir desde CNDB si existe
        if os.path.exists(CNDB_PATH):
            c = load_cndb()
            data = {"default": DEFAULT_PROFILE_NAME, "profiles": {DEFAULT_PROFILE_NAME: c}}
            return data
        return {"default": DEFAULT_PROFILE_NAME, "profiles": {}}
    with open(PROFILES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profiles(data: dict):
    ensure_dirs()
    with open(PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_effective_config(profile_name: str | None = None) -> dict:
    data = load_profiles()
    if not data.get("profiles"):
        # fallback a CNDB.json si no hay perfiles
        return load_cndb()
    if profile_name is None:
        profile_name = data.get("default") or DEFAULT_PROFILE_NAME
    cfg = data["profiles"].get(profile_name)
    if not cfg:
        raise KeyError(f"No existe el perfil '{profile_name}' en profiles.json")
    return cfg

def make_conn_str(cfg: dict) -> str:
    if cfg.get("AutenticacionUsuario", False):
        return (
            f"mssql+pyodbc://@{cfg['Servidor']},{cfg['Puerto']}/{cfg['DB']}?"
            f"driver={quote_plus(cfg['DBMS'])}&trusted_connection=yes"
        )
    else:
        return (
            f"mssql+pyodbc://{quote_plus(cfg['Usuario'])}:{quote_plus(cfg['Contrasena'])}"
            f"@{cfg['Servidor']},{cfg['Puerto']}/{cfg['DB']}?driver={quote_plus(cfg['DBMS'])}"
        )