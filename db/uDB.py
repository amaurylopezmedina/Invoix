import os
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
from typing import List, Optional, Tuple

import pyodbc

from db.DBInstaller import DBInstaller
from glib.log_g import log_event, setup_logger

# Executor global (1 o más hilos según carga)
_executor_estado_fiscal = ThreadPoolExecutor(max_workers=5)

pyodbc.pooling = True  # MÁS RÁPIDO

logger = setup_logger("uDB.log")


class ConectarDB:
    def __init__(self):
        """Inicializa la clase y la conexión a la BD usando cn.ini"""
        self.connection = self.get_db_connection()

        # Cursor persistente para writes (rápido)
        self.cursor = self.connection.cursor()
        self.cursor.fast_executemany = True

        # Cursor separado SOLO para lecturas
        self.read_cursor = self.connection.cursor()

        # Instalar estructura
        self.installer = DBInstaller(self)
        self.installer.instalar()

    # --------------------------------------------------------
    #  Cargar connection string desde cn.ini
    # --------------------------------------------------------
    def _load_connection_string(self) -> str:
        config_path = None

        # 1) Preferir config editable junto al ejecutable (distribución típica)
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            candidate = os.path.join(exe_dir, "config", "cn.ini")
            if os.path.exists(candidate):
                config_path = candidate

            # 2) Fallback: recursos empaquetados (onefile => sys._MEIPASS)
            if not config_path and hasattr(sys, "_MEIPASS"):
                candidate = os.path.join(sys._MEIPASS, "config", "cn.ini")
                if os.path.exists(candidate):
                    config_path = candidate
        else:
            # En desarrollo, la raíz del proyecto está arriba de db/
            project_root = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(project_root)
            candidate = os.path.join(project_root, "config", "cn.ini")
            if os.path.exists(candidate):
                config_path = candidate

        if not config_path:
            raise FileNotFoundError(
                "No se encontró config/cn.ini. "
                "Se buscó junto al ejecutable y/o en sys._MEIPASS (si aplica)."
            )

        config = ConfigParser()
        config.read(config_path)

        conn_str = config.get("database", "connection_string", fallback=None)
        if not conn_str:
            raise ValueError("No se encontró 'connection_string' en config/cn.ini")
        return conn_str

    def get_db_connection(self):
        connection_string = self._load_connection_string()

        return pyodbc.connect(
            connection_string, autocommit=True, timeout=5  # Solo timeout de conexión
        )

    # --------------------------------------------------------
    # Ejecutar consultas rápidas
    # --------------------------------------------------------
    def execute_query(self, query: str, params: Optional[tuple] = None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            # Limpiar posibles resultsets (SPs que devuelven algo)
            while self.cursor.nextset():
                pass

        except Exception as e:
            raise Exception(
                f"Error ejecutando query: {e}:{ traceback.extract_tb(sys.exc_info()[2])}"
            )

    # --------------------------------------------------------
    # SELECT rápido usando cursor separado
    # --------------------------------------------------------
    def fetch_query(self, query: str, params: Optional[tuple] = None) -> List[Tuple]:

        try:

            if params:
                self.read_cursor.execute(query, params)
            else:
                self.read_cursor.execute(query)

            rows = self.read_cursor.fetchall()
            return rows

        except Exception as e:
            raise Exception(
                f"Error ejecutando SELECT: {e}:{ traceback.extract_tb(sys.exc_info()[2])}"
            )

    # --------------------------------------------------------
    # Verificar vistas
    # --------------------------------------------------------
    def vista_existe(self, vista_name: str, schema: Optional[str] = None) -> bool:

        if schema:
            query = """
                SELECT name 
                FROM sys.views 
                WHERE name = ? AND schema_id = SCHEMA_ID(?)
            """
            params = (vista_name, schema)
        else:
            query = "SELECT name FROM sys.views WHERE name = ?"
            params = vista_name

        result = self.fetch_query(query, params)
        return len(result) > 0

    # --------------------------------------------------------
    # Comparar y borrar SP si cambió
    # --------------------------------------------------------
    def comparar_sp(self, nombre_sp, codigo_python):
        # Validación básica
        if (
            not isinstance(nombre_sp, str)
            or not nombre_sp.replace("_", "")
            .replace("[", "")
            .replace("]", "")
            .isalnum()
        ):
            raise ValueError("nombre_sp debe ser un nombre válido de procedimiento")

        sql = "SELECT OBJECT_DEFINITION(OBJECT_ID(?)) AS Codigo"
        resultado = self.fetch_query(sql, (nombre_sp,))

        if not resultado or not resultado[0][0]:
            return False

        codigo_sqlserver = resultado[0][0]

        def normalizar(texto):
            return (
                texto.replace(" ", "")
                .replace("\n", "")
                .replace("\r", "")
                .replace("\t", "")
                .lower()
            )

        if normalizar(codigo_sqlserver) == normalizar(codigo_python):
            return False

        # Son diferentes → borrar
        try:
            self.execute_query("DROP PROCEDURE ?", (nombre_sp,))
            return True
        except:
            return True

    def actualizar_estado_fiscal(
        self,
        Tabla,
        EstadoFiscal,
        ResultadoEstadoFiscal,
        CampoRNC,
        CampoENCF,
        RNCEmisor,
        eNCF,
        CodigoSeguridad=None,
        CodigoSeguridadCF=None,
        FechaFirma=None,
        trackId=None,
        MontoDGII=None,
        MontoITBISDGII=None,
        Enviado=None,
        XMLGenerado=None,
    ):
        # Validación básica de entradas (security)
        if not isinstance(Tabla, str) or not Tabla.isidentifier():
            raise ValueError("Tabla debe ser un nombre válido de tabla")
        if not isinstance(CampoRNC, str) or not CampoRNC.replace("_", "").isalnum():
            raise ValueError("CampoRNC debe ser un nombre válido de campo")
        if not isinstance(CampoENCF, str) or not CampoENCF.replace("_", "").isalnum():
            raise ValueError("CampoENCF debe ser un nombre válido de campo")

        log_event(
            logger,
            "info",
            f"Iniciando actualización del estado fiscal para {hash(eNCF)}...",  # Sanitiza log
        )

        self.installer.asegurar_tabla(Tabla)

        # ==========================================================
        # 1. Intentar SP principal (YA maneja transacciones internas)
        # ==========================================================
        try:
            self.execute_query(
                """
                EXEC sp_ActualizarEstadoFiscal
                    @Tabla=?, @EstadoFiscal=?, @ResultadoEstadoFiscal=?,
                    @CampoRNC=?, @CampoENCF=?, @RNCEmisor=?, @eNCF=?,
                    @TrackId=?, @CodigoSeguridad=?, @CodigoSeguridadCF=?,
                    @FechaFirma=?, @MontoDGII=?, @MontoITBISDGII=?, @Enviado=?
            """,
                (
                    Tabla,
                    EstadoFiscal,
                    ResultadoEstadoFiscal,
                    CampoRNC,
                    CampoENCF,
                    RNCEmisor,
                    eNCF,
                    trackId,
                    CodigoSeguridad,
                    CodigoSeguridadCF,
                    FechaFirma,
                    MontoDGII,
                    MontoITBISDGII,
                    Enviado,
                ),
            )

            # AUDITORÍA
            self.execute_query(
                """
                EXEC sp_LogEstadoFiscal
                    @Tabla=?, @RNCEmisor=?, @eNCF=?,
                    @EstadoAnterior=?, @EstadoNuevo=?,
                    @ResultadoEstadoFiscal=?, @TrackId=?,
                    @CodigoSeguridad=?, @CodigoSeguridadCF=?, @FechaFirma=?,
                    @MontoDGII=?, @MontoITBISDGII=?, @Enviado=?,
                    @XMLGenerado=?, @ExtraInfo=?
            """,
                (
                    Tabla,
                    RNCEmisor,
                    eNCF,
                    None,
                    EstadoFiscal,
                    ResultadoEstadoFiscal,
                    trackId,
                    CodigoSeguridad,
                    CodigoSeguridadCF,
                    FechaFirma,
                    MontoDGII,
                    MontoITBISDGII,
                    Enviado,
                    XMLGenerado,
                    "Actualización mediante SP",
                ),
            )

            log_event(
                logger,
                "info",
                f"Actualización del estado fiscal para {hash(eNCF)} completado:EstadoFiscal:{EstadoFiscal},ResultadoEstadoFiscal:{ResultadoEstadoFiscal}",
            )
            return True, "Actualizado mediante SP"

        # ====================================================================
        # FALLBACK (solo si el SP falla)
        # ====================================================================,
        except Exception:
            log_event(
                logger,
                "info",
                "Procedimiento almacenado falló. Usando respaldo...",
            )

        # ==========================================================
        # 2. RESPALDO MANUAL (CON parámetros preparados para seguridad)
        # ==========================================================
        set_clauses = []
        params = []

        set_clauses.append("EstadoFiscal = ?")
        params.append(EstadoFiscal)

        set_clauses.append("TrackId = ?")
        params.append(trackId or "")

        set_clauses.append("ResultadoEstadoFiscal = ?")
        params.append(ResultadoEstadoFiscal or "")

        if CodigoSeguridad is not None:
            set_clauses.append("CodigoSeguridad = ?")
            params.append(CodigoSeguridad)
        if CodigoSeguridadCF is not None:
            set_clauses.append("CodigoSeguridadCF = ?")
            params.append(CodigoSeguridadCF)
        if FechaFirma is not None:
            set_clauses.append("FechaFirma = ?")
            params.append(FechaFirma)
        if MontoDGII is not None:
            set_clauses.append("MontoDGII = ?")
            params.append(float(MontoDGII))
        if MontoITBISDGII is not None:
            set_clauses.append("MontoITBISDGII = ?")
            params.append(float(MontoITBISDGII))

        if Enviado is not None:
            set_clauses.append("Enviado = ?")
            params.append(Enviado)

        if XMLGenerado is not None:
            set_clauses.append("XMLGenerado = ?")
            params.append(XMLGenerado)

        update_sql = f"UPDATE {Tabla} SET {', '.join(set_clauses)} WHERE {CampoRNC} = ? AND {CampoENCF} = ?"
        params.extend([RNCEmisor, eNCF])

        log_event(logger, "info", f"Ejecutando respaldo seguro para tabla {Tabla}")

        self.execute_query(update_sql, tuple(params))

        # AUDITORÍA desde fallback
        self.execute_query(
            """
            EXEC sp_LogEstadoFiscal
                @Tabla=?, @RNCEmisor=?, @eNCF=?,
                @EstadoAnterior=?, @EstadoNuevo=?,
                @ResultadoEstadoFiscal=?, @TrackId=?,
                @CodigoSeguridad=?, @CodigoSeguridadCF=?, @FechaFirma=?,
                @MontoDGII=?, @MontoITBISDGII=?, @Enviado=?,
                @XMLGenerado=?, @ExtraInfo=?
        """,
            (
                Tabla,
                RNCEmisor,
                eNCF,
                None,
                EstadoFiscal,
                ResultadoEstadoFiscal,
                trackId,
                CodigoSeguridad,
                CodigoSeguridadCF,
                FechaFirma,
                MontoDGII,
                MontoITBISDGII,
                Enviado,
                XMLGenerado,
                "Actualización mediante SP",
            ),
        )
        return True, "Actualizado mediante respaldo"

    def actualizar_estado_fiscal_async(self, *args, wait: bool = False, **kwargs):
        """
        Ejecuta actualizar_estado_fiscal en segundo plano.

        wait = False  -> fire-and-forget (default)
        wait = True   -> espera resultado
        """

        def _task():
            try:
                return self.actualizar_estado_fiscal(*args, **kwargs)
            except Exception as e:
                log_event(
                    logger,
                    "error",
                    f"Error en actualizar_estado_fiscal_async: {e} | {traceback.format_exc()}",
                )
                return False, str(e)

        future = _executor_estado_fiscal.submit(_task)

        if wait:
            return future.result()

        return True, "Ejecutado en segundo plano"

    def _get_encabezado(self, rncs: str, encfs: str):
        query = """
            SELECT *
            FROM vFEEncabezado WITH (NOLOCK)
            WHERE rncemisor = ? AND encf = ?
        """

        cursor = self.connection.cursor()
        cursor.execute(query, (rncs, encfs))

        rows = cursor.fetchall()
        cursor.close()

        return rows or []

    def _count_encabezado(self, rncs: str, encfs: str):
        query = """
            SELECT COUNT(*)
            FROM vFEEncabezado WITH (NOLOCK)
            WHERE rncemisor = ? AND encf = ?
        """

        cursor = self.connection.cursor()
        cursor.execute(query, (rncs, encfs))
        count = cursor.fetchone()[0]
        cursor.close()

        return count

    def _get_detalle(self, rncs: str, encfs: str):
        query = """
            SELECT *
            FROM vFEDetalle WITH (NOLOCK)
            WHERE rncemisor = ? AND encf = ?
        """

        cursor = self.connection.cursor()
        cursor.execute(query, (rncs, encfs))

        rows = cursor.fetchall()
        cursor.close()

        return rows or []

    def _count_detalle(self, rncs: str, encfs: str):
        query = """
            SELECT COUNT(*)
            FROM vFEDEtalle WITH (NOLOCK)
            WHERE rncemisor = ? AND encf = ?
        """

        cursor = self.connection.cursor()
        cursor.execute(query, (rncs, encfs))
        count = cursor.fetchone()[0]
        cursor.close()

        return count

    def _get_tablapago(self, rncs: str, encfs: str):
        query = """
            SELECT *
            FROM vFETablaPago WITH (NOLOCK)
            WHERE rncemisor = ? AND encf = ?
        """

        cursor = self.connection.cursor()
        cursor.execute(query, (rncs, encfs))

        rows = cursor.fetchall()
        cursor.close()

        return rows or []

    def _get_tablaimpuestosadicionales(self, rncs: str, encfs: str):
        query = """
            SELECT *
            FROM vFETablaImpuestosAdicionales WITH (NOLOCK)
            WHERE rncemisor = ? AND encf = ?
        """

        cursor = self.connection.cursor()
        cursor.execute(query, (rncs, encfs))

        rows = cursor.fetchall()
        cursor.close()

        return rows or []

    def _get_tabladescuentosyrecargos(self, rncs: str, encfs: str):
        query = """
            SELECT *
            FROM vFETablaDescuentosyRecargos WITH (NOLOCK)
            WHERE rncemisor = ? AND encf = ?
        """

        cursor = self.connection.cursor()
        cursor.execute(query, (rncs, encfs))

        rows = cursor.fetchall()
        cursor.close()

        return rows or []

    def _get_totales(self, rncs: str, encfs: str):
        query = """
            SELECT *
            FROM vFETotales WITH (NOLOCK)
            WHERE rncemisor = ? AND encf = ?
        """

        cursor = self.connection.cursor()
        cursor.execute(query, (rncs, encfs))

        rows = cursor.fetchall()
        cursor.close()

        return rows or []

    def ejecutar_sustitucion_ncf(
        self,
        Tabla: str,
        CampoNumero: str,
        RNCEmisorFiltro: str,
        NCFFiltro: str,
    ):
        """
        Ejecuta el procedimiento almacenado:
        sp_SustituirNCFRechazados

        Returns:
            (bool, str): (True, mensaje) si fue exitoso, (False, error) si falló
        """

        try:
            sql = """
                EXEC sp_SustituirNCFRechazados
                    @Tabla = ?,
                    @CampoNumero = ?,
                    @RNCEmisorFiltro = ?,
                    @NCFFiltro = ?
            """

            cursor = self.connection.cursor()

            # Evitar bloqueos largos
            cursor.execute("SET LOCK_TIMEOUT 3000;")

            cursor.execute(
                sql,
                (
                    Tabla.strip(),
                    CampoNumero.strip(),
                    RNCEmisorFiltro.strip(),
                    NCFFiltro.strip(),
                ),
            )

            # Limpia cualquier resultset que el SP pueda devolver
            while cursor.nextset():
                pass

            cursor.close()

            return True, "Sustitución de NCF ejecutada correctamente."

        except Exception as e:
            return False, f"Error ejecutando sp_SustituirNCFRechazados: {e}"
