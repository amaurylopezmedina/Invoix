import os
import sys
import traceback

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

import time
import traceback
from collections import OrderedDict

import chilkat2
import portalocker
import pyodbc
from flask import Response
from sqlalchemy import Column, MetaData, String, Table, create_engine, select, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.uGlobalConfig import *
from db.uDB import *
from glib.log_g import log_event, setup_logger
from glib.Servicios import *
from glib.ufe import *

logger = setup_logger("FEConsulta.log")


if __name__ == "__main__":

    # Evitar que el programa se ejecute mas de una vez
    ################################################################################################
    lock_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "FEConsultaEstadoECF.lock"
    )

    # Abrir el archivo para bloqueo
    lock_file = open(lock_file_path, "w")
    try:
        # Intentar bloquear el archivo de forma exclusiva y no bloqueante
        portalocker.lock(lock_file, portalocker.LOCK_EX | portalocker.LOCK_NB)

        # Si llegamos aquí, tenemos el bloqueo

        # Escribir el PID para identificación
        lock_file.write(f"{os.getpid()}")
        lock_file.flush()
    except portalocker.LockException:
        print("¡Ya hay otra instancia del programa en ejecución!")
        sys.exit(1)

    GConfig.cargar(1)

    # Conexión a la base de datos
    cn1 = ConectarDB()
    mostrarConfiguracion(GConfig, cn1)

    IConfig = load_interval_config()
    check_interval = IConfig.get("check_interval_consulta", 5)
    logger.info(f"Intervalo de chequeo configurado: {check_interval} segundos")

    """while True:
        try:
            query = f"Select * from vFEEncabezado  WITH (NOLOCK) where EstadoFiscal = 4 and  TipoECFL = 'E' order by fechacreacion"

            vFEEncabezado = cn1.fetch_query(query)
            for row in vFEEncabezado:
                ConsultaECF(cn1, row)
        except Exception as e:
            logger.error(f"Error en el bucle principal: {e}")"""

    while True:
        try:
            query = """
                SELECT TOP 5000 *
                FROM vFEEncabezado WITH (NOLOCK)
                WHERE EstadoFiscal = 4
                AND TipoECFL = 'E'
                ORDER BY FechaCreacion
            """

            cursor = cn1.connection.cursor()

            # Timeout real para evitar bloqueos largos
            cursor.execute("SET LOCK_TIMEOUT 3000;")  # 3 segundos

            cursor.execute(query)

            row = cursor.fetchone()
            procesados = 0

            while row:
                ConsultaECF(cn1, row)
                # ConsultaECFExiste(cn1, row)
                procesados += 1
                row = cursor.fetchone()

            cursor.close()

            if procesados == 0:
                time.sleep(check_interval)

        except Exception as e:
            logger.error(
                f"Error en el bucle principal: {e}:{ traceback.extract_tb(sys.exc_info()[2])}"
            )
