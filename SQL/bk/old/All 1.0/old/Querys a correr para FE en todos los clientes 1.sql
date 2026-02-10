Alter Table transa01 add
--trackid char(255),
--FechaFirma char(20),
--CodigoSeguridad char(20),
CodigoSeguridadCF char(20),
--EstadoFiscal int, 
--URLQR char(255), 
--fechacreacion DATETIME NOT NULL DEFAULT GETDATE(),     
--EstadoImpresion  int default 0, 
ConteoImpresiones int default 0,
--tasa numeric(18,4),
transferencia numeric(18,4),
Modificado DATETIME NOT NULL DEFAULT GETDATE(),
observa3 char(254),
ResultadoEstadoFiscal TEXT,
MontoDGII numeric(18,4), 
MontoITBISDGII numeric(18,4)





Go


Alter Table impuesto add  codigodgii integer, Siglas char(5)
Go

Create Table ITBISDGII  
(codigo integer default 0,
Descri char(100),
tasa Numeric(18,4),
Siglas char(5))
Go

    /* EL INDICADOR DE FACTURA ES  */
      /*a)Indicar si es valor
      0: No Facturable -- 
      1: ITBIS 1 (18%) 
      2: ITBIS 2 (16%)
      3: ITBIS 3 (0%) --- Venta de exportacion (REvisar)
      4: Exento (E)*/

Insert into ITBISDGII  (codigo, descri,TASA,siglas) values 
(0,'No Facturable',0,'IN'),
(1,'18%',18,'I2'),
(2,'16%',16,'I1'),
(3,'0%',0,'IO'),
(4,'Exento (E)*',0,'IE')
GO

Create Table EstadoImpresion  
(estado integer default 0,
Descrip char(100))
Go




Insert into EstadoImpresion  (Estado, Descrip) values 
(0,'Sin Procesar'),
(1,'Listo para Impresión'),
(2,'Impreso')
GO


Create Table EstadoFiscal
(estado integer default 0,
Descrip char(100))
GO

Insert into EstadoFiscal (estado, descrip) values 
(0,'En Cola'),
(1,'Procesado'),
(2,'XML Generado'),
(3,'XML Firmado'),
(4,'Enviado'),
(5,'Aceptado por la DGII'),
(99,'Rechazado')
GO

alter  TABLE empresa ADD
	TipodeIngresos char (2) default '01',
    IndicadorEnvioDiferido int default 0,
	[RazonSocialEmisor] [varchar](150) NULL,
	[NombreComercial] [varchar](150) NULL,
	[Sucursal] [varchar](20) NULL,
	[DireccionEmisor] [varchar](100) NULL,
	[Municipio] [varchar](6) NULL,
	[CorreoEmisor] [varchar](80) NULL,
	[WebSite] [varchar](50) NULL,
	[ActividadEconomica] [varchar](100) NULL
Go

alter table empresa alter column provincia [varchar](6) NULL
GO


	 CREATE TABLE EmpresaTelefonos(
	[IDRNC] [varchar](11) NULL,
	[TelefonoEmisor] [varchar](12) NULL)



--Tabla de Tipo de Cuenta de Pago
	 CREATE TABLE TipoCuentaPago(
	tipo char(2) NULL,
	descrip char(150) NULL)

Insert into TipoCuentaPago (tipo, descrip) values 
('CT','Cta. Corriente'),
('AH','Ahorro'),
('OT','Otra')

CREATE TABLE [dbo].[TipoNCF](
	[codigo] [char](2) NULL,
	[descripcion] [nchar](255) NULL
) ON [PRIMARY]
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'01', N'Factura de Crédito Fisca                                                                                                                                                                                                                                       ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'02', N'Factura de Consumo                                                                                                                                                                                                                                             ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'03', N'Notas de Débito                                                                                                                                                                                                                                                ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'04', N'Notas de Crédito                                                                                                                                                                                                                                               ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'11', N'Comprobante de Compras                                                                                                                                                                                                                                         ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'12', N'Registro Único de Ingresos                                                                                                                                                                                                                                     ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'13', N'Comprobante para Gastos Menores                                                                                                                                                                                                                                ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'14', N'Comprobante de Regímenes Especiales                                                                                                                                                                                                                            ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'15', N'Comprobante Gubernamental                                                                                                                                                                                                                                      ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'16', N'Comprobante para exportaciones                                                                                                                                                                                                                                 ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'17', N'Comprobante para Pagos al Exterior                                                                                                                                                                                                                             ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'31', N'Factura de Crédito Fiscal Electrónica                                                                                                                                                                                                                          ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'32', N'Factura de Consumo Electrónica                                                                                                                                                                                                                                 ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'33', N'Nota de Débito Electrónica                                                                                                                                                                                                                                     ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'34', N'Nota de Crédito Electrónica                                                                                                                                                                                                                                    ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'41', N'Compras Electrónico                                                                                                                                                                                                                                            ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'43', N'Gastos Menores Electrónico                                                                                                                                                                                                                                     ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'44', N'Regímenes Especiales Electrónico                                                                                                                                                                                                                               ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'45', N'Gubernamental Electrónico                                                                                                                                                                                                                                      ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'46', N'Comprobante de Exportaciones Electrónico                                                                                                                                                                                                                       ')
GO
INSERT [dbo].[TipoNCF] ([codigo], [descripcion]) VALUES (N'47', N'Comprobante para Pagos al Exterior Electrónico                                                                                                                                                                                                                 ')
GO


CREATE PROCEDURE sp_UpdateDynamicField
    @TableName NVARCHAR(128),           -- Nombre de la tabla
    @FieldName NVARCHAR(128),           -- Nombre del campo a actualizar
    @NewValue NVARCHAR(MAX),            -- Nuevo valor
    @WhereConditions NVARCHAR(MAX),     -- Condiciones WHERE en formato JSON
    @Debug BIT = 0                      -- Flag para modo debug (1 = mostrar query, 0 = ejecutar)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @SQL NVARCHAR(MAX)
    DECLARE @ParamDefinition NVARCHAR(MAX)
    DECLARE @WhereClause NVARCHAR(MAX) = ''
    DECLARE @ParamList NVARCHAR(MAX) = ''
    
    -- Validar que la tabla existe
    IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = @TableName)
    BEGIN
        RAISERROR('La tabla especificada no existe.', 16, 1)
        RETURN
    END
    
    -- Validar que el campo a actualizar existe
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(@TableName) AND name = @FieldName)
    BEGIN
        RAISERROR('El campo a actualizar no existe en la tabla.', 16, 1)
        RETURN
    END
    
    -- Validar que el JSON es válido
    IF ISJSON(@WhereConditions) = 0
    BEGIN
        RAISERROR('El formato JSON de las condiciones WHERE no es válido.', 16, 1)
        RETURN
    END

    -- Construir la cláusula WHERE y la lista de parámetros dinámicamente
    SELECT @WhereClause = @WhereClause + 
           CASE WHEN @WhereClause = '' THEN '' ELSE ' AND ' END +
           QUOTENAME(Field) + ' = @' + Field,
           @ParamList = @ParamList +
           CASE WHEN @ParamList = '' THEN '' ELSE ', ' END +
           '@' + Field + ' NVARCHAR(MAX)'
    FROM OPENJSON(@WhereConditions)
    WITH (
        Field NVARCHAR(128) '$.field',
        Value NVARCHAR(MAX) '$.value'
    )

    -- Validar que todos los campos WHERE existen
    DECLARE @InvalidFields TABLE (FieldName NVARCHAR(128))
    
    INSERT INTO @InvalidFields
    SELECT DISTINCT j.Field
    FROM OPENJSON(@WhereConditions)
    WITH (
        Field NVARCHAR(128) '$.field'
    ) j
    LEFT JOIN sys.columns c ON c.object_id = OBJECT_ID(@TableName) 
        AND c.name = j.Field
    WHERE c.name IS NULL

    IF EXISTS (SELECT 1 FROM @InvalidFields)
    BEGIN
        DECLARE @InvalidFieldsList NVARCHAR(MAX)
        SELECT @InvalidFieldsList = STRING_AGG(FieldName, ', ')
        FROM @InvalidFields

        RAISERROR('Los siguientes campos no existen en la tabla: %s', 16, 1, @InvalidFieldsList)
        RETURN
    END
    
    -- Construir la consulta dinámica
    SET @SQL = N'UPDATE ' + QUOTENAME(@TableName) + 
               N' SET ' + QUOTENAME(@FieldName) + N' = @NewValue' +
               N' WHERE ' + @WhereClause
    
    -- Definir los parámetros
    SET @ParamDefinition = N'@NewValue NVARCHAR(MAX), ' + @ParamList
    
    -- Modo Debug - Mostrar la consulta
    IF @Debug = 1
    BEGIN
        PRINT 'Query a ejecutar:'
        PRINT @SQL
        PRINT 'Parámetros:'
        PRINT 'NewValue: ' + @NewValue
        PRINT 'Condiciones WHERE:'
        SELECT Field, Value
        FROM OPENJSON(@WhereConditions)
        WITH (
            Field NVARCHAR(128) '$.field',
            Value NVARCHAR(MAX) '$.value'
        )
    END
    ELSE
    BEGIN
        -- Crear tabla temporal para los parámetros
        DECLARE @Params TABLE (
            ParamName NVARCHAR(128),
            ParamValue NVARCHAR(MAX)
        )

        -- Insertar el valor nuevo
        INSERT INTO @Params VALUES ('NewValue', @NewValue)

        -- Insertar los valores WHERE
        INSERT INTO @Params
        SELECT Field, Value
        FROM OPENJSON(@WhereConditions)
        WITH (
            Field NVARCHAR(128) '$.field',
            Value NVARCHAR(MAX) '$.value'
        )

        -- Ejecutar la consulta
        BEGIN TRY
            DECLARE @ExecSQL NVARCHAR(MAX) = N'EXEC sp_executesql @SQL, @ParamDefinition'

            -- Agregar los parámetros dinámicamente
            SELECT @ExecSQL = @ExecSQL + N', @' + ParamName + N'=''' + 
                   REPLACE(ParamValue, '''', '''''') + N''''
            FROM @Params

            -- Ejecutar
            EXEC sp_executesql @ExecSQL, 
                N'@SQL NVARCHAR(MAX), @ParamDefinition NVARCHAR(MAX)',
                @SQL, @ParamDefinition

            -- Retornar el número de filas afectadas
            PRINT 'Filas actualizadas: ' + CAST(@@ROWCOUNT AS NVARCHAR(10))
        END TRY
        BEGIN CATCH
            DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE()
            DECLARE @ErrorSeverity INT = ERROR_SEVERITY()
            DECLARE @ErrorState INT = ERROR_STATE()
            
            RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState)
        END CATCH
    END
END
GO
