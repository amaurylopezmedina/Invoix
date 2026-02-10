Alter Table  add
trackid char(255),
FechaFirma char(20),
CodigoSeguridad char(20),
CodigoSeguridadCF char(20),
EstadoFiscal int, 
URLQR char(255), 
fechacreacion DATETIME NOT NULL DEFAULT GETDATE(),     
EstadoImpresion  int default 0, 
ConteoImpresiones int default 0,
tasa numeric(18,4),
transferencia numeric(18,4),
Modificado DATETIME NOT NULL DEFAULT GETDATE(),
observa3 char(254),
ResultadoEstadoFiscal TEXT,
MontoDGII numeric(18,4), 
MontoITBISDGII numeric(18,4);

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
