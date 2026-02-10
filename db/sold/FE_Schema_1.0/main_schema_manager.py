import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


import glob
import json
import traceback

import pyodbc

from config.uGlobalConfig import *
from db.uDB import *
from glib.log_g import log_event, setup_logger
from glib.Servicios import *
from glib.ufe import *
from glib.uGlobalLib import *


def apply_table(cursor, cfg):
    table = cfg["table"]
    schema = cfg.get("schema", "dbo")
    cursor.execute(
        f"IF OBJECT_ID('{schema}.{table}', 'U') IS NULL CREATE TABLE {schema}.{table} (id int)"
    )
    for col, meta in cfg["fields"].items():
        cursor.execute(
            f"""
        IF COL_LENGTH('{schema}.{table}', '{col}') IS NULL
            ALTER TABLE {schema}.{table} ADD {col} {meta['type']}
        """
        )


def apply_ddl(cursor, cfg):
    cursor.execute(cfg["ddl"])


def main():
    cn = ConectarDB()
    cur = cn.cursor

    for f in glob.glob("*.table.json"):
        apply_table(cur, json.load(open(f)))

    for f in glob.glob("*.view.json"):
        apply_ddl(cur, json.load(open(f)))

    for f in glob.glob("*.proc.json"):
        apply_ddl(cur, json.load(open(f)))


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
