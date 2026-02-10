--drop table impuesto

CREATE TABLE [dbo].[impuesto](
	[impuesto] [char](2) NOT NULL,
	[Descrip] [char](40) NOT NULL,
	[pto] [decimal](18, 3) NULL,
	[codigodgii] [int] NULL,
	[Siglas] [char](5) NULL
) ON [PRIMARY]
GO
INSERT [dbo].[impuesto] ([impuesto], [Descrip], [pto], [codigodgii], [Siglas]) VALUES (N'00', N'EXENTO                                  ', CAST(0.000 AS Decimal(18, 3)), 4, N'E    ')
GO
INSERT [dbo].[impuesto] ([impuesto], [Descrip], [pto], [codigodgii], [Siglas]) VALUES (N'01', N'I. S. R.                                ', CAST(12.000 AS Decimal(18, 3)), NULL, NULL)
GO
INSERT [dbo].[impuesto] ([impuesto], [Descrip], [pto], [codigodgii], [Siglas]) VALUES (N'02', N'ITBIS                                   ', CAST(18.000 AS Decimal(18, 3)), 1, N'I2   ')
GO
INSERT [dbo].[impuesto] ([impuesto], [Descrip], [pto], [codigodgii], [Siglas]) VALUES (N'03', N'ITBIS 16%                               ', CAST(16.000 AS Decimal(18, 3)), 2, N'I1   ')
GO
INSERT [dbo].[impuesto] ([impuesto], [Descrip], [pto], [codigodgii], [Siglas]) VALUES (N'04', N'NO FACTURABLE                           ', CAST(0.000 AS Decimal(18, 3)), 0, N'NF   ')
GO
INSERT [dbo].[impuesto] ([impuesto], [Descrip], [pto], [codigodgii], [Siglas]) VALUES (N'05', N'ITBIS 0%                                ', CAST(0.000 AS Decimal(18, 3)), 0, N'I0   ')
GO
SET ANSI_PADDING ON
GO



Alter Table transa01 add   ConteoImpresiones int default 0
Alter Table transa01 add    CodigoSeguridadCF char(10) 

CREATE TABLE [dbo].[FEToken](
	[FileToken] [varchar](250) NULL,
	[RNC] [char](20) NULL,
	[Expedido] [datetime] NULL,
	[expira] [datetime] NULL,
	[SemillaFirmada] [varchar](250) NULL,
	[token] [varchar](max) NULL,
	[Ambiente] [int] NULL,
	[compania] [int] NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO






Alter table empresa

add TipodeIngresos char(2)
go
Alter table empresa

add IndicadorEnvioDiferido int
go


update  empresa set TipodeIngresos = '02'
go

update  empresa set IndicadorEnvioDiferido = 0
go

Alter table transa01

add idfe char(3)
go



Alter table empresa

add URLEnvio char(255)
go

update  empresa set URLEnvio = 'https://4.246.130.245:8001/FGE'

update  empresa set URLEnvio = 'https://127.0.0.1:8001/FGE'
go


Alter table empresa

add URLRI char(255)
go

update  empresa set URLRI = 'https://127.0.0.1:8001/RI'
go

Alter table empresa
add 
Ambiente int
go
update  empresa set fe = 1
go
--DROP TABLE FEAMBIENTE
CREATE TABLE [dbo].[FEAmbiente](
	[ambiente] [int] NULL,
	[descrip] [varchar](255) NULL,
	[ruta] [varchar](255) NULL
) ON [PRIMARY]
GO
INSERT [dbo].[FEAmbiente] ([ambiente], [descrip], [ruta]) VALUES (0, N'Prueba', N'/TesteCF')
GO
INSERT [dbo].[FEAmbiente] ([ambiente], [descrip], [ruta]) VALUES (1, N'Certificacion', N'/CerteCF')
GO
INSERT [dbo].[FEAmbiente] ([ambiente], [descrip], [ruta]) VALUES (2, N'Produccion', N'/ecf')
GO

Select * from [FEAmbiente]

Select * from empresa


--CREAR CAMPOS PARA MANEJO ALMACEN EN FRM FACTURA
 --alter table empresa alter column fe int

 Select * from empresa
 --Buscar estos datos en la dgii https://dgii.gov.do/app/WebApps/ConsultasWeb/consultas/rnc.aspx
Update empresa set TipodeIngresos = '01'

Update empresa set IndicadorEnvioDiferido = 0

Update empresa set itbisenprecio = 0


--Campo isr en cajachicha

alter table producto add NotaImpresion varchar(max)

Alter table cxpmovi1 add isr numeric (18,4)
go
Alter table cxpmovi1 add tasa numeric(18,4) default 1
go
 alter table empresa  add encf int
 Go
 alter table empresa  add fe int
 Go


 Alter table empresa  add  Ambiente int
go

update  empresa set ambiente = 0
go
update empresa set encf=1
Go
update empresa set fe=1
GO

 alter table producto add servicio int default 0
 go

  alter table producto add notaimpresion char(2000)
 go


--20240625
alter table caja add defaultNCF char(5)
go
update caja set defaultNCF='B02'
go



--drop table sis_TipoNCF 
CREATE TABLE sis_TipoNCF(
	Codigo char(2) UNIQUE not null,	
	Descripcion char(100),
	Prefijo char(1),
	Longitud int,
	Auxiliar char(3),
	SecSQL char(10),
	Activo char(1),
	Tabla char(10),
	campo1 char(10),
	campo2 char(10)
)

/*
alter table 
sis_TipoNCF add
	Tabla char(10),
	campo1 char(10),
	campo2 char(10)
*/




 
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('31',UPPER('Factura de Credito Fiscal Electronica'),'E', 13, 'VEN' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('32',UPPER('Factura de Consumo Electronica'), 'E', 13, 'VEN' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('33',UPPER('Nota de Debito Electronica'), 'E', 13, 'CXC' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('34',UPPER('Nota de Credito Electronica'), 'E', 13, 'CXC' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('41',UPPER('Compras Electronico'), 'E', 13, 'CXP' ) --PROVEEDOR INFORMAL
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('43',UPPER('Gastos Menores Electronico'), 'E', 13, 'CXP' ) --CAJA CHICA
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('44',UPPER('Regimenes Especiales Electronico'), 'E', 13, 'VEN' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('45',UPPER('Gubernamental Electronico'), 'E', 13, 'VEN' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('46',UPPER('Comprobante de Exportaciones Electronico'), 'E', 13, 'VEN' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('47',UPPER('Comprobante para Pagos al Exterior Electronico'), 'E', 13, 'CXP' )--PAGOS BANCO
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('01',UPPER('Factura de Credito Fiscal'), 'B', 11, 'VEN' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('02',UPPER('Factura de Consumo'), 'B', 11, 'VEN' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('03',UPPER('Notas de Debito'), 'B', 11, 'CXC' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('04',UPPER('Notas de Credito'), 'B', 11, 'CXC' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('11',UPPER('Comprobante de Compras'), 'B', 11, 'CXP' ) --PROVEEDOR INFORMAL
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('12',UPPER('Registro Unico de Ingresos'), 'B', 11, 'CXC' )--FINANCIERA
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('13',UPPER('Comprobante para Gastos Menores'), 'B', 11, 'CXP' )--CAJA CHICA
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('14',UPPER('Comprobante de Regímenes Especiales'), 'B', 11, 'VEN' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('15',UPPER('Comprobante Gubernamental'), 'B', 11, 'VEN' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('16',UPPER('Comprobante para exportaciones'), 'B', 11, 'VEN' )
Go
INSERT sis_TipoNCF (codigo, descripcion, prefijo, longitud, Auxiliar) 
VALUES ('17',UPPER('Comprobante para Pagos al Exterior'), 'B', 11, 'CXP' )--PAGOS BANCO
Go

update sis_TipoNCF set campo1 = 'rncemisor', campo2= 'ncf'
go

--CREAR LOS NOMBRES DE LAS SECUENCIAS SQL PARA LOS NCFS
update sis_TipoNCF set SecSQL=prefijo+codigo
GO
update sis_TipoNCF set Activo=1
GO

-- Declara el cursor sobre la tabla temporal  
SET NOCOUNT ON;
DECLARE _Cursor CURSOR FOR 
	SELECT secsql  FROM sis_TipoNCF;

-- Abre el cursor
OPEN _Cursor;  

-- Declara variables para almacenar valores  
DECLARE	@secsql NVARCHAR(5),@sql NVARCHAR(MAX)

-- Recupera la primera fila
FETCH NEXT FROM _Cursor INTO @secsql;  

WHILE @@FETCH_STATUS = 0  
BEGIN  
	--Print ' data='+  @secsql;
	/*
	IF EXISTS (SELECT * FROM sys.sequences WHERE name = @secsql )
	BEGIN
	 SET @sql = N'DROP SEQUENCE ' + QUOTENAME(@secsql);
	 EXEC sp_executesql @sql;
	END
		*/
	
	IF NOT EXISTS (SELECT * FROM sys.sequences WHERE name = @secsql )
	BEGIN
	 SET @sql = N'CREATE SEQUENCE ' + QUOTENAME(@secsql) + 
			   ' START WITH 1 INCREMENT BY 1 MINVALUE 1 NO CYCLE CACHE 3;';
	 EXEC sp_executesql @sql;
	END

	-- Pasa a la siguiente fila		
	FETCH NEXT FROM _Cursor INTO  @secsql; 
END;  
CLOSE _Cursor;  
DEALLOCATE _Cursor;
-- fin Recupera la primera fila

--drop table sis_GlobalSec
CREATE TABLE sis_GlobalSec(
	id int IDENTITY(1,1) NOT NULL,
	NAutorizacion char(100) NULL,
	tipoSec int,
	idTipoNCF char(2) NOT NULL,
	FSolicitud datetime NOT NULL,
	FVencimiento datetime,
	NSolicitud char(100) NULL,
	CanSolicitada int NOT NULL,
	SecuInicial int NOT NULL,
	SecuFinal int NOT NULL,
	Estado int,
	notificar int
)  
GO
--VISTA SECUENCIAS GLOBALES
CREATE OR ALTER VIEW secuenciasGlobales
AS
WITH SecDisponibles AS 
( 
select t.SecSQL,s.current_value secActual, 
max(g.SecuFinal) - isnull(CAST(s.last_used_value AS int),0) restan 
from sis_globalSec g  
join sis_TipoNCF t on t.Codigo=g.idTipoNCF 
join sys.sequences s on s.name /*collate SQL_Latin1_General_CP1_CI_AS*/ = t.SecSQL 
where g.estado in (1,2) group by t.SecSQL,s.current_value,s.last_used_value  
) 
SELECT t.Auxiliar, t.Descripcion, t.SecSQL Prefijo, g.FVencimiento, g.Estado, d.restan, 
g.notificar FROM sis_TipoNCF t 
join SecDisponibles d ON d.SecSQL = t.SecSQL  
join sis_globalSec g on g.idTipoNCF=t.Codigo  
where d.secActual between g.SecuInicial and g.SecuFinal 
and t.Activo='1'  and g.estado <> 4 
go

--drop table sis_EstadoSec
CREATE TABLE sis_EstadoSec(
	id int,
	descrip char (255)
)
GO

INSERT sis_EstadoSec (id, descrip) VALUES (1,UPPER('Sin Utilizar'));
go
INSERT sis_EstadoSec (id, descrip) VALUES (2, UPPER('En Uso'));
go
INSERT sis_EstadoSec (id, descrip) VALUES (3, UPPER('Agotada'));
go
INSERT sis_EstadoSec (id, descrip) VALUES (4, UPPER('Vencida'));
GO

--si no existen crear estos campos-------------------------------------------------
Alter Table transa01 add SecSQL char(10),FVencimientoNCF datetime, ID INT IDENTITY(1,1),
EstadoFiscal int, Estadoimpresion int default 1, URLQR char(255),
fechacreacion DATETIME DEFAULT GETDATE(), CodigoSeguridad char(100), CodigoSeguridadCF char(10),Trackid char(255),  
FechaFirma char(50), RNCEmisor char(20)


Alter Table transa01 add transferencia numeric(18,4), observa3 char(254), ResultadoEstadoFiscal varchar(max), MontoDGII numeric(18,4), 
MontoITBISDGII numeric(18,4)

Alter Table cxcmovi1 add ResultadoEstadoFiscal varchar(max),CodigoSeguridadCF char(20),ConteoImpresiones int,
SecSQL char(10),FVencimientoNCF datetime, ID INT IDENTITY(1,1),
EstadoFiscal int, Estadoimpresion int default 1, URLQR char(255), 
fechacreacion DATETIME DEFAULT GETDATE(), CodigoSeguridad char(255), Trackid char(255),  
FechaFirma char(50), RNCEmisor char(20), tasa numeric(18,2)

Alter Table cxcmovi2 add CodigoSeguridadCF char(20),ResultadoEstadoFiscal varchar(max),SecSQL char(10), FVencimientoNCF datetime, ID INT IDENTITY(1,1),
EstadoFiscal int,Estadoimpresion int default 1, URLQR char(255),  
fechacreacion DATETIME DEFAULT GETDATE(), CodigoSeguridad char(255), Trackid char(255),  
FechaFirma char(50), RNCEmisor char(20)

Alter Table cxpmovi1 add ResultadoEstadoFiscal varchar(max),CodigoSeguridadCF char(20),SecSQL char(10), FVencimientoNCF datetime, ID INT IDENTITY(1,1),
EstadoFiscal int, Estadoimpresion int default 1, URLQR char(255),  
fechacreacion DATETIME DEFAULT GETDATE(), CodigoSeguridad char(255), Trackid char(255),  
FechaFirma char(50), RNCEmisor char(20)

Alter Table cxpmovi2 add CodigoSeguridadCF char(20),ResultadoEstadoFiscal varchar(max),SecSQL char(10), FVencimientoNCF datetime, ID INT IDENTITY(1,1),
EstadoFiscal int, Estadoimpresion int default 1, URLQR char(255),  
fechacreacion DATETIME DEFAULT GETDATE(), CodigoSeguridad char(255), Trackid char(255),  
FechaFirma char(50), RNCEmisor char(20)

Alter Table cxpmovi9 add CodigoSeguridadCF char(20),ResultadoEstadoFiscal varchar(max),SecSQL char(10), FVencimientoNCF datetime, ID INT IDENTITY(1,1),
EstadoFiscal int, Estadoimpresion int default 1, URLQR char(255),  
fechacreacion DATETIME DEFAULT GETDATE(), CodigoSeguridad char(255), Trackid char(255),  
FechaFirma char(50), RNCEmisor char(20)

Alter Table cajachica add CodigoSeguridadCF char(20),ResultadoEstadoFiscal varchar(max),SecSQL char(10), FVencimientoNCF datetime, ID INT IDENTITY(1,1),
EstadoFiscal int, Estadoimpresion int default 1, URLQR char(255),  
fechacreacion DATETIME DEFAULT GETDATE(), CodigoSeguridad char(255), Trackid char(255),  
FechaFirma char(50), RNCEmisor char(20)

alter table transa01 add ncf char(19)
--===============================================================================================================
/*para crear el triguer para generar NCF en transa01  */
CREATE or ALTER TRIGGER tr_NCFfacturaVenta
ON Transa01
AFTER INSERT--, UPDATE
AS
BEGIN
	SET NOCOUNT ON;
	/*Variables*/  
	DECLARE @query NVARCHAR(MAX), @SecNCF INT, @Longitud INT, @ERROR INT, @idTipoNCF char(2), 
	@Ncf char(20), 	@SecSQL NVARCHAR(5), @fv datetime, @idglobalSec INT, @estado INT, 
	@SecuFinal INT, @rncEmpresa char(20)='', @fe int, @EstadoFiscal int=98;

    /*Verifica si ya el registros existe*/
	IF NOT EXISTS ( SELECT 1 FROM Transa01 t 
	JOIN INSERTED i ON t.documento = i.documento and t.tipo = i.tipo and t.cliente= i.cliente
	WHERE t.ID != i.ID ) /* Asegura que no se trate del mismo registro recién insertado*/ 	   
	BEGIN 
	 /*Acción para INSERT, Llenando variables*/   
	 select @SecSQL = SecSQL, @EstadoFiscal= EstadoFiscal from INSERTED;
	END
	ELSE
	BEGIN
	 /*Si ya el registros existe, no hacer nada*/
	 RETURN; 
	END
	
	if @SecSQL<>''
	BEGIN
	 BEGIN TRAN
	  select @Longitud = Longitud, @idTipoNCF = codigo from sis_TipoNCF where SecSQL=@SecSQL
	  select @rncEmpresa=rnc, @fe=FE from empresa

	  if @fe=1
	  begin
	   if not @EstadoFiscal=0 or @EstadoFiscal is null
	    set @EstadoFiscal = 1;
	  end;

	 /*Buscando la secuencia unica de NCF  */
	 SET @query = N'SET @SecNCF = NEXT VALUE FOR ' + QUOTENAME(@SecSQL)
	 EXEC sp_executesql @query, N'@SecNCF INT OUTPUT', @SecNCF OUTPUT;
	
	 /*construyendo el NCF  */
	 SET @Ncf= (TRIM(@SecSQL)+RIGHT(REPLICATE('0', @Longitud-3) +CAST(@SecNCF AS VARCHAR), @Longitud-3));

	 select @fv=FVencimiento, @idglobalSec=id, @estado=estado, @SecuFinal=SecuFinal 
	 from sis_globalSec  
	 where idTipoNCF = @idTipoNCF and @SecNCF between SecuInicial and SecuFinal 

	 /*Actualizando NCF y fecha de Vencimiento  */
	 UPDATE t
     SET t.ncf = @Ncf, t.FVencimientoNCF= @fv, t.RNCEmisor = @rncEmpresa, 
	 t.EstadoFiscal= @EstadoFiscal
     FROM transa01 t 
	 INNER JOIN inserted i ON t.id = i.id;

	 if (@SecuFinal - @SecNCF)=0 
	 UPDATE sis_globalSec set estado=3 where  id=@idglobalSec
	 else
	 if @estado=1
	 UPDATE sis_globalSec set estado=2 where  id=@idglobalSec
	
	 IF @ERROR <> 0 
	 BEGIN
	  ROLLBACK TRAN
      PRINT'NCF NO PUDO SER GENERADO . . .'
	 END
	 ELSE
	  COMMIT TRAN
   END
END;
--===============================================================================================================

/*para crear el triguer para generar NCF en CXCMOVI1  */
CREATE or ALTER TRIGGER tr_NCFcxc
ON CXCMOVI1
AFTER INSERT
AS
BEGIN
	SET NOCOUNT ON;
	
	/*Variables   */
	DECLARE @query NVARCHAR(MAX), @SecNCF INT, @Longitud INT, @ERROR INT, @idTipoNCF char(2), 
	@Ncf char(20), 	@SecSQL NVARCHAR(5), @fv datetime, @idglobalSec INT, @estado INT, 
	@SecuFinal INT, @rncEmpresa char(20)=''	, @fe int, @EstadoFiscal int=98

	/*Verifica si ya el registros existe*/
	IF NOT EXISTS ( SELECT 1 FROM cxcmovi1 t 
	JOIN INSERTED i ON t.documento = i.documento and t.tipomovi = i.tipomovi and t.cliente= i.cliente
	WHERE t.ID != i.ID ) /* Asegura que no se trate del mismo registro recién insertado*/ 	   
	BEGIN 
	 /*Acción para INSERT, Llenando variables*/   
	 select @SecSQL = SecSQL from INSERTED;
	END
	ELSE
	BEGIN
	 /*Si ya el registros existe, no hacer nada*/
	 RETURN; 
    END
	  
	if @SecSQL<>''
	BEGIN
	 BEGIN TRAN
	  select @Longitud = Longitud, @idTipoNCF = codigo from sis_TipoNCF where SecSQL=@SecSQL
	  select @rncEmpresa=rnc, @fe=FE from empresa

	  if @fe=1
	   set @EstadoFiscal = 1;

	  /*Buscando la secuencia unica de NCF  */
	  SET @query = N'SET @SecNCF = NEXT VALUE FOR ' + QUOTENAME(@SecSQL)
	  EXEC sp_executesql @query, N'@SecNCF INT OUTPUT', @SecNCF OUTPUT;
	
	  /*construyendo el NCF  */
	  SET @Ncf= (TRIM(@SecSQL)+RIGHT(REPLICATE('0', @Longitud-3) +CAST(@SecNCF AS VARCHAR), @Longitud-3));
	  
	  select @fv=FVencimiento, @idglobalSec=id, @estado=estado, @SecuFinal=SecuFinal 
	  from sis_globalSec  
	  where idTipoNCF = @idTipoNCF and @SecNCF between SecuInicial and SecuFinal 

	  /*Actualizando NCF y fecha de Vencimiento  */
	  UPDATE t
	  SET t.ncf = @Ncf, t.FVencimientoNCF= @fv, t.RNCEmisor = @rncEmpresa, 
	  t.EstadoFiscal= @EstadoFiscal
      FROM cxcmovi1 t 
	  INNER JOIN inserted i ON t.id = i.id;

	  if (@SecuFinal - @SecNCF)=0 
	  UPDATE sis_globalSec set estado=3 where  id=@idglobalSec
	  else
	  if @estado=1
	  UPDATE sis_globalSec set estado=2 where  id=@idglobalSec
	
	 IF @ERROR <> 0 
	 BEGIN
	  ROLLBACK TRAN
      PRINT'NCF NO PUDO SER GENERADO . . .'
	 END
	 ELSE
	 COMMIT TRAN
   END
END;
--==============================================================================================================

/*para crear el triguer para generar NCF en CXCMOVI2  */
CREATE or ALTER TRIGGER tr_NCFcxc2
ON CXCMOVI2
AFTER INSERT
AS
BEGIN
	SET NOCOUNT ON;
	
	/*Variables   */
	DECLARE @query NVARCHAR(MAX), @SecNCF INT, @Longitud INT, @ERROR INT, @idTipoNCF char(2), 
	@Ncf char(20), 	@SecSQL NVARCHAR(5), @fv datetime, @idglobalSec INT, @estado INT, 
	@SecuFinal INT, @rncEmpresa char(20)='', @fe int, @EstadoFiscal int=98

	/*Verifica si ya el registros existe*/
	IF NOT EXISTS ( SELECT 1 FROM cxcmovi2 t 
	JOIN INSERTED i ON t.documento = i.documento and t.tipomovi = i.tipomovi and t.cliente= i.cliente
	WHERE t.ID != i.ID ) /* Asegura que no se trate del mismo registro recién insertado*/ 	   
	BEGIN 
	 /*Acción para INSERT, Llenando variables*/   
	 select @SecSQL = SecSQL from INSERTED;
	END
	ELSE
	BEGIN
	 /*Si ya el registros existe, no hacer nada*/
	 RETURN; 
    END
	  
	if @SecSQL<>''
	BEGIN
	 BEGIN TRAN
	  select @Longitud = Longitud, @idTipoNCF = codigo from sis_TipoNCF where SecSQL=@SecSQL
	  select @rncEmpresa=rnc, @fe=FE from empresa

   	  if @fe=1
	   set @EstadoFiscal = 1;

	  /*Buscando la secuencia unica de NCF  */
	  SET @query = N'SET @SecNCF = NEXT VALUE FOR ' + QUOTENAME(@SecSQL)
	  EXEC sp_executesql @query, N'@SecNCF INT OUTPUT', @SecNCF OUTPUT;
	
	  /*construyendo el NCF  */
	  SET @Ncf= (TRIM(@SecSQL)+RIGHT(REPLICATE('0', @Longitud-3) +CAST(@SecNCF AS VARCHAR), @Longitud-3));
	  
	  select @fv=FVencimiento, @idglobalSec=id, @estado=estado, @SecuFinal=SecuFinal 
	  from sis_globalSec  
	  where idTipoNCF = @idTipoNCF and @SecNCF between SecuInicial and SecuFinal 

	  /*Actualizando NCF y fecha de Vencimiento  */
	  UPDATE t
	  SET t.ncf = @Ncf, t.FVencimientoNCF= @fv, t.RNCEmisor = @rncEmpresa, 
	  t.EstadoFiscal= @EstadoFiscal
      FROM cxcmovi2 t 
	  INNER JOIN inserted i ON t.id = i.id;

	  if (@SecuFinal - @SecNCF)=0 
	  UPDATE sis_globalSec set estado=3 where  id=@idglobalSec
	  else
	  if @estado=1
	  UPDATE sis_globalSec set estado=2 where  id=@idglobalSec
	
	 IF @ERROR <> 0 
	 BEGIN
	  ROLLBACK TRAN
      PRINT'NCF NO PUDO SER GENERADO . . .'
	 END
	 ELSE
	 COMMIT TRAN
   END
END;
--==============================================================================================================

/*para crear el triguer para generar NCF en CXPMOVI1  */
CREATE or ALTER TRIGGER tr_NCFcxp
ON CXPMOVI1
AFTER INSERT
AS
BEGIN
	SET NOCOUNT ON;
	
	/*Variables   */
	DECLARE @query NVARCHAR(MAX), @SecNCF INT, @Longitud INT, @ERROR INT, @idTipoNCF char(2), 
	@Ncf char(20), 	@SecSQL NVARCHAR(5), @fv datetime, @idglobalSec INT, @estado INT, 
	@SecuFinal INT, @rncEmpresa char(20)='', @fe int, @EstadoFiscal int=98

	/*Verifica si ya el registros existe*/
	IF NOT EXISTS ( SELECT 1 FROM cxpmovi1 t 
	JOIN INSERTED i ON t.documento = i.documento and t.tipomovi = i.tipomovi and t.suplidor= i.suplidor
	WHERE t.ID != i.ID ) /* Asegura que no se trate del mismo registro recién insertado*/ 	   
	BEGIN 
	 /*Acción para INSERT, Llenando variables*/   
	 select @SecSQL = SecSQL from INSERTED;
	END
	ELSE
	BEGIN
	 /*Si ya el registros existe, no hacer nada*/
	 RETURN; 
    END
	  
	if @SecSQL<>''
	BEGIN
	 BEGIN TRAN
	  select @Longitud = Longitud, @idTipoNCF = codigo from sis_TipoNCF where SecSQL=@SecSQL
	  select @rncEmpresa=rnc, @fe=FE from empresa

   	  if @fe=1
	   set @EstadoFiscal = 1;

	  /*Buscando la secuencia unica de NCF  */
	  SET @query = N'SET @SecNCF = NEXT VALUE FOR ' + QUOTENAME(@SecSQL)
	  EXEC sp_executesql @query, N'@SecNCF INT OUTPUT', @SecNCF OUTPUT;
	
	  /*construyendo el NCF  */
	  SET @Ncf= (TRIM(@SecSQL)+RIGHT(REPLICATE('0', @Longitud-3) +CAST(@SecNCF AS VARCHAR), @Longitud-3));
	  
	  select @fv=FVencimiento, @idglobalSec=id, @estado=estado, @SecuFinal=SecuFinal 
	  from sis_globalSec  
	  where idTipoNCF = @idTipoNCF and @SecNCF between SecuInicial and SecuFinal 

	  /*Actualizando NCF y fecha de Vencimiento  */
	  UPDATE t
	  SET t.ncf = @Ncf, t.FVencimientoNCF= @fv, t.RNCEmisor = @rncEmpresa, 
	  t.EstadoFiscal= @EstadoFiscal
      FROM cxpmovi1 t 
	  INNER JOIN inserted i ON t.id = i.id;

	  if (@SecuFinal - @SecNCF)=0 
	  UPDATE sis_globalSec set estado=3 where  id=@idglobalSec
	  else
	  if @estado=1
	  UPDATE sis_globalSec set estado=2 where  id=@idglobalSec
	
	 IF @ERROR <> 0 
	 BEGIN
	  ROLLBACK TRAN
      PRINT'NCF NO PUDO SER GENERADO . . .'
	 END
	 ELSE
	 COMMIT TRAN
   END
END;
--==============================================================================================================

/*para crear el triguer para generar NCF en CXPMOVI2  */
CREATE or ALTER TRIGGER tr_NCFcxp2
ON CXPMOVI2
AFTER INSERT
AS
BEGIN
	SET NOCOUNT ON;
	
	/*Variables   */
	DECLARE @query NVARCHAR(MAX), @SecNCF INT, @Longitud INT, @ERROR INT, @idTipoNCF char(2), 
	@Ncf char(20), 	@SecSQL NVARCHAR(5), @fv datetime, @idglobalSec INT, @estado INT, 
	@SecuFinal INT, @rncEmpresa char(20)='', @fe int, @EstadoFiscal int=98

	/*Verifica si ya el registros existe*/
	IF NOT EXISTS ( SELECT 1 FROM cxpmovi2 t 
	JOIN INSERTED i ON t.documento = i.documento and t.tipomovi = i.tipomovi and t.suplidor= i.suplidor
	WHERE t.ID != i.ID ) /* Asegura que no se trate del mismo registro recién insertado*/ 	   
	BEGIN 
	 /*Acción para INSERT, Llenando variables*/   
	 select @SecSQL = SecSQL from INSERTED;
	END
	ELSE
	BEGIN
	 /*Si ya el registros existe, no hacer nada*/
	 RETURN; 
    END
	  
	if @SecSQL<>''
	BEGIN
	 BEGIN TRAN
	  select @Longitud = Longitud, @idTipoNCF = codigo from sis_TipoNCF where SecSQL=@SecSQL
	  select @rncEmpresa=rnc, @fe=FE from empresa

   	  if @fe=1
	   set @EstadoFiscal = 1;
	   
	  /*Buscando la secuencia unica de NCF  */
	  SET @query = N'SET @SecNCF = NEXT VALUE FOR ' + QUOTENAME(@SecSQL)
	  EXEC sp_executesql @query, N'@SecNCF INT OUTPUT', @SecNCF OUTPUT;
	
	  /*construyendo el NCF  */
	  SET @Ncf= (TRIM(@SecSQL)+RIGHT(REPLICATE('0', @Longitud-3) +CAST(@SecNCF AS VARCHAR), @Longitud-3));
	  
	  select @fv=FVencimiento, @idglobalSec=id, @estado=estado, @SecuFinal=SecuFinal 
	  from sis_globalSec  
	  where idTipoNCF = @idTipoNCF and @SecNCF between SecuInicial and SecuFinal 

	  /*Actualizando NCF y fecha de Vencimiento  */
	  UPDATE t
	  SET t.ncf = @Ncf, t.FVencimientoNCF= @fv, t.RNCEmisor = @rncEmpresa, 
	  t.EstadoFiscal= @EstadoFiscal
      FROM cxpmovi2 t 
	  INNER JOIN inserted i ON t.id = i.id;

	  if (@SecuFinal - @SecNCF)=0 
	  UPDATE sis_globalSec set estado=3 where  id=@idglobalSec
	  else
	  if @estado=1
	  UPDATE sis_globalSec set estado=2 where  id=@idglobalSec
	
	 IF @ERROR <> 0 
	 BEGIN
	  ROLLBACK TRAN
      PRINT'NCF NO PUDO SER GENERADO . . .'
	 END
	 ELSE
	 COMMIT TRAN
   END
END;
--==============================================================================================================

/*para crear el triguer para generar NCF en CXPMOVI9  */
CREATE or ALTER TRIGGER tr_NCFcxp9
ON CXPMOVI9
AFTER INSERT
AS
BEGIN
	SET NOCOUNT ON;
	
	/*Variables   */
	DECLARE @query NVARCHAR(MAX), @SecNCF INT, @Longitud INT, @ERROR INT, @idTipoNCF char(2), 
	@Ncf char(20), 	@SecSQL NVARCHAR(5), @fv datetime, @idglobalSec INT, @estado INT, 
	@SecuFinal INT, @rncEmpresa char(20)='', @fe int, @EstadoFiscal int=98

	/*Verifica si ya el registros existe*/
	IF NOT EXISTS ( SELECT 1 FROM cxpmovi9 t 
	JOIN INSERTED i ON t.documento = i.documento and t.tipomovi = i.tipomovi and t.suplidor= i.suplidor
	WHERE t.ID != i.ID ) /* Asegura que no se trate del mismo registro recién insertado*/ 	   
	BEGIN 
	 /*Acción para INSERT, Llenando variables*/   
	 select @SecSQL = SecSQL from INSERTED;
	END
	ELSE
	BEGIN
	 /*Si ya el registros existe, no hacer nada*/
	 RETURN; 
    END
	  
	if @SecSQL<>''
	BEGIN
	 BEGIN TRAN
	  select @Longitud = Longitud, @idTipoNCF = codigo from sis_TipoNCF where SecSQL=@SecSQL
	  select @rncEmpresa=rnc, @fe=FE from empresa

   	  if @fe=1
	   set @EstadoFiscal = 1;

	  /*Buscando la secuencia unica de NCF  */
	  SET @query = N'SET @SecNCF = NEXT VALUE FOR ' + QUOTENAME(@SecSQL)
	  EXEC sp_executesql @query, N'@SecNCF INT OUTPUT', @SecNCF OUTPUT;
	
	  /*construyendo el NCF  */
	  SET @Ncf= (TRIM(@SecSQL)+RIGHT(REPLICATE('0', @Longitud-3) +CAST(@SecNCF AS VARCHAR), @Longitud-3));
	  
	  select @fv=FVencimiento, @idglobalSec=id, @estado=estado, @SecuFinal=SecuFinal 
	  from sis_globalSec  
	  where idTipoNCF = @idTipoNCF and @SecNCF between SecuInicial and SecuFinal 

	  /*Actualizando NCF y fecha de Vencimiento  */
	  UPDATE t
	  SET t.ncf = @Ncf, t.FVencimientoNCF= @fv, t.RNCEmisor = @rncEmpresa, 
	  t.EstadoFiscal= @EstadoFiscal
      FROM cxpmovi9 t 
	  INNER JOIN inserted i ON t.id = i.id;

	  if (@SecuFinal - @SecNCF)=0 
	  UPDATE sis_globalSec set estado=3 where  id=@idglobalSec
	  else
	  if @estado=1
	  UPDATE sis_globalSec set estado=2 where  id=@idglobalSec
	
	 IF @ERROR <> 0 
	 BEGIN
	  ROLLBACK TRAN
      PRINT'NCF NO PUDO SER GENERADO . . .'
	 END
	 ELSE
	 COMMIT TRAN
   END
END;
--==============================================================================================================

--si no existe NCFTIPO
alter table cajachica add ncftipo char(2)

/*para crear el triguer para generar NCF en CAJACHICA  */
CREATE or ALTER TRIGGER tr_NCFgmenor
ON cajachica
AFTER INSERT
AS
BEGIN
	SET NOCOUNT ON;
	  
	/*Variables   */
	DECLARE @query NVARCHAR(MAX), @SecNCF INT, @Longitud INT, @ERROR INT, @idTipoNCF char(2), 
	@Ncf char(20), 	@SecSQL NVARCHAR(5), @fv datetime, @idglobalSec INT, @estado INT, 
	@SecuFinal INT, @rncEmpresa char(20)='', @fe int, @EstadoFiscal int=98

	/*Verifica si ya el registros existe*/
	IF EXISTS (SELECT 1 FROM inserted WHERE SecSQL<>'' and ncftipo='GM' and (ncf IS NULL OR ncf = ''))
	BEGIN 
	 /*Acción para INSERT, Llenando variables*/ 
	 select @SecSQL = SecSQL from INSERTED;
	END
	ELSE
	BEGIN
	 /*Si ya el registros existe, no hacer nada*/
	 RETURN; 
    END
	  
	if @SecSQL<>''
	BEGIN
	 BEGIN TRAN
	  select @Longitud = Longitud, @idTipoNCF = codigo from sis_TipoNCF where SecSQL=@SecSQL
	  select @rncEmpresa=rnc, @fe=FE from empresa

   	  if @fe=1
	   set @EstadoFiscal = 1;

	  /*Buscando la secuencia unica de NCF  */
	  SET @query = N'SET @SecNCF = NEXT VALUE FOR ' + QUOTENAME(@SecSQL)
	  EXEC sp_executesql @query, N'@SecNCF INT OUTPUT', @SecNCF OUTPUT;
	
	  /*construyendo el NCF  */
	  SET @Ncf= (TRIM(@SecSQL)+RIGHT(REPLICATE('0', @Longitud-3) +CAST(@SecNCF AS VARCHAR), @Longitud-3));
	  
	  select @fv=FVencimiento, @idglobalSec=id, @estado=estado, @SecuFinal=SecuFinal 
	  from sis_globalSec  
	  where idTipoNCF = @idTipoNCF and @SecNCF between SecuInicial and SecuFinal 

	  /*Actualizando NCF y fecha de Vencimiento  */
	  UPDATE t
	  SET t.ncf = @Ncf, t.FVencimientoNCF= @fv, t.RNCEmisor = @rncEmpresa, 
	  t.EstadoFiscal= @EstadoFiscal
	  FROM CAJACHICA t 
	  INNER JOIN inserted i ON t.TRANSA = i.TRANSA;

	  if (@SecuFinal - @SecNCF)=0 
	  UPDATE sis_globalSec set estado=3 where  id=@idglobalSec
	  else
	  if @estado=1
	  UPDATE sis_globalSec set estado=2 where  id=@idglobalSec
	
	 IF @ERROR <> 0 
	 BEGIN
	  ROLLBACK TRAN
      PRINT'NCF NO PUDO SER GENERADO . . .'
	 END
	 ELSE
	 COMMIT TRAN
   END
END;

--==============================================================================================================

CREATE OR ALTER PROCEDURE actualizarSecNCFvencidos
WITH ENCRYPTION
AS
BEGIN
	SET NOCOUNT ON;
	DECLARE _Cursor CURSOR FOR 
		SELECT g.id,g.SecuFinal+1,t.SecSQL from sis_GlobalSec g 
		join sis_TipoNCF t on t.Codigo = g.idTipoNCF
		where g.estado in (1,2) and GETDATE() > g.FVencimiento

	-- Abre el cursor
	OPEN _Cursor; 

	-- Declara variables para almacenar valores  
	DECLARE	@id int, @secFinal int, @secsql NVARCHAR(5), @sql NVARCHAR(MAX) 

	-- Recupera la primera fila
	FETCH NEXT FROM _Cursor INTO @id, @secFinal, @secsql; 

	WHILE @@FETCH_STATUS = 0  
	BEGIN  
		UPDATE sis_globalSec SET estado = 4 WHERE id=@id
		
		IF EXISTS (SELECT * FROM sys.sequences WHERE name = @secsql )
		BEGIN
		 SET @sql = N'ALTER SEQUENCE ' + QUOTENAME(@secsql)+ 
		 N' RESTART WITH ' + CAST(@secFinal AS NVARCHAR(10)); 
		 EXEC sp_executesql @sql;
		END;

		-- Pasa a la siguiente fila		
		FETCH NEXT FROM _Cursor INTO  @id, @secFinal, @secsql; 
	END;  
	CLOSE _Cursor;  
	DEALLOCATE _Cursor;
END

--==============================================================================================================
--PARA ACTUALIZAR LAS SECUENCIAS UNICAS 
CREATE OR ALTER PROCEDURE Update_secunica 
  @solicitud INT, 
  @sec_inical INT = NULL, 
  @sec_final INT = NULL
AS
BEGIN
  DECLARE @cs INT = NULL, 
          @SecSQL CHAR(3), 
          @query NVARCHAR(MAX);

  -- Obtener SecSQL y CanSolicitada si @sf es NULL
  IF @sec_final IS NULL
  BEGIN
    SELECT @SecSQL = t.SecSQL, 
           @cs = g.CanSolicitada 
    FROM sis_GlobalSec g 
    JOIN sis_TipoNCF t ON g.idTipoNCF = t.Codigo;

    UPDATE sis_GlobalSec 
    SET SecuInicial = @sec_inical,   
        SecuFinal = @sec_inical + (@cs - 1) 
    WHERE NSolicitud = @solicitud;
  END
  ELSE
  BEGIN
    SELECT @SecSQL = t.SecSQL 
    FROM sis_GlobalSec g 
    JOIN sis_TipoNCF t ON g.idTipoNCF = t.Codigo;

    UPDATE sis_GlobalSec 
    SET SecuInicial = @sec_inical, 
        SecuFinal = @sec_final, 
        CanSolicitada = (@sec_final - @sec_inical) + 1 
    WHERE NSolicitud = @solicitud;
  END

  -- Construir el comando SQL para reiniciar la secuencia
  SET @query = 'ALTER SEQUENCE ' + QUOTENAME(@SecSQL) + ' RESTART WITH ' + CAST(@sec_inical AS NVARCHAR(20));
  EXEC sp_executesql @query;

  -- Obtener el siguiente valor de la secuencia
  SET @query = 'SELECT NEXT VALUE FOR ' + QUOTENAME(@SecSQL);
  EXEC sp_executesql @query;
END;

--ejemplo de uso 
--No.solicitud, sec_inicial, sec_final (opcional) 
--EXEC Update_secunica 3,10,20     
--*************************************
Select * from impuesto


--drop taable ITBISDGII
Create Table ITBISDGII  
(codigo integer default 0,
Descri char(100),
tasa Numeric(18,4),
Siglas char(5))
Go
--*************************************
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

--drop table EstadoImpresion

Create Table EstadoImpresion  
(estado integer default 0,
Descrip char(100))
Go


Insert into EstadoImpresion  (Estado, Descrip) values 
(0,'Sin Procesar'),
(1,'Listo para Impresión'),
(2,'Impreso')
GO

--drop table EstadoFiscal

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
(6,'Aceptado Condicional por la DGII'),
(98,'Documento No Fiscal'),
(99,'Rechazado')
GO





--Tabla de Tipo de Cuenta de Pago
	 CREATE TABLE TipoCuentaPago(
	tipo char(2) NULL,
	descrip char(150) NULL)
go

Insert into TipoCuentaPago (tipo, descrip) values 
('CT','Cta. Corriente'),
('AH','Ahorro'),
('OT','Otra')

CREATE   or alter  FUNCTION [dbo].[FNCambiaHexadecimal] (@inputString VARCHAR(MAX)
)
RETURNS varchar(200)
AS
BEGIN
    
    DECLARE @replacements TABLE
    (
        specialChar CHAR(1),
        hexadecimal VARCHAR(4)
    )

    INSERT INTO @replacements (specialChar, hexadecimal)
    VALUES  ('', '%20'),
  ('!', '%21'),
  ('#', '%23'),
  ('$', '%24'),
  ('&', '%26'),
  ('''', '%27'),
  ('(', '%28'),
  (')', '%29'),
  ('*', '%2A'),
  ('+', '%2B'),
  (',', '%2C'),
  ('/', '%2F'),
  (':', '%3A'),
  (';', '%3B'),
  ('=', '%3D'),
  ('?', '%3F'),
  ('@', '%40'),
  ('[', '%5B'),
  (']', '%5D'),
  ('"', '%22'),
  ('-', '%2D'),
  ('.', '%2E'),
  ('<', '%3C'),
  ('>', '%3E'),
  ('\', '%5V'),
  ('_', '%5F'),
  ('`', '%60'),
  ('^', '%5E')
 

	DECLARE @result VARCHAR(MAX) = @inputString ;
	declare @specialChar varchar(max)
	declare @hexadecimal varchar(max)

    WHILE EXISTS (SELECT * FROM @replacements)
    BEGIN
        SELECT TOP 1 @specialChar = specialChar, @hexadecimal = hexadecimal
        FROM @replacements;

        DELETE FROM @replacements
        WHERE specialChar = @specialChar;

        SET @result = REPLACE(@result, @specialChar, @hexadecimal);
    END;

    RETURN @result;
END
GO

CREATE    FUNCTION [dbo].[FNFechaDMY] (@D DATETIME
)
RETURNS varchar(12)
AS
BEGIN
   RETURN 
   left('00',2-len(day(@D)))+cast(day(@D) as varchar)+'-'+
   left('00',2-len(MONTH(@D)))+cast(MONTH(@D) as varchar)+'-'+
   left('0000',4-len(YEAR(@D)))+cast(YEAR(@D) as varchar)
END
GO

--drop table  [TipoImpuestoAdicional]

CREATE TABLE [dbo].[TipoImpuestoAdicional](
	[codigo] [char](3) NULL,
	[tipoimpuesto] [char](20) NULL,
	[descricion] [char](255) NULL,
	[tasa] [numeric](18, 2) NULL,
	[tipomonto] [char](1) NULL
) ON [PRIMARY]
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'001', N'Propina Legal       ', N'Propina Legal                                                                                                                                                                                                                                                  ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'002', N'CDT                 ', N'Contribución al Desarrollo de las Telecomunicaciones
Ley 153-98 Art. 45                                                                                                                                                                                       ', CAST(2.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'003', N'ISC                 ', N'Servicios Seguros en general                                                                                                                                                                                                                                   ', CAST(16.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'004', N'ISC                 ', N'Servicios de Telecomunicaciones                                                                                                                                                                                                                                ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'005', N'ISPRV               ', N'Expedición de la primera placa                                                                                                                                                                                                                                 ', CAST(17.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'006', N'ISC Específico      ', N'Cerveza                                                                                                                                                                                                                                                        ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'007', N'ISC Específico      ', N'Vinos de uva                                                                                                                                                                                                                                                   ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'008', N'ISC Específico      ', N'Vermut y demás vinos de uvas frescas                                                                                                                                                                                                                           ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'009', N'ISC Específico      ', N'Demás bebidas fermentadas                                                                                                                                                                                                                                      ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'010', N'ISC Específico      ', N'Alcohol Etílico sin desnaturalizar (Mayor o igual a 80%)                                                                                                                                                                                                       ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'011', N'ISC Específico      ', N'Alcohol Etílico sin desnaturalizar (inferior a 80%)                                                                                                                                                                                                            ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'012', N'ISC Específico      ', N'Aguardientes de uva                                                                                                                                                                                                                                            ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'013', N'ISC Específico      ', N'Whisky                                                                                                                                                                                                                                                         ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'014', N'ISC Específico      ', N'Ron y demás aguardientes de caña                                                                                                                                                                                                                               ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'015', N'ISC Específico      ', N'Gin y Ginebra                                                                                                                                                                                                                                                  ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'016', N'ISC Específico      ', N'Vodka                                                                                                                                                                                                                                                          ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'017', N'ISC Específico      ', N'Licores                                                                                                                                                                                                                                                        ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'018', N'ISC Específico      ', N'Los demás (Bebidas y Alcoholes)                                                                                                                                                                                                                                ', CAST(632.58 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'019', N'ISC Específico      ', N'Cigarrillos que contengan tabaco cajetilla 20 unidades                                                                                                                                                                                                         ', CAST(53.51 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'020', N'ISC Específico      ', N'Los demás Cigarrillos que contengan 20 unidades                                                                                                                                                                                                                ', CAST(53.51 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'021', N'ISC Específico      ', N'Cigarrillos que contengan 10 unidades                                                                                                                                                                                                                          ', CAST(26.75 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'022', N'ISC Específico      ', N'Los demás Cigarrillos que contengan 10 unidades                                                                                                                                                                                                                ', CAST(26.75 AS Numeric(18, 2)), N'M')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'023', N'ISC AdValorem       ', N'Cerveza                                                                                                                                                                                                                                                        ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'024', N'ISC AdValorem       ', N'Vinos de uva                                                                                                                                                                                                                                                   ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'025', N'ISC AdValorem       ', N'Vermut y demás vinos de uvas frescas                                                                                                                                                                                                                           ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'026', N'ISC AdValorem       ', N'Demás bebidas fermentadas                                                                                                                                                                                                                                      ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'027', N'ISC AdValorem       ', N'Alcohol Etílico sin desnaturalizar (Mayor o igual a 80%)                                                                                                                                                                                                       ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'028', N'ISC AdValorem       ', N'Alcohol Etílico sin desnaturalizar (inferior a 80%)                                                                                                                                                                                                            ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'029', N'ISC AdValorem       ', N'Aguardientes de uva                                                                                                                                                                                                                                            ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'030', N'ISC AdValorem       ', N'Whisky                                                                                                                                                                                                                                                         ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'031', N'ISC AdValorem       ', N'Ron y demás aguardientes de caña                                                                                                                                                                                                                               ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'032', N'ISC AdValorem       ', N'Gin y Ginebra                                                                                                                                                                                                                                                  ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'033', N'ISC AdValorem       ', N'Vodka                                                                                                                                                                                                                                                          ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'034', N'ISC AdValorem       ', N'Licores                                                                                                                                                                                                                                                        ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'035', N'ISC AdValorem       ', N'Los demás (Bebidas y Alcoholes)                                                                                                                                                                                                                                ', CAST(10.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'036', N'ISC AdValorem       ', N'Cigarrillos que contengan tabaco cajetilla 20 unidades                                                                                                                                                                                                         ', CAST(20.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'037', N'ISC AdValorem       ', N'Los demás Cigarrillos que contengan 20 unidades                                                                                                                                                                                                                ', CAST(20.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'038', N'ISC AdValorem       ', N'Cigarrillos que contengan 10 unidades                                                                                                                                                                                                                          ', CAST(20.00 AS Numeric(18, 2)), N'T')
GO
INSERT [dbo].[TipoImpuestoAdicional] ([codigo], [tipoimpuesto], [descricion], [tasa], [tipomonto]) VALUES (N'039', N'ISC AdValorem       ', N'Los demás Cigarrillos que contengan 10 unidades                                                                                                                                                                                                                ', CAST(20.00 AS Numeric(18, 2)), N'T')
GO



