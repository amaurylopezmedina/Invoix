Select * from sis_TipoNCF

Select itbisenprecio,* from empresa

Update empresa set itbisenprecio=1

Select * From empresa       

Update empresa set
[TipodeIngresos] = '01'
      ,[IndicadorEnvioDiferido] = 0
      ,[RazonSocialEmisor] = 'LH INTERNACIONAL,S.R.L                                      '
      ,[NombreComercial] = 'LH INTERNACIONAL,S.R.L                                      '
      ,[Sucursal] = ''
      ,[DireccionEmisor]= 'AV. CIRCUNVALACION ESQ. SILVESTRE TAVERAS                   '
      ,[MunicipioFE] = ''
      ,[ProvinciaFE]= ''
      ,[CorreoEmisor]= ''
      ,[WebSite]= ''
      ,[ActividadEconomica] = ''

------------------------------------------------------------
Select * from [impuesto]

DRop table [impuesto]
GO
/****** Object:  Table [dbo].[impuesto]    Script Date: 11/3/2025 3:58:09 a. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[impuesto](
	[impuesto] [char](2) NOT NULL,
	[Descrip] [char](40) NOT NULL,
	[pto] [decimal](18, 3) NULL,
	[codigodgii] [int] NULL,
	[Siglas] [char](5) NULL
) ON [PRIMARY]
GO
INSERT [dbo].[impuesto] ([impuesto], [Descrip], [pto], [codigodgii], [Siglas]) VALUES (N'00', N'EXCENTO                                 ', CAST(0.000 AS Decimal(18, 3)), 4, N'IE   ')
GO
INSERT [dbo].[impuesto] ([impuesto], [Descrip], [pto], [codigodgii], [Siglas]) VALUES (N'01', N'I. S. R.                                ', CAST(16.000 AS Decimal(18, 3)), NULL, NULL)
GO
INSERT [dbo].[impuesto] ([impuesto], [Descrip], [pto], [codigodgii], [Siglas]) VALUES (N'02', N'ITBIS 18%                               ', CAST(18.000 AS Decimal(18, 3)), 1, N'I2   ')
GO
INSERT [dbo].[impuesto] ([impuesto], [Descrip], [pto], [codigodgii], [Siglas]) VALUES (N'03', N'ITBIS 16%                               ', CAST(16.000 AS Decimal(18, 3)), 2, N'I1   ')
GO
INSERT [dbo].[impuesto] ([impuesto], [Descrip], [pto], [codigodgii], [Siglas]) VALUES (N'04', N'NO FACTURABLE                           ', CAST(0.000 AS Decimal(18, 3)), 0, N'NF   ')
GO
INSERT [dbo].[impuesto] ([impuesto], [Descrip], [pto], [codigodgii], [Siglas]) VALUES (N'05', N'ITBIS 0%                                ', CAST(0.000 AS Decimal(18, 3)), 0, N'I0   ')
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [PK_impuesto]    Script Date: 11/3/2025 3:58:09 a. m. ******/
ALTER TABLE [dbo].[impuesto] ADD  CONSTRAINT [PK_impuesto] PRIMARY KEY NONCLUSTERED 
(
	[impuesto] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

------------------------------------------------------------


Alter table empresa
add 
Ambiente int



update  empresa set ambiente = 0

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

WITH
  e AS (
    SELECT
      itbisenprecio,
      rnc
    FROM
      empresa
    WITH
      (NOLOCK)
  ) 
 
 Select CASE
    WHEN RIGHT(tr.ncf, 2) = '32'
    AND tr.monto < 250000 THEN CONCAT(
      'https://fc.dgii.gov.do/ecf/ConsultaTimbreFC?RncEmisor=',
      TRIM(tr.rncemisor),
      '&ENCF=',
      TRIM(tr.ncf),
      '&MontoTotal=',
      tr.monto,
      '&CodigoSeguridad=',
      [dbo].[FNCambiaHexadecimal] (TRIM(tr.CodigoSeguridad))
    )
    WHEN RIGHT(tr.ncf, 2) = '47' THEN CONCAT(
      'https://ecf.dgii.gov.do/ecf/ConsultaTimbre?RncEmisor=',
      TRIM(tr.rncemisor),
      '&ENCF=',
      TRIM(tr.ncf),
      '&FechaEmision=',
      dbo.FNFechaDMY (tr.fecha),
      '&MontoTotal=',
      tr.monto,
      '&FechaFirma=',
      REPLACE(TRIM(tr.FechaFirma), ' ', '%20'),
      '&CodigoSeguridad=',
      [dbo].[FNCambiaHexadecimal] (tr.CodigoSeguridad)
    )
    ELSE CONCAT(
      'https://ecf.dgii.gov.do/ecf/ConsultaTimbre?RncEmisor=',
      TRIM(tr.rncemisor),
      '&RncComprador=',
      TRIM(tr.cedula),
      '&ENCF=',
      TRIM(tr.ncf),
      '&FechaEmision=',
      dbo.FNFechaDMY (tr.fecha),
      '&MontoTotal=',
      tr.monto,
      '&FechaFirma=',
      REPLACE(TRIM(tr.FechaFirma), ' ', '%20'),
      '&CodigoSeguridad=',
      [dbo].[FNCambiaHexadecimal] (TRIM(tr.CodigoSeguridad))
    )
  END AS URLQR
  from transa01 tr where ncf = 'E320000000014'
