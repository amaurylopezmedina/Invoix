SELECT
  NumeroFacturaInterna,
  SUBSTRING(eNCF, 1, 1) AS TipoECFL,
  RNCEmisor,
  [TipoeCF],
  [eNCF],
  [FormaPago1] AS FormaPago,
  (
    SELECT
      TOP 1 descrip
    FROM
      formapago fp
    WHERE
      e.FormaPago1 = fp.Formapago
  ) AS FormaPagoL,
  [MontoPago1] AS MontoPago,
  (
    CASE
      WHEN TipoCambio IS NULL THEN 1
      WHEN TipoCambio = 0 THEN 1
      ELSE TipoCambio
    END
  ) AS TipoCambio
FROM
  [FEEncabezado] E
WHERE
  [FormaPago1] IS NOT NULL
UNION ALL
SELECT
  NumeroFacturaInterna,
  SUBSTRING(eNCF, 1, 1) AS TipoECFL,
  RNCEmisor,
  [TipoeCF],
  [eNCF],
  [FormaPago2],
  (
    SELECT
      TOP 1 descrip
    FROM
      formapago fp
    WHERE
      e.FormaPago2 = fp.Formapago
  ),
  [MontoPago2],
  (
    CASE
      WHEN TipoCambio IS NULL THEN 1
      WHEN TipoCambio = 0 THEN 1
      ELSE TipoCambio
    END
  ) AS TipoCambio
FROM
  [FEEncabezado] e
WHERE
  [FormaPago2] IS NOT NULL
UNION ALL
SELECT
  NumeroFacturaInterna,
  SUBSTRING(eNCF, 1, 1) AS TipoECFL,
  RNCEmisor,
  [TipoeCF],
  [eNCF],
  [FormaPago3],
  (
    SELECT
      TOP 1 descrip
    FROM
      formapago fp
    WHERE
      e.FormaPago3 = fp.Formapago
  ),
  [MontoPago3],
  (
    CASE
      WHEN TipoCambio IS NULL THEN 1
      WHEN TipoCambio = 0 THEN 1
      ELSE TipoCambio
    END
  ) AS TipoCambio
FROM
  [FEEncabezado] e
WHERE
  [FormaPago3] IS NOT NULL
UNION ALL
SELECT
  NumeroFacturaInterna,
  SUBSTRING(eNCF, 1, 1) AS TipoECFL,
  RNCEmisor,
  [TipoeCF],
  [eNCF],
  [FormaPago4],
  (
    SELECT
      TOP 1 descrip
    FROM
      formapago fp
    WHERE
      e.FormaPago4 = fp.Formapago
  ),
  [MontoPago4],
  (
    CASE
      WHEN TipoCambio IS NULL THEN 1
      WHEN TipoCambio = 0 THEN 1
      ELSE TipoCambio
    END
  ) AS TipoCambio
FROM
  [FEEncabezado] e
WHERE
  [FormaPago4] IS NOT NULL
UNION ALL
SELECT
  NumeroFacturaInterna,
  SUBSTRING(eNCF, 1, 1) AS TipoECFL,
  RNCEmisor,
  [TipoeCF],
  [eNCF],
  [FormaPago5],
  (
    SELECT
      TOP 1 descrip
    FROM
      formapago fp
    WHERE
      e.FormaPago5 = fp.Formapago
  ),
  [MontoPago5],
  (
    CASE
      WHEN TipoCambio IS NULL THEN 1
      WHEN TipoCambio = 0 THEN 1
      ELSE TipoCambio
    END
  ) AS TipoCambio
FROM
  [FEEncabezado] e
WHERE
  [FormaPago5] IS NOT NULL
UNION ALL
SELECT
  NumeroFacturaInterna,
  SUBSTRING(eNCF, 1, 1) AS TipoECFL,
  RNCEmisor,
  [TipoeCF],
  [eNCF],
  [FormaPago6],
  (
    SELECT
      TOP 1 descrip
    FROM
      formapago fp
    WHERE
      e.FormaPago6 = fp.Formapago
  ),
  [MontoPago6],
  (
    CASE
      WHEN TipoCambio IS NULL THEN 1
      WHEN TipoCambio = 0 THEN 1
      ELSE TipoCambio
    END
  ) AS TipoCambio
FROM
  [FEEncabezado] e
WHERE
  [FormaPago6] IS NOT NULL
UNION ALL
SELECT
  NumeroFacturaInterna,
  SUBSTRING(eNCF, 1, 1) AS TipoECFL,
  RNCEmisor,
  [TipoeCF],
  [eNCF],
  [FormaPago7],
  (
    SELECT
      TOP 1 descrip
    FROM
      formapago fp
    WHERE
      e.FormaPago7 = fp.Formapago
  ),
  [MontoPago7],
  (
    CASE
      WHEN TipoCambio IS NULL THEN 1
      WHEN TipoCambio = 0 THEN 1
      ELSE TipoCambio
    END
  ) AS TipoCambio
FROM
  [FEEncabezado] e
WHERE
  [FormaPago7] IS NOT NULL
