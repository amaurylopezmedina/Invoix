/* =========================================================
   FE_DGII_FINAL_TODO_MAS_QUERYS
   Integra TODO el script original del usuario + versionado/log
   Version: 2026.02.01.07
   ========================================================= */

SET NOCOUNT ON;

DECLARE @ScriptName VARCHAR(255) = 'FE_DGII_FINAL_TODO_MAS_QUERYS';
DECLARE @Version    VARCHAR(50)  = '2026.02.01.07';
DECLARE @LogId      BIGINT;

------------------------------------------------------------
-- 0) TABLAS DE CONTROL
------------------------------------------------------------
IF OBJECT_ID('dbo.FE_DBVersion','U') IS NULL
BEGIN
    CREATE TABLE dbo.FE_DBVersion
    (
        Version    VARCHAR(50)  NOT NULL PRIMARY KEY,
        ScriptName VARCHAR(255) NOT NULL,
        AppliedOn  DATETIME     NOT NULL DEFAULT (GETDATE()),
        HostName   VARCHAR(128) NULL,
        LoginName  VARCHAR(128) NULL
    );
END;

IF OBJECT_ID('dbo.FE_ScriptLog','U') IS NULL
BEGIN
    CREATE TABLE dbo.FE_ScriptLog
    (
        Id         BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        ScriptName VARCHAR(255) NOT NULL,
        Version    VARCHAR(50)  NOT NULL,
        StartedAt  DATETIME     NOT NULL DEFAULT (GETDATE()),
        EndedAt    DATETIME     NULL,
        Status     VARCHAR(20)  NOT NULL DEFAULT ('STARTED'),
        Message    VARCHAR(MAX) NULL
    );
END;

INSERT INTO dbo.FE_ScriptLog (ScriptName, Version, Status, Message)
VALUES (@ScriptName, @Version, 'STARTED', 'Inicio de ejecución');
SET @LogId = SCOPE_IDENTITY();

IF EXISTS (SELECT 1 FROM dbo.FE_DBVersion WHERE Version = @Version)
BEGIN
    UPDATE dbo.FE_ScriptLog
       SET Status='SKIPPED', EndedAt=GETDATE(),
           Message='Versión ya aplicada. No se ejecutan cambios.'
     WHERE Id=@LogId;
    RETURN;
END;

BEGIN TRY
    BEGIN TRAN;

------------------------------------------------------------
-- cliente: IdentificadorExtranjero
------------------------------------------------------------
IF OBJECT_ID('dbo.cliente','U') IS NOT NULL
AND COL_LENGTH('dbo.cliente','IdentificadorExtranjero') IS NULL
BEGIN
    ALTER TABLE dbo.cliente
    ADD IdentificadorExtranjero INT NOT NULL CONSTRAINT DF_cliente_IdentificadorExtranjero DEFAULT (0);
END;

------------------------------------------------------------
-- empresa: ambiente (minúscula) DEFAULT 0 (script original)
------------------------------------------------------------
IF OBJECT_ID('dbo.empresa','U') IS NOT NULL
AND COL_LENGTH('dbo.empresa','ambiente') IS NULL
BEGIN
    ALTER TABLE dbo.empresa
    ADD ambiente INT NOT NULL CONSTRAINT DF_empresa_ambiente DEFAULT (0);
END;

------------------------------------------------------------
-- producto: servicio + NotaImpresion
------------------------------------------------------------
IF OBJECT_ID('dbo.producto','U') IS NOT NULL
BEGIN
    IF COL_LENGTH('dbo.producto','servicio') IS NULL
    BEGIN
        ALTER TABLE dbo.producto
        ADD servicio INT NOT NULL CONSTRAINT DF_producto_servicio DEFAULT (0);

        EXEC sys.sp_executesql N'UPDATE dbo.producto SET servicio = 0';
    END;

    IF COL_LENGTH('dbo.producto','NotaImpresion') IS NULL
        ALTER TABLE dbo.producto ADD NotaImpresion NVARCHAR(MAX);
END;

------------------------------------------------------------
-- ITBISDGII: tabla + datos
------------------------------------------------------------
IF OBJECT_ID('dbo.ITBISDGII','U') IS NULL
BEGIN
    CREATE TABLE dbo.ITBISDGII
    (
        codigo INT NOT NULL PRIMARY KEY,
        Descri CHAR(100),
        tasa NUMERIC(18,4),
        Siglas CHAR(5)
    );
END;

IF NOT EXISTS (SELECT 1 FROM dbo.ITBISDGII WHERE codigo=0)
    INSERT INTO dbo.ITBISDGII (codigo, Descri, tasa, Siglas) VALUES (0,'No Facturable',0,'IN');
IF NOT EXISTS (SELECT 1 FROM dbo.ITBISDGII WHERE codigo=1)
    INSERT INTO dbo.ITBISDGII (codigo, Descri, tasa, Siglas) VALUES (1,'18%',18,'I2');
IF NOT EXISTS (SELECT 1 FROM dbo.ITBISDGII WHERE codigo=2)
    INSERT INTO dbo.ITBISDGII (codigo, Descri, tasa, Siglas) VALUES (2,'16%',16,'I1');
IF NOT EXISTS (SELECT 1 FROM dbo.ITBISDGII WHERE codigo=3)
    INSERT INTO dbo.ITBISDGII (codigo, Descri, tasa, Siglas) VALUES (3,'0%',0,'IO');
IF NOT EXISTS (SELECT 1 FROM dbo.ITBISDGII WHERE codigo=4)
    INSERT INTO dbo.ITBISDGII (codigo, Descri, tasa, Siglas) VALUES (4,'Exento (E)*',0,'IE');

------------------------------------------------------------
-- impuesto: rename + recreación + datos
------------------------------------------------------------
IF OBJECT_ID('dbo.impuesto','U') IS NOT NULL
AND OBJECT_ID('dbo.impuestooldfe','U') IS NULL
    EXEC sp_rename 'dbo.impuesto', 'impuestooldfe';

IF OBJECT_ID('dbo.impuesto','U') IS NULL
BEGIN
    CREATE TABLE dbo.impuesto
    (
        impuesto   CHAR(2) NOT NULL PRIMARY KEY,
        Descrip    CHAR(40) NOT NULL,
        pto        DECIMAL(18,3) NULL,
        codigodgii INT NULL,
        Siglas     CHAR(5) NULL
    );
END;

IF NOT EXISTS (SELECT 1 FROM dbo.impuesto WHERE impuesto = '00')
    INSERT INTO dbo.impuesto (impuesto, Descrip, pto, codigodgii, Siglas)
    VALUES (N'00', N'EXENTO                                  ', CAST(0.000 AS Decimal(18, 3)), 4, N'E    ');

IF NOT EXISTS (SELECT 1 FROM dbo.impuesto WHERE impuesto = '01')
    INSERT INTO dbo.impuesto (impuesto, Descrip, pto, codigodgii, Siglas)
    VALUES (N'01', N'I. S. R.                                ', CAST(12.000 AS Decimal(18, 3)), NULL, NULL);

IF NOT EXISTS (SELECT 1 FROM dbo.impuesto WHERE impuesto = '02')
    INSERT INTO dbo.impuesto (impuesto, Descrip, pto, codigodgii, Siglas)
    VALUES (N'02', N'ITBIS                                   ', CAST(18.000 AS Decimal(18, 3)), 1, N'I2   ');

IF NOT EXISTS (SELECT 1 FROM dbo.impuesto WHERE impuesto = '03')
    INSERT INTO dbo.impuesto (impuesto, Descrip, pto, codigodgii, Siglas)
    VALUES (N'03', N'ITBIS 16%                               ', CAST(16.000 AS Decimal(18, 3)), 2, N'I1   ');

IF NOT EXISTS (SELECT 1 FROM dbo.impuesto WHERE impuesto = '04')
    INSERT INTO dbo.impuesto (impuesto, Descrip, pto, codigodgii, Siglas)
    VALUES (N'04', N'NO FACTURABLE                           ', CAST(0.000 AS Decimal(18, 3)), 0, N'NF   ');

IF NOT EXISTS (SELECT 1 FROM dbo.impuesto WHERE impuesto = '05')
    INSERT INTO dbo.impuesto (impuesto, Descrip, pto, codigodgii, Siglas)
    VALUES (N'05', N'ITBIS 0%                                ', CAST(0.000 AS Decimal(18, 3)), 0, N'I0   ');

------------------------------------------------------------
-- transa01: campos adicionales del script original
------------------------------------------------------------
IF OBJECT_ID('dbo.transa01','U') IS NOT NULL
BEGIN
    IF COL_LENGTH('dbo.transa01','ConteoImpresiones') IS NULL
        ALTER TABLE dbo.transa01 ADD ConteoImpresiones INT NOT NULL CONSTRAINT DF_transa01_ConteoImpresiones DEFAULT (0);

    IF COL_LENGTH('dbo.transa01','CodigoSeguridadCF') IS NULL
        ALTER TABLE dbo.transa01 ADD CodigoSeguridadCF NVARCHAR(10);

    IF COL_LENGTH('dbo.transa01','transferencia') IS NULL
        ALTER TABLE dbo.transa01 ADD transferencia NUMERIC(18,4);

    IF COL_LENGTH('dbo.transa01','idfe') IS NULL
        ALTER TABLE dbo.transa01 ADD idfe CHAR(3);
END;

------------------------------------------------------------
-- Campos fiscales (ResultadoEstadoFiscal, EstadoFiscal, MontoDGII, MontoITBISDGII)
------------------------------------------------------------
DECLARE @tbl SYSNAME;
DECLARE c_tbl CURSOR FOR
SELECT name FROM sys.tables
WHERE name IN ('transa01','transa02','cxcmovi1','cxcmovi2','cajachica','cxpmovi1');

OPEN c_tbl;
FETCH NEXT FROM c_tbl INTO @tbl;
WHILE @@FETCH_STATUS = 0
BEGIN
    EXEC (N'
        IF COL_LENGTH(''dbo.'+@tbl+''',''ResultadoEstadoFiscal'') IS NULL
            ALTER TABLE dbo.'+@tbl+' ADD ResultadoEstadoFiscal NVARCHAR(MAX);

        IF COL_LENGTH(''dbo.'+@tbl+''',''EstadoFiscal'') IS NULL
            ALTER TABLE dbo.'+@tbl+' ADD EstadoFiscal INT;

        IF COL_LENGTH(''dbo.'+@tbl+''',''MontoDGII'') IS NULL
            ALTER TABLE dbo.'+@tbl+' ADD MontoDGII NUMERIC(18,2);

        IF COL_LENGTH(''dbo.'+@tbl+''',''MontoITBISDGII'') IS NULL
            ALTER TABLE dbo.'+@tbl+' ADD MontoITBISDGII NUMERIC(18,2);

        IF COL_LENGTH(''dbo.'+@tbl+''',''RNCEmisor'') IS NULL
            ALTER TABLE dbo.'+@tbl+' ADD RNCEmisor NVARCHAR(20);

        IF COL_LENGTH(''dbo.'+@tbl+''',''Estadoimpresion'') IS NULL
            ALTER TABLE dbo.'+@tbl+' ADD Estadoimpresion INT;	
			
        IF COL_LENGTH(''dbo.'+@tbl+''',''CodigoSeguridadCF'') IS NULL
            ALTER TABLE dbo.'+@tbl+' ADD CodigoSeguridadCF NVARCHAR(6);
    ');
    FETCH NEXT FROM c_tbl INTO @tbl;
END
CLOSE c_tbl;
DEALLOCATE c_tbl;

------------------------------------------------------------
-- FEToken
------------------------------------------------------------
IF OBJECT_ID('dbo.FEToken','U') IS NULL
BEGIN
    CREATE TABLE dbo.FEToken
    (
        FileToken      VARCHAR(250) NULL,
        compania       INT NULL,
        Expedido       DATETIME NULL,
        expira         DATETIME NULL,
        SemillaFirmada VARCHAR(250) NULL,
        token          VARCHAR(MAX) NULL,
        ambiente       INT NULL,
        rnc            CHAR(20) NULL
    );
END;

------------------------------------------------------------
-- empresa: TipodeIngresos, IndicadorEnvioDiferido, URLEnvio, Ambiente (Mayúscula)
------------------------------------------------------------
IF OBJECT_ID('dbo.empresa','U') IS NOT NULL
BEGIN
    IF COL_LENGTH('dbo.empresa','TipodeIngresos') IS NULL
        ALTER TABLE dbo.empresa ADD TipodeIngresos CHAR(2);

    IF COL_LENGTH('dbo.empresa','IndicadorEnvioDiferido') IS NULL
        ALTER TABLE dbo.empresa ADD IndicadorEnvioDiferido INT;

    IF COL_LENGTH('dbo.empresa','URLEnvio') IS NULL
        ALTER TABLE dbo.empresa ADD URLEnvio CHAR(255);

    IF COL_LENGTH('dbo.empresa','Ambiente') IS NULL
        ALTER TABLE dbo.empresa ADD Ambiente INT;

    -- Updates según script original
    IF COL_LENGTH('dbo.empresa','TipodeIngresos') IS NOT NULL
        EXEC sys.sp_executesql N'UPDATE dbo.empresa SET TipodeIngresos = ''01'' WHERE TipodeIngresos IS NULL';

    IF COL_LENGTH('dbo.empresa','IndicadorEnvioDiferido') IS NOT NULL
        EXEC sys.sp_executesql N'UPDATE dbo.empresa SET IndicadorEnvioDiferido = 0 WHERE IndicadorEnvioDiferido IS NULL';

    IF COL_LENGTH('dbo.empresa','Ambiente') IS NOT NULL
        EXEC sys.sp_executesql N'UPDATE dbo.empresa SET Ambiente = 0 WHERE Ambiente IS NULL';

    -- itbisenprecio: solo si existe (blindado)
    IF COL_LENGTH('dbo.empresa','itbisenprecio') IS NOT NULL
    BEGIN
        DECLARE @sql_itbis NVARCHAR(MAX) = N'UPDATE dbo.empresa SET itbisenprecio = 0';
        EXEC sys.sp_executesql @sql_itbis;
    END;

    -- URLEnvio: en tu script decía "nolo pongo". Se deja comentado para que lo habilites si quieres.
    /*
    IF COL_LENGTH('dbo.empresa','URLEnvio') IS NOT NULL
        EXEC sys.sp_executesql N'UPDATE dbo.empresa SET URLEnvio = ''https://10.0.0.250:8001/FGE'' WHERE URLEnvio IS NULL';
    */
END;

------------------------------------------------------------
-- FEAmbiente: tabla + datos
------------------------------------------------------------
IF OBJECT_ID('dbo.FEAmbiente','U') IS NULL
BEGIN
    CREATE TABLE dbo.FEAmbiente
    (
        ambiente INT NULL,
        descrip  VARCHAR(255) NULL,
        ruta     VARCHAR(255) NULL
    );
END;

IF NOT EXISTS (SELECT 1 FROM dbo.FEAmbiente WHERE ambiente = 0)
    INSERT INTO dbo.FEAmbiente (ambiente, descrip, ruta)
    VALUES (0, N'Prueba', N'/TesteCF');

IF NOT EXISTS (SELECT 1 FROM dbo.FEAmbiente WHERE ambiente = 1)
    INSERT INTO dbo.FEAmbiente (ambiente, descrip, ruta)
    VALUES (1, N'Certificacion', N'/CerteCF');

IF NOT EXISTS (SELECT 1 FROM dbo.FEAmbiente WHERE ambiente = 2)
    INSERT INTO dbo.FEAmbiente (ambiente, descrip, ruta)
    VALUES (2, N'Produccion', N'/ecf');

------------------------------------------------------------
-- Funciones necesarias para el QR (aisladas)
------------------------------------------------------------
EXEC sys.sp_executesql N'CREATE OR ALTER FUNCTION dbo.FNCambiaHexadecimal (@inputString VARCHAR(MAX))
RETURNS VARCHAR(200)
AS
BEGIN
    DECLARE @result VARCHAR(MAX) = @inputString;

    -- Espacio y caracteres reservados más comunes para URL/QR
    SET @result = REPLACE(@result, '' '', ''%20'');
    SET @result = REPLACE(@result, ''!'', ''%21'');
    SET @result = REPLACE(@result, ''"'', ''%22'');
    SET @result = REPLACE(@result, ''#'', ''%23'');
    SET @result = REPLACE(@result, ''$'', ''%24'');
    SET @result = REPLACE(@result, ''&'', ''%26'');
    SET @result = REPLACE(@result, '''''''', ''%27'');
    SET @result = REPLACE(@result, ''('', ''%28'');
    SET @result = REPLACE(@result, '')'', ''%29'');
    SET @result = REPLACE(@result, ''*'', ''%2A'');
    SET @result = REPLACE(@result, ''+'', ''%2B'');
    SET @result = REPLACE(@result, '','', ''%2C'');
    SET @result = REPLACE(@result, ''-'', ''%2D'');
    SET @result = REPLACE(@result, ''.'', ''%2E'');
    SET @result = REPLACE(@result, ''/'', ''%2F'');
    SET @result = REPLACE(@result, '':'', ''%3A'');
    SET @result = REPLACE(@result, '';'', ''%3B'');
    SET @result = REPLACE(@result, ''<'', ''%3C'');
    SET @result = REPLACE(@result, ''='', ''%3D'');
    SET @result = REPLACE(@result, ''>'', ''%3E'');
    SET @result = REPLACE(@result, ''?'', ''%3F'');
    SET @result = REPLACE(@result, ''@'', ''%40'');
    SET @result = REPLACE(@result, ''['', ''%5B'');
    SET @result = REPLACE(@result, ''\'', ''%5C'');
    SET @result = REPLACE(@result, '']'', ''%5D'');
    SET @result = REPLACE(@result, ''^'', ''%5E'');
    SET @result = REPLACE(@result, ''_'', ''%5F'');
    SET @result = REPLACE(@result, ''`'', ''%60'');

    RETURN LEFT(@result, 200);
END';
EXEC sys.sp_executesql N'CREATE OR ALTER FUNCTION dbo.FNFechaDMY (@D DATETIME)
RETURNS VARCHAR(12)
AS
BEGIN
   RETURN
      RIGHT(''00'' + CAST(DAY(@D) AS VARCHAR(2)), 2) + ''-'' +
      RIGHT(''00'' + CAST(MONTH(@D) AS VARCHAR(2)), 2) + ''-'' +
      RIGHT(''0000'' + CAST(YEAR(@D) AS VARCHAR(4)), 4);
END';

------------------------------------------------------------
-- TipoImpuestoAdicional: tabla + datos (39 filas del script original)
------------------------------------------------------------
IF OBJECT_ID('dbo.TipoImpuestoAdicional','U') IS NULL
BEGIN
    CREATE TABLE dbo.TipoImpuestoAdicional
    (
        codigo      CHAR(3) NULL,
        tipoimpuesto CHAR(20) NULL,
        descricion  CHAR(255) NULL,
        tasa        NUMERIC(18,2) NULL,
        tipomonto   CHAR(1) NULL
    );
END;

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '001')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'001', N'Propina Legal       ', N'Propina Legal                                                                                                                                                                                                                                                  ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '002')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'002', N'CDT                 ', N'Contribucin al Desarrollo de las Telecomunicaciones
Ley 153-98 Art. 45                                                                                                                                                                                       ', CAST(2.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '003')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'003', N'ISC                 ', N'Servicios Seguros en general                                                                                                                                                                                                                                   ', CAST(16.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '004')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'004', N'ISC                 ', N'Servicios de Telecomunicaciones                                                                                                                                                                                                                                ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '005')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'005', N'ISPRV               ', N'Expedicin de la primera placa                                                                                                                                                                                                                                 ', CAST(17.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '006')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'006', N'ISC Especfico      ', N'Cerveza                                                                                                                                                                                                                                                        ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '007')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'007', N'ISC Especfico      ', N'Vinos de uva                                                                                                                                                                                                                                                   ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '008')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'008', N'ISC Especfico      ', N'Vermut y dems vinos de uvas frescas                                                                                                                                                                                                                           ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '009')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'009', N'ISC Especfico      ', N'Dems bebidas fermentadas                                                                                                                                                                                                                                      ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '010')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'010', N'ISC Especfico      ', N'Alcohol Etlico sin desnaturalizar (Mayor o igual a 80%)                                                                                                                                                                                                       ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '011')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'011', N'ISC Especfico      ', N'Alcohol Etlico sin desnaturalizar (inferior a 80%)                                                                                                                                                                                                            ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '012')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'012', N'ISC Especfico      ', N'Aguardientes de uva                                                                                                                                                                                                                                            ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '013')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'013', N'ISC Especfico      ', N'Whisky                                                                                                                                                                                                                                                         ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '014')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'014', N'ISC Especfico      ', N'Ron y dems aguardientes de caa                                                                                                                                                                                                                               ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '015')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'015', N'ISC Especfico      ', N'Gin y Ginebra                                                                                                                                                                                                                                                  ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '016')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'016', N'ISC Especfico      ', N'Vodka                                                                                                                                                                                                                                                          ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '017')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'017', N'ISC Especfico      ', N'Licores                                                                                                                                                                                                                                                        ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '018')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'018', N'ISC Especfico      ', N'Los dems (Bebidas y Alcoholes)                                                                                                                                                                                                                                ', CAST(632.58 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '019')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'019', N'ISC Especfico      ', N'Cigarrillos que contengan tabaco cajetilla 20 unidades                                                                                                                                                                                                         ', CAST(53.51 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '020')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'020', N'ISC Especfico      ', N'Los dems Cigarrillos que contengan 20 unidades                                                                                                                                                                                                                ', CAST(53.51 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '021')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'021', N'ISC Especfico      ', N'Cigarrillos que contengan 10 unidades                                                                                                                                                                                                                          ', CAST(26.75 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '022')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'022', N'ISC Especfico      ', N'Los dems Cigarrillos que contengan 10 unidades                                                                                                                                                                                                                ', CAST(26.75 AS Numeric(18, 2)), N'M');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '023')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'023', N'ISC AdValorem       ', N'Cerveza                                                                                                                                                                                                                                                        ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '024')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'024', N'ISC AdValorem       ', N'Vinos de uva                                                                                                                                                                                                                                                   ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '025')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'025', N'ISC AdValorem       ', N'Vermut y dems vinos de uvas frescas                                                                                                                                                                                                                           ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '026')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'026', N'ISC AdValorem       ', N'Dems bebidas fermentadas                                                                                                                                                                                                                                      ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '027')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'027', N'ISC AdValorem       ', N'Alcohol Etlico sin desnaturalizar (Mayor o igual a 80%)                                                                                                                                                                                                       ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '028')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'028', N'ISC AdValorem       ', N'Alcohol Etlico sin desnaturalizar (inferior a 80%)                                                                                                                                                                                                            ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '029')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'029', N'ISC AdValorem       ', N'Aguardientes de uva                                                                                                                                                                                                                                            ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '030')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'030', N'ISC AdValorem       ', N'Whisky                                                                                                                                                                                                                                                         ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '031')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'031', N'ISC AdValorem       ', N'Ron y dems aguardientes de caa                                                                                                                                                                                                                               ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '032')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'032', N'ISC AdValorem       ', N'Gin y Ginebra                                                                                                                                                                                                                                                  ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '033')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'033', N'ISC AdValorem       ', N'Vodka                                                                                                                                                                                                                                                          ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '034')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'034', N'ISC AdValorem       ', N'Licores                                                                                                                                                                                                                                                        ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '035')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'035', N'ISC AdValorem       ', N'Los dems (Bebidas y Alcoholes)                                                                                                                                                                                                                                ', CAST(10.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '036')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'036', N'ISC AdValorem       ', N'Cigarrillos que contengan tabaco cajetilla 20 unidades                                                                                                                                                                                                         ', CAST(20.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '037')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'037', N'ISC AdValorem       ', N'Los dems Cigarrillos que contengan 20 unidades                                                                                                                                                                                                                ', CAST(20.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '038')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'038', N'ISC AdValorem       ', N'Cigarrillos que contengan 10 unidades                                                                                                                                                                                                                          ', CAST(20.00 AS Numeric(18, 2)), N'T');

IF NOT EXISTS (SELECT 1 FROM dbo.TipoImpuestoAdicional WHERE codigo = '039')
    INSERT INTO dbo.TipoImpuestoAdicional (codigo, tipoimpuesto, descricion, tasa, tipomonto)
    VALUES (N'039', N'ISC AdValorem       ', N'Los dems Cigarrillos que contengan 10 unidades                                                                                                                                                                                                                ', CAST(20.00 AS Numeric(18, 2)), N'T');


---Campos Calculados

ALTER TABLE dbo.transa01
ADD
    montopago_devuelta AS (
        CASE 
            WHEN ISNULL(devuelta, 0) > 0 
            THEN 
                CASE 
                    WHEN ISNULL(tasa, 1) = 1 
                    THEN devuelta
                    ELSE devuelta * NULLIF(ISNULL(tasa, 1), 0)
                END
        END
    ) PERSISTED,

    codigodevuelta AS (
        CASE 
            WHEN ISNULL(devuelta, 0) > 0 THEN 0 
        END
    ) PERSISTED,

    montopago_efectivo AS (
        CASE 
            WHEN ISNULL(efectivo, 0) <> 0 
            THEN 
                CASE 
                    WHEN ISNULL(tasa, 1) = 1 
                    THEN efectivo
                    ELSE efectivo * NULLIF(ISNULL(tasa, 1), 0)
                END
        END
    ) PERSISTED,

    codigoefectivo AS (
        CASE 
            WHEN ISNULL(efectivo, 0) <> 0 THEN 1 
        END
    ) PERSISTED,

    montopago_transferencia AS (
        CASE 
            WHEN (ISNULL(transferencia, 0) + ISNULL(cheque, 0)) <> 0 
            THEN 
                CASE 
                    WHEN ISNULL(tasa, 1) = 1 
                    THEN ISNULL(transferencia, 0) + ISNULL(cheque, 0)
                    ELSE (ISNULL(transferencia, 0) + ISNULL(cheque, 0)) 
                         * NULLIF(ISNULL(tasa, 1), 0)
                END
        END
    ) PERSISTED,

    codigotransferencia AS (
        CASE 
            WHEN (ISNULL(transferencia, 0) + ISNULL(cheque, 0)) <> 0 THEN 2 
        END
    ) PERSISTED,

    montopago_tarjeta AS (
        CASE 
            WHEN ISNULL(tarjeta, 0) <> 0 
            THEN 
                CASE 
                    WHEN ISNULL(tasa, 1) = 1 
                    THEN tarjeta
                    ELSE tarjeta * NULLIF(ISNULL(tasa, 1), 0)
                END
        END
    ) PERSISTED,

    codigotarjeta AS (
        CASE 
            WHEN ISNULL(tarjeta, 0) <> 0 THEN 3 
        END
    ) PERSISTED,

    montopago_credito AS (
        CASE 
            WHEN (tipo = '34' OR tipo = '04') 
                 AND ISNULL(monto, 0) <> 0 
            THEN 
                CASE 
                    WHEN ISNULL(tasa, 1) = 1 
                    THEN monto
                    ELSE monto * NULLIF(ISNULL(tasa, 1), 0)
                END
        END
    ) PERSISTED,

    codigocredito AS (
        CASE 
            WHEN (tipo = '34' OR tipo = '04') 
                 AND ISNULL(monto, 0) <> 0 
            THEN 4 
        END
    ) PERSISTED,

    tipopago AS (
        CASE 
            WHEN tipo = '03' THEN 1
            WHEN tipo = '04' THEN 2
        END
    ) PERSISTED;
GO


--------------------------



-- MARCAR VERSIÓN + CERRAR LOG
------------------------------------------------------------
INSERT INTO dbo.FE_DBVersion (Version, ScriptName, AppliedOn, HostName, LoginName)
VALUES (@Version, @ScriptName, GETDATE(), HOST_NAME(), SUSER_SNAME());

COMMIT;

UPDATE dbo.FE_ScriptLog
   SET Status='OK', EndedAt=GETDATE(),
       Message='Ejecución completada correctamente'
 WHERE Id=@LogId;

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;

    UPDATE dbo.FE_ScriptLog
       SET Status='ERROR', EndedAt=GETDATE(),
           Message=CONCAT('Error ', ERROR_NUMBER(), ' (Linea ', ERROR_LINE(), '): ', ERROR_MESSAGE())
     WHERE Id=@LogId;

    THROW;
END CATCH;
