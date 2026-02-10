import os
import sys

import requests

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from config.uGlobalConfig import *
from db.uDB import *
from glib.log_g import log_event, setup_logger
from glib.Servicios import *
from glib.ufe import *

logger = setup_logger("FEEnvioASESYS.log")


if __name__ == "__main__":

    UnlockCK()
    GConfig.cargar(1)

    # Conexión a la base de datos
    cn1 = ConectarDB()
    # Cambia xxxxxxxxx por el RNC que quieras consultar
    rnc = "131709745"

    url = f"https://ecf.dgii.gov.do/ecf/consultadirectorio/api/consultas/obtenerdirectorioporrnc?RNC={rnc}"

    headers = {
        "accept": "application/json",
        "Authorization": f"bearer {ObtennerToken(cn1,'106014281')}",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print(f"Error: {response.status_code} - {response.text}")
