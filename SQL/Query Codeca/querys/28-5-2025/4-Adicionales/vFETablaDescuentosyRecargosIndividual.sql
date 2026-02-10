CREATE OR ALTER VIEW vFETablaDescuentosyRecargos AS
WITH Unpivoted AS (
    SELECT 
        NumeroFacturaInterna,
        TipoECFL,
        RNCEmisor,
        TipoeCF,
        eNCF,
        NumeroLineaDoR,
        TipoAjuste,
        IndicadorNorma1007,
        DescripcionDescuentooRecargo,
        TipoValor,  -- $ o %
        ValorDescuentooRecargo,
        MontoDescuentooRecargo,
        MontoDescuentooRecargoOtraMoneda,
        IndicadorFacturacionDescuentooRecargo
    FROM vFEEncabezado
    CROSS APPLY (
        VALUES
            (NumeroLineaDoR1, TipoAjuste1, IndicadorNorma10071, DescripcionDescuentooRecargo1, TipoValor1, ValorDescuentooRecargo1, MontoDescuentooRecargo1, MontoDescuentooRecargoOtraMoneda1, IndicadorFacturacionDescuentooRecargo1),
            (NumeroLineaDoR2, TipoAjuste2, IndicadorNorma10072, DescripcionDescuentooRecargo2, TipoValor2, ValorDescuentooRecargo2, MontoDescuentooRecargo2, MontoDescuentooRecargoOtraMoneda2, IndicadorFacturacionDescuentooRecargo2),
            (NumeroLineaDoR3, TipoAjuste3, IndicadorNorma10073, DescripcionDescuentooRecargo3, TipoValor3, ValorDescuentooRecargo3, MontoDescuentooRecargo3, MontoDescuentooRecargoOtraMoneda3, IndicadorFacturacionDescuentooRecargo3),
            (NumeroLineaDoR4, TipoAjuste4, IndicadorNorma10074, DescripcionDescuentooRecargo4, TipoValor4, ValorDescuentooRecargo4, MontoDescuentooRecargo4, MontoDescuentooRecargoOtraMoneda4, IndicadorFacturacionDescuentooRecargo4),
            (NumeroLineaDoR5, TipoAjuste5, IndicadorNorma10075, DescripcionDescuentooRecargo5, TipoValor5, ValorDescuentooRecargo5, MontoDescuentooRecargo5, MontoDescuentooRecargoOtraMoneda5, IndicadorFacturacionDescuentooRecargo5),
            (NumeroLineaDoR6, TipoAjuste6, IndicadorNorma10076, DescripcionDescuentooRecargo6, TipoValor6, ValorDescuentooRecargo6, MontoDescuentooRecargo6, MontoDescuentooRecargoOtraMoneda6, IndicadorFacturacionDescuentooRecargo6),
            (NumeroLineaDoR7, TipoAjuste7, IndicadorNorma10077, DescripcionDescuentooRecargo7, TipoValor7, ValorDescuentooRecargo7, MontoDescuentooRecargo7, MontoDescuentooRecargoOtraMoneda7, IndicadorFacturacionDescuentooRecargo7),
            (NumeroLineaDoR8, TipoAjuste8, IndicadorNorma10078, DescripcionDescuentooRecargo8, TipoValor8, ValorDescuentooRecargo8, MontoDescuentooRecargo8, MontoDescuentooRecargoOtraMoneda8, IndicadorFacturacionDescuentooRecargo8),
            (NumeroLineaDoR9, TipoAjuste9, IndicadorNorma10079, DescripcionDescuentooRecargo9, TipoValor9, ValorDescuentooRecargo9, MontoDescuentooRecargo9, MontoDescuentooRecargoOtraMoneda9, IndicadorFacturacionDescuentooRecargo9),
            (NumeroLineaDoR10, TipoAjuste10, IndicadorNorma100710, DescripcionDescuentooRecargo10, TipoValor10, ValorDescuentooRecargo10, MontoDescuentooRecargo10, MontoDescuentooRecargoOtraMoneda10, IndicadorFacturacionDescuentooRecargo10),
            (NumeroLineaDoR11, TipoAjuste11, IndicadorNorma100711, DescripcionDescuentooRecargo11, TipoValor11, ValorDescuentooRecargo11, MontoDescuentooRecargo11, MontoDescuentooRecargoOtraMoneda11, IndicadorFacturacionDescuentooRecargo11),
            (NumeroLineaDoR12, TipoAjuste12, IndicadorNorma100712, DescripcionDescuentooRecargo12, TipoValor12, ValorDescuentooRecargo12, MontoDescuentooRecargo12, MontoDescuentooRecargoOtraMoneda12, IndicadorFacturacionDescuentooRecargo12),
            (NumeroLineaDoR13, TipoAjuste13, IndicadorNorma100713, DescripcionDescuentooRecargo13, TipoValor13, ValorDescuentooRecargo13, MontoDescuentooRecargo13, MontoDescuentooRecargoOtraMoneda13, IndicadorFacturacionDescuentooRecargo13),
            (NumeroLineaDoR14, TipoAjuste14, IndicadorNorma100714, DescripcionDescuentooRecargo14, TipoValor14, ValorDescuentooRecargo14, MontoDescuentooRecargo14, MontoDescuentooRecargoOtraMoneda14, IndicadorFacturacionDescuentooRecargo14),
            (NumeroLineaDoR15, TipoAjuste15, IndicadorNorma100715, DescripcionDescuentooRecargo15, TipoValor15, ValorDescuentooRecargo15, MontoDescuentooRecargo15, MontoDescuentooRecargoOtraMoneda15, IndicadorFacturacionDescuentooRecargo15),
            (NumeroLineaDoR16, TipoAjuste16, IndicadorNorma100716, DescripcionDescuentooRecargo16, TipoValor16, ValorDescuentooRecargo16, MontoDescuentooRecargo16, MontoDescuentooRecargoOtraMoneda16, IndicadorFacturacionDescuentooRecargo16),
            (NumeroLineaDoR17, TipoAjuste17, IndicadorNorma100717, DescripcionDescuentooRecargo17, TipoValor17, ValorDescuentooRecargo17, MontoDescuentooRecargo17, MontoDescuentooRecargoOtraMoneda17, IndicadorFacturacionDescuentooRecargo17),
            (NumeroLineaDoR18, TipoAjuste18, IndicadorNorma100718, DescripcionDescuentooRecargo18, TipoValor18, ValorDescuentooRecargo18, MontoDescuentooRecargo18, MontoDescuentooRecargoOtraMoneda18, IndicadorFacturacionDescuentooRecargo18),
            (NumeroLineaDoR19, TipoAjuste19, IndicadorNorma100719, DescripcionDescuentooRecargo19, TipoValor19, ValorDescuentooRecargo19, MontoDescuentooRecargo19, MontoDescuentooRecargoOtraMoneda19, IndicadorFacturacionDescuentooRecargo19),
            (NumeroLineaDoR20, TipoAjuste20, IndicadorNorma100720, DescripcionDescuentooRecargo20, TipoValor20, ValorDescuentooRecargo20, MontoDescuentooRecargo20, MontoDescuentooRecargoOtraMoneda20, IndicadorFacturacionDescuentooRecargo20)
    ) AS unpvt (
        NumeroLineaDoR, TipoAjuste, IndicadorNorma1007, DescripcionDescuentooRecargo, TipoValor, ValorDescuentooRecargo, MontoDescuentooRecargo, MontoDescuentooRecargoOtraMoneda, IndicadorFacturacionDescuentooRecargo
    )
)
SELECT * FROM Unpivoted WHERE NumeroLineaDoR IS NOT NULL AND NumeroLineaDoR <> '';
