
CREATE TABLE [dbo].[movife](
	[IDFE] [char](2) NOT NULL,
	[Descripcion] [char](150) NULL,
	[Movimiento] [char](100) NULL,
	[TiposComprobantesUtilizados] [char](100) NULL,
	[TablaOrigen] [char](100) NULL,
	[CampoFiltro1] [char](100) NULL,
	[CampoFiltro2] [char](100) NULL,
	[QueryEncabezado] [varchar](max) NULL,
	[NombreQueryEncabezado] [char](100) NULL,
	[QueryDetalle] [varchar](max) NULL,
	[NombreQueryDetalle] [char](100) NULL,
	[Observaciones] [varchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
