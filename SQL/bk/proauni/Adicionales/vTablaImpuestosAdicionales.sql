
create or alter view vFETablaImpuestosAdicionales  as 
WITH Unpivoted AS (
    SELECT 
        NumeroFacturaInterna,
        TipoECFL,
        RNCEmisor,
        TipoeCF,
        eNCF,
        TipoImpuesto,
        TasaImpuestoAdicional,
        MontoImpuestoSelectivoConsumoEspecifico,
        MontoImpuestoSelectivoConsumoAdvalorem,
        OtrosImpuestosAdicionales
    FROM vFEEncabezado
    CROSS APPLY (
        VALUES 
            (TipoImpuesto1, TasaImpuestoAdicional1, MontoImpuestoSelectivoConsumoEspecifico1, MontoImpuestoSelectivoConsumoAdvalorem1, OtrosImpuestosAdicionales1),
            (TipoImpuesto2, TasaImpuestoAdicional2, MontoImpuestoSelectivoConsumoEspecifico2, MontoImpuestoSelectivoConsumoAdvalorem2, OtrosImpuestosAdicionales2),
            (TipoImpuesto3, TasaImpuestoAdicional3, MontoImpuestoSelectivoConsumoEspecifico3, MontoImpuestoSelectivoConsumoAdvalorem3, OtrosImpuestosAdicionales3),
            (TipoImpuesto4, TasaImpuestoAdicional4, MontoImpuestoSelectivoConsumoEspecifico4, MontoImpuestoSelectivoConsumoAdvalorem4, OtrosImpuestosAdicionales4),
            (TipoImpuesto5, TasaImpuestoAdicional5, MontoImpuestoSelectivoConsumoEspecifico5, MontoImpuestoSelectivoConsumoAdvalorem5, OtrosImpuestosAdicionales5),
            (TipoImpuesto6, TasaImpuestoAdicional6, MontoImpuestoSelectivoConsumoEspecifico6, MontoImpuestoSelectivoConsumoAdvalorem6, OtrosImpuestosAdicionales6),
            (TipoImpuesto7, TasaImpuestoAdicional7, MontoImpuestoSelectivoConsumoEspecifico7, MontoImpuestoSelectivoConsumoAdvalorem7, OtrosImpuestosAdicionales7),
            (TipoImpuesto8, TasaImpuestoAdicional8, MontoImpuestoSelectivoConsumoEspecifico8, MontoImpuestoSelectivoConsumoAdvalorem8, OtrosImpuestosAdicionales8),
            (TipoImpuesto9, TasaImpuestoAdicional9, MontoImpuestoSelectivoConsumoEspecifico9, MontoImpuestoSelectivoConsumoAdvalorem9, OtrosImpuestosAdicionales9),
            (TipoImpuesto10, TasaImpuestoAdicional10, MontoImpuestoSelectivoConsumoEspecifico10, MontoImpuestoSelectivoConsumoAdvalorem10, OtrosImpuestosAdicionales10)
    ) AS unpvt (
        TipoImpuesto, 
        TasaImpuestoAdicional, 
        MontoImpuestoSelectivoConsumoEspecifico, 
        MontoImpuestoSelectivoConsumoAdvalorem, 
        OtrosImpuestosAdicionales
    )
)
SELECT 
    u.*, 
    COALESCE(tia.tipoimpuesto + ' - ' + tia.descricion, 'No encontrado') AS TipoImpuestoL
FROM Unpivoted u
LEFT JOIN TipoImpuestoAdicional tia ON u.TipoImpuesto = tia.codigo
WHERE u.TipoImpuesto IS NOT NULL AND u.TipoImpuesto <> 0;
