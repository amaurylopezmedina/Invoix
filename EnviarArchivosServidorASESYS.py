import time

import pyodbc
from sqlalchemy import (Column, MetaData, String, Table, create_engine, select,
                        update)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from db.uDB import *
from glib.Servicios import *
from glib.ufe import *

from config.uGlobalConfig import *

                    