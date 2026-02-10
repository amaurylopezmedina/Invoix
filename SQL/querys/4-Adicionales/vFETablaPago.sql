--CREATE OR ALTER VIEW vFETablaPago AS
WITH Pagos AS (
    SELECT 
        tr.numero AS NumeroFacturaInterna, 
        tr.tipo AS TipoDocumento, 
        tr.RNCEmisor, 
        tr.ncf AS eNCF, 
        tr.EstadoFiscal, 
        tr.trackid, 
        tr.FechaFirma, 
        tr.CodigoSeguridad, 
        tr.EstadoImpresion, 
        fp.FormaPago, 
        fp.Descrip, 
        COALESCE(tr.tasa, 1) AS TipoCambio, 
        CASE 
            WHEN COALESCE(tr.tasa, 1.00) = 1 THEN fp.MontoPago 
            ELSE fp.MontoPago * tr.tasa 
        END AS MontoPago
    FROM transa01 tr
    CROSS APPLY (
        VALUES
            (1, 'Efectivo', tr.efectivo),
            (2, 'Cheque/Transferencia/Deposito', tr.transferencia + tr.cheque),
            (3, 'Tarjeta', tr.tarjeta),
            (CASE WHEN tr.tipo IN ('04', '34') THEN 4 END, 
             CASE WHEN tr.tipo IN ('04', '34') THEN 'Venta a Credito' END, 
             CASE WHEN tr.tipo IN ('04', '34') THEN tr.monto END)
    ) AS fp(FormaPago, Descrip, MontoPago)
    WHERE fp.MontoPago IS NOT NULL AND fp.MontoPago <> 0

   )


SELECT * FROM Pagos





