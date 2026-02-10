import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

import time

import pyodbc
from sqlalchemy import (Column, MetaData, String, Table, create_engine, select,
                        update)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from db.uDB import *
from glib.Servicios import *

from glib.ufe import *

if __name__ == "__main__":
    #Enviar XML
    ServicioEnvioAprobacionComercial()
    
