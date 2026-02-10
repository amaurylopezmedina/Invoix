--Pasos
--1 - Revisar RNC Empresa para que le RNC solo tenga Numeros
Select * from empresa

--2 Crear Tabla de impuestos Segun DGII
--drop table ITBISDGII

Select * from  ITBISDGII

Create Table ITBISDGII  
(codigo integer default 0,
Descri char(100),
tasa Numeric(18,4),
Siglas char(5))
Go
--3*************************************
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


Select * from impuesto
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
GO
Alter Table transa01 add    CodigoSeguridadCF char(10) 
GO
alter table transa01 add transferencia numeric (18,4)
GO
Alter table producto add servicio int default 0  -- si es producto o servicio
GO
aLTER tABLE producto add NotaImpresion varchar(2000)
GO
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


update  empresa set TipodeIngresos = '01'
go

update  empresa set IndicadorEnvioDiferido = 0
go


Update empresa set itbisenprecio = 0  -- 0 El precio no inclute el itbis y 1 el precio tiene el itbis incluido

Alter table transa01

add idfe char(3)
go



Alter table empresa

add URLEnvio char(255)
go

update  empresa set URLEnvio = 'https://10.0.0.250:8001/FGE' --nolo pongo
go



Alter table empresa
add 
Ambiente int
go
update  empresa set ambiente = 0  -- 0 Prueba 1 de Certificacion 2 Productivo
go

Select * from FEAMBIENTE
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

--Funciones Necesarias para el QR
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



