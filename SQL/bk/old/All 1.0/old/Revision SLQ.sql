

Alter Table transa01 add 
trackid char(255),
CodigoSeguridadCF char(20),
EstadoFiscal int, 
URLQR char(255), 
FechaCreacion DATETIME NOT NULL DEFAULT GETDATE(),     
EstadoImpresion  int default 0, 
ConteoImpresiones int default 0,
--tasa numeric(18,4),
transferencia numeric(18,4),
--Modificado DATETIME NOT NULL DEFAULT GETDATE(),
observa3 char(254),
ResultadoEstadoFiscal TEXT,
MontoDGII numeric(18,4), 
MontoITBISDGII numeric(18,4);

--Agregar al Token El Ambiente y el origen y el rnccontrobuyente.  Si es de la dgii o de un contribuyente(en este caso poner el rnc)


Alter Table impuesto add  codigodgii integer, Siglas char(5)


Select * from impuesto

    /* EL INDICADOR DE FACTURA ES  */
      /*a)Indicar si es valor
      0: No Facturable -- 
      1: ITBIS 1 (18%) 
      2: ITBIS 2 (16%)
      3: ITBIS 3 (0%) --- Venta de exportacion (REvisar)
      4: Exento (E)*/

Create Table ITBISDGII  
(codigo integer default 0,
Descri char(100),
tasa Numeric(18,4),
Siglas char(5))

Insert into ITBISDGII  (codigo, descri,TASA,siglas) values 
(0,'No Facturable',0,'IN'),
(1,'18%',18,'I2'),
(2,'16%',16,'I1'),
(3,'0%',0,'IO'),
(4,'Exento (E)*',0,'IE')

Select * from ITBISDGII

Drop Table EstadoImpresion
Create Table EstadoImpresion  
(estado integer default 0,
DescriP char(100))



Insert into EstadoImpresion  (estado, descrip) values 
(0,'Sin Procesar'),
(1,'Listo para Impresión'),
(2,'Impreso')

Select * from EstadoImpresion

Drop Table EstadoFiscal
Create Table EstadoFiscal
(estado integer default 0,
Descrip char(100))

Select * from EstadoFiscal

Insert into EstadoFiscal (estado, descrip) values 
(0,'En Cola'),
(1,'Procesado'),
(2,'XML Generado'),
(3,'XML Firmado'),
(4,'Enviado'),
(5,'Aceptado por la DGII'),
(98,'Documento No Fiscal'),
(99,'Rechazado')

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

alter table empresa alter column provincia [varchar](6) NULL




	sELECT * FROM EMPRESA

	update  empresa set  [RazonSocialEmisor] = N'ASESORIA Y SISTEMAS EMPRESARIALES ASESYS, SRL', 
	[NombreComercial] = N'ASESORIA Y SISTEMAS EMPRESARIALES ASESYS, SRL', 
	[Sucursal] = '', 
	[DireccionEmisor] = N'CALLE HOSTOS NO. 19', 
	[Municipio] = N'010101', 
	[Provincia] = N'010000', 
	[CorreoEmisor] =  N'info@asesys.com.do', 
	[WebSite] = N'www.asesys.com.do', 
	[ActividadEconomica] =N'INSTALACIONES DE PROCESAMIENTO DE DATOS Y SERVICIOS DE SOPORTE RELACIONADOS',  
	 rnc = '131709745'

	 CREATE TABLE EmpresaTelefonos(
	[IDRNC] [varchar](11) NULL,
	[TelefonoEmisor] [varchar](12) NULL)

	Select * from EmpresaTelefonos

--Tabla de Tipo de Cuenta de Pago
	 CREATE TABLE TipoCuentaPago(
	tipo char(2) NULL,
	descrip char(150) NULL)

Insert into TipoCuentaPago (tipo, descrip) values 
('CT','Cta. Corriente'),
('AH','Ahorro'),
('OT','Otra')
