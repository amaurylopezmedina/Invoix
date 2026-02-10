# ================================================================
# DBInstaller.py
# Encargado de validar, crear y sincronizar toda la estructura SQL
# (tablas y procedimientos almacenados)
# ================================================================

from datetime import datetime
from typing import Optional

from glib.log_g import log_event, setup_logger

logger = setup_logger("DBInstaller.log")


class DBInstaller:

    def __init__(self, db):
        """
        db debe ser tu clase de conexión:
        - db.execute_query(sql, params)
        - db.fetch_query(sql, params)
        """
        self.db = db

    # ================================================================
    # AUXILIAR — Compara SP con versión Python y lo elimina si difiere
    # ================================================================
    def comparar_sp_con_python(self, nombre_sp: str, codigo_python: str) -> bool:
        """
        Compara el SP almacenado en SQL Server con la definición de Python.

        RETURN:
        - True  → ES diferente y fue borrado
        - False → ES igual o NO existe
        """
        # Validación básica
        if (
            not isinstance(nombre_sp, str)
            or not nombre_sp.replace("_", "")
            .replace("[", "")
            .replace("]", "")
            .replace(".", "")
            .isalnum()
        ):
            raise ValueError("nombre_sp debe ser un nombre válido de procedimiento")

        sql = "SELECT OBJECT_DEFINITION(OBJECT_ID(?)) AS Codigo"
        resultado = self.db.fetch_query(sql, (nombre_sp,))

        # SP no existe
        if not resultado or not resultado[0][0]:
            return False

        codigo_sqlserver = resultado[0][0]

        # Normalizar para comparar contenido
        def normalizar(txt):
            return (
                txt.replace(" ", "")
                .replace("\n", "")
                .replace("\r", "")
                .replace("\t", "")
                .lower()
            )

        if normalizar(codigo_sqlserver) == normalizar(codigo_python):
            return False  # SP igual

        # Es diferente → borrar
        try:
            self.db.execute_query("DROP PROCEDURE ?", (nombre_sp,))
            return True
        except:
            return True  # aunque falle, es diferente

    # ================================================================
    # INSTALAR ESTRUCTURA COMPLETA
    # ================================================================
    def instalar(self):

        log_event(logger, "info", "Inicio verificación de estructura SQL...")

        # ------------------------------------------------------------
        # 1. Crear tabla de auditoría si no existe
        # ------------------------------------------------------------
        tabla = self.db.fetch_query(
            """
            SELECT 1 FROM sys.tables WHERE name='Log_EstadoFiscal'
        """
        )

        if not tabla:
            crear_tabla = """
            CREATE TABLE dbo.Log_EstadoFiscal (
                IdLog INT IDENTITY(1,1) PRIMARY KEY,
                FechaRegistro DATETIME NOT NULL DEFAULT GETDATE(),
                Tabla NVARCHAR(200) NOT NULL,
                RNCEmisor NVARCHAR(50) NOT NULL,
                eNCF NVARCHAR(50) NOT NULL,
                EstadoFiscalAnterior INT NULL,
                EstadoFiscalNuevo INT NOT NULL,
                ResultadoEstadoFiscal NVARCHAR(500) NULL,
                TrackId NVARCHAR(200) NULL,
                CodigoSeguridad NVARCHAR(200) NULL,
                CodigoSeguridadCF NVARCHAR(200) NULL,
                FechaFirma NVARCHAR(50) NULL,
                MontoDGII DECIMAL(18,2) NULL,
                MontoITBISDGII DECIMAL(18,2) NULL,
                XMLGenerado NVARCHAR(MAX) NULL,
                UsuarioSQL NVARCHAR(200) NULL,
                HostName NVARCHAR(200) NULL,
                ExtraInfo NVARCHAR(MAX) NULL,
                Enviado INT NULL
            );
            """
            self.db.execute_query(crear_tabla)

        # ------------------------------------------------------------
        # 2. SP: sp_LogEstadoFiscal (autosync)
        # ------------------------------------------------------------
        sp_log = r"""
                CREATE OR ALTER PROCEDURE dbo.sp_LogEstadoFiscal
                    @Tabla                NVARCHAR(200),
                    @RNCEmisor            NVARCHAR(50),
                    @eNCF                 NVARCHAR(50),

                    @EstadoAnterior       INT = NULL,
                    @EstadoNuevo          INT,

                    @ResultadoEstadoFiscal NVARCHAR(500) = NULL,
                    @TrackId               NVARCHAR(200) = NULL,
                    @CodigoSeguridad       NVARCHAR(200) = NULL,
                    @CodigoSeguridadCF     NVARCHAR(200) = NULL,
                    @FechaFirma            NVARCHAR(50)  = NULL,   -- 🔥 100% STRING
                    @MontoDGII             DECIMAL(18,2) = NULL,
                    @MontoITBISDGII        DECIMAL(18,2) = NULL,
                    @Enviado               INT = NULL,             -- 🔥 NUEVO

                    @XMLGenerado           NVARCHAR(MAX) = NULL,
                    @ExtraInfo             NVARCHAR(MAX) = NULL
                WITH ENCRYPTION
                AS
                BEGIN
                    SET NOCOUNT ON;
                    SET XACT_ABORT ON;

                    BEGIN TRY

                        INSERT INTO dbo.Log_EstadoFiscal (
                            Tabla, RNCEmisor, eNCF,
                            EstadoFiscalAnterior, EstadoFiscalNuevo,
                            ResultadoEstadoFiscal, TrackId,
                            CodigoSeguridad, CodigoSeguridadCF, FechaFirma,
                            MontoDGII, MontoITBISDGII, Enviado,
                            XMLGenerado, UsuarioSQL, HostName, ExtraInfo
                        )
                        VALUES (
                            @Tabla, @RNCEmisor, @eNCF,
                            @EstadoAnterior, @EstadoNuevo,
                            @ResultadoEstadoFiscal, @TrackId,
                            @CodigoSeguridad, @CodigoSeguridadCF, @FechaFirma,
                            @MontoDGII, @MontoITBISDGII, @Enviado,
                            @XMLGenerado, ORIGINAL_LOGIN(), HOST_NAME(), @ExtraInfo
                        );

                    END TRY
                    BEGIN CATCH
                        DECLARE @Err NVARCHAR(MAX) = ERROR_MESSAGE();
                        THROW 50052, @Err, 1; 
                    END CATCH

                END;
        """

        if self.comparar_sp_con_python("dbo.sp_LogEstadoFiscal", sp_log):
            self.db.execute_query(sp_log)
        else:
            existe = self.db.fetch_query(
                "SELECT 1 FROM sys.objects WHERE name='sp_LogEstadoFiscal' AND type='P'"
            )
            if not existe:
                self.db.execute_query(sp_log)

        # ------------------------------------------------------------
        # 3. SP: sp_ActualizarEstadoFiscal (autosync)
        # ------------------------------------------------------------
        sp_update = r"""
                CREATE OR ALTER PROCEDURE sp_ActualizarEstadoFiscal
                    @Tabla NVARCHAR(128) = NULL,
                    @EstadoFiscal INT,                             -- OBLIGATORIO
                    @EstadoImpresion INT = NULL,
                    @ResultadoEstadoFiscal NVARCHAR(255),          -- OBLIGATORIO
                    @CampoRNC NVARCHAR(50) = NULL,
                    @CampoENCF NVARCHAR(50) = NULL,
                    @RNCEmisor NVARCHAR(20) = NULL,
                    @eNCF NVARCHAR(20) = NULL,
                    @TrackId NVARCHAR(100) = NULL,
                    @CodigoSeguridad NVARCHAR(100) = NULL,
                    @CodigoSeguridadCF NVARCHAR(100) = NULL,
                    @FechaFirma NVARCHAR(50) = NULL,
                    @MontoDGII DECIMAL(18,2) = NULL,
                    @MontoITBISDGII DECIMAL(18,2) = NULL,
                    @Enviado BIT = NULL
                AS
                BEGIN
                    SET NOCOUNT ON;
                    SET XACT_ABORT ON;

                    BEGIN TRY
                        ------------------------------------------------------------
                        -- Validaciones mínimas (solo obligatorios)
                        ------------------------------------------------------------
                        IF @EstadoFiscal IS NULL
                            THROW 50001, 'EstadoFiscal es obligatorio.', 1;

                        IF @ResultadoEstadoFiscal IS NULL
                            THROW 50001, 'ResultadoEstadoFiscal es obligatorio.', 1;

                        ------------------------------------------------------------
                        -- Si faltan datos para UPDATE, salir sin error
                        ------------------------------------------------------------
                        IF @Tabla IS NULL
                        OR @CampoRNC IS NULL
                        OR @CampoENCF IS NULL
                        OR @RNCEmisor IS NULL
                        OR @eNCF IS NULL
                        BEGIN
                            RETURN;
                        END

                        DECLARE @sql NVARCHAR(MAX);

                        ------------------------------------------------------------
                        -- SQL dinámico (NO pisa valores si vienen NULL)
                        ------------------------------------------------------------
                        SET @sql = N'
                            UPDATE ' + QUOTENAME(@Tabla) + '
                            SET EstadoFiscal = @EstadoFiscal,
                                EstadoImpresion = CASE 
                                                    WHEN @EstadoImpresion IS NULL 
                                                    THEN EstadoImpresion 
                                                    ELSE @EstadoImpresion 
                                                END,
                                ResultadoEstadoFiscal = @ResultadoEstadoFiscal,
                                TrackId = CASE 
                                            WHEN @TrackId IS NULL 
                                            THEN TrackId 
                                            ELSE @TrackId 
                                        END,
                                CodigoSeguridad = CASE 
                                                    WHEN @CodigoSeguridad IS NULL 
                                                    THEN CodigoSeguridad 
                                                    ELSE @CodigoSeguridad 
                                                END,
                                CodigoSeguridadCF = CASE 
                                                    WHEN @CodigoSeguridadCF IS NULL 
                                                    THEN CodigoSeguridadCF 
                                                    ELSE @CodigoSeguridadCF 
                                                    END,
                                FechaFirma = CASE 
                                            WHEN @FechaFirma IS NULL 
                                            THEN FechaFirma 
                                            ELSE @FechaFirma 
                                            END,
                                MontoDGII = CASE 
                                            WHEN @MontoDGII IS NULL 
                                            THEN MontoDGII 
                                            ELSE @MontoDGII 
                                            END,
                                MontoITBISDGII = CASE 
                                                WHEN @MontoITBISDGII IS NULL 
                                                THEN MontoITBISDGII 
                                                ELSE @MontoITBISDGII 
                                                END,
                                Enviado = CASE 
                                            WHEN @Enviado IS NULL 
                                            THEN Enviado 
                                            ELSE @Enviado 
                                        END
                            WHERE ' + QUOTENAME(@CampoRNC) + ' = @RNCEmisor
                            AND ' + QUOTENAME(@CampoENCF) + ' = @eNCF;
                        ';

                        ------------------------------------------------------------
                        -- Ejecución segura
                        ------------------------------------------------------------
                        EXEC sp_executesql
                            @sql,
                            N'@EstadoFiscal INT,
                            @EstadoImpresion INT,
                            @ResultadoEstadoFiscal NVARCHAR(255),
                            @TrackId NVARCHAR(100),
                            @CodigoSeguridad NVARCHAR(100),
                            @CodigoSeguridadCF NVARCHAR(100),
                            @FechaFirma NVARCHAR(50),
                            @MontoDGII DECIMAL(18,2),
                            @MontoITBISDGII DECIMAL(18,2),
                            @Enviado BIT,
                            @RNCEmisor NVARCHAR(20),
                            @eNCF NVARCHAR(20)',
                            @EstadoFiscal,
                            @EstadoImpresion,
                            @ResultadoEstadoFiscal,
                            @TrackId,
                            @CodigoSeguridad,
                            @CodigoSeguridadCF,
                            @FechaFirma,
                            @MontoDGII,
                            @MontoITBISDGII,
                            @Enviado,
                            @RNCEmisor,
                            @eNCF;

                    END TRY
                    BEGIN CATCH
                        IF XACT_STATE() <> 0
                            ROLLBACK;

                        DECLARE @ErrMsg NVARCHAR(4000);
                        DECLARE @ErrNum INT;

                        SET @ErrMsg = ERROR_MESSAGE();
                        SET @ErrNum = ERROR_NUMBER();

                        THROW 50001, @ErrMsg, 1;
                    END CATCH
                END
        """

        if self.comparar_sp_con_python("dbo.sp_ActualizarEstadoFiscal", sp_update):
            self.db.execute_query(sp_update)
        else:
            existe = self.db.fetch_query(
                "SELECT 1 FROM sys.objects WHERE name='sp_ActualizarEstadoFiscal' AND type='P'"
            )
            if not existe:
                self.db.execute_query(sp_update)

        # ------------------------------------------------------------
        # 4. SP: sp_SustituirNCFRechazados (autosync)
        # ------------------------------------------------------------
        sp_rechazo = r"""
                        CREATE OR ALTER   PROCEDURE [dbo].[sp_SustituirNCFRechazados]
                            @Tabla           NVARCHAR(128),
                            @CampoNumero     NVARCHAR(50),
                            @RNCEmisorFiltro NVARCHAR(15) = NULL,
                            @NCFFiltro       VARCHAR(20)  = NULL
						WITH ENCRYPTION
                        AS
                        BEGIN
                            SET NOCOUNT ON;
                            SET XACT_ABORT ON;

                            BEGIN TRY

                                DECLARE @NCF VARCHAR(20);
                                DECLARE @Prefijo VARCHAR(5);
                                DECLARE @sql NVARCHAR(MAX);
                                DECLARE @TotalCambiados INT = 0;
                                DECLARE @InicioProceso DATETIME = GETDATE();
                                DECLARE @UltimoIdAntes INT;

                                ------------------------------------------------------------
                                -- 1) Crear tabla Log_SustitucionNCF si no existe
                                ------------------------------------------------------------
                                IF NOT EXISTS (
                                    SELECT * FROM sys.objects 
                                    WHERE object_id = OBJECT_ID(N'Log_SustitucionNCF') 
                                    AND type = 'U'
                                )
                                BEGIN
                                    CREATE TABLE Log_SustitucionNCF (
                                        Id INT IDENTITY(1,1) PRIMARY KEY,
                                        FechaRegistro DATETIME DEFAULT GETDATE(),
                                        TablaAfectada NVARCHAR(128),
                                        Fecha DATETIME NULL,
                                        Numero NVARCHAR(50) NULL,
                                        Tipo NVARCHAR(10) NULL,
                                        RNCEmisor NVARCHAR(15) NULL,
                                        MontoTotal DECIMAL(18,2) NULL,
                                        NCF_Anterior VARCHAR(20),
                                        NCF_Nuevo VARCHAR(20),
                                        ResultadoEstadoFiscal nvarchar(max)
                                    );
                                END;

                                SELECT @UltimoIdAntes = ISNULL(MAX(Id), 0)
                                FROM Log_SustitucionNCF;

                                ------------------------------------------------------------
                                -- 2) Crear tabla temporal con los NCF rechazados (filtrados)
                                ------------------------------------------------------------
                                IF OBJECT_ID('tempdb..#tmpNCF') IS NOT NULL DROP TABLE #tmpNCF;

                                CREATE TABLE #tmpNCF (ncf VARCHAR(20));

                                DECLARE @sqlCursor NVARCHAR(MAX);

                                SET @sqlCursor = N'INSERT INTO #tmpNCF SELECT ncf FROM ' + QUOTENAME(@Tabla) + N'
                                                WHERE EstadoFiscal = 99';

                                -- Filtro opcional por RNCEmisor
                                IF @RNCEmisorFiltro IS NOT NULL
                                    SET @sqlCursor = @sqlCursor 
                                        + N' AND rncemisor = ''' 
                                        + REPLACE(@RNCEmisorFiltro, '''', '''''') + N'''';

                                -- Filtro opcional por NCF específico
                                IF @NCFFiltro IS NOT NULL
                                    SET @sqlCursor = @sqlCursor 
                                        + N' AND ncf = ''' 
                                        + REPLACE(@NCFFiltro, '''', '''''') + N'''';

                                SET @sqlCursor = @sqlCursor + N';';

                                EXEC(@sqlCursor);

                                ------------------------------------------------------------
                                -- 3) Cursor para recorrer cada NCF
                                ------------------------------------------------------------
                                DECLARE cur CURSOR FOR SELECT ncf FROM #tmpNCF;

                                OPEN cur;
                                FETCH NEXT FROM cur INTO @NCF;

                                ------------------------------------------------------------
                                -- 4) Procesar cada NCF rechazado
                                ------------------------------------------------------------
                                WHILE @@FETCH_STATUS = 0
                                BEGIN
                                    SET @Prefijo = LEFT(@NCF, 3);

                                    SET @sql = N'
                                        IF OBJECT_ID(''tempdb..#TmpNCF_Det'') IS NOT NULL DROP TABLE #TmpNCF_Det;

                                        CREATE TABLE #TmpNCF_Det (
                                            Fecha DATETIME,
                                            Numero NVARCHAR(50),
                                            Tipo NVARCHAR(10),
                                            RNCEmisor NVARCHAR(15),
                                            MontoTotal DECIMAL(18,2),
                                            NCF_Anterior VARCHAR(20),
                                            NCF_Nuevo VARCHAR(20),
                                            ResultadoEstadoFiscal nvarchar(max)
                                        );

                                        UPDATE ' + QUOTENAME(@Tabla) + N'
                                        SET EstadoFiscal = 1,
                                            TrackId = NULL,
                                            ncf = ''' + @Prefijo + N''' +
                                                RIGHT(''0000000000'' + CAST(NEXT VALUE FOR ' 
                                                    + QUOTENAME(@Prefijo) + N' AS VARCHAR(20)), 10),
                                            Enviado = 0
                                        OUTPUT
                                            deleted.fecha,
                                            deleted.' + @CampoNumero + N',
                                            deleted.tipo,
                                            deleted.rncemisor,
                                            deleted.monto,
                                            deleted.ncf,
                                            inserted.ncf,
                                            deleted.ResultadoEstadoFiscal 
                                        INTO #TmpNCF_Det (
                                            Fecha, Numero, Tipo, RNCEmisor, MontoTotal,
                                            NCF_Anterior, NCF_Nuevo, ResultadoEstadoFiscal
                                        )
                                        WHERE ncf = ''' + @NCF + N'''
                                        AND EstadoFiscal = 99';

                                    -- Filtro opcional por RNCEmisor también en el UPDATE
                                    IF @RNCEmisorFiltro IS NOT NULL
                                        SET @sql = @sql 
                                            + N' AND rncemisor = ''' 
                                            + REPLACE(@RNCEmisorFiltro, '''', '''''') + N'''';

                                    SET @sql = @sql + N';

                                        INSERT INTO Log_SustitucionNCF (
                                            TablaAfectada, Fecha, Numero, Tipo,
                                            RNCEmisor, MontoTotal, NCF_Anterior, NCF_Nuevo, ResultadoEstadoFiscal
                                        )
                                        SELECT ''' + @Tabla + N''', Fecha, Numero, Tipo,
                                            RNCEmisor, MontoTotal, NCF_Anterior, NCF_Nuevo, ResultadoEstadoFiscal
                                        FROM #TmpNCF_Det;
                                    ';

                                    EXEC(@sql);

                                    IF EXISTS (
                                        SELECT 1
                                        FROM Log_SustitucionNCF
                                        WHERE Id > @UltimoIdAntes
                                        AND NCF_Anterior = @NCF
                                    )
                                        SET @TotalCambiados += 1;

                                    FETCH NEXT FROM cur INTO @NCF;
                                END;

                                CLOSE cur;
                                DEALLOCATE cur;

                                -- (Opcional) podrías devolver @TotalCambiados con un SELECT
                                -- SELECT @TotalCambiados AS TotalCambiados;

                            END TRY
                            BEGIN CATCH
                                DECLARE @Err NVARCHAR(MAX) = ERROR_MESSAGE();
                                THROW 50050, @Err, 1;
                            END CATCH

                        END;
        """

        if self.comparar_sp_con_python("dbo.sp_SustituirNCFRechazados", sp_rechazo):
            self.db.execute_query(sp_rechazo)
        else:
            existe = self.db.fetch_query(
                "SELECT 1 FROM sys.objects WHERE name='sp_SustituirNCFRechazados' AND type='P'"
            )
            if not existe:
                self.db.execute_query(sp_rechazo)

        log_event(
            logger, "info", "Estructura SQL verificada y sincronizada correctamente."
        )
        # ------------------------------------------------------------
        # FE_Empresas — Configuración general de Facturación Electrónica
        # ------------------------------------------------------------
        tabla_FE_Empresas = self.db.fetch_query(
            """
            SELECT 1
            FROM sys.tables
            WHERE name = 'FE_Empresas'
            """
        )

        if not tabla_FE_Empresas:
            log_event(logger, "info", "Creando tabla FE_Empresas...")

            crear_FE_Empresas = """
                CREATE TABLE dbo.FE_Empresas
                (
                    EmpresaId INT IDENTITY(1,1) NOT NULL
                        CONSTRAINT PK_FE_Empresas PRIMARY KEY,

                    Codigo VARCHAR(20) NOT NULL,
                    RNC VARCHAR(11) NOT NULL,
                    RazonSocial VARCHAR(150) NOT NULL,

                    NombreComercial VARCHAR(150) NULL,
                    Direccion VARCHAR(250) NULL,
                    Municipio VARCHAR(100) NULL,
                    Provincia VARCHAR(100) NULL,
                    Telefono VARCHAR(30) NULL,
                    Email VARCHAR(100) NULL,
                    WebSite VARCHAR(150) NULL,
                    ActividadEconomica VARCHAR(200) NULL,

                    ApiKey VARCHAR(100) NULL,
                    ApiSecret VARCHAR(128) NOT NULL,

                    ServidorOrigen VARCHAR(100) NULL,
                    BaseDatosOrigen VARCHAR(100) NULL,
                    UsuarioDB VARCHAR(50) NULL,
                    PasswordDB VARBINARY(256) NULL,

                    UltimaSincronizacion DATETIME NULL,
                    EstadoConexion VARCHAR(20) NOT NULL 
                        CONSTRAINT DF_FE_Empresas_EstadoConexion DEFAULT ('Desconocido'),

                    UltimaVerificacionConexion DATETIME NULL,
                    TotalDocumentosSincronizados BIGINT NOT NULL
                        CONSTRAINT DF_FE_Empresas_TotalDocs DEFAULT (0),

                    Ambiente VARCHAR(20) NOT NULL
                        CONSTRAINT DF_FE_Empresas_Ambiente DEFAULT ('Produccion'),

                    CertificadoDigital VARBINARY(MAX) NULL,
                    CertificadoPassword VARBINARY(256) NULL,

                    Activo BIT NOT NULL 
                        CONSTRAINT DF_FE_Empresas_Activo DEFAULT (1),

                    FechaCreacion DATETIME NOT NULL
                        CONSTRAINT DF_FE_Empresas_FechaCreacion DEFAULT (GETDATE()),

                    FechaModificacion DATETIME NULL,
                    ConfiguracionJSON NVARCHAR(MAX) NULL,

                    itbisenprecio CHAR(1) NOT NULL
                        CONSTRAINT DF_FE_Empresas_itbisenprecio DEFAULT ('0')
                        CONSTRAINT CK_FE_Empresas_itbisenprecio CHECK (itbisenprecio IN ('0','1')),

                    TipodeIngresos CHAR(2) NOT NULL
                        CONSTRAINT DF_FE_Empresas_TipodeIngresos DEFAULT ('01')
                        CONSTRAINT CK_FE_Empresas_TipodeIngresos CHECK 
                            (TipodeIngresos IN ('01','02','03','04','05','06')),

                    IndicadorEnvioDiferido INT NOT NULL
                        CONSTRAINT DF_FE_Empresas_IndicadorEnvioDiferido DEFAULT (0)
                        CONSTRAINT CK_FE_Empresas_IndicadorEnvioDiferido CHECK (IndicadorEnvioDiferido IN (0,1)),

                    URLEnvio VARCHAR(255) NOT NULL
                        CONSTRAINT DF_FE_Empresas_URLEnvio DEFAULT ('')
                );
            """
            self.db.execute_query(crear_FE_Empresas)

            log_event(
                logger,
                "info",
                "Insertando configuración inicial FE_Empresas (ambiente=2, fe=1)...",
            )

            self.db.execute_query(
                "INSERT INTO dbo.FE_Empresas (Ambiente, fe) VALUES (2, 1);"
            )

        else:
            # --------------------------------------------------------
            # Verificar columna FE
            # --------------------------------------------------------
            col_fe = self.db.fetch_query(
                """
                SELECT 1
                FROM sys.columns
                WHERE name = 'fe'
                AND object_id = OBJECT_ID('dbo.FE_Empresas')
                """
            )

            if not col_fe:
                log_event(logger, "info", "Agregando campo fe a FE_Empresas...")
                self.db.execute_query(
                    "ALTER TABLE dbo.FE_Empresas ADD fe INT NOT NULL DEFAULT 1;"
                )

            # --------------------------------------------------------
            # Verificar si existen registros
            # --------------------------------------------------------
            existe_registro = self.db.fetch_query("SELECT TOP 1 1 FROM dbo.FE_Empresas")

            if not existe_registro:
                log_event(
                    logger,
                    "info",
                    "FE_Empresas existe pero está vacía, insertando valores por defecto...",
                )
                # Insertando Datos de Prueba cuando no existen
                self.db.execute_query(
                    "INSERT INTO dbo.FE_Empresas (Codigo,RNC,RazonSocial,ApiSecret,Ambiente, fe) VALUES (1,'111111111','Empresa de Prueba','sk_test_4f8d3c9a7b1e6d2a9f0c123456789abc',2, 1);"
                )

    def asegurar_tabla(self, tabla: str):
        """
        Verifica que la tabla tenga todos los campos requeridos.

        Actualmente:
        - Verifica si existe el campo 'Enviado'
        - Si no existe, lo crea con INT DEFAULT 0

        En el futuro se pueden agregar más verificaciones aquí.
        """
        # Validación básica de tabla
        if not isinstance(tabla, str) or not tabla.isidentifier():
            raise ValueError("Tabla debe ser un nombre válido de tabla")

        # Verificar si existe columna Enviado
        sql = """
            SELECT 1
            FROM sys.columns
            WHERE Name = 'Enviado'
            AND Object_ID = OBJECT_ID(?)
        """

        existe = self.db.fetch_query(sql, (tabla,))

        if not existe:
            log_event(logger, "info", f"Agregando campo Enviado a {tabla}...")
            self.db.execute_query(f"ALTER TABLE {tabla} ADD Enviado INT DEFAULT 0;")
            self.db.execute_query(
                f"UPDATE {tabla} SET Enviado = 1 WHERE estadofiscal IN (5,6);"
            )
