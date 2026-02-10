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
