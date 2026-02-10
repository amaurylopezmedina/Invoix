CREATE     FUNCTION [dbo].[FNCambiaHexadecimal] (@inputString VARCHAR(MAX)
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


/****** Object:  View [dbo].[vCodigoQR]    Script Date: 30/12/2024 6:28:59 p. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[vCodigoQR]
AS
SELECT        tr.numero AS Documento, tr.tipo AS TipoDocumento, tr.ncf AS eNCF, e.rnc AS RncEmisor, tr.cedula AS RncComprador, dbo.FNFechaDMY(tr.fecha) AS FechaEmision, tr.monto AS MontoTotal, tr.FechaFirma, tr.CodigoSeguridad, 
                         tr.EstadoFiscal, tr.trackid, tr.EstadoImpresion, tr.ConteoImpresiones, CASE WHEN RIGHT(tr.ncf, 2) = '32' AND tr.monto < 250000 THEN CONCAT('https://fc.dgii.gov.do/ecf/ConsultaTimbreFC?RncEmisor=', TRIM(e.rnc), '&ENCF=', 
                         TRIM(tr.ncf), '&MontoTotal=', tr.monto, '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(tr.CodigoSeguridad))) WHEN RIGHT(tr.ncf, 2) = '47' THEN CONCAT('https://ecf.dgii.gov.do/ecf/ConsultaTimbre?RncEmisor=', 
                         TRIM(e.rnc), '&ENCF=', TRIM(tr.ncf), '&FechaEmision=', dbo.FNFechaDMY(tr.fecha), '&MontoTotal=', tr.monto, '&FechaFirma=', REPLACE(TRIM(tr.FechaFirma), ' ', '%20'), '&CodigoSeguridad=', 
                         [dbo].[FNCambiaHexadecimal](tr.CodigoSeguridad)) ELSE CONCAT('https://ecf.dgii.gov.do/ecf/ConsultaTimbre?RncEmisor=', TRIM(e.rnc), '&RncComprador=', TRIM(tr.cedula), '&ENCF=', TRIM(tr.ncf), '&FechaEmision=', 
                         dbo.FNFechaDMY(tr.fecha), '&MontoTotal=', tr.monto, '&FechaFirma=', REPLACE(TRIM(tr.FechaFirma), ' ', '%20'), '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(tr.CodigoSeguridad))) END AS URL
FROM            dbo.empresa AS e INNER JOIN
                         dbo.Transa01 AS tr ON tr.tipo IN ('03', '04', '33', '34')
WHERE        (tr.CodigoSeguridad IS NOT NULL) AND (tr.CodigoSeguridad <> '') AND (tr.FechaFirma IS NOT NULL) AND (tr.FechaFirma <> '')
GO
/****** Object:  View [dbo].[vEmpresa]    Script Date: 30/12/2024 6:28:59 p. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[vEmpresa]
AS
SELECT        itbis AS itbisenprecio, nombre, Dire, Tele, rnc, itbis, prncheque, facdetalle, Secuen1, secuen2, secuen3, secuen4, secuen5, secuen6, secuen7, secuen8, secuen9, secuen10, cliente, Suplidor, fechaini, titulo1, titulo2, titulo3, 
                         titulo4, titulo5, titulo6, vendedor, zona, Provincia, cnt, sistema1, sistema2, sistema3, sistema4, sistema5, Sistema6, pedido, despachopar, mes, ano, movi1, movi2, movi3, modivendedor, pto, vence, producto, bproducto, 
                         fechabal, valorresumen, empresa, fecha, ano1, ano2, transfe, cotiza, BANCO, empleado, Ordenp, ReporteTiempo, EMPRESATITULO, fechacxp, fechacxc, fechacnt, fechanomina, otraentrada, formula, prestamo, otroprestamo, 
                         activo, comprobante, comprobante1, comprobantend, incf, NCFccaja, NCFcaja, secuen22, id, cuentacaja, cajachica, secuen13, secuen15, DEVO, conduce, nota, cntmanoObra, cntmateriaPrima, cntCIF, credito, contado, 
                         fechaTrabajo, rayox1, rayox2, labora1, labora2, cirugia1, cirugia2, emerge1, emerge2, farmacia1, farmacia2, rayox, hemograma, orina, febrile, trabajo, NOMINA, tasa, dollar, AVON1, AVON, orden, impresora, nota1, nota2, nota3, 
                         nota4, nota5, nota6, nota7, bono, aporte, transfer, fechacostop, existenciaf, CNT1, CNT2, CNT3, CNT4, CNT5, CNT6, CNT7, CNT8, CNT9, reclama, certificado, secuen101, secuen102, id101, secuen201, secuen202, userlibre, 
                         secuen221, secuen222, id102, TipodeIngresos, IndicadorEnvioDiferido, RazonSocialEmisor, NombreComercial, Sucursal, DireccionEmisor, Municipio, CorreoEmisor, WebSite, ActividadEconomica
FROM            dbo.empresa
GO
/****** Object:  View [dbo].[vTablaPago]    Script Date: 30/12/2024 6:28:59 p. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
Select * from transa01

CREATE OR ALTER VIEW [dbo].[vTablaPago]
AS
SELECT        tr.numero AS Documento, tr.tipo AS TipoDocumento, 
ncf as eNCF, tr.EstadoFiscal, tr.trackid, tr.FechaFirma, tr.CodigoSeguridad, tr.EstadoImpresion, tr.ConteoImpresiones, 


1 AS TipoPago, 'Efectivo' AS Descrip, COALESCE (tr.tasa, 0.00) AS TipoCambio, (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN tr.efectivo * 1 ELSE tr.efectivo * tr.tasa END) 
                         AS Monto
FROM            transa01 tr
WHERE        tr.efectivo <> 0
UNION ALL
SELECT        tr.numero AS Documento, tr.tipo AS TipoDocumento, 
ncf as eNCF, tr.EstadoFiscal, tr.trackid, tr.FechaFirma, tr.CodigoSeguridad, tr.EstadoImpresion, tr.ConteoImpresiones, 


2 AS TipoPago, 'Cheque/Transferencia/Deposito' AS Descrip, COALESCE (tr.tasa, 0.00) AS TipoCambio, (CASE WHEN COALESCE (tr.tasa, 0.00) 
                         = 0 THEN (transferencia + cheque) * 1 ELSE (transferencia + cheque) * tr.tasa END) AS Monto
FROM            transa01 tr
WHERE        cheque <> 0 OR
                         transferencia <> 0
UNION ALL
SELECT        tr.numero AS Documento, tr.tipo AS TipoDocumento, 
ncf as eNCF, tr.EstadoFiscal, tr.trackid, tr.FechaFirma, tr.CodigoSeguridad, tr.EstadoImpresion, tr.ConteoImpresiones, 


3 AS TipoPago, 'Tarjeta' AS Descrip, COALESCE (tr.tasa, 0.00) AS TipoCambio, (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN tarjeta * 1 ELSE tarjeta * tr.tasa END) 
                         AS Monto
FROM            transa01 tr
WHERE        tarjeta <> 0
UNION ALL
SELECT        tr.numero AS Documento, tr.tipo AS TipoDocumento, 
ncf as eNCF, tr.EstadoFiscal, tr.trackid, tr.FechaFirma, tr.CodigoSeguridad, tr.EstadoImpresion, tr.ConteoImpresiones, 

CASE WHEN tr.tipo = '04' OR
                         tr.tipo = '34' THEN 4 END AS TipoPago, CASE WHEN tr.tipo = '04' OR
                         tr.tipo = '34' THEN 'Venta a Credito' END AS Descrip, COALESCE (tr.tasa, 0.00) AS TipoCambio, (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN tr.monto * 1 ELSE tr.monto * tr.tasa END) AS Monto
FROM            transa01 tr
WHERE        tr.tipo = '04' OR
                         tr.tipo = '34'
GO
/****** Object:  View [dbo].[vTradetalle]    Script Date: 30/12/2024 6:28:59 p. m. ******/
Select * from tradetalle
GO
CREATE VIEW [dbo].[vTradetalle]
AS
SELECT        td.orden AS NumeroLinea, td.numero AS Documento, td.tipo AS TipoDocumento, tr.ncf AS eNCF, tr.EstadoFiscal, tr.Trackid, tr.FechaFirma, tr.CodigoSeguridad, tr.EstadoImpresion, tr.ConteoImpresiones, 'Interna' AS TipoCodigo, 
                         td.producto AS CodigoItem, i.codigodgii AS IndicadorFacturacion, trim(p.descrip) AS NombreItem, CASE p.CLASIFICA2 WHEN '01' THEN 1 WHEN '02' THEN 2 ELSE 1 END AS IndicadorBienoServicio, 
                         CASE WHEN td.cantidad < 0 THEN td.cantidad * - 1 ELSE td.cantidad END AS CantidadItem, '43' AS Unidadmedida,  COALESCE (tr.tasa, 0.00) AS TipoCambio, (CASE WHEN COALESCE (tr.tasa, 0.00) 
                         = 0 THEN td.precio * 1 ELSE td.precio * tr.tasa END) AS PrecioUnitarioItem, (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN td.monto1 * 1 ELSE td.monto1 * tr.tasa END) AS MontoItem, td.itbis AS TasaITBIS, td.montoitbis, 
                         td.descuen AS TasaDescuento, td.montodesc AS MontoDescuento
FROM            dbo.tradetalle AS td LEFT OUTER JOIN
                         dbo.producto AS p ON p.producto = td.producto LEFT OUTER JOIN
                         dbo.impuesto AS i ON i.impuesto = p.impuesto LEFT OUTER JOIN
                         dbo.Transa01 AS tr ON tr.numero = td.numero AND tr.tipo = td.tipo
GO
/****** Object:  View [dbo].[vTradetalleTotales]    Script Date: 30/12/2024 6:28:59 p. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[vTradetalleTotales]
AS
SELECT        td.numero AS Documento, td.tipo AS TipoDocumento, SUM((CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN td.monto1 * 1 ELSE td.monto1 * tr.tasa END)) AS MontoTotal, 
                         SUM(CASE WHEN td.itbis <> 0 THEN (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN td.monto1 * 1 ELSE td.monto1 * tr.tasa END) ELSE 0.00 END) AS MontoGravadoTotal, 
                         SUM(CASE WHEN td.itbis = 18 THEN (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN td.monto1 * 1 ELSE td.monto1 * tr.tasa END) ELSE 0.00 END) AS MontoGravadoI1, 
                         SUM(CASE WHEN td.itbis = 16 THEN (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN td.monto1 * 1 ELSE td.monto1 * tr.tasa END) ELSE 0.00 END) AS MontoGravadoI2, SUM(CASE WHEN td.itbis = 0 THEN 0 ELSE 0.00 END) 
                         AS MontoGravadoI3, SUM(CASE WHEN td.itbis = 0 THEN (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN td.monto1 * 1 ELSE td.monto1 * tr.tasa END) ELSE 0.00 END) AS MontoExento, 
                         MAX(CASE WHEN td.itbis = 18 THEN td.itbis ELSE 0.00 END) AS ITBIS1, MAX(CASE WHEN td.itbis = 16 THEN td.itbis ELSE 0.00 END) AS ITBIS2, MAX(CASE WHEN td.itbis = 0 THEN td.itbis ELSE 0.00 END) AS ITBIS3, 
                         SUM((CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN td.montoitbis * 1 ELSE td.montoitbis * tr.tasa END)) AS TotalITBIS, SUM(CASE WHEN td.itbis = 18 THEN td.montoitbis * COALESCE (tr.tasa, 1) ELSE 0.00 END) 
                         AS TotalITBIS1, SUM(CASE WHEN td.itbis = 16 THEN td.montoitbis * COALESCE (tr.tasa, 1) ELSE 0.00 END) AS TotalITBIS2, SUM(CASE WHEN td.itbis = 0 THEN 0 ELSE 0.00 END) AS TotalITBIS3, 
                         SUM((CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN 0 ELSE td.monto1 END)) AS MontoTotalOtraMoneda, SUM(CASE WHEN td.itbis <> 0 THEN (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN 0 ELSE td.monto1 END) 
                         ELSE 0.00 END) AS MontoGravadoTotalOtraMoneda, SUM(CASE WHEN td.itbis = 18 THEN (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN 0 ELSE td.monto1 END) ELSE 0.00 END) AS MontoGravadoI1OtraMoneda, 
                         SUM(CASE WHEN td.itbis = 16 THEN (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN 0 ELSE td.monto1 END) ELSE 0.00 END) AS MontoGravadoI2OtraMoneda, SUM(CASE WHEN td.itbis = 0 THEN 0 ELSE 0.00 END) 
                         AS MontoGravadoI3OtraMoneda, SUM(CASE WHEN td.itbis = 0 THEN (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN 0 ELSE td.monto1 END) ELSE 0.00 END) AS MontoExentoOtraMoneda, SUM((CASE WHEN COALESCE (tr.tasa,
                          0.00) = 0 THEN 0 ELSE td.montoitbis END)) AS TotalITBISOtraMoneda, SUM(CASE WHEN td.itbis = 18 THEN (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN 0 ELSE td.montoitbis END) ELSE 0.00 END) 
                         AS TotalITBIS1OtraMoneda, SUM(CASE WHEN td.itbis = 16 THEN (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN 0 ELSE td.montoitbis END) ELSE 0.00 END) AS TotalITBIS2OtraMoneda, 
                         SUM(CASE WHEN td.itbis = 0 THEN 0 ELSE 0.00 END) AS TotalITBIS3OtraMoneda
FROM            dbo.tradetalle AS td LEFT OUTER JOIN
                         dbo.Transa01 AS tr ON tr.numero = td.numero AND tr.tipo = td.tipo
GROUP BY td.numero, td.tipo
GO
/****** Object:  View [dbo].[vTransa01]    Script Date: 30/12/2024 6:28:59 p. m. ******/
Select * from transa01

FVencimientoNCF


CREATE VIEW [dbo].[vTransa01]
AS
SELECT        tr.numero AS Documento, tr.tipo AS TipoDocumento, SUBSTRING(tr.ncf, 1, 1) AS TipoECFL, SUBSTRING(tr.ncf, 2, 2) AS TipoECF, tn.descripcion AS TipoECFL1, tr.ncf AS eNCF, tr.FVencimientoNCF AS FechaVencimientoSecuencia, 
                         tr.vence AS FechaLimitePago, tr.dia AS TerminoPago, CAST(tr.dia AS char(3)) + ' Dias' AS TerminoPagoL, tr.almacen AS Almacen, '01' AS TipoIngresos, 'Ingresos por Operaciones' AS TipoIngresosL, (CASE WHEN tr.tipo = '03' OR
                         tr.tipo = '33' THEN 1 WHEN tr.tipo = '04' OR
                         tr.tipo = '34' THEN 2 END) AS TipoPago, (CASE WHEN tr.tipo = '03' OR
                         tr.tipo = '33' THEN 'Contado' WHEN tr.tipo = '04' OR
                         tr.tipo = '34' THEN 'Crédito' END) AS TipoPagoL, tr.fecha AS FechaEmision, tr.cliente AS CodigoComprador, tr.cedula AS RNCComprador, c.Nombre AS RazonSocialComprador, c.Tele AS TelefonoComprador, 
                         c.Dire AS DireccionComprador, tr.vendedor AS CodigoVendedor, tr.Venname AS NombreVendedor, (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN tr.monto * 1 ELSE tr.monto * tr.tasa END) AS MontoTotal, 
                         (CASE WHEN tr.tipo = '33' OR
                         tr.tipo = '34' THEN 'USD' WHEN tr.tipo = '03' OR
                         tr.tipo = '04' THEN 'DOP' ELSE 'DOP' END) AS TipoMoneda, (CASE WHEN tr.tipo = '33' OR
                         tr.tipo = '34' THEN 'DOLAR ESTADOUNIDENSE' WHEN tr.tipo = '03' OR
                         tr.tipo = '04' THEN 'PESO DOMINICANO' ELSE 'PESO DOMINICANO' END) AS TipoMonedaL, COALESCE (tr.tasa, 0.00) AS TipoCambio, (CASE WHEN COALESCE (tr.tasa, 0.00) = 0 THEN 0 ELSE tr.monto END) 
                         AS MontoTotalOtraMoneda, tr.fechacreacion, tr.Trackid, tr.FechaFirma, tr.CodigoSeguridad, tr.EstadoImpresion, tr.ConteoImpresiones, tr.EstadoFiscal, tr.URLQR, tr.observa AS Observaciones, tr.usuario AS Creadopor, 
                         tr.Modificado AS ModificadoPor, (CASE WHEN COALESCE (tr.observa1, '') <> '' THEN tr.observa1 WHEN COALESCE (tr.observa3, '') <> '' THEN tr.observa3 ELSE '' END) AS NotaPermanente
FROM            dbo.Transa01 AS tr LEFT OUTER JOIN
                         dbo.cliente AS c ON c.cliente = tr.cliente LEFT OUTER JOIN
                         dbo.TipoNCF AS tn ON tn.codigo = SUBSTRING(tr.ncf, 2, 2)
GO
