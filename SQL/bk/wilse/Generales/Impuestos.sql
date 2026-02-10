

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

