SELECT
    td.numero,
    td.fecha,
    td.tipo,
    tr.RNCEmisor,
    tr.ncf,
    COALESCE(tr.tasa, 1.00) AS tasa,
    td.itbis,
    e.itbisenprecio AS IndicadorMontoGravado,
    (
        CASE
            WHEN e.itbisenprecio = 0 THEN SUM(
                CASE
                    WHEN td.itbis <> 0 THEN (
                        CASE
                            WHEN COALESCE(tr.tasa, 1.00) = 1 THEN td.monto1 * 1
                            ELSE td.monto1 * tr.tasa
                        END
                    )
                    ELSE 0.00
                END
            )
            WHEN e.itbisenprecio = 1 THEN SUM(
                CASE
                    WHEN td.itbis <> 0 THEN (
                        CASE
                            WHEN COALESCE(tr.tasa, 1.00) = 1 THEN td.monto1 * 1
                            ELSE td.monto1 * tr.tasa
                        END
                    )
                    ELSE 0.00
                END
            ) - SUM(
                CASE
                    WHEN COALESCE(tr.tasa, 1.00) = 1 THEN td.montoitbis * 1
                    ELSE td.montoitbis * tr.tasa
                END
            )
        END
    ) AS MontoGravadoTotal,
    (
        CASE
            WHEN e.itbisenprecio = 0
            AND td.itbis = 18 THEN SUM(
                CASE
                    WHEN td.itbis = 18 THEN (
                        CASE
                            WHEN COALESCE(tr.tasa, 1.00) = 1 THEN td.monto1 * 1
                            ELSE td.monto1 * tr.tasa
                        END
                    )
                    ELSE 0.00
                END
            )
            WHEN e.itbisenprecio = 1
            AND td.itbis = 18 THEN SUM(
                CASE
                    WHEN td.itbis = 18 THEN (
                        CASE
                            WHEN COALESCE(tr.tasa, 1.00) = 1 THEN td.monto1 * 1
                            ELSE td.monto1 * tr.tasa
                        END
                    )
                    ELSE 0.00
                END
            ) - SUM(
                CASE
                    WHEN COALESCE(tr.tasa, 1.00) = 1 THEN td.montoitbis * 1
                    ELSE td.montoitbis * tr.tasa
                END
            )
            ELSE 0.00
        END
    ) AS MontoGravadoI1,
    (
        CASE
            WHEN e.itbisenprecio = 0
            AND td.itbis = 16 THEN SUM(
                CASE
                    WHEN td.itbis = 16 THEN (
                        CASE
                            WHEN COALESCE(tr.tasa, 1.00) = 1 THEN td.monto1 * 1
                            ELSE td.monto1 * tr.tasa
                        END
                    )
                    ELSE 0.00
                END
            )
            WHEN e.itbisenprecio = 1
            AND td.itbis = 16 THEN SUM(
                CASE
                    WHEN td.itbis = 16 THEN (
                        CASE
                            WHEN COALESCE(tr.tasa, 1.00) = 1 THEN td.monto1 * 1
                            ELSE td.monto1 * tr.tasa
                        END
                    )
                    ELSE 0.00
                END
            ) - SUM(
                CASE
                    WHEN COALESCE(tr.tasa, 1.00) = 1 THEN td.montoitbis * 1
                    ELSE td.montoitbis * tr.tasa
                END
            )
            ELSE 0.00
        END
    ) AS MontoGravadoI2,
    SUM(
        CASE
            WHEN td.itbis = 0 THEN 0.00
            ELSE 0.00
        END
    ) AS MontoGravadoI3,
    SUM(
        CASE
            WHEN td.itbis = 0 THEN (
                CASE
                    WHEN COALESCE(tr.tasa, 1.00) = 1 THEN td.monto1 * COALESCE(tr.tasa, 1.00)
                    ELSE td.monto1 * tr.tasa
                END
            )
            ELSE NULL
        END
    ) AS MontoExento,
    MAX(
        CASE
            WHEN td.itbis = 18 THEN td.itbis
            ELSE NULL
        END
    ) AS ITBIS1,
    MAX(
        CASE
            WHEN td.itbis = 16 THEN td.itbis
            ELSE NULL
        END
    ) AS ITBIS2,
    MAX(
        CASE
            WHEN td.itbis = 0 THEN td.itbis
            ELSE NULL
        END
    ) AS ITBIS3,
    SUM(
        (
            CASE
                WHEN COALESCE(tr.tasa, 1) = 1 THEN td.montoitbis * COALESCE(tr.tasa, 1)
                ELSE td.montoitbis * tr.tasa
            END
        )
    ) AS TotalITBIS,
    SUM(
        CASE
            WHEN td.itbis = 18 THEN td.montoitbis * COALESCE(tr.tasa, 1)
            ELSE NULL
        END
    ) AS TotalITBIS1,
    SUM(
        CASE
            WHEN td.itbis = 16 THEN td.montoitbis * COALESCE(tr.tasa, 1)
            ELSE NULL
        END
    ) AS TotalITBIS2,
    SUM(
        CASE
            WHEN td.itbis = 0 THEN 0
            ELSE NULL
        END
    ) AS TotalITBIS3,
    MAX(
        CASE
            WHEN td.itbis = 18 THEN 1
            ELSE 0
        END
    ) AS IndicadorMontoGRabadoI18,
    MAX(
        CASE
            WHEN td.itbis = 16 THEN 1
            ELSE 0
        END
    ) AS IndicadorMontoGRabadoI16,
    MAX(
        CASE
            WHEN td.itbis = 0 THEN 1
            ELSE 0
        END
    ) AS IndicadorMontoGRabadoI0,
    SUM(
        CASE
            WHEN td.itbis <> 0 THEN (
                CASE
                    WHEN COALESCE(tr.tasa, 1.00) = 1 THEN 1
                    ELSE td.monto1
                END
            )
            ELSE 0.00
        END
    ) AS MontoGravadoTotalOtraMoneda,
    SUM(
        CASE
            WHEN td.itbis = 18 THEN (
                CASE
                    WHEN COALESCE(tr.tasa, 1.00) = 1 THEN 1
                    ELSE td.monto1
                END
            )
            ELSE 0.00
        END
    ) AS MontoGravadoI1OtraMoneda,
    SUM(
        CASE
            WHEN td.itbis = 16 THEN (
                CASE
                    WHEN COALESCE(tr.tasa, 1.00) = 1 THEN 1
                    ELSE td.monto1
                END
            )
            ELSE 0.00
        END
    ) AS MontoGravadoI2OtraMoneda,
    SUM(
        CASE
            WHEN td.itbis = 0 THEN 0
            ELSE 0.00
        END
    ) AS MontoGravadoI3OtraMoneda,
    SUM(
        CASE
            WHEN td.itbis = 0 THEN (
                CASE
                    WHEN COALESCE(tr.tasa, 0.00) = 0 THEN 0
                    ELSE td.monto1
                END
            )
            ELSE 0.00
        END
    ) AS MontoExentoOtraMoneda,
    SUM(
        (
            CASE
                WHEN COALESCE(tr.tasa, 1.00) = 1 THEN 0
                ELSE td.montoitbis
            END
        )
    ) AS TotalITBISOtraMoneda,
    SUM(
        CASE
            WHEN td.itbis = 18 THEN (
                CASE
                    WHEN COALESCE(tr.tasa, 1.00) = 1 THEN 0
                    ELSE td.montoitbis
                END
            )
            ELSE 0.00
        END
    ) AS TotalITBIS1OtraMoneda,
    SUM(
        CASE
            WHEN td.itbis = 16 THEN (
                CASE
                    WHEN COALESCE(tr.tasa, 1.00) = 1 THEN 0
                    ELSE td.montoitbis
                END
            )
            ELSE 0.00
        END
    ) AS TotalITBIS2OtraMoneda,
    SUM(
        CASE
            WHEN td.itbis = 0 THEN 0
            ELSE 0.00
        END
    ) AS TotalITBIS3OtraMoneda
FROM
    dbo.tradetalle AS td
    LEFT OUTER JOIN dbo.Transa01 AS tr ON tr.numero = td.numero
    AND tr.tipo = td.tipo
    LEFT OUTER JOIN empresa as e on e.rnc = tr.RNCEmisor
WHERE
    (tr.tipo IN ('03', '04', '33', '34', '17'))
    AND (tr.ncf IS NOT NULL)
    AND (tr.ncf <> '')
    AND (tr.EstadoFiscal IS NOT NULL)
    and td.numero = 'A00000063773'
GROUP BY
    td.numero,
    td.fecha,
    td.tipo,
    tr.RNCEmisor,
    tr.ncf,
    COALESCE(tr.tasa, 1.00),
    td.itbis,
    e.itbisenprecio