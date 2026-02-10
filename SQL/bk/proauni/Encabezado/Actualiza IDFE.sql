update  transa01   set idfe = '02' WHERE
  (tipo IN ('33', '34'))
  AND (ncf IS NOT NULL)
  AND (ncf <> '')
  AND (EstadoFiscal IS NOT NULL)