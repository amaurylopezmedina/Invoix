CREATE OR ALTER VIEW vFETablaPago AS
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

/*    UNION ALL

    SELECT 
        cxc2.documento AS NumeroFacturaInterna, 
        cxc2.tipo AS TipoDocumento, 
        cxc2.RNCEmisor, 
        cxc2.ncf AS eNCF, 
        cxc2.EstadoFiscal, 
        cxc2.trackid, 
        cxc2.FechaFirma, 
        cxc2.CodigoSeguridad, 
        cxc2.EstadoImpresion, 
        fp.FormaPago, 
        fp.Descrip, 
        COALESCE(cxc2.tasa, 1) AS TipoCambio, 
        CASE 
            WHEN COALESCE(cxc2.tasa, 1.00) = 1 THEN fp.MontoPago 
            ELSE fp.MontoPago * cxc2.tasa 
        END AS MontoPago
    FROM CXCMovi2 cxc2
    CROSS APPLY (
        VALUES
            (1, 'Efectivo', cxc2.efectivo),
            (2, 'Cheque/Transferencia/Deposito', cxc2.transferencia + cxc2.cheque),
            (3, 'Tarjeta', cxc2.tarjeta)
    ) AS fp(FormaPago, Descrip, MontoPago)
    WHERE fp.MontoPago IS NOT NULL AND fp.MontoPago <> 0*/
)
SELECT * FROM Pagos;


