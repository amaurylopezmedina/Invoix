import sys
import time

import pyodbc
from sqlalchemy import Column, MetaData, String, Table, create_engine, select, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from db.database import fetch_invoice_data
from db.uDB import *
from glib.ufe import *
from glib.uGlobalLib import *

from .log_g import log_event, setup_logger

# import locale


# locale.setlocale(locale.LC_TIME, 'es_ES')

# def ServicioEnvio():

# def ServicioFirma():


# ef ServicioGenerarXML():


logger = setup_logger("LogGeneral.log")


def ServicioGenerarXMLAprobacionComercial():
    UnlockCK()
    GConfig.cargar(1)

    # Conexión a la base de datos
    cn1 = ConectarDB()

    try:
        query = f"Select * from AprobacionComercial with (nolock) where EstadoFiscal = 1 order by FechaCreacion"
        qAprobacionComercial = cn1.fetch_query(query)
        for row in qAprobacionComercial:
            if int(row.EstadoFiscal) == 1:
                try:
                    GenerarXMLAprobacionComercial(
                        cn1, row.RNCEmisor.strip(), row.eNCF.strip()
                    )
                    Tabla = "AprobacionComercial"
                    query = f"Update {row.Tabla} set EstadoFiscal = 2  where  {row.campo1} = '{row.RNCEmisor.strip()}' and {row.campo2} = '{row.eNCF.strip()}'"
                    cn1.execute_query(query)
                except Exception as e:
                    logger.error(f"Error al procesar el registro: {row}. Detalles: {e}")
        # time.sleep(5)
    except Exception as e:
        logger.error(f"Error en el bucle principal: {e}")


def ServicioFirmaAprobacionComercial():
    UnlockCK()
    GConfig.cargar(1)

    # Conexión a la base de datos
    cn1 = ConectarDB()

    try:
        query = f"Select * from AprobacionComercialwith (nolock) where EstadoFiscal = 2 order by FechaCreacion"
        vFEEncabezado = cn1.fetch_query(query)
        for row in vFEEncabezado:
            if int(row.EstadoFiscal) == 2:
                try:
                    NombreXML = (
                        GConfig.FEDGII.RutaXML
                        + f"AprobacionComercial\\{row.RNCEmisor.strip()+row.eNCF.strip()}.xml"
                    )
                    # Controlar si el archivo existe, si no existe generarlo o tomar decision en base a su estado
                    _, _, FechayHoradeFirma = FirmarXML(NombreXML, "ACECF")
                    Tabla = "AprobacionComercial"
                    query = f"Update {row.Tabla.strip()} set EstadoFiscal = 3,FechaHoraFirma='{FechayHoradeFirma}'  where {row.campo1.strip()} = '{row.eNCF.strip()}' and {row.campo2.strip()} = '{row.RNCEmisor.strip()}'"
                    cn1.execute_query(query)

                except Exception as e:
                    logger.error(f"Error al procesar el registro: {row}. Detalles: {e}")

        # time.sleep(5)

    except Exception as e:
        logger.error(f"Error en el bucle principal: {e}")


def ServicioEnvioAprobacionComercial():
    UnlockCK()
    GConfig.cargar(1)

    # Conexión a la base de datos
    cn1 = ConectarDB()

    try:
        query = f"Select * from AprobacionComercial with (nolock) where  EstadoFiscal = 3 order by FechaCreacion"
        vAprobacionComercial = cn1.fetch_query(query)
        for row in vAprobacionComercial:
            if int(row.EstadoFiscal) == 3:
                try:
                    # Procesar el envío de XML
                    Ruta = "AprobacionComercial\\firmadas\\"
                    # Ruta     = 'AprobacionComercial\\'

                    NombreXML = f"{GConfig.FEDGII.RutaXML}{Ruta}{row.RNCEmisor.strip()+row.eNCF.strip()}.xml"

                    # REVISAR SI EL ARCHIVO EXISTE

                    codigo, estado, mensaje = EnvioAprobacionComercial(
                        NombreXML, ObtennerToken(cn1, row.RNCEmisor.strip())
                    )

                    query = f"Update AprobacionComercial set EstadoFiscal = 4,  DetalleMotivoRechazo= '{'Estado:'+estado+', Codigo:'+codigo+' - Mensaje:'+mensaje}' where eNCF = '{row.eNCF.strip()}' and RNCComprador = '{row.RNCComprador.strip()}'"
                    cn1.execute_query(query)

                    if False:
                        sbResponseBody = ConsultaEstadoECF(
                            row.RNCEmisor.strip(),
                            row.eNCF.strip(),
                            row.RNCComprador.strip(),
                            row.CodigoSeguridad.strip(),
                            ObtennerToken(cn1, row.RNCEmisor.strip()),
                        )

                        jsonResponse = chilkat2.JsonObject()
                        jsonResponse.LoadSb(sbResponseBody)
                        jsonResponse.EmitCompact = False
                        codigo = jsonResponse.IntOf("codigo")

                        if codigo == 0:
                            log_event(
                                logger,
                                "info",
                                f"No se pudo procesar el archivo: {NombreXML}",
                            )
                        elif codigo == 1:
                            log_event(
                                logger, "info", f"Envío exitoso de XML: {NombreXML}"
                            )
                            montoTotal = jsonResponse.IntOf("montoTotal")
                            totalITBIS = jsonResponse.IntOf("totalITBIS")

                            query = f"Update {Tabla} set MontoDGII = '{montoTotal}', MontoITBISDGII ='{totalITBIS}', where  eNCF = '{row.eNCF}' and RNCEmisor = '{row.RNCEmisor}'"
                            cn1.execute_query(query)

                            # Enviar XML
                            rlRecepcion, urlAceptacion, urlOpcional = (
                                ConsultaDirectorioRNC(
                                    row.RNCComprador.strip(),
                                    ObtennerToken(cn1, row.RNCEmisor.strip()),
                                )
                            )
                            if urlOpcional != "":
                                # Autenticarse
                                xy = 0
                            else:
                                # Enviar XML al RNC
                                yx = 0
                            # GRabar datos en tabla
                        elif codigo == 2:
                            # Agregar Consulta Resultado
                            i = 0
                            count_i = jsonResponse.SizeOfArray("mensajes")
                            while i < count_i:
                                jsonResponse.I = i
                                valor = jsonResponse.StringOf("mensajes[i].valor")
                                codigo = jsonResponse.IntOf("mensajes[i].codigo")
                                i = i + 1
                            query = f"Update transa01 set ResultadoEstadoFiscal = '{codigo}'-'{valor}', where documento = '{row.Documento}' and tipo = '{row.Documento}'"
                            cn1.execute_query(query)
                        # log_event(logger, "info",f"E XML: {NombreXML} fue rechazado")

                except Exception as e:
                    logger.error(f"Error al procesar el registro: {row}. Detalles: {e}")
        # time.sleep(5)
    except Exception as e:
        logger.error(f"Error en el bucle principal: {e}")
    except Exception as e:
        logger.error(f"Error en el bucle principal: {e}")
