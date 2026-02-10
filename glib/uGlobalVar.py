# Variables Globales


# Campso para el log de actividadesde Facturación E. DGII
campos_log = {
    "ID": "int IDENTITY(1,1) NOT NULL",
    "RncEmisor": "NVARCHAR(20) NOT NULL",
    "encf": "NVARCHAR(50) NOT NULL",
    "TipoActividad": "NVARCHAR(50) NOT NULL",
    "FechaActividad": "DATETIME2 NOT NULL",
    "Equipo": "NVARCHAR(100)",
    "RutaImpresion": "NVARCHAR(255)",
    "impresora": "NVARCHAR(100)",
}
