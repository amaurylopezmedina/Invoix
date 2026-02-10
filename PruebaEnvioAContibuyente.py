import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

import os
import sys
import time

import portalocker
import pyodbc
from sqlalchemy import Column, MetaData, String, Table, create_engine, select, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.uGlobalConfig import *
from db.uDB import *
from glib.log_g import log_event, setup_logger
from glib.ufe import *
from glib.uGlobalLib import *

logger = setup_logger("FEEnvioASESYS.log")


if __name__ == "__main__":

    ################################################################################################

    UnlockCK()
    GConfig.cargar(1)

    # Conexión a la base de datos
    cn1 = ConectarDB()

    """    ConsultaDirectorioServicios(cn1)

    rnc, nombre, urlRecepcion, urlAceptacion, urlOpcional = (
        ConsultaDirectorioServiciosRNC("102008531", ObtennerToken(cn1, "106014281"))
    )"""

    rnc, nombre, urlRecepcion, urlAceptacion, urlOpcional = (
        ConsultaDirectorioServiciosRNC("401506254", ObtennerToken(cn1, "131870201"))
    )

    print(ObtennerToken(cn1, "131870201", 2, urlOpcional))

    if validaurl(urlOpcional):

        URLSemilla = urlOpcional + "/fe/autenticacion/api/semilla"
        URLToken = urlOpcional + "/api/semilla/validacioncertificado"

        URLEnvioXML = urlRecepcion + "/fe/recepción/api/ecf"
        URLaprobacion = urlAceptacion + "/fe/aprobacioncomercial/api/ecf"
